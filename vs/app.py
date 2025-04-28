from dash import Dash, html, dcc, Input, Output
import threading
from datetime import datetime
import plotly.graph_objects as go
import paho.mqtt.client as mqtt
import json

# Thread-safe shared data
latest_data = {
    "temperature": 24.5,
    "humidity": 65,
    "light": 750,
    "co2": 450,
    "timestamp": datetime.now()
}
data_lock = threading.Lock()

# MQTT Settings
mqtt_broker = "test.mosquitto.org"  # Public broker
mqtt_port = 1883
mqtt_topic = "stm32/sensor_data"

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker with code {rc}")
    client.subscribe(mqtt_topic)

def on_message(client, userdata, msg):
    global latest_data
    try:
        payload = json.loads(msg.payload.decode())
        with data_lock:
            latest_data.update({
                "temperature": float(payload['temperature']),
                "humidity": float(payload['humidity']),
                "light": int(payload['light']),
                "co2": int(payload['co2']),
                "timestamp": datetime.now()
            })
        print(f"Received and updated: {latest_data}")
    except Exception as e:
        print(f"Error parsing MQTT message: {e}")

# Start MQTT client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(mqtt_broker, mqtt_port, 60)
mqtt_client.loop_start()

# Dash app
server = None
app = Dash(__name__, assets_folder='assets')
server = app.server  # Needed for Render deployment

# Danger thresholds
THRESHOLDS = {
    'temperature': (15, 30),  
    'humidity': (30, 70),
    'light': (300, 1000),
    'co2': (300, 800)
}

def metric_style(bg_color):
    return {
        'backgroundColor': bg_color,
        'padding': '20px',
        'borderRadius': '15px',
        'display': 'flex',
        'alignItems': 'center'
    }

# Layout
app.layout = html.Div(
    style={'backgroundColor': '#e0f7e9', 'minHeight': '100vh', 'padding': '20px'},
    children=[
        html.Div([
            html.Img(src='/assets/enit.png', style={'height': '70px', 'marginRight': '20px'}),
            html.H1("Environmental Monitoring ENIT", style={'color': '#333', 'margin': '0'})
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '30px'}),

        html.Div([
            html.Div([
                html.Div("🌡️", style={'fontSize': '40px', 'marginRight': '15px'}),
                html.Div([
                    html.Div("Temperature", style={'color': '#FF6B6B', 'fontSize': '18px'}),
                    html.Div(id='live-temperature', style={'color': '#333', 'fontSize': '24px', 'fontWeight': 'bold'})
                ]),
            ], style=metric_style('#d0f0c0')),

            html.Div([
                html.Div("💧", style={'fontSize': '40px', 'marginRight': '15px'}),
                html.Div([
                    html.Div("Humidity", style={'color': '#4ECDC4', 'fontSize': '18px'}),
                    html.Div(id='live-humidity', style={'color': '#333', 'fontSize': '24px', 'fontWeight': 'bold'})
                ]),
            ], style=metric_style('#d0f0c0')),

            html.Div([
                html.Div("🔆", style={'fontSize': '40px', 'marginRight': '15px'}),
                html.Div([
                    html.Div("Light", style={'color': '#FFE66D', 'fontSize': '18px'}),
                    html.Div(id='live-light', style={'color': '#333', 'fontSize': '24px', 'fontWeight': 'bold'})
                ]),
            ], style=metric_style('#d0f0c0')),

            html.Div([
                html.Div("🌿", style={'fontSize': '40px', 'marginRight': '15px'}),
                html.Div([
                    html.Div("CO2", style={'color': '#96CEB4', 'fontSize': '18px'}),
                    html.Div(id='live-co2', style={'color': '#333', 'fontSize': '24px', 'fontWeight': 'bold'})
                ]),
            ], style=metric_style('#d0f0c0')),
        ], style={
            'display': 'grid',
            'gridTemplateColumns': 'repeat(auto-fit, minmax(250px, 1fr))',
            'gap': '20px'
        }),

        html.Div(id='alert-message', style={
            'color': 'red',
            'fontSize': '24px',
            'fontWeight': 'bold',
            'textAlign': 'center',
            'marginTop': '20px'
        }),

        dcc.Interval(id='update-interval', interval=2000),
    ]
)

# Callbacks
@app.callback(
    [Output('live-temperature', 'children'),
     Output('live-humidity', 'children'),
     Output('live-light', 'children'),
     Output('live-co2', 'children'),
     Output('alert-message', 'children')],
    [Input('update-interval', 'n_intervals')]
)
def update_metrics(n):
    with data_lock:
        temp = latest_data['temperature']
        humidity = latest_data['humidity']
        light = latest_data['light']
        co2 = latest_data['co2']

    alerts = []

    if not (THRESHOLDS['temperature'][0] <= temp <= THRESHOLDS['temperature'][1]):
        alerts.append(f"⚠️ Temperature out of range: {temp:.1f}°C")
    if not (THRESHOLDS['humidity'][0] <= humidity <= THRESHOLDS['humidity'][1]):
        alerts.append(f"⚠️ Humidity out of range: {humidity:.1f}%")
    if not (THRESHOLDS['light'][0] <= light <= THRESHOLDS['light'][1]):
        alerts.append(f"⚠️ Light out of range: {light} lux")
    if not (THRESHOLDS['co2'][0] <= co2 <= THRESHOLDS['co2'][1]):
        alerts.append(f"⚠️ CO2 level out of range: {co2} ppm")

    alert_message = ' | '.join(alerts) if alerts else ''

    return (
        f"{temp:.1f}°C",
        f"{humidity:.1f}%",
        f"{light} lux",
        f"{co2} ppm",
        alert_message
    )

# Run
if __name__ == '__main__':
    app.run_server(debug=True, host="0.0.0.0", port=8050)
