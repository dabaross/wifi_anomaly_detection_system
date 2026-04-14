"""
MQTT bridge — subscribes to wifi/readings, forwards to FastAPI.

Run separately (outside Docker) or add as a service.
Topic format: wifi/readings
Payload: JSON matching WiFiReading schema
"""

import json
import os
import httpx
import paho.mqtt.client as mqtt

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = "wifi/readings"
API_URL = os.getenv("API_URL", "http://localhost:8000/readings")


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"[mqtt] Connected to broker (rc={reason_code})")
    client.subscribe(MQTT_TOPIC)
    print(f"[mqtt] Subscribed to {MQTT_TOPIC}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"[mqtt] Received: {payload}")

        response = httpx.post(API_URL, json=payload, timeout=5.0)
        result = response.json()
        status = "🚨 ANOMALY" if result.get("is_anomaly") else "✅ normal"
        print(f"[mqtt] Prediction for {payload.get('device_id')}: {status} "
              f"(score={result.get('anomaly_score')})")

    except Exception as e:
        print(f"[mqtt] Error processing message: {e}")


def run():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT)
    print(f"[mqtt] Bridge started, listening on {MQTT_BROKER}:{MQTT_PORT}")
    client.loop_forever()


if __name__ == "__main__":
    run()
