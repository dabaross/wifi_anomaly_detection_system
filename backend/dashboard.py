import streamlit as st
import sqlite3
import pandas as pd
import time
from sklearn.ensemble import IsolationForest
import joblib


MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "wifi/stats"
DB_PATH = "baza.db" 

conn = sqlite3.connect(DB_PATH)
data = pd.read_sql("SELECT * FROM measurements", conn)
conn.close()

features  = data[['packets_per_second', 'unique_mac', 'rssi']]
model = IsolationForest(contamination=0.05)
model.fit(features)
joblib.dump(model, "model.pkl")
model = joblib.load("model.pkl")

start = time.time()

while True:
    conn = sqlite3.connect(DB_PATH)
    data = pd.read_sql("SELECT * FROM measurements", conn)
    conn.close()

    st.title("Data")
    st.write(data)
    st.line_chart(data['packets_per_second'])
    st.metric("Total measurements", len(data))
    mean = data['packets_per_second'].mean()
    st.metric("Avg packets/s", mean)
    features = data[['packets_per_second', 'unique_mac', 'rssi']]
    data['anomaly'] = model.predict(features)
    anomalies = data[data['anomaly'] == -1]
    st.metric("Anomalies detected", len(anomalies))
    time.sleep(1)
    now = time.time()
    minutes_passed = (now - start)/60
    if minutes_passed >= 5:
        model.fit(features)
        joblib.dump(model, "model.pkl")
        model = joblib.load("model.pkl")
        start = time.time()
    st.rerun()

