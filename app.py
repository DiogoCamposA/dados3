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

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  
    
    # Inserir a mensagem no banco de dados
    insert_message(MQTT_TOPIC, payload)

# Configurar o cliente MQTT
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)

# Criar a tabela no banco de dados (se ainda não existir)
create_table()

# Iniciar a thread do cliente MQTT
mqtt_client.loop_start()

def on_message(client, userdata, msg):
    global mqtt_values_daily
    mqtt_data = get_messages()

    mqtt_data11 = mqtt_data[2][13:-49] if mqtt_data and len(mqtt_data) > 2 else 0
    mqtt_data22 = mqtt_data[2][34:-28] if mqtt_data and len(mqtt_data) > 2 else 0
    mqtt_data33 = mqtt_data[2][59:-4] if mqtt_data and len(mqtt_data) > 2 else 0

    mqtt_data_1 = float(mqtt_data11)
    mqtt_data_2 = float(mqtt_data22)
    mqtt_data_3 = float(mqtt_data33)

    timestamp = int(time.time())  # Obtém o timestamp atual
    year = int(time.strftime("%Y", time.localtime(timestamp)))  # Extrai o ano
    month = int(time.strftime("%m", time.localtime(timestamp)))  # Extrai o mês
    day = int(time.strftime("%d", time.localtime(timestamp)))  # Extrai o dia
    hour = int(time.strftime("%H", time.localtime(timestamp)))  # Extrai a hora

    if year not in mqtt_values_daily:
        mqtt_values_daily[year] = {}
    if month not in mqtt_values_daily[year]:
        mqtt_values_daily[year][month] = {}
    if day not in mqtt_values_daily[year][month]:
        mqtt_values_daily[year][month][day] = {}
    if hour not in mqtt_values_daily[year][month][day]:
        mqtt_values_daily[year][month][day][hour] = []

    mqtt_values_daily[year][month][day][hour].append({
        'temp': float(mqtt_data_1),
        'umid': float(mqtt_data_2),
        'solo': float(mqtt_data_3),
    })


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
