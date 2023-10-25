from flask import Flask, render_template
import paho.mqtt.client as mqtt
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

# Configurações MQTT
MQTT_BROKER_HOST = "broker.hivemq.com"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "MQTTINCBTempUmidDiogo"

# Diretório para armazenar o banco de dados
DB_DIRECTORY = "data"
DB_NAME = "mqtt_data.db"
DB_PATH = os.path.join(DB_DIRECTORY, DB_NAME)

def create_table():
    conn = sqlite3.connect(DB_PATH)
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

# Certifique-se de que o diretório exista
os.makedirs(DB_DIRECTORY, exist_ok=True)

# Chamar a função de criação da tabela apenas uma vez, ao iniciar a aplicação
create_table()

def insert_message(topic, payload):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (topic, payload) VALUES (?, ?)
    ''', (topic, payload))
    conn.commit()
    conn.close()

def get_messages():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM messages ORDER BY timestamp DESC LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    return result

def on_connect(client, userdata, flags, rc):
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    insert_message(MQTT_TOPIC, payload)

# Configurar o cliente MQTT
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)

# Iniciar a thread do cliente MQTT
mqtt_client.loop_start()

@app.route("/")
def index():
    values_last_31_days = get_values_last_31_days()
    return render_template("index.html", values_last_31_days=values_last_31_days)

def get_values_last_31_days():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM messages  
        ORDER BY timestamp
    ''')
    result = cursor.fetchall()
    conn.close()
    return result

if __name__ == "__main__":
    app.run(debug=True)
