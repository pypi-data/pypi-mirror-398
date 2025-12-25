import secrets
import time
from typing import Optional, Tuple, List

import logging
from .runpipe import RunPipe
from .pipeline_schema import PIPELINE_SCHEMAS, NODE_TYPE_TO_POOL_ATTR, normalize_pipeline_type

from ..pipelines.customimputation import imps
from ..pipelines.customclf import clfs
from ..pipelines.customrsp import rsps
from ..pipelines.customhbd import hybrid_factories
from ..pipelines.customautoml import automls
from ..pipelines.customsurvival import survival_models, survival_resamplers, survival_unsupervised_models
from ..pipelines.customunsupervised import unsupervised_models
from ..pipelines.customreduction import reduction_models
from ..pipelines.customanomaly import anomaly_models

from ..pipelines import refresh_custom_components
from ..components.hybrids import RunAutoSmote
from ..processing.utils import Result
from ..processing.selectiontree import BinaryTree
from ..components.model_filters import ModelFiltering
from ..exceptions import SearchBudgetExceededError, PipelineError
from ..pipelines.execution.image_preflight import prepare_images


class AutoImblearn:
    """ The core class that defines how to search the optimal pipeline given a dataset
    Parameters
    ----------
    run_pipe : RunPipe class
        The helper class that has two functions:
            1) handles loading, splitting the data
            2) run the pipelines and get the results

    metric : The evaluation metric defined by user to use during training and final evaluation

    Attributes
    ----------
    resamplers : The list of re-samplers available to choose from

    classifiers : The list of classifiers available to choose from

    hybrids : The list of hybrid re-sampler and classifier methods available to choose from

    imputers : The list of imputers available to choose from

    automls : The list of AutoMLs available to choose from

    run_pipe : RunPipe class

    metric : Evaluation metric
    """
    def __init__(self, run_pipe: RunPipe, metric):
        refresh_custom_components()

        self.resamplers = list(rsps.keys())
        self.classifiers = list(clfs.keys())
        self.hybrids = list(hybrid_factories.keys())
        self.automls = list(automls.keys())
        self.survival_models = list(survival_models.keys())
        self.survival_resamplers = list(survival_resamplers.keys())
        self.unsupervised_models = list(unsupervised_models.keys())
        self.reduction_models = list(reduction_models.keys())
        self.anomaly_models = list(anomaly_models.keys())
        self.survival_unsupervised_models = list(survival_unsupervised_models.keys())
        self.unsupervised_models = list(unsupervised_models.keys())
        self.imputers = list(imps.keys())
        self.run_pipe = run_pipe
        self.metric = metric
        # self.pipeline_type = normalize_pipeline_type(getattr(run_pipe.args, "pipeline_type", None))
        self.pipeline_type = run_pipe.args.pipeline_type
        self.schema_paths: List[List[str]] = []
        self.local_best_pipes = BinaryTree(schema_paths=PIPELINE_SCHEMAS.get(self.pipeline_type, []))
        self.logger = logging.getLogger("autoimblearn")

    def preflight_images(self):
        """Ensure all required Docker images exist before any execution."""
        allow_build = getattr(self.run_pipe.args, "allow_image_build_preflight", True)
        self.logger.info("Running image preflight")
        # Restrict preflight to the node types used by the current pipeline_type
        self.pipeline_type = normalize_pipeline_type(getattr(self.run_pipe.args, "pipeline_type", self.pipeline_type))
        node_types = set()
        for path in PIPELINE_SCHEMAS.get(self.pipeline_type, []):
            node_types.update(path)
        providers = []
        from ..pipelines.customimputation import get_imputer_provider
        from ..pipelines.customrsp import get_resampler_provider
        from ..pipelines.customclf import get_classifier_provider
        from ..pipelines.customhbd import get_hybrid_provider
        from ..pipelines.customautoml import get_automl_provider
        from ..pipelines.customsurvival.customsurvivalresampler import get_survival_resampler_provider
        from ..pipelines.customsurvival.customsurvivalsupervised import get_survival_model_provider
        from ..pipelines.customsurvival.customsurvivalunsupervised import get_survival_unsupervised_provider
        from ..pipelines.customunsupervised import get_unsupervised_provider

        def _collect(keys, getter):
            for key in keys:
                provider = getter(key)
                if provider:
                    providers.append(provider)

        if "imp" in node_types:
            _collect(self.imputers, get_imputer_provider)
        if "rsp" in node_types:
            _collect(self.resamplers, get_resampler_provider)
        if "surv_rsp" in node_types:
            _collect(self.survival_resamplers, get_survival_resampler_provider)
        if "clf" in node_types:
            _collect(self.classifiers, get_classifier_provider)
        if "hbd" in node_types:
            _collect(self.hybrids, get_hybrid_provider)
        if "automl" in node_types:
            _collect(self.automls, get_automl_provider)
        if "unsup" in node_types:
            _collect(self.unsupervised_models, get_unsupervised_provider)
            _collect(self.reduction_models, get_unsupervised_provider)
            _collect(self.anomaly_models, get_unsupervised_provider)
        if "surv_supv" in node_types:
            _collect(self.survival_models, get_survival_model_provider)
        if "surv_unsup" in node_types:
            _collect(self.survival_unsupervised_models, get_survival_unsupervised_provider)

        prepare_images(providers, allow_build=allow_build)

    def _get_pool_for_node_type(self, node_type: str) -> List[str]:
        """Return the current component pool for a given schema node_type."""
        attr = NODE_TYPE_TO_POOL_ATTR.get(node_type)
        if not attr:
            return []
        return getattr(self, attr, [])

    def _select_schema_paths(self) -> List[List[str]]:
        """Resolve pipeline_type and return usable schema paths based on non-empty pools."""
        requested_type = getattr(self.run_pipe.args, "pipeline_type", None)
        self.pipeline_type = normalize_pipeline_type(requested_type) if requested_type else self.pipeline_type
        base_paths = PIPELINE_SCHEMAS.get(self.pipeline_type, PIPELINE_SCHEMAS["supervised"])

        self.logger.info(
            "Selecting schema paths | pipeline_type=%s requested_type=%s base_paths=%s",
            self.pipeline_type,
            requested_type,
            base_paths,
            extra={"ui_log": True, "stage": "init_tree"},
        )

        usable_paths = []
        for path in base_paths:
            empty_nodes = []
            if all(self._get_pool_for_node_type(node_type) for node_type in path):
                usable_paths.append(path)
            else:
                for node_type in path:
                    if not self._get_pool_for_node_type(node_type):
                        empty_nodes.append(node_type)
                self.logger.warning(
                    "Skipping schema path due to empty pools | path=%s empty_pools=%s",
                    path,
                    empty_nodes,
                    extra={"ui_log": True, "stage": "init_tree"},
                )

        if not usable_paths:
            self.logger.error(
                "No available components after filtering | pipeline_type=%s base_paths=%s",
                self.pipeline_type,
                base_paths,
                extra={"ui_log": True, "stage": "init_tree"},
            )
            raise ValueError(f"No available components for pipeline_type {self.pipeline_type} after applying model choices.")

        self.schema_paths = usable_paths
        return usable_paths

    def _train_automl(self, pipeline):
        """ Train the selected automl model """
        if len(pipeline) != 1:
            raise ValueError("Pipeline {} length is not correct, not an automl model")
        # TODO test this function
        result = self.run_pipe.fit_automl(pipeline)
        return result

    def _train_hybird(self, pipeline, args=None, train_ratio=1.0):
        """ Train the pipeline with hybrid resampling method """
        if len(pipeline) != 2:
            raise ValueError("Pipeline {} length is not correct, not a hybrid method pipeline")
        result = self.run_pipe.fit_hybrid(pipeline)
        return result

    def _train_regular(self, pipeline):
        """ Train the pipeline with regular (imputer, resampler, classifier) pipeline """
        if len(pipeline) != 3:
            raise ValueError("Pipeline {} length is not correct, not a regular method pipeline")
        result = self.run_pipe.fit(pipeline)
        return result

    def _train_survival(self, pipeline):
        """ Train the pipeline with survival (imputer, survival_resampler, survival_model) pipeline """
        if len(pipeline) != 3:
            raise ValueError("Pipeline {} length is not correct, not a survival method pipeline")
        # Check if it's actually a survival pipeline
        if pipeline[2] not in self.survival_models:
            raise ValueError(f"Pipeline {pipeline} does not contain a survival model")
        result = self.run_pipe.fit(pipeline)
        return result

    def _train_unsupervised(self, pipeline):
        """ Train the pipeline with unsupervised (imputer, unsupervised_model) pipeline """
        if len(pipeline) != 2:
            raise ValueError("Pipeline {} length is not correct, not an unsupervised pipeline")
        # Check if it's actually an unsupervised pipeline
        if pipeline[1] not in self.unsupervised_models:
            raise ValueError(f"Pipeline {pipeline} does not contain an unsupervised model")
        result = self.run_pipe.fit(pipeline)
        return result

    def _train_survival_unsupervised(self, pipeline):
        """ Train the pipeline with survival unsupervised (imputer, survival_unsupervised_model) pipeline """
        if len(pipeline) != 2:
            raise ValueError("Pipeline {} length is not correct, not a survival unsupervised pipeline")
        # Check if it's actually a survival unsupervised pipeline
        if pipeline[1] not in self.survival_unsupervised_models:
            raise ValueError(f"Pipeline {pipeline} does not contain a survival unsupervised model")
        result = self.run_pipe.fit(pipeline)
        return result

    def _init_result_tree(self, schema_paths: List[List[str]]) -> BinaryTree:
        """
        Seed the search tree with available components using the provided schema paths.
        """
        self.schema_paths = schema_paths
        result_tree = BinaryTree(schema_paths=schema_paths)
        seeded_components = {}

        for path in schema_paths:
            components = []
            for node_type in path:
                pool = self._get_pool_for_node_type(node_type)
                if not pool:
                    components = []
                    break

                component = seeded_components.get(node_type)
                if component is None:
                    component = secrets.choice(pool)
                    seeded_components[node_type] = component
                components.append(component)

            if len(components) == len(path):
                result_tree.insert_path(components, path)

        return result_tree

    def _compute_current_pipe(self, result_tree: BinaryTree):
        """Select an initial path from the configured schema."""
        if not result_tree.leaf_node_types:
            raise ValueError("No available schema paths to build a pipeline.")

        node_type = secrets.choice(list(result_tree.leaf_node_types))
        pipe = result_tree.build_pipe(node_type)
        result_tree.replace(node_type, 0, pipe[-1])

        self.model_filtering(topn=3)

    def model_filtering(self, topn=3):
        # Get dataset description
        dp = self.run_pipe.dataloader.get_data_description(self.run_pipe.args.dataset)

        # Get model description TODO

        # Filter models
        model_filter = ModelFiltering(dp, self.run_pipe.dataloader.container_data_root)
        # TODO make this work
        # filtered_models = model_filter.get_topn()
        # print(filtered_models)

        imputers = model_filter.get_topn("imputer")
        self.imputers = [imputer for imputer in imputers if imputer in self.imputers]

        resamplers = model_filter.get_topn("resampler")
        self.resamplers = [resampler for resampler in resamplers if resampler in self.resamplers]

        classifiers = model_filter.get_topn("classifier")
        self.classifiers = [classifier for classifier in classifiers if classifier in self.classifiers]


    def exhaustive_search(self, checked=None, train_ratio=1.0):
        saver = Result(train_ratio, self.metric)
        saver.load_saved_result()

        for imp in self.imputers:
            for resampler in self.resamplers:
                for classifier in self.classifiers:
                    pipe = [imp, resampler, classifier]
                    print(pipe)
                    if is_checked(pipe, checked):
                        tmp = checked[imp][resampler][classifier]
                    else:
                        if saver.is_in(pipe):
                            tmp = saver.get(pipe)
                        else:
                            try:
                                if resampler == "autosmote":
                                    run_autosmote = RunAutoSmote()
                                    tmp = run_autosmote.fit(clf=classifier, imp=imp, metric=self.metric, train_ratio=train_ratio)
                                else:
                                    tmp = self.run_pipe.fit(pipe)
                            except Exception as e:
                                raise e
                                tmp = 0

                            saver.append(pipe, tmp)
                        checked[imp][resampler][classifier] = tmp
                    print("Current pipe: {}, result: {}".format(pipe, tmp))


    def find_best(self, checked=None, train_ratio=1.0,
                  max_iterations: Optional[int] = None,
                  time_budget_seconds: Optional[float] = None,
                  early_stopping_patience: int = 10) -> Tuple[List, int, float]:
        """
        Find the best pipeline using greedy search with budget controls.

        Args:
            checked: Previously checked pipelines (for resuming searches)
            train_ratio: Fraction of training data to use (for faster evaluation)
            max_iterations: Maximum number of NEW pipeline evaluations (None = no limit)
            time_budget_seconds: Maximum time in seconds (None = no limit)
            early_stopping_patience: Stop if no improvement for N iterations (default: 10)

        Returns:
            Tuple of (best_pipeline, num_evaluations, best_score)

        Raises:
            SearchBudgetExceededError: If budget exceeded with warning
        """
        # Validate inputs
        if max_iterations is not None and max_iterations < 1:
            raise ValueError(f"max_iterations must be >= 1, got {max_iterations}")
        if time_budget_seconds is not None and time_budget_seconds <= 0:
            raise ValueError(f"time_budget_seconds must be > 0, got {time_budget_seconds}")

        # Initialize timing
        start_time = time.time()

        # saver = Result(train_ratio, self.metric, self.run_pipe.args.dataset)
        saver = self.run_pipe.saver
        saver.load_saved_result()

        try:
            schema_paths = self._select_schema_paths()
        except Exception as e:
            self.logger.error(
                "Schema path selection failed | pipeline_type=%s requested_type=%s pools={imp:%d,rsp:%d,clf:%d,hbd:%d,automl:%d,surv_models:%d,surv_rsp:%d,surv_unsup:%d,unsup:%d}",
                self.pipeline_type,
                getattr(self.run_pipe.args, "pipeline_type", None),
                len(self.imputers),
                len(self.resamplers),
                len(self.classifiers),
                len(self.hybrids),
                len(self.automls),
                len(self.survival_models),
                len(self.survival_resamplers),
                len(self.survival_unsupervised_models),
                len(self.unsupervised_models),
                exc_info=True,
                extra={
                    "ui_log": True,
                    "stage": "init_tree",
                },
            )
            raise
        automl_paths = [path for path in schema_paths if len(path) == 1 and path[0] == "automl"]
        search_paths = [path for path in schema_paths if len(path) > 1]

        # Evaluate AutoML-only pipelines up front (if available)
        best_pipe = []
        best_score = 0
        counter = 0  # Number of NEW evaluations (not from cache)
        total_checks = 0  # Total pipelines checked (including cached)
        if automl_paths:
            for automl_model in self.automls:
                total_checks += 1
                tmp_pipe = [automl_model]

                if saver.is_in(tmp_pipe):
                    result = saver.get(tmp_pipe)
                    logging.debug(f"Cache HIT for {tmp_pipe}: {result}")
                else:
                    try:
                        result = self._train_automl(tmp_pipe)
                    except Exception as e:
                        logging.error(f"AutoML pipeline {tmp_pipe} failed: {e}", exc_info=True)
                        result = 0.0

                    saver.append(tmp_pipe, result)
                    counter += 1

                if result > best_score or not best_pipe:
                    best_pipe = list(tmp_pipe)
                    best_score = result

        # If only AutoML path is usable, return the best AutoML result
        if not search_paths:
            elapsed_time = time.time() - start_time
            logging.info(
                f"SEARCH COMPLETE (AutoML only) | Best: {best_pipe} score={best_score:.4f} "
                f"evaluations={counter} time={elapsed_time:.1f}s"
            )
            return best_pipe, counter, best_score

        result_tree = self._init_result_tree(schema_paths)
        self._compute_current_pipe(result_tree)
        current_pipe = result_tree.best_pipe()

        iterations_since_improvement = 0
        # TODO test saving result , 1) add auto-sklearn to automls (using flask rest API)
        #                                from flask import Flask, jsonify
        final_result = set([])

        def resolve_current_schema_path() -> List[str]:
            node_types_path = result_tree.best_node_types()
            for path in self.schema_paths:
                if path == node_types_path:
                    return path
            for path in self.schema_paths:
                if len(path) == len(node_types_path) and path and node_types_path and path[-1] == node_types_path[-1]:
                    return path
            raise ValueError("Current tree path does not align with configured schema.")

        def update_best_pipe(tmp_pipe, result):
            nonlocal best_pipe, best_score, current_pipe, iterations_since_improvement
            if result > best_score:
                best_pipe = list(tmp_pipe)
                best_score = result
                iterations_since_improvement = 0  # Reset counter on improvement
                logging.info(f"🎉 NEW BEST: {best_score:.4f} with {best_pipe}")
            else:
                iterations_since_improvement += 1

            if result_tree.update_pipe(tmp_pipe, result):
                current_pipe = result_tree.best_pipe()
            logging.info(f"This is the best result so far: {best_score} {best_pipe}, This is the current result: {result}, {tmp_pipe}")

        def train_and_update(tmp_pipe):
            nonlocal counter, total_checks
            total_checks += 1

            if saver.is_in(tmp_pipe):
                result = saver.get(tmp_pipe)
                logging.debug(f"Cache HIT for {tmp_pipe}: {result}")
            else:
                # NEW evaluation
                try:
                    if len(tmp_pipe) == 2:
                        # Check if unsupervised
                        if tmp_pipe[1] in self.survival_unsupervised_models:
                            result = self._train_survival_unsupervised(tmp_pipe)
                        elif tmp_pipe[1] in self.unsupervised_models:
                            result = self._train_unsupervised(tmp_pipe)
                        else:
                            result = self._train_hybird(tmp_pipe)
                    elif len(tmp_pipe) == 3:
                        # Check if it's a survival pipeline
                        if tmp_pipe[2] in self.survival_models:
                            result = self._train_survival(tmp_pipe)
                        else:
                            result = self._train_regular(tmp_pipe)
                    else:
                        result = self._train_automl(tmp_pipe)
                except Exception as e:
                    logging.error(f"Pipeline {tmp_pipe} failed: {e}", exc_info=True)
                    result = 0.0  # Assign worst score on failure

                saver.append(tmp_pipe, result)
                counter += 1
                logging.info(f"Evaluated {counter}/{max_iterations or '∞'} pipelines, "
                           f"time: {time.time() - start_time:.1f}s")

            update_best_pipe(tmp_pipe, result)
            return result

        def check_budget() -> bool:
            """Check if any budget is exceeded. Returns True if should continue."""
            # Check iteration budget
            if max_iterations is not None and counter >= max_iterations:
                elapsed = time.time() - start_time
                logging.warning(
                    f"⏱️ Iteration budget exceeded: {counter}/{max_iterations} evaluations "
                    f"in {elapsed:.1f}s. Best: {best_score:.4f}"
                )
                return False

            # Check time budget
            if time_budget_seconds is not None:
                elapsed = time.time() - start_time
                if elapsed >= time_budget_seconds:
                    logging.warning(
                        f"⏱️ Time budget exceeded: {elapsed:.1f}s/{time_budget_seconds}s "
                        f"with {counter} evaluations. Best: {best_score:.4f}"
                    )
                    return False

            # Check early stopping
            if iterations_since_improvement >= early_stopping_patience:
                elapsed = time.time() - start_time
                logging.info(
                    f"🛑 Early stopping: No improvement for {early_stopping_patience} iterations. "
                    f"Total: {counter} evaluations in {elapsed:.1f}s. Best: {best_score:.4f}"
                )
                return False

            return True

        # Main search loop with budget control
        while check_budget():
            for model in self.imputers:
                tmp_pipe = result_tree.sub_best_pipe(node_type="imp")
                if not tmp_pipe:
                    continue
                if len(tmp_pipe) not in (2, 3):
                    raise ValueError(
                        "Pipeline length of {} is not compatible with AutoImblearn".format(tmp_pipe))
                tmp_pipe = [model] + tmp_pipe[1:]
                result = train_and_update(tmp_pipe)

                if result > best_score:
                    best_pipe = list(tmp_pipe)
                    best_score = result

            current_pipe = result_tree.best_pipe()
            current_schema_path = resolve_current_schema_path()

            if len(current_schema_path) > 1:
                second_node_type = current_schema_path[1]
                second_pool = self._get_pool_for_node_type(second_node_type)
                leaf_node_type = current_schema_path[-1]
                for model in second_pool:
                    if len(current_schema_path) == 2:
                        tmp_pipe = [current_pipe[0], model]
                    else:
                        sub_pipe = result_tree.sub_best_pipe(node_type=leaf_node_type)
                        tmp_pipe = [current_pipe[0], model] + sub_pipe

                    result = train_and_update(tmp_pipe)
                    if result > best_score:
                        best_pipe = list(tmp_pipe)
                        best_score = result

            current_pipe = result_tree.best_pipe()
            current_schema_path = resolve_current_schema_path()

            if len(current_schema_path) == 3:
                leaf_node_type = current_schema_path[2]
                leaf_pool = self._get_pool_for_node_type(leaf_node_type)
                for model in leaf_pool:
                    tmp_pipe = current_pipe[:2] + [model]
                    result = train_and_update(tmp_pipe)
                    if result > best_score:
                        best_pipe = list(tmp_pipe)
                        best_score = result

            if set(best_pipe) == final_result:
                logging.info("🏁 Converged: Best pipeline stabilized")
                break
            else:
                final_result = set(best_pipe)

        # Final statistics
        elapsed_time = time.time() - start_time
        result_tree.print_tree()

        logging.info("="*60)
        logging.info("SEARCH COMPLETE")
        logging.info(f"  Best pipeline: {best_pipe}")
        logging.info(f"  Best score: {best_score:.4f}")
        logging.info(f"  New evaluations: {counter}")
        logging.info(f"  Total checks (incl. cache): {total_checks}")
        logging.info(f"  Time elapsed: {elapsed_time:.1f}s")
        logging.info(f"  Avg time per evaluation: {elapsed_time/max(counter, 1):.2f}s")
        logging.info("="*60)

        return best_pipe, counter, best_score

    def run_best(self, pipeline=None):
        # Re-run the best pipeline found with 100% of data
        # saver = Result(1.0, self.metric, self.run_pipe.args.dataset)
        saver = self.run_pipe.saver
        saver.load_saved_result()
        if saver.is_in(pipeline):
            result = saver.get(pipeline)
        else:
            if len(pipeline) == 1:
                result = self._train_automl(pipeline)
            elif len(pipeline) == 2:
                # Check if unsupervised
                if pipeline[1] in self.survival_unsupervised_models:
                    result = self._train_survival_unsupervised(pipeline)
                elif pipeline[1] in self.unsupervised_models:
                    result = self._train_unsupervised(pipeline)
                else:
                    result = self._train_hybird(pipeline, args, 1.0)
            elif len(pipeline) == 3:
                # Check if it's a survival pipeline
                if pipeline[2] in self.survival_models:
                    result = self._train_survival(pipeline)
                else:
                    result = self._train_regular(pipeline)
            else:
                raise Exception("Pipeline {} is not in the correct length".format(pipeline))

        return result

    def count_pipe(self, pipeline=None):
        # Find the optimal and count how many pipelines to check
        counters = []
        for _ in range(100):
            checked = []
            final, count, best_score = self.find_best(checked)
            while final != set(pipeline):
                final, count, best_score = self.find_best(checked)
            counters.append(count)
        return counters


if __name__ == "__main__":
    class Args:
        def __init__(self):
            self.train_ratio=1.0
            self.n_splits = 10
            self.repeat = 0
            self.dataset = "test"
            self.metric = "auroc"
    args = Args()
    run_pipe = RunPipe(args)
    autoimb = AutoImblearn(run_pipe, metric=args.metric)
    schema_paths = PIPELINE_SCHEMAS["supervised"]
    tmp_tree = autoimb._init_result_tree(schema_paths)
    tmp_tree.print_tree()

    autoimb._compute_current_pipe(tmp_tree)

    tmp_pipe = tmp_tree.best_pipe()
    # print(tmp_pipe)
    # tmp_tree.print_tree()
    result = tmp_tree.build_pipe("clf")
    print(result)

    tmp_tree.update_pipe(["ii", "smote", "mlp"], 2)
    tmp_tree.update_pipe(["ii", "under", "svm"], 1)
    tmp_tree.print_tree()
