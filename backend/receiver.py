import paho.mqtt.client as mqtt
import json
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)

MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "wifi/stats"
DB_PATH = "baza.db" 

client = mqtt.Client()
client.connect(MQTT_HOST, MQTT_PORT)
client.subscribe(MQTT_TOPIC)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS measurements (numer INTEGER, packets_per_second INTEGER, unique_mac INTEGER, rssi INTEGER)")
counter = 0

def on_message(client, userdata, message):
    try:
        global counter 
        counter = counter + 1
        data = message.payload.decode()
        received = json.loads(data)
        received['numer'] = counter
        logging.info(f"Received data: {received}")
        cursor.execute("INSERT INTO measurements VALUES (?, ?, ?, ?)", (
                int(received['numer']),
                int(received['packets_per_second']),
                int(received['unique_mac']),
                int(received['rssi'])
            ))
        conn.commit()
        logging.info(f"Saved measurement #{counter}: {received}")
    except Exception as e:
        logging.error(f"Błąd: {e}")
        return

client.on_message = on_message
client.loop_forever()