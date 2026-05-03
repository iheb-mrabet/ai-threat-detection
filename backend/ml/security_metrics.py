import json
import os
import warnings

import numpy as np
import pandas as pd
from sklearn.metrics import (
    confusion_matrix,
    roc_curve,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score
)

from backend.ml.inference import ml_detector


warnings.filterwarnings("ignore", category=UserWarning)

DATASET_PATH = "data/ml_dataset.csv"
OUTPUT_PATH = "models/security_metrics.json"


def compute_far_frr_eer(y_true, y_scores, threshold=0.5):
    y_pred = (y_scores >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    far = fp / (fp + tn) if (fp + tn) else 0.0
    frr = fn / (fn + tp) if (fn + tp) else 0.0

    fpr, tpr, thresholds = roc_curve(y_true, y_scores)
    fnr = 1 - tpr

    idx = np.nanargmin(np.abs(fpr - fnr))
    eer = float((fpr[idx] + fnr[idx]) / 2.0)
    eer_threshold = float(thresholds[idx])

    return {
        "threshold": float(threshold),
        "confusion_matrix": {
            "TP": int(tp),
            "TN": int(tn),
            "FP": int(fp),
            "FN": int(fn)
        },
        "FAR": round(float(far), 6),
        "FRR": round(float(frr), 6),
        "EER": round(float(eer), 6),
        "EER_threshold": round(float(eer_threshold), 6),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 6),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 6),
        "f1_score": round(float(f1_score(y_true, y_pred, zero_division=0)), 6),
        "roc_auc": round(float(roc_auc_score(y_true, y_scores)), 6),
        "pr_auc": round(float(average_precision_score(y_true, y_scores)), 6),
        "interpretation": {
            "FAR": "False Acceptance Rate: benign traffic incorrectly accepted as malicious. Equivalent to false positive rate in this system.",
            "FRR": "False Rejection Rate: malicious traffic incorrectly rejected as benign. Equivalent to false negative rate in this system.",
            "EER": "Equal Error Rate: threshold point where FAR and FRR are approximately equal."
        }
    }


def evaluate_security_metrics():
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError("Dataset not found. Run: python -m backend.ml.synthetic")

    if not ml_detector.ready:
        raise RuntimeError(f"ML detector not ready: {ml_detector.status()}")

    df = pd.read_csv(DATASET_PATH)

    y_true = df["label"].astype(int).values
    X = df.drop("label", axis=1)

    scores = []

    for _, row in X.iterrows():
        result = ml_detector.predict(row.to_dict())
        scores.append(result["ml_score"])

    y_scores = np.array(scores)

    metrics = compute_far_frr_eer(y_true, y_scores, threshold=0.5)

    os.makedirs("models", exist_ok=True)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(metrics, f, indent=4)

    print(json.dumps(metrics, indent=4))
    print(f"Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    evaluate_security_metrics()
