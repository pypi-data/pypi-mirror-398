"""
This module provides classes for extracting behavioral features and detecting anomalies.
"""

import time
import hashlib
import numpy as np
import psutil
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from dataclasses import dataclass
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib


@dataclass
class BehaviorPattern:
    """Represents a user's behavior pattern for analysis."""

    user_id: str
    session_duration: float
    request_frequency: float
    operation_sequence: List[str]
    timestamp: float


class FeatureExtractor:
    """
    Extracts a feature vector from system metrics for anomaly detection.
    """

    def __init__(self):
        self._last_cpu_times = None

    def collect_features(self) -> np.ndarray:
        """
        Collects system features and returns them as a NumPy array.

        Features:
        - CPU usage percentage
        - Memory usage percentage
        - Battery level percentage (-1.0 if no battery)

        Returns:
            A 2D NumPy array of shape (1, 3) containing the features.
        """
        # CPU Usage
        current_cpu_times = psutil.cpu_times()
        if self._last_cpu_times:
            delta_user = current_cpu_times.user - self._last_cpu_times.user
            delta_system = current_cpu_times.system - self._last_cpu_times.system
            delta_idle = current_cpu_times.idle - self._last_cpu_times.idle
            delta_total = delta_user + delta_system + delta_idle
            cpu_usage = (delta_user + delta_system) / delta_total if delta_total > 0 else 0.0
        else:
            cpu_usage = 0.0
        self._last_cpu_times = current_cpu_times

        # Memory Usage
        mem = psutil.virtual_memory()
        mem_usage = mem.percent / 100.0

        # Battery Level
        try:
            battery = psutil.sensors_battery()
            if battery:
                battery_level = battery.percent / 100.0
            else:
                battery_level = -1.0  # No battery
        except (AttributeError, NotImplementedError):
            battery_level = -1.0  # No battery support

        return np.array([[cpu_usage, mem_usage, battery_level]], dtype=np.float64)


class AnomalyDetector:
    """
    Uses an Isolation Forest model to detect anomalies in feature vectors.
    """

    def __init__(self, contamination: str = "auto"):
        """
        Initializes the AnomalyDetector.

        Args:
            contamination: The expected proportion of outliers in the data set.
        """
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self._is_trained = False

    def train(self, normal_data: np.ndarray):
        """
        Trains the Isolation Forest model on a set of normal feature vectors.

        Args:
            normal_data: A NumPy array of shape (n_samples, n_features) representing normal behavior.
        """
        if len(normal_data.shape) != 2 or normal_data.shape[0] == 0:
            raise ValueError("Input data must be a 2D array with at least one sample.")
        self.model.fit(normal_data)
        self._is_trained = True

    def predict(self, features: np.ndarray) -> tuple[int, float]:
        """
        Predicts whether a feature vector is an anomaly.

        Args:
            features: A 2D NumPy array of shape (1, n_features) to predict.

        Returns:
            A tuple containing:
            - prediction (int): 1 for normal, -1 for anomaly.
            - score (float): The anomaly score (lower is more anomalous).
        """
        if not self._is_trained:
            raise RuntimeError("The model must be trained before making predictions.")

        prediction = self.model.predict(features)[0]
        score = self.model.decision_function(features)[0]
        return int(prediction), float(score)

    def save_model(self, file_path: str):
        """Saves the trained model to a file."""
        if not self._is_trained:
            raise RuntimeError("Cannot save an untrained model.")
        joblib.dump(self.model, file_path)

    def load_model(self, file_path: str):
        """Loads a trained model from a file."""
        self.model = joblib.load(file_path)
        self._is_trained = True


