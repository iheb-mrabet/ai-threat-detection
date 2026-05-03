import pandas as pd
import numpy as np
import os
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


def load_data():
    df = pd.read_csv("data/synthetic_threat_dataset.csv")
    X = df.drop("label", axis=1)
    y = df["label"]
    return X, y


def preprocess(X_train, X_test):
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    return X_train_scaled, X_test_scaled, scaler


def train_models(X_train, y_train):
    models = {}

    # Random Forest
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)
    models["RandomForest"] = rf

    # Logistic Regression
    lr = LogisticRegression(max_iter=1000)
    lr.fit(X_train, y_train)
    models["LogisticRegression"] = lr

    return models


def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)

    return {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1_score": f1_score(y_test, y_pred)
    }


def main():
    os.makedirs("models", exist_ok=True)

    print("Loading data...")
    X, y = load_data()

    print("Splitting data...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("Preprocessing...")
    X_train_scaled, X_test_scaled, scaler = preprocess(X_train, X_test)

    print("Training models...")
    models = train_models(X_train_scaled, y_train)

    results = {}

    print("\nModel Evaluation:")
    for name, model in models.items():
        metrics = evaluate_model(model, X_test_scaled, y_test)
        results[name] = metrics

        print(f"\n{name}:")
        for k, v in metrics.items():
            print(f"{k}: {v:.4f}")

    # Select best model based on F1-score
    best_model_name = max(results, key=lambda x: results[x]["f1_score"])
    best_model = models[best_model_name]

    print(f"\nBest model: {best_model_name}")

    # Save model + scaler together
    joblib.dump({
        "model": best_model,
        "scaler": scaler
    }, "models/threat_model.pkl")

    print("Model saved to models/threat_model.pkl")


if __name__ == "__main__":
    main()
