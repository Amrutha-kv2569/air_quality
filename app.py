import streamlit as st
import pandas as pd
import numpy as np
import requests
import pydeck as pdk
import plotly.express as px
from datetime import datetime, timedelta

# Conditional import for Kriging/GeoPandas (Required for the 'Kriging Heatmap' tab)
try:
    from krigging import perform_kriging_correct
    import geopandas as gpd
    # Dummy implementation in case dependencies are not installed, allowing the rest of the app to run
except ImportError:
    def perform_kriging_correct(df, bounds):
        st.error("Kriging functionality is disabled. Install 'krigging' and 'geopandas' to enable.")
        return np.array([DELHI_LON]), np.array([DELHI_LAT]), np.array([100])
    def load_delhi_boundary_from_url():
        return None, None

# ==========================
# PAGE CONFIGURATION
# ==========================
st.set_page_config(
    layout="wide",
    page_title="Tale SEO Agency - Delhi Air Quality",
    page_icon="💨"
)

# ==========================
# STATIC CONFIG
# ==========================
API_TOKEN = "97a0e712f47007556b57ab4b14843e72b416c0f9"
DELHI_BOUNDS = "28.404,76.840,28.883,77.349"
DELHI_LAT = 28.6139
DELHI_LON = 77.2090
DELHI_GEOJSON_URL = "https://raw.githubusercontent.com/shuklaneerajdev/IndiaStateTopojsonFiles/master/Delhi.geojson"

# Twilio Configuration (Placeholder credentials - REPLACE THESE)
TWILIO_ACCOUNT_SID = "AC2cc57109fc63de336609901187eca69d"
TWILIO_AUTH_TOKEN = "62b791789bb490f91879e89fa2ed959d"
TWILIO_PHONE_NUMBER = "+13856005348"

# **STRICT COLORS BASED ON TEMPLATE ANALYSIS (ORANGE/DARK GREY/CLEAN BG)**
TALE_ORANGE = "#f36715"
TALE_DARK_TEXT = "#4a4a4a"
TALE_DARK_BLUE = "#1a364d"
TALE_LIGHT_BG = "#f7f7f7" # Closely matches background of HTML template sections