class MLAnomalyDetector:
    """
    A machine learning-based anomaly detector for device fingerprints.

    This class uses an Isolation Forest model for robust anomaly detection and
    maintains online statistics for feature normalization.
    """

    def __init__(self, window_size: int = 1000, contamination: float = 0.05):
        if not IsolationForest:
            raise ImportError("scikit-learn is required for MLAnomalyDetector.")

        self.window_size = window_size
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.scaler = StandardScaler()

        self.feature_stats = defaultdict(lambda: {"mean": 0.0, "std": 1.0, "count": 0})
        self.recent_features = deque(maxlen=window_size)
        self.is_fitted = False

    def extract_features(
        self, fingerprint_data: Dict[str, Any], session_info: Optional[Dict[str, Any]] = None
    ) -> np.ndarray:
        """Extracts and hashes features from fingerprint and session data."""
        features = []

        # Categorical features are hashed to a numerical representation
        categorical_features = [
            fingerprint_data.get("cpu_model", ""),
            fingerprint_data.get("os_family", ""),
            fingerprint_data.get("cpu_arch", ""),
            fingerprint_data.get("mac_hash", ""),
        ]
        for feature in categorical_features:
            features.append(int(hashlib.sha256(str(feature).encode()).hexdigest(), 16) % 10000)

        # Numerical features
        features.append(fingerprint_data.get("ram_gb", 0))

        if session_info:
            features.extend(
                [
                    session_info.get("duration", 0),
                    session_info.get("request_count", 0),
                    session_info.get("time_since_last", 3600),
                ]
            )
        else:
            features.extend([0, 0, 3600])

        # Temporal features
        current_time = time.time()
        features.append(int((current_time % 86400) / 3600))  # Hour of day
        features.append(int((current_time / 86400) % 7))  # Day of week

        return np.array(features, dtype=float).reshape(1, -1)

    def fit_model(self):
        """Fits the Isolation Forest model with the collected recent features."""
        if len(self.recent_features) < 50:  # Need a minimum number of samples
            return

        feature_matrix = np.array(list(self.recent_features))
        self.scaler.fit(feature_matrix)
        scaled_features = self.scaler.transform(feature_matrix)
        self.model.fit(scaled_features)
        self.is_fitted = True

    def detect_anomaly(
        self, fingerprint_data: Dict[str, Any], session_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Detects anomalies in fingerprint data using the trained model.

        If the model is not yet fitted, it collects features. Once enough data is
        available, it trains the model and starts predicting.
        """
        features = self.extract_features(fingerprint_data, session_info)
        self.recent_features.append(features[0])

        if not self.is_fitted and len(self.recent_features) >= self.window_size:
            self.fit_model()

        if not self.is_fitted:
            return {
                "anomaly_score": 0.0,
                "is_anomaly": False,
                "confidence": len(self.recent_features) / self.window_size,
                "status": "collecting_data",
            }

        scaled_features = self.scaler.transform(features)
        anomaly_score = -self.model.score_samples(scaled_features)[0]
        is_anomaly = self.model.predict(scaled_features)[0] == -1

        return {
            "anomaly_score": anomaly_score,
            "is_anomaly": bool(is_anomaly),
            "confidence": 1.0,
            "status": "predicting",
        }


class AdaptiveSecurityManager:
    """
    Adjusts security levels based on real-time ML-driven threat assessment.
    """

    def __init__(self, anomaly_detector: MLAnomalyDetector):
        self.anomaly_detector = anomaly_detector
        self.security_levels = {
            "low": {"checks": ["basic"]},
            "medium": {"checks": ["basic", "timing"]},
            "high": {"checks": ["basic", "timing", "vm_detection"]},
            "critical": {"checks": ["forensic", "vm_detection"]},
        }
        self.current_level = "medium"
        self.threat_history = deque(maxlen=100)

    def assess_and_adapt(
        self, fingerprint_data: Dict[str, Any], session_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Assesses the current threat level and adapts security measures accordingly.
        """
        ml_result = self.anomaly_detector.detect_anomaly(fingerprint_data, session_info)
        self.threat_history.append(ml_result["anomaly_score"])

        avg_threat = np.mean(list(self.threat_history)) if self.threat_history else 0

        if avg_threat > 0.7:
            recommended_level = "critical"
        elif avg_threat > 0.6:
            recommended_level = "high"
        elif avg_threat > 0.5:
            recommended_level = "medium"
        else:
            recommended_level = "low"

        # Apply hysteresis to prevent rapid switching
        if self.current_level != recommended_level:
            self.current_level = recommended_level

        return {
            "current_security_level": self.current_level,
            "recommended_security_level": recommended_level,
            "average_threat_score": avg_threat,
            "ml_analysis": ml_result,
            "required_checks": self.security_levels[self.current_level]["checks"],
        }


# Global singleton instances
_anomaly_detector_instance: Optional[MLAnomalyDetector] = None
_adaptive_security_instance: Optional[AdaptiveSecurityManager] = None


def get_anomaly_detector() -> MLAnomalyDetector:
    """Returns a singleton instance of the MLAnomalyDetector."""
    global _anomaly_detector_instance
    if _anomaly_detector_instance is None:
        _anomaly_detector_instance = MLAnomalyDetector()
    return _anomaly_detector_instance


def get_adaptive_security_manager() -> AdaptiveSecurityManager:
    """Returns a singleton instance of the AdaptiveSecurityManager."""
    global _adaptive_security_instance
    if _adaptive_security_instance is None:
        detector = get_anomaly_detector()
        _adaptive_security_instance = AdaptiveSecurityManager(detector)
    return _adaptive_security_instance
