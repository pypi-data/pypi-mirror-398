import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import os

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "synthetic_pilr_10hz_dc_2h.csv")

# ===============================
# Load raw 10 Hz PILR data
# ===============================
df = pd.read_csv(DATA_FILE)
df["timestamp"] = pd.to_datetime(df["timestamp"], format='ISO8601', utc=True)
df["hour"] = df["timestamp"].dt.hour

# Get available hours in dataset
AVAILABLE_HOURS = sorted([int(h) for h in df["hour"].unique()])
MIN_HOUR = AVAILABLE_HOURS[0]
MAX_HOUR = AVAILABLE_HOURS[-1]

# ===============================
# Constants for grid processing
# ===============================
GRID_RES_METERS = 50
METERS_PER_DEG_LAT = 111_320
METERS_PER_DEG_LON = 85_000  # approx for DC latitude
EPS = 1e-12  # avoid log(0)

# ===============================
# Create Dash app
# ===============================
app = Dash(__name__)
app.title = "DC PILR Daily Interactive Heatmap"

# ===============================
# App layout
# ===============================
app.layout = html.Div([
    html.H1("Washington DC PILR Heatmap (Geometric Mean)"),
    html.Div([
        html.Div([
            html.Label("Start Hour:"),
            dcc.Dropdown(
                id='start-hour-dropdown',
                options=[{'label': f"{i}:00", 'value': i} for i in AVAILABLE_HOURS],
                value=MIN_HOUR,
                clearable=False,
                style={'width': '150px'}
            ),
        ], style={'display': 'inline-block', 'marginRight': '20px'}),
        html.Div([
            html.Label("End Hour:"),
            dcc.Dropdown(
                id='end-hour-dropdown',
                options=[{'label': f"{i}:00", 'value': i} for i in AVAILABLE_HOURS],
                value=MAX_HOUR,
                clearable=False,
                style={'width': '150px'}
            ),
        ], style={'display': 'inline-block'}),
    ], style={'margin': '20px'}),
    html.Div(id='stats-display', style={'margin': '20px', 'fontSize': '16px'}),
    dcc.Graph(id='pilr-heatmap', style={'height': '800px'}, config={'displayModeBar': False, 'displaylogo': False})
])

# ===============================
# Callback for interactive update
# ===============================
@app.callback(
    [Output('pilr-heatmap', 'figure'),
     Output('stats-display', 'children')],
    [Input('start-hour-dropdown', 'value'),
     Input('end-hour-dropdown', 'value')]
)
def update_heatmap(min_hour, max_hour):
    try:
        # Ensure min_hour <= max_hour
        if min_hour > max_hour:
            min_hour, max_hour = max_hour, min_hour
        
        # Filter by hour range
        df_hour = df[(df["hour"] >= min_hour) & (df["hour"] <= max_hour)].copy()
        
        if df_hour.empty:
            empty_fig = go.Figure(go.Scattermap(
                lat=[38.9072],
                lon=[-77.0369],
                mode='markers',
                marker=dict(size=0)
            ))
            empty_fig.update_layout(
                map=dict(
                    style="open-street-map",
                    center=dict(lat=38.9072, lon=-77.0369),
                    zoom=14
                ),
                margin={"r":0,"t":40,"l":0,"b":0},
                title=f"No data for hours {min_hour}:00–{max_hour+1}:00"
            )
            return empty_fig, "No data available for this time range."
        
        # Snap to spatial grid
        lat0 = df_hour["latitude"].min()
        lon0 = df_hour["longitude"].min()
        
        df_hour["grid_x"] = (
            (df_hour["longitude"] - lon0) * METERS_PER_DEG_LON / GRID_RES_METERS
        ).round().astype(int)
        
        df_hour["grid_y"] = (
            (df_hour["latitude"] - lat0) * METERS_PER_DEG_LAT / GRID_RES_METERS
        ).round().astype(int)
        
        # Geometric mean aggregation
        def geo_mean(x):
            return np.exp(np.mean(np.log(x + EPS)))
        
        agg = (
            df_hour
            .groupby(["grid_x", "grid_y"], as_index=False)
            .agg(
                lat=("latitude", "mean"),
                lon=("longitude", "mean"),
                pilr_geo_mean=("pilr", geo_mean),
                sample_count=("pilr", "count")
            )
        )
        
        # Create interactive map
        fig = go.Figure()
        
        fig.add_trace(go.Scattermap(
            lat=agg["lat"],
            lon=agg["lon"],
            mode='markers',
            marker=dict(
                size=16,
                color=agg["pilr_geo_mean"],
                colorscale='Plasma',
                showscale=True,
                colorbar=dict(
                    title="Geometric<br>Mean PILR",
                    thickness=15,
                    len=0.7
                ),
                opacity=1.0
            ),
            text=[f"PILR: {pilr:.2f}<br>Samples: {count}<br>Lat: {lat:.5f}<br>Lon: {lon:.5f}" 
                  for pilr, count, lat, lon in zip(agg["pilr_geo_mean"], agg["sample_count"], 
                                                    agg["lat"], agg["lon"])],
            hovertemplate='%{text}<extra></extra>',
            name='PILR Data'
        ))
        
        fig.update_layout(
            map=dict(
                style="open-street-map",
                center=dict(
                    lat=agg["lat"].mean(),
                    lon=agg["lon"].mean()
                ),
                zoom=15
            ),
            margin={"r":0,"t":40,"l":0,"b":0},
            title=f"PILR Heatmap (Geometric Mean) - Hours {min_hour}:00–{max_hour+1}:00",
            hovermode='closest'
        )
        
        # Stats display
        stats_text = f"""
        📊 Hours {min_hour}:00–{max_hour+1}:00 | 
        Grid cells: {len(agg)} | 
        Total samples: {agg['sample_count'].sum():,} | 
        Mean PILR: {agg['pilr_geo_mean'].mean():.2f} | 
        Grid resolution: {GRID_RES_METERS}m
        """
        
        return fig, stats_text
    
    except Exception as e:
        # Error handling
        error_fig = go.Figure()
        error_fig.update_layout(
            title=f"Error: {str(e)}",
            annotations=[dict(text=f"Error processing data: {str(e)}", showarrow=False)]
        )
        return error_fig, f"Error: {str(e)}"

# ===============================
# Run app
# ===============================
if __name__ == '__main__':
    print("Starting PILR Visualization...")
    print("Open your browser to http://localhost:8051")
    app.run(debug=False, port=8051, host='0.0.0.0')
