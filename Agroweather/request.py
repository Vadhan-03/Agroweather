import requests

# API URL
url = "http://api.weatherapi.com/v1/forecast.json?key=8020d4c562174c73949144417252404&q=tiruvallur&days=14&aqi=yes&alerts=yes"

# Request data
response = requests.get(url)
data = response.json()

# Extract unique weather conditions
unique_conditions = set()

if "forecast" in data:
    for day in data["forecast"]["forecastday"]:
        condition = day["day"]["condition"]["text"]
        unique_conditions.add(condition)

    print("🌦️ Unique Weather Conditions for Tiruvallur (Next 14 Days):")
    for cond in unique_conditions:
        print(f"• {cond}")
else:
    print("⚠️ Failed to retrieve forecast data.")
