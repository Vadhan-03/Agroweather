import os
import pandas as pd
import requests
from flask import Flask, request, jsonify, render_template, redirect, url_for
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier
from sklearn.metrics import classification_report
from sqlalchemy import create_engine
from twilio.rest import Client
from googletrans import Translator


# --- Config ---
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', 'your weather api key')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_SID', 'your twilio sid') 
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_TOKEN', 'your twilio token')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_FROM', 'Your Twilio Number')
DEFAULT_LOCATION = os.getenv('DEFAULT_LOCATION', 'Tiruvallur')
DB_URI = os.getenv('DATABASE_URI', 'mysql+pymysql://root:1234@localhost/farmers_data')

# --- App Setup ---
app = Flask(__name__, static_folder='static', template_folder='templates')
engine = create_engine(DB_URI)

# --- Model Setup ---
# Load and preprocess data
try:
    agro_weather_data = pd.read_csv('data/agro_weather_data.csv')
except FileNotFoundError:
    # Fallback path if the file is not in the expected location
    agro_weather_data = pd.read_csv('agro_weather_data.csv')

# Fill missing values
agro_weather_data['winddirection'].fillna(agro_weather_data['winddirection'].mean())
agro_weather_data['windspeed'].fillna(agro_weather_data['windspeed'].mean())

# Encode the target variable
label_encoder = LabelEncoder()
agro_weather_data['rainfall'] = label_encoder.fit_transform(agro_weather_data['rainfall'])

# Split the data
X = agro_weather_data.drop(columns=['rainfall'])
y = agro_weather_data['rainfall']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the model
xgb_model = XGBClassifier(
    objective='binary:logistic',
    learning_rate=0.05,
    max_depth=6,
    n_estimators=1000,
    verbosity=0,
    early_stopping_rounds=50,
    use_label_encoder=False
)
xgb_model.fit(X_train, y_train, eval_set=[(X_train, y_train), (X_test, y_test)], verbose=False)

# Get rainfall prediction probability
y_pred_proba = xgb_model.predict_proba(X_test)
rainfall_percentage = y_pred_proba[:, 1] * 100

# --- Helper Functions ---
def fetch_weather_data(WEATHER_API_KEY, location, days=1):
    """Fetch weather data from the API"""
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={location}&days={days}&aqi=yes&alerts=yes"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None

def get_forecast_block(hour_data):
    """Format the forecast data block"""
    return {
        "time": hour_data['time'].split()[1],
        "temp": hour_data['temp_c'],
        "condition": hour_data['condition']['text'],
        "humidity": hour_data['humidity'],
        "wind_kph": hour_data['wind_kph'],
        "wind_dir": hour_data['wind_dir']
    }

def get_advisory(forecast_data, crop_type, specific_hour, rainfall_prediction_percentage):
    """Generate crop-specific advisory based on weather data"""
    hour_data = forecast_data['forecast']['forecastday'][0]['hour'][specific_hour]
    weather_condition = hour_data['condition']['text']
    temperature = hour_data['temp_c']
    humidity = hour_data['humidity']

    advisory_message = (f"In the next {specific_hour} hour(s), weather will be {weather_condition}. "
                        f"Temperature will be {temperature}°C & Humidity will be {humidity}%. "
                        f"Predicted rainfall: {rainfall_prediction_percentage:.1f}%. ")

    # Crop-specific advice
    if crop_type == "Rice":
        if temperature > 30:
            advisory_message += "Irrigate the field to prevent water stress."
        elif humidity < 50:
            advisory_message += "Consider irrigation to maintain soil moisture."
    elif crop_type == "Tomatoes":
        if humidity > 70:
            advisory_message += "Apply fungicides to prevent blight."
    elif crop_type == "Mangoes":
        if temperature > 35:
            advisory_message += "Ensure adequate watering to prevent fruit drop."
    elif crop_type == "Sugarcane":
        if humidity < 60:
            advisory_message += "Consider irrigation to support growth."
    elif crop_type == "Okra":
        if temperature > 32:
            advisory_message += "Water the plants to promote healthy growth."
    elif crop_type == "Bananas":
        if humidity < 50:
            advisory_message += "Increase watering to prevent stress."
    elif crop_type == "Millets":
        if temperature > 30 and humidity < 40:
            advisory_message += "Provide adequate irrigation."
    elif crop_type == "Brinjal":
        if humidity > 60:
            advisory_message += "Watch for pests and apply pesticides if necessary."
    elif crop_type == "Vegetables":
        if temperature > 28:
            advisory_message += "Ensure proper watering to keep the plants hydrated."
    elif crop_type == "Finger Millet":
        if humidity < 50:
            advisory_message += "Irrigate to maintain soil moisture."
    elif crop_type == "Groundnut":
        if temperature > 30:
            advisory_message += "Water the plants to avoid stress."
    elif crop_type == "Pulses":
        if humidity > 70:
            advisory_message += "Apply fungicides to prevent diseases."
    elif crop_type == "Fruits":
        if temperature > 30 and humidity < 50:
            advisory_message += "Ensure adequate watering to support fruit development."
    else:
        advisory_message += "Monitor weather conditions regularly and adjust farming practices accordingly."

    return advisory_message