# ==========================
# CUSTOM CSS FOR STYLING (STRICTLY ADAPTED TO TEMPLATE)
# ==========================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="st-"] {{
        font-family: 'Open Sans', sans-serif;
    }}

    /* Main background - Light Gray/Neutral */
    .stApp {{
        background-color: {TALE_LIGHT_BG};
    }}

    /* Hide Streamlit's default header and footer */
    header, footer, #MainMenu {{
        visibility: hidden;
    }}
    
    /* Pre-Header Style Mimicry (Invisible in Streamlit but using colors) */
    .pre-header-bar {{
        background-color: {TALE_DARK_BLUE};
        color: white;
        padding: 0.5rem 1rem;
        font-size: 0.8rem;
        font-weight: 400;
        margin-bottom: -1px; /* Align with top */
    }}

    /* Main title section (.main-banner mimic) */
    .main-banner-container {{
        /* Placeholder image mimicking the gradient background of main-banner */
        background: url(https://i.imgur.com/K81jE5o.jpg) no-repeat center center; 
        background-size: cover;
        padding: 4rem 0 6rem 0;
        text-align: left;
        color: white;
        margin-bottom: 2rem;
    }}
    .main-banner-h4 {{
        font-size: 3rem;
        font-weight: 800;
        color: white;
        margin-bottom: 0.5rem;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
    }}
    .main-banner-h6 {{
        font-size: 1rem;
        font-weight: 600;
        color: {TALE_ORANGE};
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }}
    .line-dec {{
        border-bottom: 3px solid {TALE_ORANGE};
        width: 50px;
        margin-bottom: 1rem;
    }}

    /* Metric cards styling - Mimics service-item structure */
    .metric-card {{
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 1.5rem;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        text-align: left;
        height: 100%;
    }}
    .metric-card-label {{
        font-size: 0.9rem;
        font-weight: 600;
        color: {TALE_DARK_BLUE};
        margin-bottom: 0.5rem;
    }}
    .metric-card-value {{
        font-size: 2.2rem;
        font-weight: 800;
        color: {TALE_ORANGE};
        margin: 0.3rem 0;
    }}
    .metric-card-delta {{
        font-size: 0.8rem;
        color: {TALE_DARK_TEXT};
        font-weight: 500;
    }}

    /* Weather widget styling */
    .weather-widget {{
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 1.5rem;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        height: 100%;
    }}
    .weather-temp {{
        font-size: 2.2rem;
        font-weight: 800;
        color: {TALE_DARK_BLUE};
    }}

    /* Styling for Streamlit tabs - Mimics nav links */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
        background-color: transparent;
        padding: 0.5rem 0;
        border-bottom: 2px solid #e0e0e0;
        margin-top: 1rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        font-size: 0.95rem;
        font-weight: 600;
        background-color: #FFFFFF;
        border-radius: 8px 8px 0 0;
        padding: 0.75rem 1.5rem;
        border: 1px solid #e0e0e0;
        border-bottom: none;
        color: {TALE_DARK_TEXT};
        box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.05);
        transition: all 0.2s;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        background-color: {TALE_LIGHT_BG};
        color: {TALE_ORANGE};
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: {TALE_ORANGE};
        color: white !important;
        border: 1px solid {TALE_ORANGE};
        border-bottom: 1px solid {TALE_ORANGE}; /* Ensure continuity with content card */
    }}

    /* General card for content - Mimics section content */
    .content-card {{
        background-color: #FFFFFF;
        padding: 2.5rem 2rem;
        border-radius: 0 15px 15px 15px; /* Matches tab styling */
        border: 1px solid #e0e0e0;
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
        margin-top: -1px; /* Align with tabs */
        margin-bottom: 2rem;
    }}

    /* Section headers - Mimics .section-heading */
    .section-header {{
        font-size: 2rem;
        font-weight: 800;
        color: {TALE_DARK_BLUE};
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
    }}
    .section-header em {{
        color: {TALE_ORANGE};
        font-style: normal;
    }}
    .section-header span {{
        color: {TALE_ORANGE};
    }}
    .section-header .line-dec {{
        border-bottom: 3px solid {TALE_ORANGE};
        width: 50px;
        margin: 0.5rem 0 1.5rem 0;
    }}

    /* Primary Button Styling (Orange Button) */
    .stButton>button {{
        background-color: {TALE_ORANGE};
        color: white;
        border-radius: 20px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        border: none;
        box-shadow: 0 5px 15px rgba(243, 103, 21, 0.4);
        transition: background-color 0.2s, transform 0.1s;
    }}
    .stButton>button:hover {{
        background-color: #d85c14; 
        transform: translateY(-1px);
    }}
    
    /* Input field styling for a cleaner look */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {{
        border-radius: 8px;
        border: 1px solid #dddddd;
        padding: 0.5rem 1rem;
    }}
    
    .stTextArea>div>div>textarea {{
        border-radius: 8px;
        border: 1px solid #dddddd;
        padding: 0.5rem 1rem;
    }}


