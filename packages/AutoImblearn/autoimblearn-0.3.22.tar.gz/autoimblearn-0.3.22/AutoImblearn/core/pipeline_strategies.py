# AutoImblearn/core/pipeline_strategies.py
"""
Pipeline execution strategies using the Strategy Pattern.

This module eliminates code duplication in runpipe.py by providing
separate strategy classes for different pipeline types.
"""

import os
import pickle
import numpy as np
import logging
import json
import hashlib
from abc import ABC, abstractmethod

from ..processing.utils import Samplar, SurvivalSamplar
from ..pipelines.customimputation import CustomImputer
from ..pipelines.customrsp import CustomResamplar
from ..pipelines.customclf import CustomClassifier
from ..pipelines.customhbd import CustomHybrid
from ..pipelines.customautoml import CustomAutoML
from ..pipelines.customsurvival import CustomSurvivalModel, CustomSurvivalResamplar
from ..pipelines.customunsupervised import CustomUnsupervisedModel
from ..pipelines.customsurvival import CustomSurvivalUnsupervisedModel


def average(lst):
    """Calculate average of a list"""
    return sum(lst) / len(lst)


class BasePipelineStrategy(ABC):
    """
    Abstract base class for pipeline execution strategies.

    Each strategy handles a specific pipeline type and encapsulates
    the logic for data loading, K-fold splitting, training, and evaluation.
    """

    def __init__(self, args, dataloader, preprocessor, saver):
        """
        Initialize the strategy.

        Args:
            args: Command-line arguments
            dataloader: DataLoader instance
            preprocessor: DataPreprocess instance
            saver: Result instance for saving/loading results
        """
        self.args = args
        self.dataloader = dataloader
        self.preprocessor = preprocessor
        self.saver = saver

    def _dataset_interim_dir(self) -> str:
        """Folder under container_data_root/interim for this dataset."""
        base = self.dataloader.get_interim_data_folder()
        dataset_dir = os.path.join(base, self.args.dataset)
        os.makedirs(dataset_dir, exist_ok=True)
        return dataset_dir

    @abstractmethod
    def validate_pipeline(self, pipe):
        """Validate that the pipeline has the correct format"""
        pass

    @abstractmethod
    def execute_fold(self, pipe, X_train, y_train, X_test, y_test):
        """Execute one fold of the pipeline"""
        pass

    def execute(self, pipe, train_ratio=1.0):
        """
        Main execution method for the pipeline strategy.

        This method:
        1. Validates the pipeline
        2. Loads and preprocesses data
        3. Applies train_ratio if needed
        4. Executes K-fold cross-validation
        5. Averages and saves results

        Args:
            pipe: Pipeline specification (list of component names)
            train_ratio: Fraction of data to use (default 1.0)

        Returns:
            Average result across all folds
        """
        # Validate pipeline format
        self.validate_pipeline(pipe)

        # Reset fold counter for this pipeline run so logs and artifact names
        # reflect the current CV loop instead of accumulating across runs.
        self.args.repeat = 0

        # Load and preprocess raw data (with missing values)
        X, y = self.preprocessor.preprocess(self.args)

        # Apply train_ratio if needed
        if train_ratio != 1.0:
            X, y = self._stratified_sample(X, y, train_ratio)

        logging.info("Data loaded and preprocessed")

        # Create K-fold splits on RAW data (before imputation)
        train_sampler = Samplar(np.array(X), np.array(y))

        results = []
        for X_train, y_train, X_test, y_test in train_sampler.apply_kfold(self.args.n_splits):
            logging.info(f"\t Fold {self.args.repeat}")

            # Execute this fold (strategy-specific logic)
            result = self.execute_fold(pipe, X_train, y_train, X_test, y_test)
            results.append(result)
            try:
                logging.info(
                    f"\t Fold {self.args.repeat} result: {result}",
                    extra={"ui_log": True, "stage": "fold", "fold": self.args.repeat},
                )
            except Exception:
                logging.info(f"\t Fold {self.args.repeat} result: {result}")

            self.args.repeat += 1

        # Average results and save
        avg_result = average(results)
        self.saver.append(pipe, avg_result)
        return avg_result

    def _stratified_sample(self, X, y, train_ratio):
        """Apply stratified sampling to reduce dataset size"""
        import pandas as pd

        data = pd.concat([X, y], axis=1)
        new_data = data.groupby('Status', group_keys=False).apply(
            lambda x: x.sample(frac=train_ratio)
        )
        new_data.sort_index(inplace=True)
        new_data.reset_index(inplace=True, drop=True)
        columns = list(new_data.columns.values)
        columns.remove("Status")
        X = new_data[columns].copy()
        y = new_data["Status"].copy()
        return X, y

    def _impute_with_caching(self, imp, X_train, y_train, X_test, y_test=None):
        """
        Perform imputation with intelligent caching.

        This method checks if cached imputation results exist for this fold.
        If so, it loads them. Otherwise, it runs imputation and caches the results.

        Args:
            imp: Imputer name (e.g., 'mean', 'knn')
            X_train: Training features
            y_train: Training labels
            X_test: Test features

        Returns:
            Tuple of (X_train_imputed, X_test_imputed)
        """
        result_file_name = f"imp_{imp}_fold{self.args.repeat}.p"
        interim_dir = self._dataset_interim_dir()
        result_file_path = os.path.join(interim_dir, result_file_name)
        result_test_file_path = result_file_path.replace('.p', '_test.p')
        meta_file_path = result_file_path + ".meta"

        def _hash_array(arr):
            arr = np.asarray(arr)
            return hashlib.sha256(arr.tobytes()).hexdigest()

        def _hash_resampler_params(resampler_name: str, params: dict) -> str:
            """Hash the resampler name + params to invalidate cache on param changes."""
            if params is None:
                params = {}
            payload = {
                "resampler": resampler_name,
                "params": params,
            }
            return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

        expected_meta = {
            "y_train_hash": _hash_array(y_train),
            "y_train_len": int(len(y_train)),
        }
        if y_test is not None:
            expected_meta.update(
                {
                    "y_test_hash": _hash_array(y_test),
                    "y_test_len": int(len(y_test)),
                }
            )

        # Check if cached imputation results exist and match the current split signature
        cache_valid = False
        if (
            os.path.exists(result_file_path)
            and os.path.exists(result_test_file_path)
            and os.path.exists(meta_file_path)
        ):
            try:
                logging.info(f"\t Loading cached imputation from {result_file_name}")
                with open(meta_file_path, "r") as mf:
                    meta = json.load(mf)
                if meta == expected_meta:
                    with open(result_file_path, "rb") as f:
                        X_train_imputed = pickle.load(f)
                    with open(result_test_file_path, "rb") as f:
                        X_test_imputed = pickle.load(f)
                    cache_valid = True
                    logging.info("\t Cached imputation loaded")
                else:
                    logging.warning("\t Cached imputation signature mismatch; recomputing.")
            except Exception as cache_err:
                logging.warning("\t Failed to load cached imputation (%s); recomputing.", cache_err)

        if not cache_valid:
            # Run imputation - results will be cached automatically
            logging.info("\t Imputation Started")
            imputer = CustomImputer(
                method=imp,
                host_data_root=self.args.host_data_root,
                dataset_name=self.args.dataset,
                result_file_path=result_file_path
            )

            # Fit on train, transform both
            X_train_imputed = imputer.fit_transform(self.args, X_train)
            X_test_imputed = imputer.transform(X_test)

            logging.info("\t Imputation Done")
            try:
                with open(meta_file_path, "w") as mf:
                    json.dump(expected_meta, mf, indent=2)
            except Exception as meta_err:
                logging.warning("\t Failed to write imputation meta: %s", meta_err)

        return X_train_imputed, X_test_imputed


