import os
import requests
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

class WeatherHandler:
    def __init__(self):
        self.api_key = os.environ['OPENWEATHERMAP_API_KEY']
        self.base_url = 'http://api.openweathermap.org/data/2.5/weather'
        
        # Initialize cache in session state
        if 'weather_cache' not in st.session_state:
            st.session_state.weather_cache = {}
        if 'weather_cache_time' not in st.session_state:
            st.session_state.weather_cache_time = {}

    def get_weather(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Get weather data for given coordinates with caching
        """
        # Create cache key from coordinates (rounded to 2 decimal places)
        cache_key = f"{round(lat, 2)},{round(lon, 2)}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            return st.session_state.weather_cache[cache_key]
            
        try:
            # Fetch new weather data
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'imperial'  # Use imperial units (Fahrenheit)
            }
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            weather_data = response.json()
            
            # Format weather data
            formatted_data = {
                'temperature': round(weather_data['main']['temp']),
                'feels_like': round(weather_data['main']['feels_like']),
                'humidity': weather_data['main']['humidity'],
                'description': weather_data['weather'][0]['description'].capitalize(),
                'icon': weather_data['weather'][0]['icon'],
                'wind_speed': round(weather_data['wind']['speed']),
                'timestamp': datetime.now()
            }
            
            # Update cache
            st.session_state.weather_cache[cache_key] = formatted_data
            st.session_state.weather_cache_time[cache_key] = datetime.now()
            
            return formatted_data
            
        except Exception as e:
            st.error(f"Error fetching weather data: {str(e)}")
            return None
            
    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if cached weather data is still valid (less than 30 minutes old)
        """
        if cache_key in st.session_state.weather_cache_time:
            cache_age = datetime.now() - st.session_state.weather_cache_time[cache_key]
            return cache_age < timedelta(minutes=30)
        return False

    def get_weather_icon_url(self, icon_code: str) -> str:
        """
        Get the URL for a weather icon
        """
        return f"http://openweathermap.org/img/w/{icon_code}.png"

    def format_weather_html(self, weather_data: Dict) -> str:
        """
        Format weather data as HTML for display
        """
        if not weather_data:
            return ""
            
        return f"""
        <div style="padding: 10px; background-color: #f0f2f6; border-radius: 10px; margin: 10px 0;">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <img src="{self.get_weather_icon_url(weather_data['icon'])}" 
                     style="width: 50px; height: 50px;" 
                     alt="Weather icon">
                <div style="margin-left: 10px;">
                    <div style="font-size: 24px; font-weight: bold;">
                        {weather_data['temperature']}°F
                    </div>
                    <div style="color: #666;">
                        {weather_data['description']}
                    </div>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                <div>Feels like: {weather_data['feels_like']}°F</div>
                <div>Humidity: {weather_data['humidity']}%</div>
                <div>Wind: {weather_data['wind_speed']} mph</div>
            </div>
        </div>
        """
