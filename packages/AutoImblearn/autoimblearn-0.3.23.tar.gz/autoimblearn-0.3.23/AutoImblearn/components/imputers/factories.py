from sklearn.impute import SimpleImputer
import pandas as pd


def stat_imputer_factory(strategy: str):
    """
    Factory generator for creating a wrapped SimpleImputer with
    dataset-aware storage metadata.

    Parameters
    ----------
    strategy : str
        The imputation strategy (e.g., "mean", "median", "most_frequent", "constant").

    Returns
    -------
    factory : callable
        A closure that can be called with keyword arguments to produce
        a WrappedImputer instance configured with storage metadata.
    """
    def factory(**kw):
        # Extract (and remove) any saving-related keyword arguments so they don't
        # get passed to SimpleImputer directly
        dataset_name = kw.pop("dataset_name", None)
        save_name    = kw.pop("save_name", None)
        save_format  = kw.pop("save_format", "csv")
        save_index   = kw.pop("save_index", False)
        _            = kw.pop("host_data_root")
        _            = kw.pop("result_file_path")


        base = SimpleImputer(strategy=strategy, **kw)

        class WrappedImputer:
            """
            A wrapper around sklearn's SimpleImputer that remembers dataset
            metadata and can reconstruct DataFrame outputs with appropriate
            columns and indices.
            """
            def __init__(self, base):
                self.base         = base
                self._cols        = None
                self._idx         = None

                self.strategy     = strategy
                self.dataset_name = dataset_name
                self.save_name    = save_name
                self.save_format  = save_format
                self.save_index   = save_index

            def fit(self, _,  X_train, y_train=None, X_test=None, y_test=None):
                """
                Fit the underlying imputer on training data.
                The first argument `_` is a placeholder (e.g., args) and ignored.
                """
                if isinstance(X_train, pd.DataFrame):
                    self._cols = X_train.columns.to_list()
                    self._idx = X_train.index
                else:
                    self._cols = None
                    self._idx = None
                return self.base.fit(X_train, y_train)

            def transform(self, X, y=None, dockerfile_dir="."):
                """
                Apply the fitted imputer to input X and return a DataFrame
                with correct column names and indices if available.
                """
                X_imp = self.base.transform(X)

                if isinstance(X, pd.DataFrame):
                    # If original input is DataFrame, keep its structure
                    return pd.DataFrame(X_imp, columns=self._cols, index=X.index)
                elif self._cols is not None:
                    # If fit saw a DataFrame but input here is ndarray, use stored structure
                    return pd.DataFrame(X_imp, columns=self._cols, index=self._idx)
                else:
                    # if never saw DF, just wrap with generic column names
                    cols = [f"x{i}" for i in range(X_imp.shape[1])]
                    return pd.DataFrame(X_imp, columns=cols)
                return X_out

            def fit_transform(self, X, y=None):
                self.fit(X, y)
                return self.transform(X)

            def __getattr__(self, name):
                """
                Delegate attribute access to the underlying base imputer,
                so this wrapper behaves like a SimpleImputer for other methods.
                """
                return getattr(self.base, name)

        return WrappedImputer(base)

    return factory

