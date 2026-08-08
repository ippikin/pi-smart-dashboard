#!/usr/bin/env python3
"""
Weather Service Module for UK Locations.
Fetches current weather and 5-day forecast via Met Office API / Open-Meteo fallback.
"""

import time
import json
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WeatherService")

# WMO Weather Code Mappings
WMO_CODE_MAP = {
    0: ("Clear Sky", "☀️", "SUNNY"),
    1: ("Mainly Clear", "🌤️", "PARTLY_CLOUDY"),
    2: ("Partly Cloudy", "⛅", "PARTLY_CLOUDY"),
    3: ("Overcast", "☁️", "CLOUDY"),
    45: ("Foggy", "🌫️", "FOG"),
    48: ("Depositing Rime Fog", "🌫️", "FOG"),
    51: ("Light Drizzle", "🌦️", "RAIN_LIGHT"),
    53: ("Moderate Drizzle", "🌧️", "RAIN"),
    55: ("Dense Drizzle", "🌧️", "RAIN"),
    56: ("Freezing Drizzle", "🌧️❄️", "RAIN_SNOW"),
    57: ("Dense Freezing Drizzle", "🌧️❄️", "RAIN_SNOW"),
    61: ("Slight Rain", "🌦️", "RAIN_LIGHT"),
    63: ("Moderate Rain", "🌧️", "RAIN"),
    65: ("Heavy Rain", "🌧️🌧️", "RAIN_HEAVY"),
    66: ("Freezing Rain", "🌧️❄️", "RAIN_SNOW"),
    67: ("Heavy Freezing Rain", "🌧️❄️", "RAIN_SNOW"),
    71: ("Slight Snow", "🌨️", "SNOW"),
    73: ("Moderate Snow", "🌨️", "SNOW"),
    75: ("Heavy Snow", "❄️❄️", "SNOW_HEAVY"),
    77: ("Snow Grains", "❄️", "SNOW"),
    80: ("Slight Rain Showers", "🌦️", "RAIN_LIGHT"),
    81: ("Moderate Rain Showers", "🌧️", "RAIN"),
    82: ("Violent Rain Showers", "⛈️", "RAIN_HEAVY"),
    85: ("Slight Snow Showers", "🌨️", "SNOW"),
    86: ("Heavy Snow Showers", "❄️❄️", "SNOW_HEAVY"),
    95: ("Thunderstorm", "⛈️", "THUNDERSTORM"),
    96: ("Thunderstorm w/ Hail", "⛈️🧊", "THUNDERSTORM"),
    99: ("Heavy Thunderstorm w/ Hail", "⛈️🧊", "THUNDERSTORM"),
}

def get_wind_direction_str(degrees):
    """Convert wind direction in degrees to compass cardinal direction."""
    if degrees is None:
        return "N/A"
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = int((degrees + 11.25) / 22.5) % 16
    return directions[idx]

