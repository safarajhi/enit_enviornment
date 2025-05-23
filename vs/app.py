from dash import Dash, html, dcc, Input, Output
import threading
from datetime import datetime
import paho.mqtt.client as mqtt
import json

# Thread-safe shared data
latest_data = {
    "temperature": 24.5,
    "humidity": 65,
    "luminosity": 750,
    "iaq": 150,
    "tvoc": 100,
    "eco2": 400,
    "timestamp": datetime.now()
}
data_lock = threading.Lock()

# MQTT Settings
mqtt_broker = "test.mosquitto.org"
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
                "luminosity": int(payload['luminosity']),
                "iaq": int(payload['iaq']),
                "tvoc": int(payload['tvoc']),
                "eco2": int(payload['eco2']),
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
app = Dash(__name__, assets_folder='assets')
server = app.server

THRESHOLDS = {
    'temperature': (15, 30),  
    'humidity': (30, 70),
    'luminosity': (300, 1000),
    'eco2': (300, 800),
    'tvoc': (0, 300),
    'iaq': (0, 300)
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
            html.Img(src='/assets/enit.png', style={'height': '70px'}),
            html.H1("Environmental Monitoring ENIT", style={
                'color': '#333',
                'margin': '0',
                'fontSize': '36px',
                'fontWeight': 'bold',
                'textAlign': 'center',
                'flexGrow': 1
            }),
            html.Img(src='/assets/manar.png', style={'height': '70px'})
        ], style={
            'display': 'flex',
            'justifyContent': 'space-between',
            'alignItems': 'center',
            'marginBottom': '30px'
        }),

        html.Div([
            html.Div([
                html.Div("\ud83c\udf21\ufe0f", style={'fontSize': '40px', 'marginRight': '15px'}),
                html.Div([
                    html.Div("Temperature", style={'color': '#FF6B6B', 'fontSize': '18px'}),
                    html.Div(id='live-temperature', style={'color': '#333', 'fontSize': '24px', 'fontWeight': 'bold'})
                ]),
            ], style=metric_style('#d0f0c0')),

            html.Div([
                html.Div("\ud83d\udca7", style={'fontSize': '40px', 'marginRight': '15px'}),
                html.Div([
                    html.Div("Humidity", style={'color': '#4ECDC4', 'fontSize': '18px'}),
                    html.Div(id='live-humidity', style={'color': '#333', 'fontSize': '24px', 'fontWeight': 'bold'})
                ]),
            ], style=metric_style('#d0f0c0')),

            html.Div([
                html.Div("\ud83d\udd06", style={'fontSize': '40px', 'marginRight': '15px'}),
                html.Div([
                    html.Div("Luminosity", style={'color': '#FFE66D', 'fontSize': '18px'}),
                    html.Div(id='live-luminosity', style={'color': '#333', 'fontSize': '24px', 'fontWeight': 'bold'})
                ]),
            ], style=metric_style('#d0f0c0')),

            html.Div([
                html.Div("\ud83c\udf2b\ufe0f", style={'fontSize': '40px', 'marginRight': '15px'}),
                html.Div([
                    html.Div("IAQ", style={'color': '#FFA07A', 'fontSize': '18px'}),
                    html.Div(id='live-iaq', style={'color': '#333', 'fontSize': '24px', 'fontWeight': 'bold'})
                ]),
            ], style=metric_style('#d0f0c0')),

            html.Div([
                html.Div("\ud83e\uddea", style={'fontSize': '40px', 'marginRight': '15px'}),
                html.Div([
                    html.Div("TVOC", style={'color': '#F08080', 'fontSize': '18px'}),
                    html.Div(id='live-tvoc', style={'color': '#333', 'fontSize': '24px', 'fontWeight': 'bold'})
                ]),
            ], style=metric_style('#d0f0c0')),

            html.Div([
                html.Div("\ud83e\udab1", style={'fontSize': '40px', 'marginRight': '15px'}),
                html.Div([
                    html.Div("eCO2", style={'color': '#A0CED9', 'fontSize': '18px'}),
                    html.Div(id='live-eco2', style={'color': '#333', 'fontSize': '24px', 'fontWeight': 'bold'})
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
     Output('live-luminosity', 'children'),
     Output('live-iaq', 'children'),
     Output('live-tvoc', 'children'),
     Output('live-eco2', 'children'),
     Output('alert-message', 'children')],
    [Input('update-interval', 'n_intervals')]
)
def update_metrics(n):
    with data_lock:
        temp = latest_data['temperature']
        humidity = latest_data['humidity']
        luminosity = latest_data['luminosity']
        iaq = latest_data['iaq']
        tvoc = latest_data['tvoc']
        eco2 = latest_data['eco2']

    alerts = []

    if not (THRESHOLDS['temperature'][0] <= temp <= THRESHOLDS['temperature'][1]):
        alerts.append(f"\u26a0\ufe0f Temperature out of range: {temp:.1f}°C")
    if not (THRESHOLDS['humidity'][0] <= humidity <= THRESHOLDS['humidity'][1]):
        alerts.append(f"\u26a0\ufe0f Humidity out of range: {humidity:.1f}%")
    if not (THRESHOLDS['luminosity'][0] <= luminosity <= THRESHOLDS['luminosity'][1]):
        alerts.append(f"\u26a0\ufe0f Luminosity out of range: {luminosity} lux")
    if not (THRESHOLDS['iaq'][0] <= iaq <= THRESHOLDS['iaq'][1]):
        alerts.append(f"\u26a0\ufe0f IAQ level out of range: {iaq}")
    if not (THRESHOLDS['tvoc'][0] <= tvoc <= THRESHOLDS['tvoc'][1]):
        alerts.append(f"\u26a0\ufe0f TVOC level out of range: {tvoc} ppb")
    if not (THRESHOLDS['eco2'][0] <= eco2 <= THRESHOLDS['eco2'][1]):
        alerts.append(f"\u26a0\ufe0f eCO2 level out of range: {eco2} ppm")

    alert_message = ' | '.join(alerts) if alerts else ''

    return (
        f"{temp:.1f}°C",
        f"{humidity:.1f}%",
        f"{luminosity} lux",
        f"{iaq}",
        f"{tvoc} ppb",
        f"{eco2} ppm",
        alert_message
    )

# Run
if __name__ == '__main__':
    app.run_server(debug=True, host="0.0.0.0", port=8050)
