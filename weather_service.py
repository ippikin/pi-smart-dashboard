#!/usr/bin/env python3
"""
Weather Service Module for UK Locations.
Fetches current weather and 5-day forecast via official Met Office Site-Specific API (UKV 1.5km model)
with automatic Open-Meteo fallback.
"""

import time
import json
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WeatherService")

# WMO Weather Code Mappings (Open-Meteo)
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

# Met Office Weather Code Mappings
MET_OFFICE_CODE_MAP = {
    0: ("Clear Night", "🌙", "SUNNY"),
    1: ("Sunny", "☀️", "SUNNY"),
    2: ("Partly Cloudy", "🌤️", "PARTLY_CLOUDY"),
    3: ("Partly Cloudy", "⛅", "PARTLY_CLOUDY"),
    4: ("Not Used", "☁️", "CLOUDY"),
    5: ("Mist", "🌫️", "FOG"),
    6: ("Foggy", "🌫️", "FOG"),
    7: ("Cloudy", "☁️", "CLOUDY"),
    8: ("Overcast", "☁️", "CLOUDY"),
    9: ("Light Rain Shower", "🌦️", "RAIN_LIGHT"),
    10: ("Light Rain Shower", "🌦️", "RAIN_LIGHT"),
    11: ("Drizzle", "🌦️", "RAIN_LIGHT"),
    12: ("Light Rain", "🌧️", "RAIN_LIGHT"),
    13: ("Heavy Rain Shower", "🌧️", "RAIN"),
    14: ("Heavy Rain Shower", "🌧️", "RAIN"),
    15: ("Heavy Rain", "🌧️🌧️", "RAIN_HEAVY"),
    16: ("Sleet Shower", "🌧️❄️", "RAIN_SNOW"),
    17: ("Sleet Shower", "🌧️❄️", "RAIN_SNOW"),
    18: ("Sleet", "🌧️❄️", "RAIN_SNOW"),
    19: ("Hail Shower", "⛈️🧊", "THUNDERSTORM"),
    20: ("Hail Shower", "⛈️🧊", "THUNDERSTORM"),
    21: ("Hail", "⛈️🧊", "THUNDERSTORM"),
    22: ("Light Snow Shower", "🌨️", "SNOW"),
    23: ("Light Snow Shower", "🌨️", "SNOW"),
    24: ("Light Snow", "🌨️", "SNOW"),
    25: ("Heavy Snow Shower", "❄️❄️", "SNOW_HEAVY"),
    26: ("Heavy Snow Shower", "❄️❄️", "SNOW_HEAVY"),
    27: ("Heavy Snow", "❄️❄️", "SNOW_HEAVY"),
    28: ("Thunder Shower", "⛈️", "THUNDERSTORM"),
    29: ("Thunder Shower", "⛈️", "THUNDERSTORM"),
    30: ("Thunderstorm", "⛈️", "THUNDERSTORM"),
}

