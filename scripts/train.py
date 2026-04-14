"""Entrypoint: train and save the Isolation Forest model."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.model import generate_normal_data, train_model, save_artifacts

if __name__ == "__main__":
    print("[train] Generating data and training model...")
    X = generate_normal_data(n=2000)
    model = train_model(X)
    save_artifacts(model)
    print("[train] Complete.")