class ThreeElementPipelineStrategy(BasePipelineStrategy):
    """
    Strategy for 3-element pipelines: Imputer -> Resampler -> Classifier

    Example: ['median', 'smote', 'lr']
    """

    def validate_pipeline(self, pipe):
        """Ensure pipeline has exactly 3 elements"""
        if len(pipe) != 3:
            raise ValueError(
                f"Pipeline {pipe} length is not correct, not a regular method pipeline"
            )

    def execute_fold(self, pipe, X_train, y_train, X_test, y_test):
        """
        Execute one fold of a 3-element pipeline.

        Steps:
        1. Imputation (with caching)
        2. Resampling (on training data only)
        3. Classification
        4. Prediction
        """
        imp, rsp, clf = pipe
        interim_dir = self._dataset_interim_dir()

        # Imputation level - FIT on train, TRANSFORM both train and test
        X_train_imputed, X_test_imputed = self._impute_with_caching(
            imp, X_train, y_train, X_test, y_test
        )

        # Resampling level - ONLY on training data, with caching on imputed inputs and params
        resample_file_path = os.path.join(interim_dir, f"rsp_{rsp}_fold{self.args.repeat}.p")
        resample_y_path = resample_file_path.replace(".p", "_y.p")
        resample_meta_path = resample_file_path + ".meta"

        def _hash_array(arr):
            arr = np.asarray(arr)
            return hashlib.sha256(arr.tobytes()).hexdigest()

        # Build cache signature on imputed data and resampler params
        resampler_params = {}
        if hasattr(self.args, "hyperparams") and self.args.hyperparams:
            resampler_params = self.args.hyperparams.get(rsp, {}) or {}
        resampler_signature = {
            "resampler": rsp,
            "params_hash": hashlib.sha256(json.dumps(resampler_params, sort_keys=True).encode("utf-8")).hexdigest(),
            "X_train_hash": _hash_array(X_train_imputed),
            "y_train_hash": _hash_array(y_train),
            "X_train_shape": list(np.asarray(X_train_imputed).shape),
            "y_train_shape": list(np.asarray(y_train).shape),
        }

        cache_valid = False
        if (
            os.path.exists(resample_file_path)
            and os.path.exists(resample_y_path)
            and os.path.exists(resample_meta_path)
        ):
            try:
                with open(resample_meta_path, "r") as mf:
                    meta = json.load(mf)
                if meta == resampler_signature:
                    logging.info("\t Loading cached resampling result")
                    with open(resample_file_path, "rb") as f:
                        X_train_imputed_cached = pickle.load(f)
                    with open(resample_y_path, "rb") as f:
                        y_train_cached = pickle.load(f)
                    X_train_imputed, y_train = X_train_imputed_cached, y_train_cached
                    cache_valid = True
                else:
                    logging.info("\t Resampler cache mismatch; recomputing.")
            except Exception as cache_err:
                logging.warning("\t Failed to load cached resampling (%s); recomputing.", cache_err)

        if not cache_valid:
            resamplar = CustomResamplar(
                method=rsp,
                host_data_root=self.args.host_data_root,
                dataset_name=self.args.dataset,
                result_file_path=resample_file_path,
                result_file_name=os.path.basename(resample_file_path),
                **(resampler_params or {}),
            )
            try:
                if resamplar.need_resample(y_train):
                    logging.info("\t Re-Sampling Started")
                    X_train_imputed, y_train = resamplar.fit_resample(self.args, X_train_imputed, y_train)
                    logging.info("\t Re-Sampling Done")

                    # Persist cache artifacts
                    with open(resample_file_path, "wb") as f:
                        pickle.dump(X_train_imputed, f)
                    with open(resample_y_path, "wb") as f:
                        pickle.dump(y_train, f)
                    with open(resample_meta_path, "w") as mf:
                        json.dump(resampler_signature, mf, indent=2)
            finally:
                try:
                    resamplar.cleanup()
                except Exception:
                    logging.warning("Resampler cleanup failed", exc_info=True)

        # Classification level
        logging.info(f"\t Training in fold {self.args.repeat} Start")
        clf_result_path = os.path.join(interim_dir, f"clf_{clf}_fold{self.args.repeat}.p")
        trainer = CustomClassifier(
            method=clf,
            host_data_root=self.args.host_data_root,
            metric=self.args.metric,
            dataset_name=self.args.dataset,
            result_file_path=clf_result_path,
        )
        trainer.fit(self.args, X_train_imputed, y_train)
        logging.info(f"\t Training in fold {self.args.repeat} Done")

        # Validation on imputed test data
        result = trainer.score(X_test_imputed, y_test)

        try:
            trainer.cleanup()
        except Exception:
            logging.warning("Classifier cleanup failed", exc_info=True)

        try:
            resamplar.cleanup()
        except Exception:
            logging.warning("Resampler cleanup failed", exc_info=True)

        del trainer

        return result