def format_uk_date(date_str):
    """Format YYYY-MM-DD into UK Day Month format: e.g. 8 Aug."""
    try:
        struct = time.strptime(date_str[:10], "%Y-%m-%d")
        return f"{int(time.strftime('%d', struct))} {time.strftime('%b', struct)}"
    except Exception:
        return date_str

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
                 met_office_api_key=""):
        self.latitude = latitude
        self.longitude = longitude
        self.location_name = location_name
        self.met_office_api_key = met_office_api_key
        
        self._cache = None
        self._last_fetch_time = 0
        self.cache_ttl_sec = 300  # 5 minutes cache

    def fetch_weather(self, force_refresh=False):
        """Fetch weather data using Met Office Site-Specific API with Open-Meteo fallback."""
        now = time.time()
        if not force_refresh and self._cache and (now - self._last_fetch_time < self.cache_ttl_sec):
            return self._cache

        # 1. Try Met Office Site-Specific API if key provided
        if self.met_office_api_key:
            try:
                data = self._fetch_met_office()
                if data:
                    self._cache = data
                    self._last_fetch_time = now
                    logger.info("Successfully fetched weather from Met Office Site-Specific API.")
                    return data
            except Exception as e:
                logger.warning(f"Met Office API fetch error: {e}")

        # 2. Fallback to Open-Meteo
        try:
            data = self._fetch_open_meteo()
            if data:
                self._cache = data
                self._last_fetch_time = now
                logger.info("Fetched weather from Open-Meteo fallback.")
                return data
        except Exception as e:
            logger.warning(f"Open-Meteo fetch error: {e}")

        return self._get_fallback_weather()

    def _fetch_met_office(self):
        """Fetch official Met Office UKV 1.5km site-specific forecast data."""
        headers = {
            "apikey": self.met_office_api_key,
            "accept": "application/json"
        }
        
        # Hourly forecast for current weather
        hourly_url = (
            f"https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/hourly?"
            f"includeLocationName=true&latitude={self.latitude}&longitude={self.longitude}"
        )
        res_h = requests.get(hourly_url, headers=headers, timeout=10)
        res_h.raise_for_status()
        raw_h = res_h.json()
        
        props_h = raw_h["features"][0]["properties"]
        ts_h = props_h.get("timeSeries", [])
        if not ts_h:
            return None
        
        curr_h = ts_h[0]
        loc_name = props_h.get("location", {}).get("name", self.location_name)
        curr_temp = round(curr_h.get("screenTemperature", 0.0), 1)
        feels_like = round(curr_h.get("feelsLikeTemperature", 0.0), 1)
        humidity = curr_h.get("screenRelativeHumidity", 0)
        wind_speed_mph = round(curr_h.get("windSpeed10m", 0.0) * 2.23694, 1)
        wind_dir = get_wind_direction_str(curr_h.get("windDirectionFrom10m"))
        wcode = curr_h.get("significantWeatherCode", 1)
        desc, emoji, category = MET_OFFICE_CODE_MAP.get(wcode, ("Clear", "☀️", "SUNNY"))

        # Daily forecast for 5-day outlook
        daily_url = (
            f"https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/daily?"
            f"includeLocationName=true&latitude={self.latitude}&longitude={self.longitude}"
        )
        res_d = requests.get(daily_url, headers=headers, timeout=10)
        res_d.raise_for_status()
        raw_d = res_d.json()
        
        ts_d = raw_d["features"][0]["properties"].get("timeSeries", [])
        
        # Fetch astronomy data (sunrise/sunset) from Open-Meteo fallback
        sunrises, sunsets = self._fetch_astronomy_open_meteo()
        
        today_str = time.strftime("%Y-%m-%d")

        forecast = []
        for entry in ts_d:
            d_time = entry.get("time", "")[:10]
            if d_time < today_str:
                continue  # Skip past days (e.g. yesterday)

            i = len(forecast)
            if i >= 5:
                break

            d_name = self._get_day_name(d_time)
            d_uk = format_uk_date(d_time)
            
            t_max = round(entry.get("dayMaxScreenTemperature", entry.get("maxScreenAirTemp", 0)))
            t_min = round(entry.get("nightMinScreenTemperature", entry.get("minScreenAirTemp", 0)))
            
            pop_day = entry.get("dayProbOfPrecipitation", 0)
            pop_night = entry.get("nightProbOfPrecipitation", 0)
            pop = max(pop_day, pop_night)
            
            f_code = entry.get("daySignificantWeatherCode", entry.get("significantWeatherCode", 1))
            f_desc, f_emoji, _ = MET_OFFICE_CODE_MAP.get(f_code, ("Clear", "☀️", "SUNNY"))
            
            wind_max_mph = round(entry.get("midday10MWindSpeed", 0.0) * 2.23694, 1)
            wind_dir_str = get_wind_direction_str(entry.get("midday10MWindDirection"))
            uv = entry.get("maxUvIndex", entry.get("middayUvIndex", 0))
            
            day_sunrise = sunrises[i][-5:] if i < len(sunrises) and sunrises[i] else "--"
            day_sunset = sunsets[i][-5:] if i < len(sunsets) and sunsets[i] else "--"

            forecast.append({
                "date": d_time,
                "date_uk": d_uk,
                "day_name": d_name,
                "temp_max": t_max,
                "temp_min": t_min,
                "pop": pop,
                "precip_sum": round(entry.get("totalPrecipitationAmount", 0.0), 1),
                "desc": f_desc,
                "emoji": f_emoji,
                "sunrise": day_sunrise,
                "sunset": day_sunset,
                "uv_index": uv,
                "wind_max_mph": wind_max_mph,
                "wind_dir": wind_dir_str,
            })

        top_sunrise = sunrises[0][-5:] if sunrises and len(sunrises) > 0 and sunrises[0] else "--"
        top_sunset = sunsets[0][-5:] if sunsets and len(sunsets) > 0 and sunsets[0] else "--"

        return {
            "location": loc_name,
            "temp": curr_temp,
            "feels_like": feels_like,
            "humidity": humidity,
            "precipitation": round(curr_h.get("totalPrecipAmount", 0.0), 1),
            "wind_speed_mph": wind_speed_mph,
            "wind_direction": wind_dir,
            "weather_code": wcode,
            "description": desc,
            "emoji": emoji,
            "category": category,
            "forecast": forecast,
            "sunrise": top_sunrise,
            "sunset": top_sunset,
            "source": "Met Office DataHub",
            "updated_at": time.strftime("%H:%M:%S")
        }

    def _fetch_astronomy_open_meteo(self):
        """Fetch sunrise and sunset times from Open-Meteo free API."""
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={self.latitude}&longitude={self.longitude}"
                f"&daily=sunrise,sunset&timezone=Europe%2FLondon"
            )
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                daily = res.json().get("daily", {})
                return daily.get("sunrise", []), daily.get("sunset", [])
        except Exception as e:
            logger.warning(f"Astronomy fetch error: {e}")
        return [], []

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
        curr_precip = curr.get("precipitation", 0.0)
        if wcode in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82] and curr_precip < 0.1:
            wcode = 3 # Overcast

        desc, emoji, category = WMO_CODE_MAP.get(wcode, ("Unknown", "❓", "UNKNOWN"))

        today_str = time.strftime("%Y-%m-%d")
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

        for idx_raw, t_val in enumerate(time_list):
            if t_val < today_str:
                continue
            i = len(forecast)
            if i >= 5:
                break
                
            f_code = codes_list[idx_raw] if idx_raw < len(codes_list) else 0
            f_pop = pop_list[idx_raw] if idx_raw < len(pop_list) else 0
            f_precip_sum = precip_sum_list[idx_raw] if idx_raw < len(precip_sum_list) else 0.0
            
            if f_code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82] and f_pop < 15 and f_precip_sum < 0.2:
                f_code = 3  # Overcast

            f_desc, f_emoji, _ = WMO_CODE_MAP.get(f_code, ("Clear", "☀️", "SUNNY"))
            forecast.append({
                "date": t_val,
                "date_uk": format_uk_date(t_val),
                "day_name": self._get_day_name(t_val),
                "temp_max": round(max_temps[idx_raw]) if idx_raw < len(max_temps) else 0,
                "temp_min": round(min_temps[idx_raw]) if idx_raw < len(min_temps) else 0,
                "pop": f_pop,
                "precip_sum": f_precip_sum,
                "desc": f_desc,
                "emoji": f_emoji,
                "sunrise": sunrise_list[idx_raw][-5:] if idx_raw < len(sunrise_list) and sunrise_list[idx_raw] else "--",
                "sunset": sunset_list[idx_raw][-5:] if idx_raw < len(sunset_list) and sunset_list[idx_raw] else "--",
                "uv_index": uv_list[idx_raw] if idx_raw < len(uv_list) else 0.0,
                "wind_max_mph": round(wind_max_list[idx_raw] * 0.621371, 1) if idx_raw < len(wind_max_list) and wind_max_list[idx_raw] else 0.0,
                "wind_dir": get_wind_direction_str(wind_dir_list[idx_raw]) if idx_raw < len(wind_dir_list) else "N/A",
            })

        sunrise_val = sunrise_list[0][-5:] if sunrise_list and sunrise_list[0] else "--"
        sunset_val = sunset_list[0][-5:] if sunset_list and sunset_list[0] else "--"

        return {
            "location": self.location_name,
            "temp": round(curr.get("temperature_2m", 0.0), 1),
            "feels_like": round(curr.get("apparent_temperature", 0.0), 1),
            "humidity": curr.get("relative_humidity_2m", 0),
            "precipitation": curr.get("precipitation", 0.0),
            "wind_speed_mph": round(curr.get("wind_speed_10m", 0.0) * 0.621371, 1),
            "wind_direction": get_wind_direction_str(curr.get("wind_direction_10m")),
            "weather_code": wcode,
            "description": desc,
            "emoji": emoji,
            "category": category,
            "forecast": forecast,
            "sunrise": sunrise_val,
            "sunset": sunset_val,
            "source": "Open-Meteo",
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
            "source": "Offline",
            "updated_at": time.strftime("%H:%M:%S")
        }

if __name__ == "__main__":
    service = WeatherService()
    weather = service.fetch_weather()
    print("Weather data test:")
    print(json.dumps(weather, indent=2))
