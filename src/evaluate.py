import pandas as pd
import numpy as np
import os
import joblib
import json
import matplotlib.pyplot as plt

from sklearn.metrics import (
    confusion_matrix,
    roc_curve,
    auc,
    precision_score,
    recall_score,
    f1_score,
    accuracy_score
)
from sklearn.model_selection import train_test_split


def load_model():
    data = joblib.load("models/threat_model.pkl")
    return data["model"], data["scaler"]


def load_data():
    df = pd.read_csv("data/synthetic_threat_dataset.csv")
    X = df.drop("label", axis=1)
    y = df["label"]
    return X, y


def compute_far_frr(y_true, y_pred):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    far = fp / (fp + tn) if (fp + tn) > 0 else 0
    frr = fn / (fn + tp) if (fn + tp) > 0 else 0

    return far, frr


def compute_eer(y_true, y_scores):
    fpr, tpr, thresholds = roc_curve(y_true, y_scores)
    fnr = 1 - tpr

    eer_threshold = thresholds[np.nanargmin(np.absolute(fnr - fpr))]
    eer = fpr[np.nanargmin(np.absolute(fnr - fpr))]

    return eer, eer_threshold, fpr, fnr, thresholds


def plot_confusion_matrix(cm):
    plt.figure()
    plt.imshow(cm, cmap="Blues")
    plt.title("Confusion Matrix")
    plt.colorbar()

    labels = ["Benign", "Malicious"]
    plt.xticks([0, 1], labels)
    plt.yticks([0, 1], labels)

    for i in range(2):
        for j in range(2):
            plt.text(j, i, cm[i, j], ha="center", va="center")

    plt.xlabel("Predicted")
    plt.ylabel("Actual")

    os.makedirs("reports", exist_ok=True)
    plt.savefig("reports/confusion_matrix.png")
    plt.close()


def plot_roc_curve(fpr, tpr, roc_auc):
    plt.figure()
    plt.plot(fpr, tpr, label=f"ROC curve (AUC = {roc_auc:.2f})")
    plt.plot([0, 1], [0, 1], linestyle="--")

    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")
    plt.legend()

    plt.savefig("reports/roc_curve.png")
    plt.close()


def plot_far_frr(fpr, fnr, thresholds):
    plt.figure()
    plt.plot(thresholds, fpr, label="FAR")
    plt.plot(thresholds, fnr, label="FRR")

    plt.xlabel("Threshold")
    plt.ylabel("Rate")
    plt.title("FAR vs FRR")
    plt.legend()

    plt.savefig("reports/far_frr_curve.png")
    plt.close()


def main():
    print("Loading model...")
    model, scaler = load_model()

    print("Loading data...")
    X, y = load_data()

    print("Splitting data...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    X_test_scaled = scaler.transform(X_test)

    print("Predicting...")
    y_pred = model.predict(X_test_scaled)
    y_scores = model.predict_proba(X_test_scaled)[:, 1]

    # Metrics
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    far, frr = compute_far_frr(y_test, y_pred)
    eer, eer_threshold, fpr, fnr, thresholds = compute_eer(y_test, y_scores)

    roc_auc = auc(fpr, 1 - fnr)

    print("\nEvaluation Results:")
    print(f"Accuracy: {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall: {rec:.4f}")
    print(f"F1-score: {f1:.4f}")
    print(f"FAR: {far:.4f}")
    print(f"FRR: {frr:.4f}")
    print(f"EER: {eer:.4f}")

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    plot_confusion_matrix(cm)

    # ROC
    fpr_roc, tpr_roc, _ = roc_curve(y_test, y_scores)
    plot_roc_curve(fpr_roc, tpr_roc, roc_auc)

    # FAR/FRR curve
    plot_far_frr(fpr, fnr, thresholds)

    # Save metrics
    metrics = {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "FAR": far,
        "FRR": frr,
        "EER": eer
    }

    with open("reports/metrics.json", "w") as f:
        json.dump(metrics, f, indent=4)

    print("\nReports saved in /reports")


if __name__ == "__main__":
    main()