class HybridPipelineStrategy(BasePipelineStrategy):
    """
    Strategy for 2-element pipelines: Imputer -> Hybrid Method

    Hybrid methods combine resampling and classification in one step.
    Example: ['median', 'autosmote']
    """

    def validate_pipeline(self, pipe):
        """Ensure pipeline has exactly 2 elements"""
        if len(pipe) != 2:
            raise ValueError(
                f"Pipeline {pipe} length is not correct, not a hybrid method pipeline"
            )

    def execute_fold(self, pipe, X_train, y_train, X_test, y_test):
        """
        Execute one fold of a 2-element hybrid pipeline.

        Steps:
        1. Imputation (with caching)
        2. Hybrid method (combines resampling + classification)
        3. Prediction
        """
        imp, hbd = pipe
        interim_dir = self._dataset_interim_dir()

        # Imputation level - FIT on train, TRANSFORM both train and test
        X_train_imputed, X_test_imputed = self._impute_with_caching(
            imp, X_train, y_train, X_test, y_test
        )

        # Hybrid method (combines resampling + classification)
        logging.info(f"\t Training in fold {self.args.repeat} Start")
        hybrid_result_path = os.path.join(interim_dir, f"hybrid_{hbd}_fold{self.args.repeat}.p")

        trainer = CustomHybrid(
            method=hbd,
            host_data_root=self.args.host_data_root,
            dataset_name=self.args.dataset,
            metric=self.args.metric,
            result_file_path=hybrid_result_path,
            imputer_method=imp,
        )

        runtime_params = {}
        if hasattr(self.args, "hyperparams") and isinstance(self.args.hyperparams, dict):
            runtime_params = dict(self.args.hyperparams.get(hbd, {}) or {})

        if hbd == "autorsp":
            runtime_params.setdefault(
                "target",
                getattr(self.args, "target_name", None),
            )
            runtime_params.setdefault("metric", "macro_f1")

        try:
            trainer.fit(
                X_train=X_train_imputed,
                y_train=y_train,
                X_test=X_test_imputed,
                y_test=y_test,
                runtime_params=runtime_params or None,
            )
            logging.info(f"\t Training in fold {self.args.repeat} Done")

            trainer.predict(X_test=X_test_imputed)
            result = trainer.result
        finally:
            trainer.cleanup()

        return result


