import paho.mqtt.client as mqtt
import json
import time
import random
import logging

logging.basicConfig(level=logging.INFO)
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "wifi/stats"

client = mqtt.Client()
client.connect(MQTT_HOST, MQTT_PORT)

while(True):
    data = {
        "packets_per_second": random.randint(10, 200),
        "unique_mac": random.randint(1, 15),
        "rssi": random.randint(-90, -30)
    }
    text = json.dumps(data)
    client.publish(MQTT_TOPIC, text)
    logging.info("Data sent")
    time.sleep(0.5)
    
