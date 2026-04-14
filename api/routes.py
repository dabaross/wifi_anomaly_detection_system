from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import WiFiReading, PredictionResponse, AnomalyRecord
from ml.model import predict
from db.database import get_db
from db.crud import save_anomaly, get_recent_anomalies

router = APIRouter()


@router.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc)}


@router.post("/readings", response_model=PredictionResponse, tags=["Detections"])
async def submit_reading(reading: WiFiReading, db: AsyncSession = Depends(get_db)):
    """
    Submit a WiFi reading and receive an anomaly prediction.

    The model uses 5 features: rssi, channel, num_devices,
    packet_loss_pct, latency_ms.
    """
    features = [
        reading.rssi,
        float(reading.channel),
        float(reading.num_devices),
        reading.packet_loss_pct,
        reading.latency_ms,
    ]

    try:
        result = predict(features)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    timestamp = datetime.now(timezone.utc)

    if result["is_anomaly"]:
        await save_anomaly(db, reading, result["anomaly_score"], timestamp)

    return PredictionResponse(
        device_id=reading.device_id,
        is_anomaly=result["is_anomaly"],
        anomaly_score=result["anomaly_score"],
        timestamp=timestamp,
    )


@router.get("/anomalies", response_model=list[AnomalyRecord], tags=["Detections"])
async def list_anomalies(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Return the most recent anomalies stored in the database."""
    return await get_recent_anomalies(db, limit=limit)
