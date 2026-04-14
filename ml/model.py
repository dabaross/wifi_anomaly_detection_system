"""
WiFi anomaly detection — data simulator + model trainer.

Simulates realistic RSSI/channel/device-count readings,
trains an Isolation Forest and persists it with joblib.
"""

import numpy as np
import joblib
import os
from sklearn.ensemble import IsolationForest
from pathlib import Path

MODEL_PATH = Path(__file__).parent / "model.joblib"
SCALER_PATH = Path(__file__).parent / "scaler.joblib"

# Feature order: [rssi, channel, num_devices, packet_loss_pct, latency_ms]
FEATURE_NAMES = ["rssi", "channel", "num_devices", "packet_loss_pct", "latency_ms"]


def generate_normal_data(n: int = 2000, seed: int = 42) -> np.ndarray:
    """Simulate normal WiFi environment readings."""
    rng = np.random.default_rng(seed)
    rssi = rng.normal(loc=-60, scale=8, size=n)                  # typical indoor RSSI
    channel = rng.choice([1, 6, 11], size=n).astype(float)       # non-overlapping channels
    num_devices = rng.integers(1, 15, size=n).astype(float)
    packet_loss = rng.uniform(0, 3, size=n)                       # 0–3% normal loss
    latency = rng.normal(loc=20, scale=5, size=n)                 # ms

    return np.column_stack([rssi, channel, num_devices, packet_loss, latency])


def generate_anomaly_data(n: int = 100, seed: int = 99) -> np.ndarray:
    """Simulate anomalous readings for evaluation only (not used in training)."""
    rng = np.random.default_rng(seed)
    rssi = rng.normal(loc=-85, scale=5, size=n)       # very weak signal
    channel = rng.choice([1, 6, 11], size=n).astype(float)
    num_devices = rng.integers(20, 50, size=n).astype(float)  # crowded network
    packet_loss = rng.uniform(15, 40, size=n)                  # high loss
    latency = rng.normal(loc=200, scale=50, size=n)            # high latency

    return np.column_stack([rssi, channel, num_devices, packet_loss, latency])


def train_model(X_train: np.ndarray) -> IsolationForest:
    model = IsolationForest(
        n_estimators=100,
        contamination=0.05,   # assume 5% anomalies in production stream
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train)
    return model


def save_artifacts(model: IsolationForest) -> None:
    joblib.dump(model, MODEL_PATH)
    print(f"[trainer] Model saved → {MODEL_PATH}")


def load_model() -> IsolationForest:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found at {MODEL_PATH}. Run `python ml/train.py` first."
        )
    return joblib.load(MODEL_PATH)


def predict(features: list[float]) -> dict:
    """
    Run inference on a single reading.

    Returns:
        {
          "is_anomaly": bool,
          "anomaly_score": float   # more negative = more anomalous
        }
    """
    model = load_model()
    X = np.array(features).reshape(1, -1)
    prediction = model.predict(X)[0]          # 1 = normal, -1 = anomaly
    score = model.score_samples(X)[0]

    return {
        "is_anomaly": bool(prediction == -1),
        "anomaly_score": round(float(score), 4),
    }


if __name__ == "__main__":
    print("[trainer] Generating training data...")
    X_train = generate_normal_data(n=2000)

    print("[trainer] Training Isolation Forest...")
    model = train_model(X_train)
    save_artifacts(model)

    # Quick sanity check
    normal_sample = [-60.0, 6.0, 5.0, 1.0, 18.0]
    anomaly_sample = [-88.0, 6.0, 35.0, 30.0, 250.0]

    print(f"[trainer] Normal sample  → {predict(normal_sample)}")
    print(f"[trainer] Anomaly sample → {predict(anomaly_sample)}")
    print("[trainer] Done.")