def send_sms(mobile_numbers, message):
    """Send SMS using Twilio"""
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    responses = []
    
    # Convert single number to list if needed
    if isinstance(mobile_numbers, str):
        mobile_numbers = [mobile_numbers]
        
    for mobile_number in mobile_numbers:
        try:
            message_response = client.messages.create(
                body=message,
                from_=TWILIO_PHONE_NUMBER,
                to=mobile_number
            )
            print(f"Message sent to {mobile_number}: {message_response.sid}")
            responses.append({'to': mobile_number, 'sid': message_response.sid})
        except Exception as e:
            print(f"Failed to send message to {mobile_number}: {e}")
            responses.append({'to': mobile_number, 'error': str(e)})
    
    return responses

def get_farmers_data():
    """Fetch farmers data from database"""
    try:
        query = "SELECT mobile_number, crops_cultivated FROM farmers"
        farmers_df = pd.read_sql(query, engine)
        return farmers_df
    except Exception as e:
        print(f"Error fetching farmers data: {e}")
        return pd.DataFrame(columns=['mobile_number', 'crops_cultivated'])

# --- Routes ---
@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login functionality"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'admin123':
            return redirect(url_for('admin_dashboard'))
        return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    """Render admin dashboard"""
    return render_template('admin.html')

# --- API: Weather Data (Page 1) ---
@app.route('/api/weather/current')
def current_weather():
    """Return weather data for a selected date"""
    location = request.args.get('location', DEFAULT_LOCATION)
    selected_date = request.args.get('date')

    data = fetch_weather_data(WEATHER_API_KEY, location, days=14)
    
    if not data:
        return jsonify({"error": "Failed to fetch weather data"}), 500
    
    current = data['current']
    
    # Find the matching day
    forecast_day = None
    if selected_date:
        for day in data['forecast']['forecastday']:
            if day['date'] == selected_date:
                forecast_day = day
                current_hour = int(current['last_updated'].split()[1].split(':')[0])
                break
    else:
        forecast_day = data['forecast']['forecastday'][0]
        current_hour = int(current['last_updated'].split()[1].split(':')[0])

    if not forecast_day:
        return jsonify({"error": "Selected date forecast not found"}), 404

    # Get current time's forecast for the selected date
    #current_time = current['last_updated'].split()[1]
    current_hour_data = forecast_day['hour'][current_hour]

    # Prepare forecast data
    forecast = [get_forecast_block(hour) for hour in forecast_day['hour']]

    return jsonify({
        "location": f"{data['location']['name']}, {data['location']['country']}",
        "datetime": current['last_updated'] if not selected_date else f"{forecast_day['date']} {current['last_updated'].split()[1]}",
        "weather": current['condition']['text'] if not selected_date else current_hour_data['condition']['text'],
        "temp": current['temp_c'] if not selected_date else current_hour_data['temp_c'],
        "feels_like": current['feelslike_c'] if not selected_date else current_hour_data['feelslike_c'],
        "cloud": current_hour_data['cloud'],
        "humidity": current['humidity'] if not selected_date else current_hour_data['humidity'],
        "uv_index": current['uv'] if not selected_date else current_hour_data['uv'],
        "wind_dir": current['wind_dir'] if not selected_date else current_hour_data['wind_dir'],
        "wind_kph": current['wind_kph'] if not selected_date else current_hour_data['wind_kph'],
        "pressure_mb": current['pressure_mb'] if not selected_date else current_hour_data['pressure_mb'],
        "rain": forecast_day['day']['daily_will_it_rain'],
        "snow": forecast_day['day']['daily_chance_of_snow'],
        "max_temp": forecast_day['day']['maxtemp_c'],
        "min_temp": forecast_day['day']['mintemp_c'],
        "forecast": forecast
    })

# --- API: Weather Advisory (Page 3) ---
@app.route('/api/weather/advisory')
def weather_advisory():
    """Return weather advisory for specific crop"""
    location = request.args.get('location', DEFAULT_LOCATION)
    crop = request.args.get('crop', 'generic')
    hour = int(request.args.get('hour', 2))
    
    data = fetch_weather_data(WEATHER_API_KEY, location) 
    if not data:
        return jsonify({"error": "Failed to fetch weather data"}), 500
    
    rainfall_pred = rainfall_percentage.mean()
    advisory = get_advisory(data, crop, hour, rainfall_pred)
    
    return jsonify({
        "advisory": advisory,
        "crop": crop,
        "location": location,
        "hour": hour,
        "rainfall_probability": float(rainfall_pred)
    })

