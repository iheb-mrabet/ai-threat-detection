import json
import os
import uuid
import datetime

import joblib
import pandas as pd
import numpy as np
import torch
import torch.nn as nn

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report

from backend.ml.validation import validate_model, passes_gate, build_metadata
from backend.ml.autoencoder import Autoencoder
from backend.ml.dataset_builder import build_dataset_from_events


MODEL_DIR = "models"
SYNTHETIC_DATASET_PATH = "data/ml_dataset.csv"
MIN_REAL_EVENTS_FOR_TRAINING = 1000


def train_autoencoder(X_benign, input_dim, epochs=60, lr=0.001):
    model = Autoencoder(input_dim=input_dim)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    x_tensor = torch.tensor(X_benign, dtype=torch.float32)

    model.train()

    for epoch in range(epochs):
        optimizer.zero_grad()
        reconstructed = model(x_tensor)
        loss = criterion(reconstructed, x_tensor)
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 10 == 0:
            print(f"Autoencoder epoch {epoch + 1}/{epochs} - loss={loss.item():.6f}")

    return model


def load_training_dataset():
    print("Building dataset from stored real events...")
    real_df = build_dataset_from_events()

    if real_df.shape[0] >= MIN_REAL_EVENTS_FOR_TRAINING and real_df["label"].nunique() == 2:
        print("Using stored real events for retraining.")
        return real_df, "stored_events"

    print("Not enough stored real events or only one class found.")
    print("Using synthetic fallback dataset.")

    if not os.path.exists(SYNTHETIC_DATASET_PATH):
        raise FileNotFoundError(
            f"{SYNTHETIC_DATASET_PATH} not found. Run: python -m backend.ml.synthetic"
        )

    synthetic_df = pd.read_csv(SYNTHETIC_DATASET_PATH)
    return synthetic_df, "synthetic_fallback"


def train():
    os.makedirs(MODEL_DIR, exist_ok=True)

    print("Loading training dataset...")
    df, dataset_source = load_training_dataset()

    X = df.drop("label", axis=1)
    y = df["label"]
    feature_names = list(X.columns)

    print("Dataset source:", dataset_source)
    print("Dataset shape:", df.shape)
    print("Class distribution:")
    print(y.value_counts())

    print("Splitting...")
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y
    )

    print("Scaling...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print("Training RandomForest...")
    rf = RandomForestClassifier(
        n_estimators=250,
        max_depth=10,
        min_samples_leaf=4,
        class_weight="balanced",
        random_state=42
    )
    rf.fit(X_train_scaled, y_train)

    y_pred = rf.predict(X_test_scaled)
    y_proba = rf.predict_proba(X_test_scaled)[:, 1]

    print("RandomForest report:")
    print(classification_report(y_test, y_pred))

    print("Training IsolationForest on benign traffic...")
    benign_train = X_train_scaled[y_train == 0]

    iso = IsolationForest(
        n_estimators=200,
        contamination=0.08,
        random_state=42
    )
    iso.fit(benign_train)

    print("Training PyTorch Autoencoder...")
    input_dim = X_train_scaled.shape[1]

    ae = train_autoencoder(
        X_benign=benign_train,
        input_dim=input_dim,
        epochs=60,
        lr=0.001
    )

    print("Building anomaly calibration thresholds...")
    ae.eval()

    with torch.no_grad():
        benign_tensor = torch.tensor(benign_train, dtype=torch.float32)
        ae_recon = ae(benign_tensor).numpy()

    ae_errors = np.mean((benign_train - ae_recon) ** 2, axis=1)
    ae_threshold = float(np.percentile(ae_errors, 95))

    iso_raw = -iso.decision_function(benign_train)
    iso_threshold = float(np.percentile(iso_raw, 95))

    print("Validating RandomForest...")
    metrics = validate_model(y_test, y_pred, y_proba)

    print("Metrics:")
    print(json.dumps(metrics, indent=4))

    if not passes_gate(metrics):
        print("Model rejected: validation gates failed.")
        return

    print("Model passed validation gates.")

    model_version = str(uuid.uuid4())[:8]
    trained_at = datetime.datetime.now(datetime.UTC).isoformat()

    print("Saving models...")
    joblib.dump(rf, os.path.join(MODEL_DIR, "random_forest.pkl"))
    joblib.dump(iso, os.path.join(MODEL_DIR, "isolation_forest.pkl"))
    joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.pkl"))

    torch.save(
        {
            "model_state_dict": ae.state_dict(),
            "input_dim": input_dim
        },
        os.path.join(MODEL_DIR, "autoencoder.pt")
    )

    metadata = build_metadata(metrics, feature_names)
    metadata["model_version"] = model_version
    metadata["trained_at"] = trained_at
    metadata["autoencoder_type"] = "pytorch"
    metadata["dataset_source"] = dataset_source
    metadata["calibration"] = {
        "ae_threshold_95": ae_threshold,
        "iso_threshold_95": iso_threshold
    }
    metadata["dataset"] = {
        "rows": int(df.shape[0]),
        "features": int(X.shape[1]),
        "attack_ratio": float(y.mean())
    }
    metadata["notes"] = (
        "Retraining prefers stored events with heuristic/reviewed labels. "
        "If stored events are insufficient, synthetic fallback data is used."
    )

    with open(os.path.join(MODEL_DIR, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=4)

    print("Training complete.")
    print(f"Model version: {model_version}")
    print(f"Dataset source: {dataset_source}")


if __name__ == "__main__":
    train()
