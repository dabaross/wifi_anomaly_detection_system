<img width="1033" height="459" alt="image" src="https://github.com/user-attachments/assets/e5fd8e46-a25a-4674-9725-b23fb7dfbf4c" />

## 🧱 Architektura systemu

```mermaid
flowchart LR

A[ESP32<br/>C / ESP-IDF] --> B[MQTT<br/>Mosquitto]
B --> C[receiver.py<br/>paho-mqtt]

C --> D[TimescaleDB<br/>PostgreSQL]
D --> E[SQLAlchemy ORM]

E --> F[ML Model<br/>Isolation Forest]
F --> G[Retraining<br/>co 5 min]

F --> H[FastAPI]
H --> I[REST API]
H --> J[WebSocket]

I --> K[React Dashboard]
J --> K
