"""
Docker client for anomaly detection models.

Supports:
- IsolationForest: Isolation Forest
- OneClassSVM: One-Class SVM
- LOF: Local Outlier Factor
- EllipticEnvelope: Robust covariance estimation
- DBSCAN: Can be used for anomaly detection (noise points)
"""

from AutoImblearn.components.model_client.base_estimator import BaseEstimator
from AutoImblearn.components.model_client.image_spec import ImageSpec
from pathlib import Path
import os


class RunAnomalyDetection(BaseEstimator):
    """
    Docker client for anomaly detection models.

    Args:
        model: Model name (e.g., 'isoforest', 'ocsvm', 'lof')
        host_data_root: Path to data folder for volume mounting
    """

    def __init__(self, model="isoforest", host_data_root=None):
        if host_data_root is None:
            raise ValueError("host_data_root cannot be None")

        image_spec = ImageSpec(
            image="anomaly-api",
            context=Path(__file__).resolve().parent,
        )

        super().__init__(
            image_spec=image_spec,
            container_name=f"{model}_anomaly_container",
            host_data_root=host_data_root,
            api_base_url="http://localhost",
            port_bindings={5000: None}  # Random host port
        )

        self.model_name = model
        self.supported_metrics = [
            'anomaly_score',   # Anomaly scores
            'precision',       # Precision (if labels available)
            'recall',          # Recall (if labels available)
            'f1',              # F1 score (if labels available)
        ]