class AutoMLPipelineStrategy(BasePipelineStrategy):
    """
    Strategy for 1-element pipelines: AutoML only

    AutoML methods handle imputation, resampling, and classification internally.
    Example: ['autosklearn']

    Note: This strategy doesn't use K-fold cross-validation because
    AutoML methods typically handle cross-validation internally.
    """

    def validate_pipeline(self, pipe):
        """Ensure pipeline has exactly 1 element"""
        if len(pipe) != 1:
            raise ValueError(
                f"Pipeline {pipe} length is not correct, not a AutoML method pipeline"
            )

    def execute(self, pipe, train_ratio=1.0):
        """
        Execute AutoML pipeline (overrides base execute method).

        AutoML methods don't use K-fold cross-validation - they handle
        validation internally.
        """
        self.validate_pipeline(pipe)

        automl = pipe[0]

        # Load and preprocess data
        X, y = self.preprocessor.preprocess(self.args)

        # Fit
        logging.info(f"\t Training of {pipe} Start")
        trainer = CustomAutoML(self.args, automl)
        trainer.train(X, y)
        logging.info(f"\t Training of {pipe} Ended")

        # Predict
        logging.info(f"\t Predicting of {pipe} Start")
        result = trainer.predict()
        logging.info(f"\t Predicting of {pipe} Ended")

        self.args.repeat += 1

        self.saver.append(pipe, result)
        return result

    def execute_fold(self, pipe, X_train, y_train, X_test, y_test):
        """Not used for AutoML pipelines"""
        raise NotImplementedError("AutoML pipelines don't use fold-based execution")


