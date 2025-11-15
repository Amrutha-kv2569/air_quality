import os
import requests
from twilio.rest import Client
from typing import Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# --- CONFIGURATION (Load environment variables securely) ---
# NOTE: Render uses environment variables directly, but dotenv is good for local testing
load_dotenv() 

API_TOKEN = os.getenv("WAQI_API_TOKEN", "97a0e712f47007556b57ab4b14843e72b416c0f9")
DELHI_BOUNDS = "28.404,76.840,28.883,77.349"
# Twilio details must be set in Render environment variables
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# --- INITIAL SETUP ---
app = FastAPI(title="Delhi AQI Backend API")

# Configure CORS to allow your frontend (e.g., netlify.app, vercel.app) to access the API
origins = [
    "*", # CHANGE THIS TO YOUR FRONTEND DOMAIN IN PRODUCTION
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- UTILITY FUNCTIONS (Rewritten from Streamlit to standard Python) ---

def get_aqi_category(aqi: float):
    """Categorizes AQI value and provides advice."""
    if aqi <= 50:
        return "Good", "Enjoy outdoor activities."
    elif aqi <= 100:
        return "Moderate", "Sensitive people should limit prolonged exertion."
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups", "Sensitive groups should reduce prolonged or heavy exertion."
    elif aqi <= 200:
        return "Unhealthy", "Everyone may begin to experience health effects."
    else:
        return "Hazardous", "Health warnings of emergency conditions. Stay indoors."

def fetch_live_data_internal():
    """Fetches and processes live AQI data from the WAQI API."""
    url = f"https://api.waqi.info/map/bounds/?latlng={DELHI_BOUNDS}&token={API_TOKEN}"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "ok":
            return [
                {
                    "aqi": float(station['aqi']) if station['aqi'] != "-" else None,
                    "lat": station['lat'],
                    "lon": station['lon'],
                    "station_name": station.get('station', {}).get('name', 'N/A'),
                    "last_updated": station.get('station', {}).get('time', {}).get('s', 'N/A'),
                    "category": get_aqi_category(float(station['aqi']) if station['aqi'] != "-" else 0)[0],
                }
                for station in data["data"] if station.get('aqi') and station['aqi'] != "-"
            ]
        return []
    except requests.RequestException as e:
        print(f"API Fetch Error: {e}")
        return []

def send_sms_alert_internal(phone_number: str, message: str) -> Dict[str, str]:
    """Send SMS alert using Twilio."""
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        raise HTTPException(status_code=500, detail="Twilio credentials not configured in environment.")
    
    if not phone_number.startswith('+'):
        raise HTTPException(status_code=400, detail="Phone number must include country code starting with '+'")

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        sent_message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        return {"status": "success", "sid": sent_message.sid, "message": f"Alert sent successfully to {phone_number}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Twilio error: {str(e)}")

# --- API MODELS (Pydantic for validation) ---

class StationData(BaseModel):
    aqi: float
    lat: float
    lon: float
    station_name: str
    last_updated: str
    category: str

class SMSRequest(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+\d{10,15}$", description="E.164 format, e.g., +919876543210")
    message: str

# --- API ENDPOINTS ---

@app.get("/api/aqi/live", response_model=list[StationData])
async def get_live_aqi_data():
    """Endpoint to fetch and clean live AQI data for the map and metrics."""
    data = fetch_live_data_internal()
    if not data:
        raise HTTPException(status_code=503, detail="Could not fetch live AQI data from external source.")
    return data

@app.post("/api/sms/alert")
async def send_sms_alert_endpoint(request: SMSRequest):
    """Endpoint to securely send an SMS alert via Twilio."""
    try:
        result = send_sms_alert_internal(request.phone_number, request.message)
        return result
    except HTTPException as e:
        # Re-raise HTTP exceptions with status code
        raise e
    except Exception as e:
        # Catch other errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Delhi AQI API is running. See /docs for endpoints."}
