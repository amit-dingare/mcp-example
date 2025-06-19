"""Weather tool for location information using OpenWeatherMap API"""
import asyncio
import aiohttp
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file in parent directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

TOOL_NAME = "weather"
TOOL_DESCRIPTION = "Get current weather information for a location using OpenWeatherMap API"

# Get API key from environment variable
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '')

async def tool_function(location: str) -> str:
    """Get weather for location using OpenWeatherMap API"""
    try:
        if not OPENWEATHER_API_KEY or OPENWEATHER_API_KEY == 'your_openweather_api_key_here':
            return f"""🌤️ Weather API key not configured properly.

To get real weather data:
1. Sign up for a free API key at https://openweathermap.org/api
2. Edit the .env file in the project root
3. Replace 'your_openweather_api_key_here' with your actual API key
4. Restart the server

For now, showing mock data for {location}: 22°C, Sunny with light clouds"""
        
        # Call OpenWeatherMap API
        url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': location,
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric'  # Use metric units (Celsius, m/s, etc.)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract weather information
                    city = data['name']
                    country = data['sys']['country']
                    temp = data['main']['temp']
                    feels_like = data['main']['feels_like']
                    humidity = data['main']['humidity']
                    pressure = data['main']['pressure']
                    description = data['weather'][0]['description'].title()
                    wind_speed = data['wind']['speed']
                    
                    # Format the response
                    weather_info = f"""🌤️ Weather in {city}, {country}:
Temperature: {temp}°C (feels like {feels_like}°C)
Conditions: {description}
Humidity: {humidity}%
Pressure: {pressure} hPa
Wind Speed: {wind_speed} m/s"""
                    
                    return weather_info
                    
                elif response.status == 404:
                    return f"❌ Location '{location}' not found. Please check the spelling and try again."
                elif response.status == 401:
                    return f"❌ Invalid API key. Please check your OpenWeatherMap API key in the .env file."
                else:
                    error_data = await response.json()
                    return f"❌ Weather API error: {error_data.get('message', 'Unknown error')}"
                    
    except aiohttp.ClientError as e:
        return f"❌ Network error while fetching weather: {str(e)}"
    except json.JSONDecodeError:
        return f"❌ Error parsing weather data"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"