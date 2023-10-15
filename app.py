from flask import Flask, render_template
import paho.mqtt.client as mqtt
import time

app = Flask(__name__)

# Configurações MQTT
MQTT_BROKER_HOST = "broker.hivemq.com"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "MQTTINCBTempUmidDiogo"

# Dicionários para armazenar os valores MQTT por ano, mês, dia e hora
mqtt_values_daily = {}

# Função para conectar-se ao servidor MQTT
def on_connect(client, userdata, flags, rc):
    print("Conectado ao servidor MQTT com código de resultado " + str(rc))
    client.subscribe(MQTT_TOPIC)

# Função para receber mensagens MQTT e armazenar os valores
def on_message(client, userdata, msg):
    global mqtt_values_daily
    mqtt_data = msg.payload.decode()
    mqtt_data_1 = mqtt_data[13:-49]
    mqtt_data_2 = mqtt_data[34:-28]
    mqtt_data_3 = mqtt_data[59:-4]

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

def calcular_media(year, month, day, hour):
    global mqtt_values_daily

    if year in mqtt_values_daily and \
            month in mqtt_values_daily[year] and \
            day in mqtt_values_daily[year][month] and \
            hour in mqtt_values_daily[year][month][day] and \
            len(mqtt_values_daily[year][month][day][hour]) > 0:

        temp_values = [entry['temp'] for entry in mqtt_values_daily[year][month][day][hour]]
        umid_values = [entry['umid'] for entry in mqtt_values_daily[year][month][day][hour]]
        solo_values = [entry['solo'] for entry in mqtt_values_daily[year][month][day][hour]]

        temp_media = sum(temp_values) / len(temp_values)
        umid_media = sum(umid_values) / len(umid_values)
        solo_media = sum(solo_values) / len(solo_values)

        return {
            'temp': temp_media,
            'umid': umid_media,
            'solo': solo_media,
        }
    else:
        return {
            'temp': 0.0,
            'umid': 0.0,
            'solo': 0.0,
        }

@app.route("/")
def index():
    current_year = int(time.strftime("%Y", time.localtime(time.time())))
    current_month = int(time.strftime("%m", time.localtime(time.time())))
    current_day = int(time.strftime("%d", time.localtime(time.time())))
    current_hour = int(time.strftime("%H", time.localtime(time.time())))

    medias_por_hora = {}
    medias_por_hora1 = {}

    for year in range(current_year, current_year - 1, -1):
        for month in range(1, 13):
            for day in range(1, 32):
                for hour in range(24):
                    medias_por_hora1[f"{year}-{month:02d}-{day:02d} {hour:02d}:00"] = calcular_media(year, month, day, hour)
                    medias_por_hora = medias_por_hora1

    return render_template("index.html", medias_por_hora=medias_por_hora)

if __name__ == "__main__":
    app.run(debug=True)
