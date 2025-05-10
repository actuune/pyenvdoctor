import numpy as np
from sklearn.ensemble import IsolationForest
from ..core.models import PythonInstallation

class InstallationPredictor:
    def __init__(self, installations):
        self.installations = installations
        self.model = IsolationForest(contamination=0.1)

    def predict_anomalies(self):
        features = self._extract_features()
        return self.model.fit_predict(features)

    def _extract_features(self):
        return np.array([
            [len(install.packages), install.size_mb] 
            for install in self.installations
        ])
