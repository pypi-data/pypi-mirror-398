"""
Central catalog of supported metrics per pipeline type.

Each entry includes a machine-readable key and a human-friendly label.
"""

from typing import Dict, List

MetricEntry = Dict[str, str]

# Map pipeline metric families to metric entries
SUPPORTED_METRICS: Dict[str, List[MetricEntry]] = {
    "classification": [
        {"key": "auroc", "label": "Area under the ROC curve (AUROC)"},
        {"key": "macro_f1", "label": "Macro-averaged F1 score"},
    ],
    "survival_supervised": [
        {"key": "c_index", "label": "Concordance index for right-censored data"},
        {
            "key": "c_index_ipcw",
            "label": "Concordance index for right-censored data based on inverse probability of censoring weights",
        },
        {"key": "integrated_brier_score", "label": "Integrated Brier score"},
        {"key": "brier_score", "label": "Brier score (time-dependent)"},
        {"key": "time_dependent_auc", "label": "Time-dependent AUC (cumulative/dynamic)"},
    ],
    "survival_unsupervised": [
        {"key": "log_rank", "label": "Log-rank statistic"},
        {"key": "c_index", "label": "Concordance index for right-censored data"},
    ],
    "clustering": [
        {"key": "silhouette", "label": "Silhouette score"},
        {"key": "calinski", "label": "Calinski-Harabasz score"},
        {"key": "davies_bouldin", "label": "Davies-Bouldin score (lower is better)"},
    ],
    "anomaly": [
        {"key": "anomaly_score", "label": "Anomaly score"},
        {"key": "precision", "label": "Precision (requires labels)"},
        {"key": "recall", "label": "Recall (requires labels)"},
        {"key": "f1", "label": "F1 score (requires labels)"},
    ],
}

# Default metric per pipeline metric family
DEFAULT_METRIC: Dict[str, str] = {
    "classification": "auroc",
    "survival_supervised": "c_index",
    "survival_unsupervised": "c_index",
    "clustering": "silhouette",
    "anomaly": "anomaly_score",
}

# Per-model metric support overrides (model IDs match registry keys/factory keys)
MODEL_METRICS: Dict[str, Dict[str, List[str]]] = {
    "survival_supervised": {
        # SVM variants don't expose survival functions; exclude Brier/IBS/AUC
        "SVM": ["c_index", "c_index_ipcw"],
        "KSVM": ["c_index", "c_index_ipcw"],
        # Others inherit full family list
    },
    "classification": {},
    "survival_unsupervised": {},
    "clustering": {},
    "anomaly": {},
}

# Mapping from UI pipeline type to metric family
PIPELINE_TO_METRIC_FAMILY: Dict[str, str] = {
    "classification": "classification",
    "hybrid": "classification",
    "survival_classification": "survival_supervised",
    "survival_clustering": "survival_unsupervised",
    "clustering": "clustering",
    "reduction": "clustering",
    "anomaly": "anomaly",
}


def get_metric_family(pipeline_type: str) -> str:
    """Return the metric family for a given pipeline type."""
    return PIPELINE_TO_METRIC_FAMILY.get(pipeline_type, "classification")


def get_metrics_for_pipeline(pipeline_type: str) -> List[MetricEntry]:
    """Return supported metrics (with labels) for the given pipeline type."""
    family = get_metric_family(pipeline_type)
    return SUPPORTED_METRICS.get(family, [])


def get_default_metric(pipeline_type: str) -> str:
    """Return the default metric key for the given pipeline type."""
    family = get_metric_family(pipeline_type)
    return DEFAULT_METRIC.get(family, DEFAULT_METRIC["classification"])


def is_metric_supported(pipeline_type: str, metric: str) -> bool:
    """Check if a metric key is supported for the given pipeline type."""
    return metric in {m["key"] for m in get_metrics_for_pipeline(pipeline_type)}


def get_model_supported_metrics(pipeline_type: str, model_ids: List[str]) -> List[str]:
    """Return metrics supported by the provided models (intersection)."""
    family = get_metric_family(pipeline_type)
    family_metrics = {m["key"] for m in SUPPORTED_METRICS.get(family, [])}
    overrides = MODEL_METRICS.get(family, {})

    # Start with family-wide metrics
    intersection = set(family_metrics)

    for mid in model_ids:
        # If no override, assume full family metrics
        allowed = set(overrides.get(mid, family_metrics))
        intersection &= allowed

    return sorted(intersection)