class SurvivalPipelineStrategy(BasePipelineStrategy):
    """
    Strategy for 3-element survival pipelines: Imputer -> Survival Resampler -> Survival Model

    Example: ['median', 'rus', 'CPH']

    Handles survival data with structured arrays containing event indicators and times.
    """

    def validate_pipeline(self, pipe):
        """Ensure pipeline has exactly 3 elements"""
        if len(pipe) != 3:
            raise ValueError(
                f"Pipeline {pipe} length is not correct, not a survival method pipeline"
            )

    def execute(self, pipe, train_ratio=1.0):
        """
        Override execute to use SurvivalSamplar (stratified on event indicator).
        """
        self.validate_pipeline(pipe)

        # Reset fold counter per survival pipeline run for accurate logging
        self.args.repeat = 0

        X, y = self.preprocessor.preprocess(self.args)

        if train_ratio != 1.0:
            X, y = self._stratified_sample(X, y, train_ratio)

        logging.info("Data loaded and preprocessed")

        train_sampler = SurvivalSamplar(X, y)

        results = []
        for X_train, y_train, X_test, y_test in train_sampler.apply_kfold(self.args.n_splits):
            logging.info(f"\t Fold {self.args.repeat}")
            result = self.execute_fold(pipe, X_train, y_train, X_test, y_test)
            results.append(result)
            try:
                logging.info(
                    f"\t Fold {self.args.repeat} result: {result}",
                    extra={"ui_log": True, "stage": "fold", "fold": self.args.repeat},
                )
            except Exception:
                logging.info(f"\t Fold {self.args.repeat} result: {result}")
            self.args.repeat += 1

        avg_result = average(results)
        self.saver.append(pipe, avg_result)
        return avg_result

    def execute_fold(self, pipe, X_train, y_train, X_test, y_test):
        """
        Execute one fold of a 3-element survival pipeline.

        Steps:
        1. Imputation (with caching) - same as regular pipelines
        2. Survival-aware resampling (on training data only, preserves censoring)
        3. Survival model training and prediction

        Args:
            pipe: [imputer, survival_resampler, survival_model]
            X_train, y_train: Training data (y_train is structured survival array)
            X_test, y_test: Test data (y_test is structured survival array)
        """
        imp, rsp, model = pipe
        interim_dir = self._dataset_interim_dir()

        # Imputation level - FIT on train, TRANSFORM both train and test
        # Note: Imputation only works on features (X), not on survival outcomes (y)
        X_train_imputed, X_test_imputed = self._impute_with_caching(
            imp, X_train, y_train, X_test, y_test
        )

        # Store original y_train for Uno's C-index calculation
        y_train_original = y_train.copy()

        resample_file_path = os.path.join(interim_dir, f"rsp_{rsp}_fold{self.args.repeat}.p")
        resample_y_path = resample_file_path.replace(".p", "_y.p")
        resample_meta_path = resample_file_path + ".meta"

        def _hash_array(arr):
            arr = np.asarray(arr)
            return hashlib.sha256(arr.tobytes()).hexdigest()

        resampler_params = {}
        if hasattr(self.args, "hyperparams") and self.args.hyperparams:
            resampler_params = self.args.hyperparams.get(rsp, {}) or {}
        resampler_signature = {
            "resampler": rsp,
            "params_hash": hashlib.sha256(json.dumps(resampler_params, sort_keys=True).encode("utf-8")).hexdigest(),
            "X_train_hash": _hash_array(X_train_imputed),
            "y_train_hash": _hash_array(y_train),
            "X_train_shape": list(np.asarray(X_train_imputed).shape),
            "y_train_shape": list(np.asarray(y_train).shape),
        }

        cache_valid = False
        if (
            os.path.exists(resample_file_path)
            and os.path.exists(resample_y_path)
            and os.path.exists(resample_meta_path)
        ):
            try:
                with open(resample_meta_path, "r") as mf:
                    meta = json.load(mf)
                if meta == resampler_signature:
                    logging.info("\t Loading cached survival resampling result")
                    with open(resample_file_path, "rb") as f:
                        X_train_imputed_cached = pickle.load(f)
                    with open(resample_y_path, "rb") as f:
                        y_train_cached = pickle.load(f)
                    X_train_imputed, y_train = X_train_imputed_cached, y_train_cached
                    cache_valid = True
                else:
                    logging.info("\t Survival resampler cache mismatch; recomputing.")
            except Exception as cache_err:
                logging.warning("\t Failed to load cached survival resampling (%s); recomputing.", cache_err)

        if not cache_valid:
            resamplar = CustomSurvivalResamplar(
                method=rsp,
                host_data_root=self.args.host_data_root,
                result_file_path=resample_file_path,
                result_file_name=os.path.basename(resample_file_path),
                **(resampler_params or {}),
            )
            try:
                if resamplar.need_resample(y_train):
                    logging.info("\t Survival Re-Sampling Started")
                    X_train_imputed, y_train = resamplar.fit_resample(self.args, X_train_imputed, y_train)
                    logging.info("\t Survival Re-Sampling Done")

                    # Persist cache artifacts
                    with open(resample_file_path, "wb") as f:
                        pickle.dump(X_train_imputed, f)
                    with open(resample_y_path, "wb") as f:
                        pickle.dump(y_train, f)
                    with open(resample_meta_path, "w") as mf:
                        json.dump(resampler_signature, mf, indent=2)
            finally:
                try:
                    resamplar.cleanup()
                except Exception:
                    logging.warning("Survival resampler cleanup failed", exc_info=True)

        # Survival model training
        logging.info(f"\t Survival Training in fold {self.args.repeat} Start")
        trainer = CustomSurvivalModel(
            method=model,
            host_data_root=self.args.host_data_root,
            metric=self.args.metric,
        )
        try:
            trainer.fit(self.args, X_train_imputed, y_train, X_test=X_test, y_test=y_test)
            logging.info(f"\t Survival Training in fold {self.args.repeat} Done")

            # Prediction and evaluation on test data
            result = trainer.score(X_test_imputed, y_test, y_train=y_train_original)
        finally:
            try:
                trainer.cleanup()
            except Exception:
                logging.warning("Survival model cleanup failed", exc_info=True)
            del trainer

        return result


