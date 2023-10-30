from flask import Flask, render_template
import paho.mqtt.client as mqtt
import psycopg2
from datetime import datetime

app = Flask(__name__)

# Configurações MQTT
MQTT_BROKER_HOST = "broker.hivemq.com"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "MQTTINCBTempUmidDiogo"

# Configuração do banco de dados PostgreSQL
POSTGRES_HOST = "database-temp.ct8moxkr9qvc.us-east-1.rds.amazonaws.com"
POSTGRES_PORT = 5432
POSTGRES_DB = "temp_dados"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "123456789"

def create_table():
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DB
    )
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            topic TEXT,
            payload TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def insert_message(topic, payload):
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DB
    )
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (topic, payload) VALUES (%s, %s)
    ''', (topic, payload))
    conn.commit()
    conn.close()

def get_messages():
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DB
    )
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

# Configuração do cliente MQTT
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)

# Inicialização do cliente MQTT em uma thread separada
mqtt_client.loop_start()

def get_values_last_31_days():
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DB
    )
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM messages  
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
