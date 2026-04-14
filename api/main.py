"""
WiFi Anomaly Detection — FastAPI application.

Endpoints:
  POST /readings      — submit a WiFi reading, get anomaly prediction
  GET  /anomalies     — list recent anomalies from the database
  GET  /health        — liveness check
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import WiFiReading, PredictionResponse, AnomalyRecord
from api.routes import router
from db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="WiFi Anomaly Detection API",
    description=(
        "Real-time WiFi anomaly detection using Isolation Forest. "
        "Accepts sensor readings via REST or MQTT bridge, "
        "classifies them, and stores anomalies in PostgreSQL."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
