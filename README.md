<img width="1033" height="459" alt="image" src="https://github.com/user-attachments/assets/56177110-7d42-4b48-81c3-de02aa5032b6" />
# WiFi Anomaly Detection System

Real-time WiFi anomaly detection using **ESP32**, **MQTT**, **Isolation Forest**, and a **FastAPI + PostgreSQL** backend — fully containerised with Docker.

---

## Architecture

```
┌─────────────┐     MQTT      ┌──────────────┐    HTTP POST   ┌─────────────────┐
│    ESP32    │ ────────────▶ │ MQTT Bridge  │ ─────────────▶ │   FastAPI API   │
│  (scanner)  │  wifi/readings│ (bridge.py)  │   /readings    │  (Uvicorn/ASGI) │
└─────────────┘               └──────────────┘                └────────┬────────┘
                                                                        │
                                                              ┌─────────▼────────┐
                                                              │  Isolation Forest │
                                                              │     (joblib)      │
                                                              └─────────┬────────┘
                                                                        │ anomaly?
                                                              ┌─────────▼────────┐
                                                              │    PostgreSQL     │
                                                              │  (anomalies tbl)  │
                                                              └──────────────────┘
```

**Data flow:**
1. ESP32 scans nearby WiFi networks every 10 s and publishes a JSON reading to the `wifi/readings` MQTT topic
2. The MQTT bridge subscribes to the topic and forwards each reading to the FastAPI REST endpoint
3. FastAPI runs the reading through an Isolation Forest model; if anomalous, the record is stored in PostgreSQL
4. Any client can query `/anomalies` to retrieve recent detections

---

## Features

- **Unsupervised anomaly detection** — Isolation Forest trained on 5 WiFi features: RSSI, channel, visible device count, packet loss %, and latency
- **REST API** with automatic Swagger UI at `/docs`
- **MQTT integration** — ESP32-compatible publish/subscribe pipeline
- **PostgreSQL persistence** — all anomalous readings stored with timestamp and score
- **Fully dockerised** — one command starts the entire stack
- **Pydantic v2 validation** — strict input schemas with useful error messages
- **Test suite** — unit tests (ML model) and async integration tests (API)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Microcontroller | ESP32 + MicroPython |
| Transport | MQTT (Eclipse Mosquitto 2) |
| API | FastAPI 0.111, Uvicorn, Pydantic v2 |
| ML | scikit-learn IsolationForest, joblib |
| Database | PostgreSQL 16, SQLAlchemy 2 (async) |
| Containerisation | Docker, docker-compose |
| Testing | pytest, pytest-asyncio, httpx |

---

## Quick Start

### Prerequisites
- Docker + Docker Compose
- Python 3.12 (for local development)

### 1. Clone and configure

```bash
git clone https://github.com/dabaross/wifi_anomaly_detection_system.git
cd wifi_anomaly_detection_system
cp .env.example .env
```

### 2. Start the full stack

```bash
docker compose up --build
```

This will:
- Start PostgreSQL and create the `anomalies` table automatically
- Start Eclipse Mosquitto on port 1883
- Train the Isolation Forest model
- Start FastAPI on port 8000

### 3. Explore the API

Open **http://localhost:8000/docs** for the interactive Swagger UI.

**Submit a normal reading:**
```bash
curl -X POST http://localhost:8000/readings \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "esp32-01",
    "rssi": -62.0,
    "channel": 6,
    "num_devices": 7,
    "packet_loss_pct": 1.5,
    "latency_ms": 22.0
  }'
```

**Submit an anomalous reading:**
```bash
curl -X POST http://localhost:8000/readings \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "esp32-01",
    "rssi": -91.0,
    "channel": 6,
    "num_devices": 42,
    "packet_loss_pct": 35.0,
    "latency_ms": 280.0
  }'
```

**Query stored anomalies:**
```bash
curl http://localhost:8000/anomalies
```

---

## Local Development (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Train the model
python scripts/train.py

# Run the API (requires PostgreSQL running separately)
uvicorn api.main:app --reload

# Run MQTT bridge
python mqtt/bridge.py

# Run tests
pytest tests/ -v
```

---

## ESP32 Setup

The firmware in `mqtt/esp32_firmware.py` runs on MicroPython.

```bash
# Flash to device (requires mpremote)
pip install mpremote
mpremote cp mqtt/esp32_firmware.py :main.py
```

Edit the top of `esp32_firmware.py` to set your WiFi credentials and the IP address of the MQTT broker before flashing.

---

## API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/readings` | Submit a WiFi reading |
| `GET` | `/anomalies` | List recent anomalies (default: last 50) |

Full schema available at `/docs`.

---

## Project Structure

```
wifi_anomaly_detection_system/
├── api/
│   ├── main.py          # FastAPI app, lifespan, middleware
│   ├── routes.py        # Endpoint handlers
│   └── schemas.py       # Pydantic models
├── db/
│   ├── database.py      # Async SQLAlchemy engine + session
│   ├── models.py        # ORM model (Anomaly table)
│   └── crud.py          # DB read/write helpers
├── ml/
│   └── model.py         # Data generator, training, inference
├── mqtt/
│   ├── bridge.py        # MQTT → FastAPI bridge (Python)
│   └── esp32_firmware.py# MicroPython firmware for ESP32
├── scripts/
│   └── train.py         # Standalone training entrypoint
├── tests/
│   └── test_api.py      # Unit + integration tests
├── docker-compose.yml
├── Dockerfile
├── mosquitto.conf
└── requirements.txt
```