</style>
""", unsafe_allow_html=True)

# ==========================
# HELPER FUNCTIONS (KEPT FROM ORIGINAL CODE)
# ==========================

@st.cache_data(show_spinner="Loading Delhi boundary...")
def load_delhi_boundary_from_url():
    """Loads and caches the Delhi boundary GeoJSON from a URL."""
    try:
        # Check if geopandas is available
        if 'gpd' not in globals():
             raise ImportError("geopandas not available")
             
        gdf = gpd.read_file(DELHI_GEOJSON_URL)
        gdf = gdf.to_crs(epsg=4326) 
        delhi_polygon = gdf.unary_union 
        return gdf, delhi_polygon
    except Exception as e:
        # st.error(f"Error loading boundary: {e}") # Suppress error to avoid clutter
        return None, None

@st.cache_data(ttl=600, show_spinner="Fetching Air Quality Data...")
def fetch_live_data():
    """Fetches and processes live AQI data from the WAQI API."""
    url = f"https://api.waqi.info/map/bounds/?latlng={DELHI_BOUNDS}&token={API_TOKEN}"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "ok":
            df = pd.DataFrame(data["data"])
            df = df[df['aqi'] != "-"]
            df['aqi'] = pd.to_numeric(df['aqi'], errors='coerce')
            df = df.dropna(subset=['aqi'])

            def safe_get_name(x):
                if isinstance(x, dict):
                    return x.get('name', 'N/A')
                elif isinstance(x, str):
                    return x
                else:
                    return 'N/A'

            def safe_get_time(x):
                if isinstance(x, dict):
                    time_data = x.get('time', {})
                    if isinstance(time_data, dict):
                        return time_data.get('s', 'N/A')
                    elif isinstance(time_data, str):
                        return time_data
                    else:
                        return 'N/A'
                else:
                    return 'N/A'

            df['station_name'] = df['station'].apply(safe_get_name)
            df['last_updated'] = df['station'].apply(safe_get_time)
            df[['category', 'color', 'emoji', 'advice']] = df['aqi'].apply(
                get_aqi_category).apply(pd.Series)
            df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
            df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
            df = df.dropna(subset=['lat', 'lon'])
            return df
        return pd.DataFrame()
    except requests.RequestException:
        return pd.DataFrame()

@st.cache_data(ttl=1800, show_spinner="Fetching Weather Data...")
def fetch_weather_data():
    """Fetches current weather data from Open-Meteo API."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={DELHI_LAT}&longitude={DELHI_LON}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&timezone=Asia/Kolkata"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def get_aqi_category(aqi):
    """Categorizes AQI value and provides color, emoji, and health advice."""
    if aqi <= 50:
        return "Good", [0, 158, 96], "✅", "Enjoy outdoor activities."
    elif aqi <= 100:
        return "Moderate", [255, 214, 0], "🟡", "Unusually sensitive people should consider reducing prolonged or heavy exertion."
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups", [249, 115, 22], "🟠", "Sensitive groups should reduce prolonged or heavy exertion."
    elif aqi <= 200:
        return "Unhealthy", [220, 38, 38], "🔴", "Everyone may begin to experience health effects."
    elif aqi <= 300:
        return "Very Unhealthy", [147, 51, 234], "🟣", "Health alert: everyone may experience more serious health effects."
    else:
        return "Hazardous", [126, 34, 206], "☠️", "Health warnings of emergency conditions. The entire population is more likely to be affected."


