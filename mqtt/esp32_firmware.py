"""
ESP32 firmware — MicroPython
Scans visible WiFi networks, publishes readings via MQTT.

Flash with: mpremote cp esp32_firmware.py :main.py
"""

import network
import ubinascii
import ujson
import utime
from umqtt.simple import MQTTClient
import machine

# ── Configuration ──────────────────────────────────────────────────────────────
WIFI_SSID = "YOUR_SSID"
WIFI_PASS = "YOUR_PASSWORD"

MQTT_BROKER = "192.168.1.100"   # IP of the machine running Mosquitto
MQTT_PORT   = 1883
MQTT_TOPIC  = b"wifi/readings"
DEVICE_ID   = "esp32-" + ubinascii.hexlify(machine.unique_id()).decode()

SCAN_INTERVAL_SEC = 10
# ───────────────────────────────────────────────────────────────────────────────


def connect_wifi() -> network.WLAN:
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print(f"[wifi] Connecting to {WIFI_SSID}...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        timeout = 15
        while not wlan.isconnected() and timeout:
            utime.sleep(1)
            timeout -= 1
    print(f"[wifi] Connected: {wlan.ifconfig()}")
    return wlan


def scan_wifi(wlan: network.WLAN) -> dict:
    """
    Scan visible APs and derive features.
    scan() returns list of (ssid, bssid, channel, RSSI, authmode, hidden).
    """
    networks = wlan.scan()
    if not networks:
        return None

    rssi_values = [n[3] for n in networks]
    best_rssi   = max(rssi_values)
    channels    = [n[2] for n in networks]
    primary_ch  = max(set(channels), key=channels.count)

    return {
        "device_id":       DEVICE_ID,
        "rssi":            float(best_rssi),
        "channel":         int(primary_ch),
        "num_devices":     len(networks),
        "packet_loss_pct": 0.0,   # extend with ping-based measurement
        "latency_ms":      0.0,   # extend with ICMP or TCP probe
    }


def main():
    wlan = connect_wifi()
    client = MQTTClient(DEVICE_ID, MQTT_BROKER, port=MQTT_PORT)
    client.connect()
    print(f"[mqtt] Connected to broker at {MQTT_BROKER}")

    while True:
        reading = scan_wifi(wlan)
        if reading:
            payload = ujson.dumps(reading)
            client.publish(MQTT_TOPIC, payload)
            print(f"[mqtt] Published: {payload}")
        utime.sleep(SCAN_INTERVAL_SEC)


main()
