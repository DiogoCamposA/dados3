from flask import Flask, render_template, request, redirect, url_for, session, flash
import paho.mqtt.client as mqtt
import psycopg2
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'chave_secreta'

# Configurações MQTT
MQTT_BROKER_HOST = "broker.hivemq.com"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "MQTTINCBTempUmidDiogo"

# Configuração do banco de dados PostgreSQL
POSTGRES_HOST = "database-temp.ct8moxkr9qvc.us-east-1.rds.amazonaws.com"
POSTGRES_PORT = 5432
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "123456789"

def create_tables():
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )
    cursor = conn.cursor()
    
    # Tabela para mensagens MQTT
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            topic TEXT,
            payload TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabela para usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
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
    )
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (topic, payload) VALUES (%s, %s)
    ''', (topic, payload))
    conn.commit()
    conn.close()

def register_user(username, password):
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (username, password) VALUES (%s, %s)
    ''', (username, password))
    conn.commit()
    conn.close()

def get_user(username):
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
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
create_tables()

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
    )
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM messages  
        ORDER BY timestamp
    ''')
    result = cursor.fetchall()
    conn.close()
    return result

@app.route("/index")
def index():
    values_last_31_days = get_values_last_31_days()
    
    return render_template("index.html", values_last_31_days=values_last_31_days)

# Rota para a página de cadastro
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = get_user(username)

        if user and user[2] == password:
            session['username'] = username
            flash('Login bem-sucedido!')
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha inválidos.')

    return render_template("login.html")

# Rota para a página de cadastro
@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Verificar se o usuário já existe
        if get_user(username):
            flash('Usuário já existe. Escolha outro nome.')
        else:
            # Registrar o novo usuário
            register_user(username, password)
            flash('Cadastro realizado com sucesso. Faça o login.')
            return redirect(url_for('login'))

    return render_template("cadastro.html")

if __name__ == "__main__":
    app.run(debug=True)