def get_weather_info(code):
    """Converts WMO weather code to a description and icon."""
    codes = {
        0: ("Clear sky", "☀️"), 1: ("Mainly clear", "🌤️"), 2: ("Partly cloudy", "⛅"),
        3: ("Overcast", "☁️"), 45: ("Fog", "🌫️"), 48: ("Depositing rime fog", "🌫️"),
        51: ("Light drizzle", "💧"), 53: ("Moderate drizzle", "💧"), 55: ("Dense drizzle", "💧"),
        61: ("Slight rain", "🌧️"), 63: ("Moderate rain", "🌧️"), 65: ("Heavy rain", "🌧️"),
        80: ("Slight rain showers", "🌦️"), 81: ("Moderate rain showers", "🌦️"),
        82: ("Violent rain showers", "⛈️"), 95: ("Thunderstorm", "⚡"),
        96: ("Thunderstorm, slight hail", "⛈️"), 99: ("Thunderstorm, heavy hail", "⛈️")
    }
    return codes.get(code, ("Unknown", "❓"))

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates using Haversine formula."""
    from math import radians, sin, cos, sqrt, atan2

    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance

def get_nearby_stations(df, user_lat, user_lon, radius_km=10):
    """Get stations within specified radius of user location."""
    df['distance'] = df.apply(
        lambda row: calculate_distance(
            user_lat, user_lon, row['lat'], row['lon']),
        axis=1
    )
    nearby = df[df['distance'] <= radius_km].sort_values('distance')
    return nearby

def send_sms_alert(phone_number, message):
    """Send SMS alert using Twilio."""
    try:
        from twilio.rest import Client

        if TWILIO_ACCOUNT_SID == "your_twilio_account_sid" or not TWILIO_ACCOUNT_SID.startswith("AC"):
            return False, "⚠️ Twilio Account SID not configured correctly. It should start with 'AC' and be 34 characters long."

        if TWILIO_AUTH_TOKEN == "your_twilio_auth_token" or len(TWILIO_AUTH_TOKEN) < 30:
            return False, "⚠️ Twilio Auth Token not configured correctly. It should be 32 characters long."

        if TWILIO_PHONE_NUMBER == "your_twilio_phone_number" or not TWILIO_PHONE_NUMBER.startswith("+"):
            return False, "⚠️ Twilio Phone Number not configured correctly. It should start with '+' and include country code."

        if not phone_number.startswith("+"):
            return False, "⚠️ Recipient phone number must include country code starting with '+'"

        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        sent_message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )

        return True, f"✅ Alert sent successfully! Message SID: {sent_message.sid}"
    except ImportError:
        return False, "❌ Twilio library not installed. Run: pip install twilio"
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "authenticate" in error_msg.lower():
            return False, f"🔐 Authentication Error: Your Twilio credentials are incorrect.\n\nError details: {error_msg}"
        elif "unverified" in error_msg.lower():
            return False, f"📱 Phone Number Not Verified: For trial accounts, you must verify the recipient number in Twilio Console.\n\nError details: {error_msg}"
        else:
            return False, f"❌ Error sending SMS: {error_msg}"


def create_alert_message(nearby_stations, weather_data, location_name):
    """Create alert message with AQI and weather information."""
    if nearby_stations.empty:
        return "No nearby air quality monitoring stations found."

    avg_aqi = nearby_stations['aqi'].mean()
    worst_station = nearby_stations.iloc[0]

    weather_desc = "N/A"
    temp = "N/A"
    if weather_data and 'current' in weather_data:
        current = weather_data['current']
        weather_desc, _ = get_weather_info(current.get('weather_code', 0))
        temp = f"{current['temperature_2m']:.1f}°C"

    category, _, emoji, advice = get_aqi_category(avg_aqi)

    message = f"""🌍 Air Quality Alert - {location_name}\n\n{emoji} AQI Status: {category}\n📊 Average AQI: {avg_aqi:.0f}\n\n🔴 Worst Station: {worst_station['station_name']}\nAQI: {worst_station['aqi']:.0f} ({worst_station['distance']:.1f} km away)\n\n🌤️ Weather: {weather_desc}\n🌡️ Temperature: {temp}\n\n💡 Advice: {advice}\n\nStay safe!"""

    return message

# ==========================
# UI RENDERING FUNCTIONS
# ==========================

def render_header(df):
    """Renders the main header with summary metrics and weather, adapted for Tale SEO style."""
    
    # Pre-Header Area (Simple line to mimic the top bar)
    st.markdown('<div class="pre-header-bar">Air Quality Monitoring Service | Last updated: 2025-11-15 15:47 IST</div>', unsafe_allow_html=True)
    
    # Main Banner Area (Section Header)
    st.markdown(f"""
    <div class="main-banner-container">
        <div style="padding-left: 15px;">
            <h6 class="main-banner-h6">AIR QUALITY MONITORING</h6>
            <div class="line-dec"></div>
            <h4 class="main-banner-h4">Monitor <em>Delhi's Air</em> Quality <span>With Tale</span></h4>
            <p style="color: white; max-width: 500px; line-height: 1.6;">
                This dashboard provides real-time Air Quality Index (AQI) data for Delhi, offering maps, health alerts, and a forecast.
            </p>
            
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <div class="main-button scroll-to-section">
                    <button class="orange-button" onclick="document.getElementById('services').scrollIntoView()">Discover More</button>
                </div>
                <div class="second-button">
                    <button style="background: white; color: {TALE_ORANGE}; border: 1px solid white; border-radius: 20px; padding: 0.5rem 1.5rem; font-weight: 600;">Check our FAQs</button>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Service/Metrics Area (Below the banner, using 4 columns)

    c1, c2, c3, c4 = st.columns(4)
    if not df.empty:
        with c1:
            st.markdown(
                f'<div class="metric-card"><div class="metric-card-label">Average AQI</div><div class="metric-card-value">{df["aqi"].mean():.1f}</div><div class="metric-card-delta">Overall Status: {get_aqi_category(df["aqi"].mean())[0]}</div></div>', unsafe_allow_html=True)
        with c2:
            min_station = df.loc[df["aqi"].idxmin()]["station_name"]
            st.markdown(
                f'<div class="metric-card"><div class="metric-card-label">Minimum AQI</div><div class="metric-card-value">{df["aqi"].min():.0f}</div><div class="metric-card-delta">Cleanest Station: {min_station}</div></div>', unsafe_allow_html=True)
        with c3:
            max_station = df.loc[df["aqi"].idxmax()]["station_name"]
            st.markdown(
                f'<div class="metric-card"><div class="metric-card-label">Maximum AQI</div><div class="metric-card-value">{df["aqi"].max():.0f}</div><div class="metric-card-delta">Most Polluted: {max_station}</div></div>', unsafe_allow_html=True)

    with c4:
        weather_data = fetch_weather_data()
        if weather_data and 'current' in weather_data:
            current = weather_data['current']
            desc, icon = get_weather_info(current.get('weather_code', 0))
            st.markdown(f"""
            <div class="weather-widget">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <div class="metric-card-label">Current Weather</div>
                        <div class="weather-temp">{current['temperature_2m']:.1f}°C</div>
                    </div>
                    <div style="font-size: 3rem;">{icon}</div>
                </div>
                <div style="text-align: left; font-size: 0.9rem; color: {TALE_DARK_TEXT}; margin-top: 1rem; font-weight: 500;">
                    {desc}<br/>Humidity: {current['relative_humidity_2m']}%<br/>Wind: {current['wind_speed_10m']} km/h
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="weather-widget">
                <div class="metric-card-label">Current Weather</div>
                <div style="color: {TALE_DARK_TEXT}; margin-top: 1rem;">Weather data unavailable</div>
            </div>
            """, unsafe_allow_html=True)


