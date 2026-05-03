import pandas as pd
import numpy as np
import joblib
import json
import os

from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split


# =========================
# LOAD
# =========================
def load_model():
    data = joblib.load("models/threat_model.pkl")
    return data["model"], data["scaler"]


def load_data():
    df = pd.read_csv("data/synthetic_threat_dataset.csv")
    X = df.drop("label", axis=1)
    y = df["label"]
    return X, y


# =========================
# METRICS
# =========================
def compute_far_frr(y_true, y_pred):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    far = fp / (fp + tn) if (fp + tn) > 0 else 0
    frr = fn / (fn + tp) if (fn + tp) > 0 else 0

    return far, frr


def evaluate(model, scaler, X, y):
    X_scaled = scaler.transform(X)
    y_pred = model.predict(X_scaled)

    acc = accuracy_score(y, y_pred)
    far, frr = compute_far_frr(y, y_pred)

    return acc, far, frr


# =========================
# STRONG ATTACKS
# =========================

# 1. Strong Noise attack
def noise_attack(X):
    X_noisy = X.copy()
    noise = np.random.normal(0, 1.5, X.shape)  # MUCH stronger noise
    return X_noisy + noise


# 2. Strong Spoofing attack
def spoofing_attack(X, y):
    X_spoofed = X.copy()
    malicious_idx = (y == 1)

    # Make malicious look VERY benign
    X_spoofed.loc[malicious_idx, "failed_login_count"] *= 0.1
    X_spoofed.loc[malicious_idx, "suspicious_payload_score"] *= 0.1
    X_spoofed.loc[malicious_idx, "request_rate"] *= 0.2
    X_spoofed.loc[malicious_idx, "geo_anomaly_score"] *= 0.2
    X_spoofed.loc[malicious_idx, "privilege_escalation_attempts"] = 0

    return X_spoofed


# 3. Strong Compression attack
def compression_attack(X):
    return np.round(X, 0)  # heavy quantization


# 4. Strong Adversarial attack
def adversarial_attack(X):
    X_adv = X.copy()

    # Push ALL samples toward decision boundary
    X_adv["suspicious_payload_score"] = 0.5 + np.random.normal(0, 0.1, len(X))
    X_adv["geo_anomaly_score"] = 0.5 + np.random.normal(0, 0.1, len(X))
    X_adv["request_rate"] = 50 + np.random.normal(0, 10, len(X))
    X_adv["failed_login_count"] = 2 + np.random.normal(0, 1, len(X))

    return X_adv


# =========================
# MAIN
# =========================
def main():
    os.makedirs("reports", exist_ok=True)

    print("Loading model...")
    model, scaler = load_model()

    print("Loading data...")
    X, y = load_data()

    print("Splitting...")
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    results = {}

    # BASELINE
    print("\nBaseline evaluation...")
    acc, far, frr = evaluate(model, scaler, X_test, y_test)
    results["baseline"] = {
        "accuracy": acc,
        "FAR": far,
        "FRR": frr
    }

    # NOISE
    print("Noise attack...")
    X_noise = noise_attack(X_test)
    acc, far, frr = evaluate(model, scaler, X_noise, y_test)
    results["noise_attack"] = {
        "accuracy": acc,
        "FAR": far,
        "FRR": frr
    }

    # SPOOFING
    print("Spoofing attack...")
    X_spoof = spoofing_attack(X_test, y_test)
    acc, far, frr = evaluate(model, scaler, X_spoof, y_test)
    results["spoofing_attack"] = {
        "accuracy": acc,
        "FAR": far,
        "FRR": frr
    }

    # COMPRESSION
    print("Compression attack...")
    X_comp = compression_attack(X_test)
    acc, far, frr = evaluate(model, scaler, X_comp, y_test)
    results["compression_attack"] = {
        "accuracy": acc,
        "FAR": far,
        "FRR": frr
    }

    # ADVERSARIAL
    print("Adversarial attack...")
    X_adv = adversarial_attack(X_test)
    acc, far, frr = evaluate(model, scaler, X_adv, y_test)
    results["adversarial_attack"] = {
        "accuracy": acc,
        "FAR": far,
        "FRR": frr
    }

    # SAVE
    with open("reports/attack_results.json", "w") as f:
        json.dump(results, f, indent=4)

    print("\nAttack results saved to reports/attack_results.json")

    print("\n=== SUMMARY ===")
    for attack, metrics in results.items():
        print(f"\n{attack}:")
        for k, v in metrics.items():
            print(f"{k}: {v:.4f}")


if __name__ == "__main__":
    main()
