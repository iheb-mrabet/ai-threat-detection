import pandas as pd

from backend.app.storage import EVENTS


def heuristic_label(event: dict) -> int:
    """
    Labeling strategy:
    - reviewed_label is future-ready for human-reviewed events
    - matched rules mean malicious
    - high score means likely malicious
    - otherwise benign
    """
    if "reviewed_label" in event and event["reviewed_label"] is not None:
        return int(event["reviewed_label"])

    if event.get("matched_rules"):
        return 1

    if event.get("score", 0) >= 0.70:
        return 1

    return 0


def build_dataset_from_events() -> pd.DataFrame:
    rows = []

    for event in EVENTS:
        features = event.get("extracted_features", {})

        if not features:
            continue

        row = features.copy()
        row["label"] = heuristic_label(event)
        rows.append(row)

    df = pd.DataFrame(rows)
    print(f"[Dataset Builder] Built dataset from stored events: {df.shape}")

    return df
