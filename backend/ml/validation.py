import json
import datetime

from sklearn.metrics import (
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    average_precision_score
)


def validate_model(y_true, y_pred, y_proba):
    metrics = {
        "f1": f1_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred),
        "recall": recall_score(y_true, y_pred),
        "roc_auc": roc_auc_score(y_true, y_proba),
        "pr_auc": average_precision_score(y_true, y_proba),
    }

    return metrics


def passes_gate(metrics):
    return (
        metrics["f1"] >= 0.80 and
        metrics["pr_auc"] >= 0.85
    )


def build_metadata(metrics, feature_names):
    return {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "metrics": metrics,
        "features": feature_names,
        "ensemble": {
            "rf_weight": 0.4,
            "ae_weight": 0.4,
            "if_weight": 0.2
        },
        "status": "valid" if passes_gate(metrics) else "rejected"
    }
