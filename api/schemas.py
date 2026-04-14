from pydantic import BaseModel, Field
from datetime import datetime


class WiFiReading(BaseModel):
    """Incoming WiFi sensor reading."""
    device_id: str = Field(..., example="esp32-01", description="Unique sensor ID")
    rssi: float = Field(..., ge=-120, le=0, description="Signal strength in dBm")
    channel: int = Field(..., ge=1, le=14, description="WiFi channel (1–14)")
    num_devices: int = Field(..., ge=0, description="Visible devices on channel")
    packet_loss_pct: float = Field(..., ge=0, le=100, description="Packet loss %")
    latency_ms: float = Field(..., ge=0, description="Round-trip latency in ms")

    model_config = {
        "json_schema_extra": {
            "example": {
                "device_id": "esp32-01",
                "rssi": -62.0,
                "channel": 6,
                "num_devices": 7,
                "packet_loss_pct": 1.5,
                "latency_ms": 22.0,
            }
        }
    }


class PredictionResponse(BaseModel):
    """Model prediction result."""
    device_id: str
    is_anomaly: bool
    anomaly_score: float
    timestamp: datetime


class AnomalyRecord(BaseModel):
    """Anomaly stored in the database."""
    id: int
    device_id: str
    rssi: float
    channel: int
    num_devices: int
    packet_loss_pct: float
    latency_ms: float
    anomaly_score: float
    timestamp: datetime

    model_config = {"from_attributes": True}
