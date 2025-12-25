import logging
import os
import pickle

import pandas as pd

from hyperimpute.plugins.imputers import Imputers, ImputerPlugin
from AutoImblearn.components.api import BaseTransformerAPI

# imps = {
#     "gain": lambda **kw: RunHyperImpute(model="gain", **kw),
#     "MIRACLE": lambda **kw: RunHyperImpute(model="MIRACLE", **kw),
#     "MIWAE": lambda **kw: RunHyperImpute(model="MIWAE", **kw),
# }
# imps = {
#     "MIWAE": Imputers().get(self.method.lower(), random_state=42, batch_size = 128),
# }

class RunHyperImputerAPI(BaseTransformerAPI):
    def __init__(self):
        super().__init__(__name__)

        self.result = None
        self.dict_types = None  # Store column dtypes
        self.param_space = {
            "miwae": {
                "random_state": {
                    "type": "int", "min": 0, "max": 10000, "default": 42
                },
                "batch_size": {
                    "type": "int", "min": 32, "max": 512, "default": 128
                },
                "epochs": {
                    "type": "int", "min": 10, "max": 500, "default": 50
                },
                "latent_dim": {
                    "type": "int", "min": 4, "max": 64, "default": 16
                },
                "lr": {
                    "type": "float", "min": 1e-5, "max": 1e-2, "default": 1e-3, "log_scale": True
                },
            },
            "miracle": {
                "n_components": {
                    "type": "int", "min": 2, "max": 100, "default": 10
                },
                "tol": {
                    "type": "float", "min": 1e-6, "max": 1e-2, "default": 1e-3, "log_scale": True
                },
                "max_iter": {
                    "type": "int", "min": 50, "max": 1000, "default": 200
                },
            },
            "gain": {
                "random_state": {
                    "type": "int", "min": 0, "max": 10000, "default": 0
                },
                "batch_size": {
                    "type": "int", "min": 32, "max": 512, "default": 128
                },
                "epochs": {
                    "type": "int", "min": 10, "max": 500, "default": 100
                },
                "hint_rate": {
                    "type": "float", "min": 0.1, "max": 1.0, "default": 0.9
                },
                "alpha": {
                    "type": "int", "min": 1, "max": 200, "default": 10
                },
            },
        }

    def get_hyperparameter_search_space(self):
        return self.param_space

    def _validate_kwargs(self, name: str, kwargs: dict):
        allowed = set(self.param_space[name].keys())
        unknown = set(kwargs) - allowed
        if unknown:
            raise ValueError(
                f"Unsupported parameters for '{name}': {sorted(unknown)}. "
                f"Allowed: {sorted(allowed)}"
            )


    def fit(self, params, *args, **kwargs):
        # Get parameters
        model_name = params.model
        imputer_kwargs = params.imputer_kwargs
        categorical_columns = params.categorical_columns

        # Handle both data formats: full dataset (string) or just X_train
        if 'data' in kwargs:
            # Old format: full dataset as DataFrame
            data = kwargs.get('data')
            X_train = data
        elif 'X_train' in kwargs:
            # New format: X_train only (no y needed - imputation is unsupervised)
            X_train = kwargs.get('X_train')
        else:
            raise ValueError("No data passed in (expected 'data' or 'X_train')")

        # Store metadata
        self.dict_types = dict(X_train.dtypes)
        self.columns = X_train.columns

        # Fit the imputer on training data and transform it
        model_name = model_name.lower()
        imputer = Imputers().get(model_name, **imputer_kwargs)
        X_train_imputed = imputer.fit_transform(X_train)

        # Convert to DataFrame with previous column names and dtypes
        if not isinstance(X_train_imputed, pd.DataFrame):
            X_train_imputed = pd.DataFrame(X_train_imputed, columns=X_train.columns)
        else:
            X_train_imputed.columns = X_train.columns
        X_train_imputed = X_train_imputed.astype(self.dict_types)

        # Store transformed training data
        self.result = X_train_imputed

        logging.info("finished training (fit_transform on X_train)")

        # RETURN the fitted model (sklearn pattern!)
        # Base class will assign it to self.fitted_model and save to disk
        return imputer

    def _save_fitted_model(self, params):
        """
        Save the trained HyperImpute GainImputer to disk using its native API.

        This replaces the default pickle-based method to ensure compatibility
        with dynamically loaded plugin models (like GainPlugin).
        """
        if self.fitted_model is None:
            logging.warning("No fitted_model to save. Skipping persistence.")
            return

        dataset_name = params.dataset_name
        model_dir = os.path.join("/data/interim", dataset_name)
        os.makedirs(model_dir, exist_ok=True)

        model_path = os.path.join(model_dir, "fitted_transformer.pkl")

        try:
            # Use HyperImpute's safe serialization
            if hasattr(self.fitted_model, "save"):
                self.fitted_model.save(model_path)
                logging.info(f"✓ Saved GainImputer model using .save() to {model_path}")
            else:
                # Fallback for non-hyperimpute models
                import pickle
                with open(model_path, "wb") as f:
                    pickle.dump(self.fitted_model, f)
                logging.info(f"✓ Saved fallback model via pickle to {model_path}")

            # Save metadata
            metadata = {
                "columns": getattr(self, "columns", None),
                "model_class": type(self.fitted_model).__name__,
                "framework": "hyperimpute",
            }
            metadata_path = os.path.join(model_dir, "fitted_transformer_metadata.pkl")
            import pickle
            with open(metadata_path, "wb") as f:
                pickle.dump(metadata, f)
            logging.info(f"✓ Saved metadata to {metadata_path}")

        except Exception as e:
            logging.exception(f"⚠️ Failed to save fitted GainImputer model: {e}")

    def _load_fitted_model(self, params):
        """
        Load the fitted model from disk if it exists.

        Automatically detects HyperImpute-based imputers (like GainImputer)
        and loads them using their native .load() API. Falls back to pickle
        for sklearn or custom transformers.

        Called automatically before transform() if fitted_model is None.
        """
        dataset_name = params.dataset_name
        base_dir = os.path.join("/data/interim", dataset_name)
        model_path = os.path.join(base_dir, "fitted_transformer.pkl")
        metadata_path = os.path.join(base_dir, "fitted_transformer_metadata.pkl")

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Fitted model not found at {model_path}. "
                f"Make sure fit() was called before transform()."
            )

        try:
            # Try HyperImpute native load
            if ImputerPlugin.can_load(model_path):
                self.fitted_model = ImputerPlugin.load(model_path)
                logging.info(f"✓ Loaded HyperImpute model via ImputerPlugin.load() from {model_path}")
            else:
                # Fallback: standard pickle
                with open(model_path, "rb") as f:
                    self.fitted_model = pickle.load(f)
                logging.info(f"✓ Loaded pickled model from {model_path}")

            # Load metadata (columns, model_class, etc.)
            if os.path.exists(metadata_path):
                with open(metadata_path, "rb") as f:
                    metadata = pickle.load(f)
                    self.columns = metadata.get("columns", None)
                    model_class = metadata.get("model_class", "unknown")
                logging.info(f"✓ Loaded metadata for {model_class} from {metadata_path}")

        except Exception as e:
            logging.exception(f"⚠️ Failed to load fitted model from {model_path}: {e}")
            raise

    def transform(self, *args, **kwargs):
        # If data is provided, transform it; otherwise return cached result
        if 'data' in kwargs:
            data = kwargs.get('data')

            # Base class handles loading from disk if needed
            # We just use self.fitted_model directly (sklearn pattern!)
            imp_out = self.fitted_model.transform(data)

            # Change back to DataFrame with previous column names
            if not isinstance(imp_out, pd.DataFrame):
                imp_out = pd.DataFrame(imp_out, columns=self.columns)
            else:
                imp_out.columns = self.columns

            # Change back to old column dtypes
            imp_out = imp_out.astype(self.dict_types)

            return imp_out
        else:
            # Fallback to cached result for backward compatibility
            return self.result

RunHyperImputerAPI().run()