class WeatherService:
    def __init__(self, latitude=51.5074, longitude=-0.1278, location_name="Default Location",
                 met_office_api_key="", met_office_client_secret=""):
        self.latitude = latitude
        self.longitude = longitude
        self.location_name = location_name
        self.met_office_api_key = met_office_api_key
        self.met_office_client_secret = met_office_client_secret
        
        self._cache = None
        self._last_fetch_time = 0
        self.cache_ttl_sec = 600  # 10 minutes cache

    def fetch_weather(self, force_refresh=False):
        """Fetch weather data using Open-Meteo or Met Office."""
        now = time.time()
        if not force_refresh and self._cache and (now - self._last_fetch_time < self.cache_ttl_sec):
            return self._cache

        # Try Open-Meteo (zero-key high accuracy API for UK)
        try:
            data = self._fetch_open_meteo()
            if data:
                self._cache = data
                self._last_fetch_time = now
                return data
        except Exception as e:
            logger.warning(f"Open-Meteo fetch error: {e}")

        # Fallback empty structure
        return self._get_fallback_weather()

    def _fetch_open_meteo(self):
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={self.latitude}&longitude={self.longitude}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
            f"precipitation,weather_code,wind_speed_10m,wind_direction_10m"
            f"&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,sunrise,sunset,uv_index_max,wind_speed_10m_max,wind_direction_10m_dominant"
            f"&timezone=Europe%2FLondon"
        )
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        raw = res.json()

        curr = raw.get("current", {})
        daily = raw.get("daily", {})

        wcode = curr.get("weather_code", 0)
        
        # Current weather rain heuristic
        curr_precip = curr.get("precipitation", 0.0)
        if wcode in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82] and curr_precip < 0.1:
            wcode = 3 # Overcast

        desc, emoji, category = WMO_CODE_MAP.get(wcode, ("Unknown", "❓", "UNKNOWN"))

        # Build 5-day forecast
        forecast = []
        time_list = daily.get("time", [])
        codes_list = daily.get("weather_code", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        pop_list = daily.get("precipitation_probability_max", [])
        precip_sum_list = daily.get("precipitation_sum", [])
        sunrise_list = daily.get("sunrise", [])
        sunset_list = daily.get("sunset", [])
        uv_list = daily.get("uv_index_max", [])
        wind_max_list = daily.get("wind_speed_10m_max", [])
        wind_dir_list = daily.get("wind_direction_10m_dominant", [])

        for i in range(min(5, len(time_list))):
            f_code = codes_list[i] if i < len(codes_list) else 0
            f_pop = pop_list[i] if i < len(pop_list) else 0
            f_precip_sum = precip_sum_list[i] if i < len(precip_sum_list) else 0.0
            
            # Heuristic to suppress false-positive rain icons for trace/zero amounts
            if f_code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82] and f_pop < 15 and f_precip_sum < 0.2:
                f_code = 3  # Overcast

            f_desc, f_emoji, _ = WMO_CODE_MAP.get(f_code, ("Clear", "☀️", "SUNNY"))
            forecast.append({
                "date": time_list[i],
                "day_name": self._get_day_name(time_list[i]),
                "temp_max": round(max_temps[i]) if i < len(max_temps) else 0,
                "temp_min": round(min_temps[i]) if i < len(min_temps) else 0,
                "pop": f_pop,
                "precip_sum": f_precip_sum,
                "desc": f_desc,
                "emoji": f_emoji,
                "sunrise": sunrise_list[i][-5:] if i < len(sunrise_list) and sunrise_list[i] else "--",
                "sunset": sunset_list[i][-5:] if i < len(sunset_list) and sunset_list[i] else "--",
                "uv_index": uv_list[i] if i < len(uv_list) else 0.0,
                "wind_max_mph": round(wind_max_list[i] * 0.621371, 1) if i < len(wind_max_list) and wind_max_list[i] else 0.0,
                "wind_dir": get_wind_direction_str(wind_dir_list[i]) if i < len(wind_dir_list) else "N/A",
            })

        return {
            "location": self.location_name,
            "temp": round(curr.get("temperature_2m", 0.0), 1),
            "feels_like": round(curr.get("apparent_temperature", 0.0), 1),
            "humidity": curr.get("relative_humidity_2m", 0),
            "precipitation": curr.get("precipitation", 0.0),
            "wind_speed_mph": round(curr.get("wind_speed_10m", 0.0) * 0.621371, 1), # km/h to mph
            "wind_direction": get_wind_direction_str(curr.get("wind_direction_10m")),
            "weather_code": wcode,
            "description": desc,
            "emoji": emoji,
            "category": category,
            "forecast": forecast,
            "updated_at": time.strftime("%H:%M:%S")
        }

    def _get_day_name(self, date_str):
        try:
            struct = time.strptime(date_str, "%Y-%m-%d")
            return time.strftime("%a", struct)
        except Exception:
            return date_str

    def _get_fallback_weather(self):
        return {
            "location": self.location_name,
            "temp": "--",
            "feels_like": "--",
            "humidity": "--",
            "precipitation": 0.0,
            "wind_speed_mph": "--",
            "wind_direction": "N/A",
            "weather_code": 0,
            "description": "Offline / Weather Unavailable",
            "emoji": "☁️",
            "category": "UNKNOWN",
            "forecast": [],
            "updated_at": time.strftime("%H:%M:%S")
        }

if __name__ == "__main__":
    service = WeatherService()
    weather = service.fetch_weather()
    print("Weather data test:")
    print(json.dumps(weather, indent=2))
