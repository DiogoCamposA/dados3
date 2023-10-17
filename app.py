from flask import Flask, render_template
import paho.mqtt.client as mqtt
import sqlite3
import time
from datetime import datetime


app = Flask(__name__)

# Configurações MQTT
MQTT_BROKER_HOST = "broker.hivemq.com"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "MQTTINCBTempUmidDiogo"

mqtt_values_daily = {}

# Configuração do banco de dados SQLite
DB_NAME = "mqtt_data.db"

def create_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT,
            payload TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def insert_message(topic, payload):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (topic, payload) VALUES (?, ?)
    ''', (topic, payload))
    conn.commit()
    conn.close()

def get_messages():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM messages ORDER BY timestamp DESC LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    return result

def on_connect(client, userdata, flags, rc):

    client.subscribe(MQTT_TOPIC)

# Configuração do cliente MQTT
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)

# Inicialização do cliente MQTT em uma thread separada
mqtt_client.loop_start()

def get_values_last_31_days():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM messages 
        WHERE timestamp >= datetime('now', '-31 days') 
        ORDER BY timestamp
    ''')
    result = cursor.fetchall()
    conn.close()
    return result

@app.route("/")
def index():
    values_last_31_days = get_values_last_31_days()
    
    return render_template("index.html", values_last_31_days=values_last_31_days)

if __name__ == "__main__":
    app.run(debug=True)