class UnsupervisedPipelineStrategy(BasePipelineStrategy):
    """
    Strategy for 2-element unsupervised pipelines: Imputer -> Unsupervised Model

    Supports clustering, dimensionality reduction, and anomaly detection.
    Example: ['median', 'kmeans'], ['knn', 'pca'], ['mean', 'isoforest']
    """

    def validate_pipeline(self, pipe):
        """Ensure pipeline has exactly 2 elements"""
        if len(pipe) != 2:
            raise ValueError(
                f"Pipeline {pipe} length is not correct, not an unsupervised pipeline"
            )

    def execute_fold(self, pipe, X_train, y_train, X_test, y_test):
        """
        Execute one fold of a 2-element unsupervised pipeline.

        Steps:
        1. Imputation (with caching)
        2. Unsupervised model training and prediction

        Note: y_train and y_test may be used for evaluation but not for training
        """
        imp, model = pipe

        # Imputation level - FIT on train, TRANSFORM both train and test
        X_train_imputed, X_test_imputed = self._impute_with_caching(
            imp, X_train, y_train, X_test, y_test
        )

        # Unsupervised model training
        logging.info(f"\t Training unsupervised model in fold {self.args.repeat} Start")
        trainer = CustomUnsupervisedModel(
            method=model,
            host_data_root=self.args.host_data_root,
            metric=self.args.metric,
        )
        trainer.fit(self.args, X_train_imputed, y_train)
        logging.info(f"\t Training unsupervised model in fold {self.args.repeat} Done")

        # Prediction and evaluation on test data
        result = trainer.score(X_test_imputed, y_test)

        del trainer

        return result


class SurvivalUnsupervisedPipelineStrategy(BasePipelineStrategy):
    """
    Strategy for 2-element survival unsupervised pipelines: Imputer -> Survival Unsupervised Model

    Supports survival clustering and risk stratification.
    Example: ['median', 'survival_tree'], ['knn', 'survival_kmeans']
    """

    def validate_pipeline(self, pipe):
        """Ensure pipeline has exactly 2 elements"""
        if len(pipe) != 2:
            raise ValueError(
                f"Pipeline {pipe} length is not correct, not a survival unsupervised pipeline"
            )

    def execute_fold(self, pipe, X_train, y_train, X_test, y_test):
        """
        Execute one fold of a 2-element survival unsupervised pipeline.

        Steps:
        1. Imputation (with caching) - same as regular pipelines
        2. Survival unsupervised model training and prediction

        Args:
            pipe: [imputer, survival_unsupervised_model]
            X_train, y_train: Training data (y_train is structured survival array)
            X_test, y_test: Test data (y_test is structured survival array)
        """
        imp, model = pipe

        # Imputation level - FIT on train, TRANSFORM both train and test
        X_train_imputed, X_test_imputed = self._impute_with_caching(
            imp, X_train, y_train, X_test, y_test
        )

        # Survival unsupervised model training
        logging.info(f"\t Training survival unsupervised model in fold {self.args.repeat} Start")
        trainer = CustomSurvivalUnsupervisedModel(
            method=model,
            host_data_root=self.args.host_data_root,
            metric=self.args.metric,
        )
        trainer.fit(self.args, X_train_imputed, y_train)
        logging.info(f"\t Training survival unsupervised model in fold {self.args.repeat} Done")

        # Prediction and evaluation on test data
        result = trainer.score(X_test_imputed, y_test)

        del trainer

        return result
