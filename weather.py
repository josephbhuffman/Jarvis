import requests

class WeatherAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://api.weatherapi.com/v1"
    
    def get_current_weather(self, location="Quincy, IL"):
        """Get current weather for location"""
        try:
            url = f"{self.base_url}/current.json"
            params = {
                "key": self.api_key,
                "q": location,
                "aqi": "no"
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if response.status_code == 200:
                current = data['current']
                location_data = data['location']
                
                weather = {
                    "temp_f": current['temp_f'],
                    "temp_c": current['temp_c'],
                    "condition": current['condition']['text'],
                    "feels_like_f": current['feelslike_f'],
                    "humidity": current['humidity'],
                    "wind_mph": current['wind_mph'],
                    "location": f"{location_data['name']}, {location_data['region']}"
                }
                
                return weather
            else:
                return None
                
        except Exception as e:
            print(f"Weather API error: {e}")
            return None
    
    def get_forecast(self, location="Quincy, IL", days=3):
        """Get weather forecast"""
        try:
            url = f"{self.base_url}/forecast.json"
            params = {
                "key": self.api_key,
                "q": location,
                "days": days,
                "aqi": "no"
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if response.status_code == 200:
                forecast_days = []
                for day in data['forecast']['forecastday']:
                    forecast_days.append({
                        "date": day['date'],
                        "max_temp_f": day['day']['maxtemp_f'],
                        "min_temp_f": day['day']['mintemp_f'],
                        "condition": day['day']['condition']['text'],
                        "chance_of_rain": day['day']['daily_chance_of_rain']
                    })
                
                return forecast_days
            else:
                return None
                
        except Exception as e:
            print(f"Forecast API error: {e}")
            return None
    
    def get_weather_summary(self, location="Quincy, IL"):
        """Get human-readable weather summary"""
        weather = self.get_current_weather(location)
        
        if weather:
            temp = int(weather['temp_f'])
            condition = weather['condition']
            feels_like = int(weather['feels_like_f'])
            
            summary = f"It's currently {temp}°F and {condition.lower()} in {weather['location']}"
            
            if abs(temp - feels_like) > 5:
                summary += f", feels like {feels_like}°F"
            
            return summary
        else:
            return "I couldn't get the weather right now."

# Test
if __name__ == "__main__":
    weather = WeatherAPI("d1973d164bd642c2b4805536262602")
    print(weather.get_weather_summary())
