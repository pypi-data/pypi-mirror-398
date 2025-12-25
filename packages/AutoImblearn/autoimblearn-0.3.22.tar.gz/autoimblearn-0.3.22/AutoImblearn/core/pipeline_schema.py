from typing import Dict, List, Optional

PIPELINE_SCHEMAS: Dict[str, List[List[str]]] = {
    "supervised": [["imp", "rsp", "clf"], ["imp", "hbd"], ["automl"]],
    "unsupervised": [["imp", "unsup"]],
    "survival_supervised": [["imp", "surv_rsp", "surv_supv"]],
    "survival_unsupervised": [["imp", "surv_unsup"]],
}

NODE_TYPE_TO_POOL_ATTR: Dict[str, str] = {
    "imp": "imputers",
    "rsp": "resamplers",
    "clf": "classifiers",
    "hbd": "hybrids",
    "automl": "automls",
    "unsup": "unsupervised_models",
    "surv_rsp": "survival_resamplers",
    "surv_supv": "survival_models",
    "surv_unsup": "survival_unsupervised_models",
}

# Map UI/legacy pipeline type labels to canonical schema keys.
PIPELINE_TYPE_ALIASES: Dict[str, str] = {
    "classification": "supervised",
    "hybrid": "supervised",
    "automl": "supervised",
    "survival_classification": "survival_supervised",
    "survival": "survival_supervised",
    "survival_clustering": "survival_unsupervised",
    "clustering": "unsupervised",
    "reduction": "unsupervised",
    "anomaly": "unsupervised",
}


def normalize_pipeline_type(pipeline_type: Optional[str]) -> str:
    """Return a canonical pipeline_type supported by PIPELINE_SCHEMAS."""
    if not pipeline_type:
        return "supervised"

    normalized = pipeline_type.lower()
    normalized = PIPELINE_TYPE_ALIASES.get(normalized, normalized)

    if normalized not in PIPELINE_SCHEMAS:
        return "supervised"

    return normalized