# --- API: Send SMS Notifications ---
@app.route('/api/notify', methods=['POST'])
def notify():
    """Send SMS notifications to farmers"""
    payload = request.get_json()
    message = payload.get('message')
    numbers = payload.get('numbers', [])
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    if not numbers:
        return jsonify({"error": "At least one mobile number is required"}), 400
    
    responses = send_sms(numbers, message)
    return jsonify(responses)

# --- API: Get Farmers Data ---
@app.route('/api/farmers')
def farmers_data():
    """Return all farmers data"""
    try:
        farmers = get_farmers_data()
        return jsonify(farmers.to_dict(orient='records'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- API: Send Bulk Advisory ---
@app.route('/api/send-bulk-advisory', methods=['POST'])
def send_bulk_advisory():
    """Send weather advisory to all farmers"""
    location = request.json.get('location', DEFAULT_LOCATION)
    hour = int(request.json.get('hour', 2))
    
    weather_data = fetch_weather_data(WEATHER_API_KEY, location)
    if not weather_data:
        return jsonify({"error": "Failed to fetch weather data"}), 500
    
    farmers_df = get_farmers_data()
    if farmers_df.empty:
        return jsonify({"error": "No farmers found in database"}), 404
    
    responses = []
    for i, row in farmers_df.iterrows():
        mobile_number = row['mobile_number']
        crop_type = row.get('crops_cultivated', 'generic')
        
        rainfall_pred = rainfall_percentage.mean()
        advisory_message = get_advisory(weather_data, crop_type, hour, rainfall_pred)
        
        # Send SMS
        result = send_sms(mobile_number, advisory_message)
        responses.append({
            "farmer": mobile_number,
            "crop": crop_type,
            "message": advisory_message,
            "status": result
        })
    
    return jsonify({
        "messages_sent": len(responses),
        "responses": responses
    })

# --- Helper route to demonstrate manual SMS sending ---
@app.route('/send-test-sms')
def send_test_sms():
    """Send a test SMS to specified numbers"""
    mobile_numbers = request.args.get('numbers', 'registered mobile numbers').split(',')
    location = request.args.get('location', DEFAULT_LOCATION)
    hour = int(request.args.get('hour', 2))
    
    weather_data = fetch_weather_data(WEATHER_API_KEY, location)
    if not weather_data:
        return jsonify({"error": "Failed to fetch weather data"}), 500
    
    rainfall_pred = rainfall_percentage.mean()
    advisory_message = get_advisory(weather_data, 'generic crop', hour, rainfall_pred)
    
    results = send_sms(mobile_numbers, advisory_message)
    return jsonify({
        "message": advisory_message,
        "results": results
    })

# Add this route after your existing routes


def translate_to_tamil(text):
    """Translate text to Tamil but fix specific location names after translation"""
    translator = Translator()
    
    # Dictionary of location-specific corrections (incorrect → correct)
    location_corrections = {
        'திருவல்லூர்': 'திருவள்ளூர்',
        'திருவல்லூருக்கான': 'திருவள்ளூர்',
        'அவதிக்கான':'ஆவடி',
        'ஆவடிக்கு':'ஆவடி',
        'சென்னைக்கான': 'சென்னை',
        'சென்னைக்கு': 'சென்னை',
        # Add more corrections as needed
    }
    
    try:
        # First, translate the entire text normally
        result = translator.translate(text, dest='ta')
        translated_text = result.text
        
        # After translation, apply our specific corrections
        for incorrect, correct in location_corrections.items():
            translated_text = translated_text.replace(incorrect, correct)
        
        return translated_text
    except Exception as e:
        print(f"Translation error: {e}")
        return text

@app.route('/send-advisory', methods=['POST'])
def handle_send_advisory():
    """Handle sending weather advisory from admin dashboard"""
    try:
        data = request.json
        location = data.get('city', DEFAULT_LOCATION)
        
        # Default phone numbers (you can modify these)
        mobile_numbers = ['registered mobile numbers']
        
        # Get weather data
        weather_data = fetch_weather_data(WEATHER_API_KEY, location)
        if not weather_data:
            return jsonify({"error": "Failed to fetch weather data"}), 500
        
        data['condition'] = weather_data['current']['condition']['text']
        
        # Create advisory message using the data sent from frontend
        english_message= f"""
Weather Advisory for {data['city']} on {data.get('date', 'selected date')}:
Temperature: {data['temperature']}°C
Wind: {data['windDirection']} at {data['windSpeed']} kph
Humidity: {data['humidity']}%
Rain Chance: {data['rainChance']}%
"""
        tamil_message = translate_to_tamil(english_message)
        
        # Send both English and Tamil messages
        
        # Send SMS
        results = send_sms(mobile_numbers, tamil_message)
        
        
        return jsonify({
            "success": True,
            "message": "Advisory sent successfully in Tamil",
            "results": results,
            "tamil": tamil_message
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
