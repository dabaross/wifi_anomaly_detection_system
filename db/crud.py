from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from db.models import Anomaly
from api.schemas import WiFiReading


async def save_anomaly(
    db: AsyncSession,
    reading: WiFiReading,
    score: float,
    timestamp: datetime,
) -> Anomaly:
    record = Anomaly(
        device_id=reading.device_id,
        rssi=reading.rssi,
        channel=reading.channel,
        num_devices=reading.num_devices,
        packet_loss_pct=reading.packet_loss_pct,
        latency_ms=reading.latency_ms,
        anomaly_score=score,
        timestamp=timestamp,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def get_recent_anomalies(db: AsyncSession, limit: int = 50) -> list[Anomaly]:
    result = await db.execute(
        select(Anomaly).order_by(desc(Anomaly.timestamp)).limit(limit)
    )
    return result.scalars().all()
