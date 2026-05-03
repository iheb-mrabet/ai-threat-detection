import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import roc_curve, precision_recall_curve, auc

from backend.ml.inference import ml_detector


DATASET_PATH = "data/ml_dataset.csv"
REPORTS_DIR = "reports"


def generate_graphs():
    os.makedirs(REPORTS_DIR, exist_ok=True)

    df = pd.read_csv(DATASET_PATH)
    y_true = df["label"].astype(int).values
    X = df.drop("label", axis=1)

    scores = []

    for _, row in X.iterrows():
        result = ml_detector.predict(row.to_dict())
        scores.append(result["ml_score"])

    y_scores = np.array(scores)

    # ROC curve
    fpr, tpr, roc_thresholds = roc_curve(y_true, y_scores)
    roc_auc = auc(fpr, tpr)

    plt.figure()
    plt.plot(fpr, tpr, label=f"ROC AUC = {roc_auc:.4f}")
    plt.plot([0, 1], [0, 1], linestyle="--")
    plt.xlabel("False Positive Rate / FAR")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")
    plt.legend()
    plt.grid(True)
    plt.savefig(f"{REPORTS_DIR}/roc_curve.png", bbox_inches="tight")
    plt.close()

    # FAR / FRR / EER curve
    fnr = 1 - tpr
    idx = np.nanargmin(np.abs(fpr - fnr))
    eer = (fpr[idx] + fnr[idx]) / 2
    eer_threshold = roc_thresholds[idx]

    plt.figure()
    plt.plot(roc_thresholds, fpr, label="FAR")
    plt.plot(roc_thresholds, fnr, label="FRR")
    plt.scatter([eer_threshold], [eer], label=f"EER = {eer:.4f}")
    plt.xlabel("Threshold")
    plt.ylabel("Error Rate")
    plt.title("FAR / FRR / EER Curve")
    plt.legend()
    plt.grid(True)
    plt.savefig(f"{REPORTS_DIR}/far_frr_eer_curve.png", bbox_inches="tight")
    plt.close()

    # Precision / Recall curve
    precision, recall, pr_thresholds = precision_recall_curve(y_true, y_scores)
    pr_auc = auc(recall, precision)

    plt.figure()
    plt.plot(recall, precision, label=f"PR AUC = {pr_auc:.4f}")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall Curve")
    plt.legend()
    plt.grid(True)
    plt.savefig(f"{REPORTS_DIR}/precision_recall_curve.png", bbox_inches="tight")
    plt.close()

    summary = {
        "roc_auc": round(float(roc_auc), 6),
        "pr_auc": round(float(pr_auc), 6),
        "eer": round(float(eer), 6),
        "eer_threshold": round(float(eer_threshold), 6),
        "graphs": [
            "reports/roc_curve.png",
            "reports/far_frr_eer_curve.png",
            "reports/precision_recall_curve.png"
        ]
    }

    with open(f"{REPORTS_DIR}/metrics_graphs_summary.json", "w") as f:
        json.dump(summary, f, indent=4)

    print(json.dumps(summary, indent=4))


if __name__ == "__main__":
    generate_graphs()
