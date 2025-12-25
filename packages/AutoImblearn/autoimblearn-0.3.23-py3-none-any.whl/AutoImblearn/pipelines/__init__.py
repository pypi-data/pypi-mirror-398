from . import (
    customautoml,
    customclf,
    customhbd,
    customimputation,
    customrsp,
    customsurvival,
    customunsupervised,
)
from .customimputation import imps as imputers, CustomImputer, reload_custom_components as reload_imputers
from .customautoml import automls, CustomAutoML, reload_custom_components as reload_automls
from .customhbd import hybrid_factories as hybrid_imbalanced_classifiers, CustomHybrid, reload_custom_components as reload_hybrids
from .customclf import clfs as classifiers, CustomClassifier, reload_custom_components as reload_classifiers
from .customrsp import rsps as resamplers, CustomResamplar, reload_custom_components as reload_resamplers
from .customreduction import reduction_models, CustomReductionModel, reload_custom_components as reload_reduction
from .customanomaly import anomaly_models, CustomAnomalyModel, reload_custom_components as reload_anomaly
from .customsurvival import (
    survival_models,
    survival_resamplers,
    survival_unsupervised_models,
    CustomSurvivalModel,
    CustomSurvivalResamplar,
    CustomSurvivalUnsupervisedModel,
    reload_custom_components as reload_survival,
)
from .customunsupervised import (
    unsupervised_models,
    CustomUnsupervisedModel,
    reload_custom_components as reload_unsupervised,
)


def refresh_custom_components():
    """
    Reload custom component registries so newly approved models are available.

    This covers all pipeline families (classification, survival, unsupervised,
    hybrids, and AutoML).
    """
    reload_imputers()
    reload_resamplers()
    reload_classifiers()
    reload_hybrids()
    reload_automls()
    reload_reduction()
    reload_anomaly()
    reload_survival()
    reload_unsupervised()
