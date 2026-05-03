import pandas as pd
import numpy as np
import os

# Set seed for reproducibility
np.random.seed(42)


def generate_dataset(n_samples=3000):
    data = []

    for _ in range(n_samples):
        # Randomly choose label
        label = np.random.choice([0, 1], p=[0.7, 0.3])  # 70% benign, 30% malicious

        if label == 0:
            # BENIGN behavior
            failed_login_count = np.random.poisson(1)
            request_rate = np.random.normal(20, 5)
            avg_packet_size = np.random.normal(500, 50)
            unique_ports_accessed = np.random.randint(1, 5)
            suspicious_payload_score = np.random.normal(0.2, 0.1)
            geo_anomaly_score = np.random.normal(0.1, 0.05)
            session_duration = np.random.normal(300, 50)
            privilege_escalation_attempts = np.random.binomial(1, 0.05)

        else:
            # MALICIOUS behavior
            failed_login_count = np.random.poisson(5)
            request_rate = np.random.normal(80, 20)
            avg_packet_size = np.random.normal(700, 100)
            unique_ports_accessed = np.random.randint(5, 20)
            suspicious_payload_score = np.random.normal(0.7, 0.2)
            geo_anomaly_score = np.random.normal(0.6, 0.2)
            session_duration = np.random.normal(100, 40)
            privilege_escalation_attempts = np.random.binomial(1, 0.6)

        # Add overlap noise for realism
        failed_login_count += np.random.normal(0, 1)
        request_rate += np.random.normal(0, 5)

        data.append([
            max(failed_login_count, 0),
            max(request_rate, 0),
            max(avg_packet_size, 0),
            max(unique_ports_accessed, 1),
            np.clip(suspicious_payload_score, 0, 1),
            np.clip(geo_anomaly_score, 0, 1),
            max(session_duration, 1),
            privilege_escalation_attempts,
            label
        ])

    columns = [
        "failed_login_count",
        "request_rate",
        "avg_packet_size",
        "unique_ports_accessed",
        "suspicious_payload_score",
        "geo_anomaly_score",
        "session_duration",
        "privilege_escalation_attempts",
        "label"
    ]

    df = pd.DataFrame(data, columns=columns)
    return df


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)

    df = generate_dataset(n_samples=3000)
    df.to_csv("data/synthetic_threat_dataset.csv", index=False)

    print("Dataset generated successfully!")
    print("Saved to: data/synthetic_threat_dataset.csv")
    print(df.head())
