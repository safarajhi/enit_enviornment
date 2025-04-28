from dash import Dash, html, dcc, Input, Output
from flask import Flask, request, jsonify
import threading
from datetime import datetime
import plotly.graph_objects as go

# Thread-safe shared data
latest_data = {
    "temperature": 24.5,
    "humidity": 65,
    "light": 750,
    "co2": 450,
    "timestamp": datetime.now()
}
data_lock = threading.Lock()

# Flask server
server = Flask(__name__)

# Dash app
app = Dash(__name__, server=server, assets_folder='assets')

# Danger thresholds
THRESHOLDS = {
    'temperature': (15, 30),  
    'humidity': (30, 70),
    'light': (300, 1000),
    'co2': (300, 800)
}

# Flask API route
@server.route('/api/sensors', methods=['POST'])
def handle_sensor_data():
    global latest_data
    try:
        sensor_data = request.json
        required_keys = ['temperature', 'humidity', 'light', 'co2']

        if not all(key in sensor_data for key in required_keys):
            return jsonify({"error": "Incomplete data"}), 400

        with data_lock:
            latest_data.update({
                "temperature": float(sensor_data['temperature']),
                "humidity": float(sensor_data['humidity']),
                "light": int(sensor_data['light']),
                "co2": int(sensor_data['co2']),
                "timestamp": datetime.now()
            })

        return jsonify({"status": "success"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Dash Layout
def metric_style(bg_color):
    return {
        'backgroundColor': bg_color,
        'padding': '20px',
        'borderRadius': '15px',
        'display': 'flex',
        'alignItems': 'center'
    }

app.layout = html.Div(
    style={'backgroundColor': '#e0f7e9', 'minHeight': '100vh', 'padding': '20px'},  # Light green
    children=[
        html.Div([
            html.Img(src='/assets/enit.png', style={'height': '70px', 'marginRight': '20px'}),
            html.H1("Environmental Monitoring ENIT", style={'color': '#333', 'margin': '0'})
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '30px'}),

        html.Div([
            # Temperature
            html.Div([
                html.Div("🌡️", style={'fontSize': '40px', 'marginRight': '15px'}),
                html.Div([
                    html.Div("Temperature", style={'color': '#FF6B6B', 'fontSize': '18px'}),
                    html.Div(id='live-temperature', style={'color': '#333', 'fontSize': '24px', 'fontWeight': 'bold'})
                ]),
            ], style=metric_style('#d0f0c0')),

            # Humidity
            html.Div([
                html.Div("💧", style={'fontSize': '40px', 'marginRight': '15px'}),
                html.Div([
                    html.Div("Humidity", style={'color': '#4ECDC4', 'fontSize': '18px'}),
                    html.Div(id='live-humidity', style={'color': '#333', 'fontSize': '24px', 'fontWeight': 'bold'})
                ]),
            ], style=metric_style('#d0f0c0')),

            # Light
            html.Div([
                html.Div("🔆", style={'fontSize': '40px', 'marginRight': '15px'}),
                html.Div([
                    html.Div("Light", style={'color': '#FFE66D', 'fontSize': '18px'}),
                    html.Div(id='live-light', style={'color': '#333', 'fontSize': '24px', 'fontWeight': 'bold'})
                ]),
            ], style=metric_style('#d0f0c0')),

            # CO2
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

# Dash Callbacks
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

# Run server
if __name__ == '__main__':
    app.run_server(debug=True, host="0.0.0.0", port=8050)
