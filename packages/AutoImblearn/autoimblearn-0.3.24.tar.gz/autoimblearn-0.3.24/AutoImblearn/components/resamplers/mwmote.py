from sklearn.base import BaseEstimator
import numpy as np
import smote_variants as sv
import logging

logging.getLogger(sv.__name__).setLevel(logging.CRITICAL)


class MWMOTE(BaseEstimator):
    """MWMOTE"""

    def __init__(self, sampling_strategy=1, random_state=0, info_method=None):
        self.X = None
        self.y = None
        self.random_state = random_state
        self.info_method = info_method
        self.sampling_strategy = sampling_strategy
        self.resampler = sv.MWMOTE(proportion=self.sampling_strategy, random_state=42)

    def fit_resample(self, X: np.ndarray, y: np.ndarray):
        """Fit and transform X and y for under sampling"""
        X_samp, y_samp = self.resampler.sample(X, y)

        return X_samp, y_samp