def render_map_tab(df):
    """Renders the interactive map of AQI stations."""
    st.markdown(f'<div class="section-header">📍 <em>Interactive</em> Air Quality <span>Map</span><div class="line-dec"></div></div>',
                unsafe_allow_html=True)

    # Add Legend
    st.markdown(f"""
    <div style="background-color: white; padding: 1rem; border-radius: 10px; border: 1px solid #e0e0e0; margin-bottom: 1rem;">
        <div style="font-weight: 700; color: {TALE_DARK_BLUE}; margin-bottom: 0.75rem; font-size: 1.1rem;">AQI Color Legend</div>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;"><div style="width: 15px; height: 15px; border-radius: 50%; background-color: rgb(0, 158, 96);"></div><span style="color: #1E293B; font-weight: 500;">Good (0-50)</span></div>
            <div style="display: flex; align-items: center; gap: 0.5rem;"><div style="width: 15px; height: 15px; border-radius: 50%; background-color: rgb(255, 214, 0);"></div><span style="color: #1E293B; font-weight: 500;">Moderate (51-100)</span></div>
            <div style="display: flex; align-items: center; gap: 0.5rem;"><div style="width: 15px; height: 15px; border-radius: 50%; background-color: rgb(249, 115, 22);"></div><span style="color: #1E293B; font-weight: 500;">Unhealthy for Sensitive (101-150)</span></div>
            <div style="display: flex; align-items: center; gap: 0.5rem;"><div style="width: 15px; height: 15px; border-radius: 50%; background-color: rgb(220, 38, 38);"></div><span style="color: #1E293B; font-weight: 500;">Unhealthy (151-200)</span></div>
            <div style="display: flex; align-items: center; gap: 0.5rem;"><div style="width: 15px; height: 15px; border-radius: 50%; background-color: rgb(147, 51, 234);"></div><span style="color: #1E293B; font-weight: 500;">Very Unhealthy (201-300)</span></div>
            <div style="display: flex; align-items: center; gap: 0.5rem;"><div style="width: 15px; height: 15px; border-radius: 50%; background-color: rgb(126, 34, 206);"></div><span style="color: #1E293B; font-weight: 500;">Hazardous (300+)</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.pydeck_chart(pdk.Deck(
        map_style="light",
        initial_view_state=pdk.ViewState(
            latitude=DELHI_LAT, longitude=DELHI_LON, zoom=9.5, pitch=50),
        layers=[pdk.Layer(
            "ScatterplotLayer",
            data=df,
            get_position='[lon, lat]',
            get_fill_color='color',
            get_radius=250,
            pickable=True,
            opacity=0.8,
            stroked=True,
            get_line_color=[0, 0, 0, 100],
            line_width_min_pixels=1,
        )],
        tooltip={"html": "<b>{station_name}</b><br/>AQI: {aqi}<br/>Category: {category}<br/>Last Updated: {last_updated}",
                 "style": {"color": "white"}}
    ))


def render_kriging_tab(df):
    st.markdown(f'<div class="section-header">🌡️ <em>Interpolated</em> AQI <span>Heatmap</span><div class="line-dec"></div></div>', unsafe_allow_html=True)

    delhi_gdf, delhi_polygon = load_delhi_boundary_from_url()
    
    if delhi_gdf is None or delhi_polygon is None:
        st.warning("Cannot render Kriging map: Dependencies (krigging/geopandas) are missing or Delhi shapefile could not be loaded.")
        return
        
    if df.empty:
        st.warning("No AQI stations available.")
        return

    if df["aqi"].nunique() < 2:
        st.error("Kriging cannot run because all AQI values are identical.")
        return

    if len(df) < 4:
        st.error("Not enough AQI stations available for kriging (need ≥ 4).")
        return

    if df[['lat','lon']].duplicated().any():
        st.error("Duplicate station coordinates found — kriging cannot proceed.")
        return

    delhi_bounds_tuple = (28.40, 28.88, 76.84, 77.35)

    with st.spinner("Performing spatial interpolation..."):
        lon_grid, lat_grid, z = perform_kriging_correct(df, delhi_bounds_tuple)


    heatmap_df = pd.DataFrame({
        "lon": lon_grid.flatten(),
        "lat": lat_grid.flatten(),
        "aqi": z.flatten()
    })

    fig = px.density_mapbox(
        heatmap_df,
        lat="lat",
        lon="lon",
        z="aqi",
        radius=10,
        center=dict(lat=28.6139, lon=77.2090),
        zoom=9,
        mapbox_style="carto-positron",
        color_continuous_scale=[
            "#009E60", "#FFD600", "#F97316",
            "#DC2626", "#9333EA", "#7E22CE"
        ]
    )

    st.plotly_chart(fig, use_container_width=True)


def render_alerts_tab(df):
    """Renders health alerts and advice based on current AQI levels."""
    st.markdown(f'<div class="section-header">🔔 <em>Health</em> Alerts & <span>Recommendations</span><div class="line-dec"></div></div>',
                unsafe_allow_html=True)
    max_aqi = df['aqi'].max()
    advice = get_aqi_category(max_aqi)[3]
    st.info(
        f"**Current Situation:** Based on the highest AQI of **{max_aqi:.0f}**, the recommended action is: **{advice}**", icon="ℹ️")

    alerts = {
        "Hazardous": (df[df['aqi'] > 300], "alert-hazardous"),
        "Very Unhealthy": (df[(df['aqi'] > 200) & (df['aqi'] <= 300)], "alert-very-unhealthy"),
        "Unhealthy": (df[(df['aqi'] > 150) & (df['aqi'] <= 200)], "alert-unhealthy")
    }
    has_alerts = False
    for level, (subset, card_class) in alerts.items():
        if not subset.empty:
            has_alerts = True
            st.markdown(
                f"**{subset.iloc[0]['emoji']} {level} Conditions Detected**")
            # Using native Streamlit warnings/errors for consistency with the new color theme
            for _, row in subset.sort_values('aqi', ascending=False).iterrows():
                if level == "Hazardous":
                    st.error(f"{row['station_name']} | **AQI {row['aqi']:.0f}**", icon="🚨")
                else:
                    st.warning(f"{row['station_name']} | **AQI {row['aqi']:.0f}**", icon="⚠️")
            
    if not has_alerts:
        st.success("✅ No significant air quality alerts at the moment. AQI levels are currently within the good to moderate range for most areas.", icon="✅")


def render_alert_subscription_tab(df):
    """Renders alert subscription form."""
    st.markdown(f'<div class="section-header">📱 <em>SMS</em> Alert <span>Subscription</span><div class="line-dec"></div></div>',
                unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background-color: {TALE_LIGHT_BG}; padding: 1rem; border-radius: 10px; border-left: 4px solid {TALE_ORANGE}; margin-bottom: 1.5rem;">
        <p style="color: {TALE_DARK_BLUE}; margin: 0; font-weight: 500;">
        📍 Get real-time air quality and weather alerts for your location via SMS. 
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        location_name = st.text_input(
            "📍 Your Location Name",
            placeholder="e.g., Connaught Place, New Delhi",
            help="Enter your area/locality name"
        )

        user_lat = st.number_input(
            "Latitude",
            min_value=28.4,
            max_value=28.9,
            value=28.6139,
            step=0.0001,
            format="%.4f",
            help="Your location's latitude"
        )

        user_lon = st.number_input(
            "Longitude",
            min_value=76.8,
            max_value=77.4,
            value=77.2090,
            step=0.0001,
            format="%.4f",
            help="Your location's longitude"
        )

    with col2:
        phone_number = st.text_input(
            "📱 Phone Number",
            placeholder="+91XXXXXXXXXX",
            help="Enter with country code (e.g., +919876543210)"
        )

        radius = st.slider(
            "Search Radius (km)",
            min_value=1,
            max_value=20,
            value=10,
            help="Find stations within this radius"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        send_alert_btn = st.button(
            "📤 Send Alert Now", type="primary", use_container_width=True)

    if send_alert_btn:
        if not location_name or not phone_number:
            st.error(
                "Please fill in all required fields: Location Name and Phone Number", icon="⚠️")
        elif not phone_number.startswith('+'):
            st.error(
                "Phone number must include country code (e.g., +919876543210)", icon="⚠️")
        else:
            with st.spinner("Finding nearby stations and preparing alert..."):
                nearby_stations = get_nearby_stations(
                    df, user_lat, user_lon, radius)

                if nearby_stations.empty:
                    st.warning(
                        f"No monitoring stations found within {radius} km of your location. Try increasing the search radius.", icon="⚠️")
                else:
                    weather_data = fetch_weather_data()
                    alert_message = create_alert_message(
                        nearby_stations, weather_data, location_name)

                    st.markdown("### 📄 Alert Preview")
                    st.info(alert_message)

                    st.markdown("### 📍 Nearby Monitoring Stations")
                    display_nearby = nearby_stations[[
                        'station_name', 'aqi', 'category', 'distance']].head(5)
                    display_nearby['distance'] = display_nearby['distance'].round(
                        2).astype(str) + ' km'
                    st.dataframe(display_nearby,
                                 use_container_width=True, hide_index=True)

                    success, message = send_sms_alert(
                        phone_number, alert_message)

                    if success:
                        st.success(message, icon="✅")
                    else:
                        st.error(message, icon="❌")
                        st.info("💡 **Note:** Twilio setup is required to send real SMS messages. Please replace placeholder credentials.", icon="ℹ️")


def render_dummy_forecast_tab():
    """Render a dummy 24-hour AQI forecast using simulated data."""
    st.markdown(f'<div class="section-header">📈 <em>24-Hour</em> AQI <span>Forecast</span><div class="line-dec"></div></div>',
                unsafe_allow_html=True)

    st.markdown(f"""
    <p style="color: {TALE_DARK_TEXT};">
    This sample forecast simulates how the Air Quality Index (AQI) may change over the next 24 hours.
    </p>
    """)

    # Simulate a smooth AQI forecast for 24 hours
    hours = np.arange(0, 24)
    base_aqi = 120 + 40 * np.sin(hours / 3) + np.random.normal(0, 5, size=24)
    timestamps = [datetime.now() + timedelta(hours=i) for i in range(24)]
    forecast_df = pd.DataFrame({
        "timestamp": timestamps,
        "forecast_aqi": np.clip(base_aqi, 40, 300)
    })

    # Plot forecast trend
    fig = px.line(
        forecast_df,
        x="timestamp",
        y="forecast_aqi",
        title="Predicted AQI Trend for Next 24 Hours (Simulated)",
        markers=True,
        line_shape="spline"
    )
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Predicted AQI",
        showlegend=False,
        margin=dict(t=40, b=20, l=0, r=20),
        paper_bgcolor='white',
        plot_bgcolor='white',
        title_font_color=TALE_DARK_BLUE,
        font_color=TALE_DARK_TEXT,
        xaxis=dict(gridcolor='#e0e0e0'),
        yaxis=dict(gridcolor='#e0e0e0')
    )

    st.plotly_chart(fig, use_container_width=True)

    # Display summary
    avg_aqi = forecast_df["forecast_aqi"].mean()
    max_aqi = forecast_df["forecast_aqi"].max()
    min_aqi = forecast_df["forecast_aqi"].min()

    st.markdown(f"""
    <div style="background-color: white; padding: 1rem; border-radius: 10px; border-left: 5px solid {TALE_ORANGE}; margin-top: 1rem; color: {TALE_DARK_TEXT};">
        <b>Average Forecasted AQI:</b> {avg_aqi:.1f}  <br>
        <br><b>Expected Range:</b> {min_aqi:.1f} – {max_aqi:.1f}<br>
        <br><b>Air Quality Outlook:</b> Moderate to Unhealthy range over the next day.<br>
    </div>
    """, unsafe_allow_html=True)

def render_analytics_tab(df):
    """Renders charts and data analytics."""
    st.markdown(f'<div class="section-header">📊 <em>Data</em> <span>Analytics</span><div class="line-dec"></div></div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1])

    with c1:
        st.markdown("**AQI Category Distribution**")
        category_counts = df['category'].value_counts()
        fig = px.pie(
            values=category_counts.values, names=category_counts.index, hole=0.4,
            color=category_counts.index,
            color_discrete_map={
                "Good": "#009E60", "Moderate": "#FFD600", "Unhealthy for Sensitive Groups": "#F97316",
                "Unhealthy": "#DC2626", "Very Unhealthy": "#9333EA", "Hazardous": "#7E22CE"
            }
        )
        fig.update_traces(textinfo='percent+label',
                          pull=[0.05]*len(category_counts.index))
        fig.update_layout(
            showlegend=False,
            margin=dict(t=0, b=0, l=0, r=0),
            paper_bgcolor='white', 
            plot_bgcolor='white'  
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("**Top 10 Most Polluted Stations**")
        top_10 = df.nlargest(10, 'aqi').sort_values('aqi', ascending=True)
        fig = px.bar(
            top_10, x='aqi', y='station_name', orientation='h',
            color='aqi', color_continuous_scale=px.colors.sequential.Reds
        )
        fig.update_layout(
            xaxis_title="AQI",
            yaxis_title="",
            showlegend=False,
            margin=dict(t=20, b=20, l=0, r=20),
            paper_bgcolor='white', 
            plot_bgcolor='white',   
            xaxis=dict(gridcolor='#e0e0e0'),
            yaxis=dict(gridcolor='#e0e0e0')
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Full Station Data**")
    display_df = df[['station_name', 'aqi', 'category',
                     'last_updated']].sort_values('aqi', ascending=False)
    st.dataframe(display_df, use_container_width=True, hide_index=True)


# ==========================
# MAIN APP EXECUTION
# ==========================
aqi_data = fetch_live_data()
render_header(aqi_data)

if aqi_data.empty:
    st.error("⚠️ **Could not fetch live AQI data.** The API may be down or there's a network issue. Please try again later.", icon="🚨")
else:
    # Use st.tabs with the new, clean styling
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["🗺️ Live Map", "🔔 Alerts & Health",
         "📊 Analytics", "📱 SMS Alerts","📈 Forecast","🔥 Kriging Heatmap"])

    # Wrap each tab's content in the custom "content-card" div
    with tab1:
        with st.container():
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            render_map_tab(aqi_data)
            st.markdown('</div>', unsafe_allow_html=True)
    with tab2:
        with st.container():
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            render_alerts_tab(aqi_data)
            st.markdown('</div>', unsafe_allow_html=True)
    with tab3:
        with st.container():
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            render_analytics_tab(aqi_data)
            st.markdown('</div>', unsafe_allow_html=True)
    with tab4:
        with st.container():
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            render_alert_subscription_tab(aqi_data)
            st.markdown('</div>', unsafe_allow_html=True)
    with tab5:
        with st.container():
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            render_dummy_forecast_tab()
            st.markdown('</div>', unsafe_allow_html=True)
    with tab6:
        with st.container():
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            render_kriging_tab(aqi_data)
            st.markdown('</div>', unsafe_allow_html=True)
