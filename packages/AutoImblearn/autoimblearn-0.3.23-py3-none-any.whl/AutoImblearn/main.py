import argparse
import os.path
import warnings
import io

import joblib

from .core.runpipe import RunPipe
from .core.autoimblearn import AutoImblearn
import logging

from .processing.utils import ArgsNamespace

warnings.filterwarnings("ignore")


class AutoImblearnTraining:
    def __init__(self,
                dataset,      # Dataset name
                target_name,  # Set the name of the prediction target

                # Model parameters
                T_model,      # Traditional models
                repeat,

                # Pre-Processing
                aggregation,
                missing,      # Handle null values

                # K-Fold
                n_splits,     # Number of split in for K-fold

                # Resample related
                infor_method, # Choose how to handle AUDM
                resampling,
                resample_method,
                samratio,     # target sample ratio

                # Feature Importance
                feature_importance,   # Which model to use

                # GridSearchCV
                grid,         # Use Grid search to find best hyper-parameter

                # top k feature
                top_k,        # The number of features to keep

                # Auto-Imblearn related
                train_ratio,  # Only use certain ratio of dataset
                metric,       # Determine the metric
                rerun,        # Re-run the best pipeline found with 100% data
                exhaustive,   # run exhaustive search instead of AutoImblearn
                host_data_root = None,  # the path that stores the data folder root on the host
                container_data_root = None, # the path that stores the data folder path in the container
                component_filters=None,  # Optional allowlists for model families
                event_column=None,  # Survival event/status column
                time_column=None,  # Survival time-to-event column
                pipeline_type=None,  # Optional pipeline type from UI (e.g., survival_classification)
                ):
        self.args = ArgsNamespace(
            dataset=dataset,
            target_name=target_name,
            event_column=event_column,
            time_column=time_column,
            T_model=T_model,
            repeat=repeat,
            aggregation=aggregation,
            missing=missing,
            n_splits=n_splits,
            infor_method=infor_method,
            resampling=resampling,
            resample_method=resample_method,
            samratio=samratio,
            feature_importance=feature_importance,
            grid=grid,
            top_k=top_k,
            train_ratio=train_ratio,
            metric=metric,
            rerun=rerun,
            exhaustive=exhaustive,
            host_data_root=host_data_root,
            container_data_root=container_data_root,
            pipeline_type=pipeline_type,
        )
        if not self.args.host_data_root:
            raise ValueError("host_data_root is required for AutoImblearnTraining")
        if not self.args.container_data_root:
            raise ValueError("container_data_root is required for AutoImblearnTraining")
        self.component_filters = component_filters or {}

        data_root = self.args.container_data_root
        self.model_dir = os.path.join(data_root, "interim", self.args.dataset, "saved_models")
        os.makedirs(self.model_dir, exist_ok=True)
        self.model_path = os.path.join(self.model_dir, "autoimblearn.pkl")

        # Save the result
        self.result = None   # save the final result from training
        self.run_pipe = None  # set during fit
        self.saver = None     # set during fit

    @staticmethod
    def _max_score_from_results(saved_result):
        """Recursively extract maximum score from nested result dict."""
        if saved_result is None:
            return None
        if isinstance(saved_result, dict):
            vals = []
            for v in saved_result.values():
                m = AutoImblearnTraining._max_score_from_results(v)
                if m is not None:
                    vals.append(m)
            return max(vals) if vals else None
        try:
            return float(saved_result)
        except (TypeError, ValueError):
            return None

    def fit(self):
        log_stream = io.StringIO()
        stream_handler = logging.StreamHandler(log_stream)
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        class AutoImbFilter(logging.Filter):
            def filter(self, record: logging.LogRecord) -> bool:
                # Allow AutoImblearn modules or explicitly tagged UI logs
                pathname = getattr(record, "pathname", "") or ""
                return "AutoImblearn" in pathname or getattr(record, "ui_log", False)

        stream_handler.addFilter(AutoImbFilter())

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(stream_handler)

        try:
            logging.info("-------------------------")

            for arg, value in sorted(vars(self.args).items()):
                logging.info("Argument {}: {}".format(arg, value))

            # Load the data
            run_pipe = RunPipe(args=self.args)
            run_pipe.loadData()
            self.run_pipe = run_pipe
            self.saver = run_pipe.saver

            # Run Auto-Imblearn to find best pipeline
            checked = {}
            automl = AutoImblearn(run_pipe, metric=self.args.metric)
            if self.component_filters:
                self._apply_component_filters(automl)
            automl.preflight_images()

            if self.args.exhaustive:
                logging.info("Exhaustive search...")
                automl.exhaustive_search(checked=checked, train_ratio=self.args.train_ratio)

            else:
                logging.info("Finding best pipeline...")
                best_pipe, counter, best_score = automl.find_best(checked=checked, train_ratio=self.args.train_ratio)

                logging.info(f'Final result. Best pipe: {" ".join(list(best_pipe))}, counter: {counter}, best score: {best_score}')
                if self.args.train_ratio != 1.0 and self.args.rerun:
                    # Re-run the best pipeline with whole dataset to get the output score
                    logging.info("Re-running best pipeline")
                    best_score = automl.run_best(best_pipe)

                # Fallback: if best_score is falsy/zero, derive max from saver cache
                if not best_score and run_pipe.saver:
                    alt = self._max_score_from_results(run_pipe.saver.saved_result)
                    if alt is not None:
                        best_score = alt

                logging.info(
                    f'Final result. Best pipe: {" ".join(list(best_pipe))}, counter: {counter}, best score: {best_score}')
            self.result = {'best_pipeline': best_pipe, 'counter': counter, 'best_score': best_score}
            return log_stream.getvalue()
        finally:
            root_logger.removeHandler(stream_handler)

    def _apply_component_filters(self, automl):
        """Restrict search space to UI-selected components."""
        key_map = {
            "imputers": "imputers",
            "resamplers": "resamplers",
            "classifiers": "classifiers",
            "hybrid_imbalanced_classifiers": "hybrids",
            "automls": "automls",
            "survival_resamplers": "survival_resamplers",
            "survival_models": "survival_models",
            "clustering_models": "clustering_models",
            "reduction_models": "reduction_models",
            "anomaly_models": "anomaly_models",
            "survival_unsupervised_models": "survival_unsupervised_models",
            "unsupervised_models": "unsupervised_models",
        }

        for ui_key, attr in key_map.items():
            if ui_key in self.component_filters:
                allowed = self.component_filters.get(ui_key) or []
                current = getattr(automl, attr, [])
                subset = [m for m in current if m in allowed] if allowed else []
                setattr(automl, attr, subset)
            else:
                # If the pool isn't present in the allowlist, clear it so we don't
                # search unselected model families.
                setattr(automl, attr, [])

    def predict(self):
        return self.result

    def save_model(self):
        if self.result:
            joblib.dump(self.result, self.model_path)

    def load_model(self):
        if os.path.exists(self.model_path):
            self.result = joblib.load(self.model_path)
        else:
            raise FileNotFoundError("No trained model found")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--dataset', type=str, default="nhanes.csv")
    parser.add_argument('--target', default="Status", type=str)  # Set the name of the prediction target

    #
    # Model parameters
    #
    parser.add_argument('--T_model', default="lr",
                        choices=["SVM", 'LSVM', 'lr', 'rf', 'mlp', 's2sl', 's2sLR', 'ensemble', 'ada',
                                 'bst'])  # Traditional models

    parser.add_argument('--repeat', default=0, type=int)

    #
    # Pre-Processing
    #
    parser.add_argument('--aggregation', default="binary", choices=["categorical", "binary"])

    parser.add_argument('--missing', default='median', choices=['median', 'mean', 'dropna', 'knn', 'ii', 'gain', 'MIRACLE', 'MIWAE'],
                        type=str)  # Handle null values

    # K-Fold
    parser.add_argument('--n_splits', default=10, type=int)  # Number of split in for K-fold

    # Resample related
    parser.add_argument('--infor_method', default='normal', choices=['normal', 'nothing'])  # Choose how to handle AUDM

    parser.add_argument('--resampling', default=False, action="store_true")
    parser.add_argument('--resample_method', default="under",
                        choices=['under', 'over', 'combined', 'herding', 's2sl_mwmote', 'MWMOTE', "smote"])
    parser.add_argument('--samratio', default=0.4, type=float)  # target sample ratio

    # Feature Importance
    parser.add_argument('--feature_importance', default='NA', choices=['NA', 'lime', 'shap'],
                        type=str)  # Which model to use

    # GridSearchCV
    parser.add_argument('--grid', default=False, action="store_true")  # Use Grid search to find best hyper-parameter

    # top k feature
    parser.add_argument('--top_k', default=-1, type=int)  # The number of features to keep

    # Auto-Imblearn related
    parser.add_argument('--train_ratio', default=1.0, type=float)  # Only use certain ratio of dataset
    parser.add_argument('--metric', default='auroc', choices=['auroc', 'macro_f1'], type=str)  # Determine the metric
    # parser.add_argument('--rerun', default=False, action="store_true")  # Re-run the best pipeline found with 100% data
    parser.add_argument('--rerun', default=False, action="store_true")  # Re-run the best pipeline found with 100% data
    parser.add_argument('--exhaustive', default=False, action="store_true") # run exhaustive search instead of AutoImblearn

    args = parser.parse_args()

    logging.info("-------------------------")

    for arg, value in sorted(vars(args).items()):
        logging.info("Argument {}: {}".format(arg, value))

    # Load the data
    run_pipe = RunPipe(args=args)
    run_pipe.loadData()

    # Run Auto-Imblearn to find best pipeline
    checked = {}
    automl = AutoImblearn(run_pipe, metric=args.metric)

    if args.exhaustive:
        print("exhaustive search")
        automl.exhaustive_search(checked=checked, train_ratio=args.train_ratio)

    else:
        best_pipe, counter, best_score = automl.find_best(checked=checked, train_ratio=args.train_ratio)

        print("Final result:", best_pipe, args.metric, counter, end=" ")
        if args.train_ratio != 1.0 and args.rerun:
            # Re-run the best pipeline with whole dataset to get the output score
            print("Re-running best pipeline")
            best_score = automl.run_best(best_pipe)

        print(best_score)
        best_pipe = list(best_pipe)
        logging.info("Final result. Best pipe: {}, {}, {}, counter: {}, best score: {}".format(best_pipe[0], best_pipe[1],
                                                                                               best_pipe[2], counter,
                                                                                               best_score))
