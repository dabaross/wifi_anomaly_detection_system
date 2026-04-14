"""
Integration tests for the WiFi Anomaly Detection API.
Run with: pytest tests/ -v
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def normal_reading():
    return {
        "device_id": "esp32-test",
        "rssi": -62.0,
        "channel": 6,
        "num_devices": 5,
        "packet_loss_pct": 1.0,
        "latency_ms": 20.0,
    }


@pytest.fixture
def anomaly_reading():
    return {
        "device_id": "esp32-test",
        "rssi": -92.0,
        "channel": 6,
        "num_devices": 40,
        "packet_loss_pct": 35.0,
        "latency_ms": 300.0,
    }


# ── ML unit tests ─────────────────────────────────────────────────────────────

def test_generate_normal_data():
    from ml.model import generate_normal_data
    X = generate_normal_data(n=100)
    assert X.shape == (100, 5)
    # RSSI should be in plausible range
    assert X[:, 0].mean() < -40
    assert X[:, 0].mean() > -100


def test_generate_anomaly_data():
    from ml.model import generate_anomaly_data
    X = generate_anomaly_data(n=50)
    assert X.shape == (50, 5)
    # Anomaly RSSI should be weaker than normal
    from ml.model import generate_normal_data
    normal = generate_normal_data(n=50)
    assert X[:, 0].mean() < normal[:, 0].mean()


def test_train_and_predict():
    from ml.model import generate_normal_data, train_model, predict
    import joblib, tempfile, os
    from pathlib import Path
    import ml.model as model_module

    X = generate_normal_data(n=500)
    model = train_model(X)

    # Patch MODEL_PATH to a temp file so we don't clobber the real model
    with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as f:
        tmp_path = Path(f.name)

    try:
        joblib.dump(model, tmp_path)
        original_path = model_module.MODEL_PATH
        model_module.MODEL_PATH = tmp_path

        normal_result = predict([-60.0, 6.0, 5.0, 1.0, 20.0])
        assert "is_anomaly" in normal_result
        assert "anomaly_score" in normal_result
        assert isinstance(normal_result["is_anomaly"], bool)
        assert isinstance(normal_result["anomaly_score"], float)

    finally:
        model_module.MODEL_PATH = original_path
        os.unlink(tmp_path)


def test_anomaly_score_ordering():
    """Anomalous readings should have a lower (more negative) score than normal ones."""
    from ml.model import generate_normal_data, train_model, predict
    import joblib, tempfile, os
    import ml.model as model_module
    from pathlib import Path

    X = generate_normal_data(n=1000)
    model = train_model(X)

    with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as f:
        tmp_path = Path(f.name)

    try:
        joblib.dump(model, tmp_path)
        original_path = model_module.MODEL_PATH
        model_module.MODEL_PATH = tmp_path

        normal = predict([-60.0, 6.0, 5.0, 1.0, 20.0])
        anomalous = predict([-95.0, 6.0, 45.0, 40.0, 350.0])
        assert anomalous["anomaly_score"] < normal["anomaly_score"]

    finally:
        model_module.MODEL_PATH = original_path
        os.unlink(tmp_path)


# ── API integration tests ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_endpoint():
    from api.main import app

    with patch("db.database.init_db", new_callable=AsyncMock):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_submit_normal_reading(normal_reading):
    from api.main import app

    mock_predict = {"is_anomaly": False, "anomaly_score": -0.05}

    with patch("db.database.init_db", new_callable=AsyncMock), \
         patch("api.routes.predict", return_value=mock_predict), \
         patch("api.routes.get_db"):

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/readings", json=normal_reading)

    assert response.status_code == 200
    data = response.json()
    assert data["is_anomaly"] is False
    assert data["device_id"] == "esp32-test"
    assert "anomaly_score" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_submit_anomaly_reading(anomaly_reading):
    from api.main import app

    mock_predict = {"is_anomaly": True, "anomaly_score": -0.45}
    mock_save = AsyncMock()

    with patch("db.database.init_db", new_callable=AsyncMock), \
         patch("api.routes.predict", return_value=mock_predict), \
         patch("api.routes.save_anomaly", mock_save), \
         patch("api.routes.get_db"):

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/readings", json=anomaly_reading)

    assert response.status_code == 200
    data = response.json()
    assert data["is_anomaly"] is True


@pytest.mark.asyncio
async def test_invalid_rssi_rejected():
    from api.main import app

    bad_reading = {
        "device_id": "esp32-test",
        "rssi": 10.0,   # invalid: RSSI must be <= 0
        "channel": 6,
        "num_devices": 5,
        "packet_loss_pct": 1.0,
        "latency_ms": 20.0,
    }

    with patch("db.database.init_db", new_callable=AsyncMock):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/readings", json=bad_reading)

    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_list_anomalies_empty():
    from api.main import app

    with patch("db.database.init_db", new_callable=AsyncMock), \
         patch("api.routes.get_recent_anomalies", new_callable=AsyncMock, return_value=[]), \
         patch("api.routes.get_db"):

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/anomalies")

    assert response.status_code == 200
    assert response.json() == []
