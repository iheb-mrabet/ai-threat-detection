import json
import os
from typing import Dict, Any, List

import joblib
import numpy as np
import onnxruntime as ort


MODEL_DIR = "models"


class MLDetector:
    def __init__(self):
        self.ready = False
        self.metadata: Dict[str, Any] = {}
        self.feature_names: List[str] = []

        try:
            self.rf = joblib.load(os.path.join(MODEL_DIR, "random_forest.pkl"))
            self.iso = joblib.load(os.path.join(MODEL_DIR, "isolation_forest.pkl"))
            self.scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))

            metadata_path = os.path.join(MODEL_DIR, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    self.metadata = json.load(f)

            self.feature_names = self.metadata.get("features", [])

            onnx_path = os.path.join(MODEL_DIR, "autoencoder.onnx")
            self.onnx_session = ort.InferenceSession(
                onnx_path,
                providers=["CPUExecutionProvider"]
            )
            self.onnx_input_name = self.onnx_session.get_inputs()[0].name

            self.ready = True

        except Exception as e:
            self.ready = False
            self.metadata = {
                "error": str(e),
                "status": "models_not_loaded"
            }

    def status(self) -> Dict[str, Any]:
        return {
            "ready": self.ready,
            "inference_backend": {
                "random_forest": "sklearn",
                "isolation_forest": "sklearn",
                "autoencoder": "onnxruntime"
            },
            "models": {
                "random_forest": os.path.exists(os.path.join(MODEL_DIR, "random_forest.pkl")),
                "isolation_forest": os.path.exists(os.path.join(MODEL_DIR, "isolation_forest.pkl")),
                "autoencoder_onnx": os.path.exists(os.path.join(MODEL_DIR, "autoencoder.onnx")),
                "scaler": os.path.exists(os.path.join(MODEL_DIR, "scaler.pkl")),
            },
            "metadata": self.metadata
        }

    def _ordered_features(self, features_dict: Dict[str, float]) -> np.ndarray:
        if self.feature_names:
            values = [features_dict.get(name, 0.0) for name in self.feature_names]
        else:
            values = list(features_dict.values())

        return np.array([values], dtype=np.float32)

    def predict(self, features_dict: Dict[str, float]) -> Dict[str, float]:
        if not self.ready:
            return {
                "ml_ready": 0.0,
                "rf_score": 0.0,
                "isolation_score": 0.0,
                "autoencoder_score": 0.0,
                "ml_score": 0.0
            }

        X = self._ordered_features(features_dict)
        X_scaled = self.scaler.transform(X).astype(np.float32)

        rf_score = float(self.rf.predict_proba(X_scaled)[0][1])

        raw_iso = float(-self.iso.decision_function(X_scaled)[0])
        iso_threshold = self.metadata.get("calibration", {}).get("iso_threshold_95", 0.1)
        isolation_score = min(max(raw_iso / (iso_threshold + 1e-6), 0.0), 1.0)

        reconstructed = self.onnx_session.run(
            None,
            {self.onnx_input_name: X_scaled}
        )[0]

        reconstruction_error = float(np.mean((X_scaled - reconstructed) ** 2))
        ae_threshold = self.metadata.get("calibration", {}).get("ae_threshold_95", 1.0)
        autoencoder_score = min(max(reconstruction_error / (ae_threshold + 1e-6), 0.0), 1.0)

        ml_score = (
            0.40 * rf_score +
            0.40 * autoencoder_score +
            0.20 * isolation_score
        )

        return {
            "ml_ready": 1.0,
            "rf_score": round(rf_score, 4),
            "isolation_score": round(isolation_score, 4),
            "autoencoder_score": round(autoencoder_score, 4),
            "ml_score": round(float(ml_score), 4)
        }


ml_detector = MLDetector()


def reload_ml_detector() -> MLDetector:
    global ml_detector
    ml_detector = MLDetector()
    return ml_detector
