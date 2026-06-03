"""
Weather service — wraps OpenWeatherMap API calls.

Endpoints used:
  Current weather:  https://api.openweathermap.org/data/2.5/weather
  5-day forecast:   https://api.openweathermap.org/data/2.5/forecast
  Air quality:      https://api.openweathermap.org/data/2.5/air_pollution
"""

import requests
from django.conf import settings

BASE = "https://api.openweathermap.org/data/2.5"
GEO  = "https://api.openweathermap.org/geo/1.0"


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _key():
    return settings.OPENWEATHER_API_KEY


def _get(url, params):
    params["appid"] = _key()
    params.setdefault("units", "imperial")
    try:
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 401:
            return None, "Invalid API key. Check your OPENWEATHER_API_KEY."
        if e.response is not None and e.response.status_code == 404:
            return None, "City not found."
        return None, f"API error: {e}"
    except requests.exceptions.ConnectionError:
        return None, "Network error. Check your internet connection."
    except requests.exceptions.Timeout:
        return None, "Request timed out."
    except Exception as e:
        return None, str(e)


def _wind_dir(deg):
    dirs = ["N","NE","E","SE","S","SW","W","NW"]
    return dirs[round(deg / 45) % 8]


def _uv_label(uv):
    if uv < 3:   return ("Low", "#4CAF50")
    if uv < 6:   return ("Moderate", "#FFC107")
    if uv < 8:   return ("High", "#FF9800")
    if uv < 11:  return ("Very High", "#F44336")
    return ("Extreme", "#9C27B0")


def _aqi_label(aqi):
    labels = {1: ("Good","#4CAF50"), 2: ("Fair","#8BC34A"),
              3: ("Moderate","#FFC107"), 4: ("Poor","#FF9800"), 5: ("Very Poor","#F44336")}
    return labels.get(aqi, ("Unknown", "#9E9E9E"))


# ─── Public API ──────────────────────────────────────────────────────────────

def get_weather_by_city(city: str, units: str = "imperial"):
    data, err = _get(f"{BASE}/weather", {"q": city, "units": units})
    if err:
        return None, err
    return _parse_current(data, units), None


def get_weather_by_coords(lat: float, lon: float, units: str = "imperial"):
    data, err = _get(f"{BASE}/weather", {"lat": lat, "lon": lon, "units": units})
    if err:
        return None, err
    return _parse_current(data, units), None


def get_forecast_by_coords(lat: float, lon: float, units: str = "imperial"):
    data, err = _get(f"{BASE}/forecast", {"lat": lat, "lon": lon, "units": units, "cnt": 40})
    if err:
        return None, err
    return _parse_forecast(data, units), None


def get_forecast_by_city(city: str, units: str = "imperial"):
    data, err = _get(f"{BASE}/forecast", {"q": city, "units": units, "cnt": 40})
    if err:
        return None, err
    return _parse_forecast(data, units), None


def get_air_quality(lat: float, lon: float):
    data, err = _get(f"{BASE}/air_pollution", {"lat": lat, "lon": lon})
    if err:
        return None
    try:
        aqi = data["list"][0]["main"]["aqi"]
        label, color = _aqi_label(aqi)
        comp = data["list"][0]["components"]
        return {
            "aqi": aqi,
            "label": label,
            "color": color,
            "pm25": round(comp.get("pm2_5", 0), 1),
            "pm10": round(comp.get("pm10", 0), 1),
            "o3":   round(comp.get("o3", 0), 1),
            "no2":  round(comp.get("no2", 0), 1),
        }
    except (KeyError, IndexError):
        return None


def geocode_city(city: str):
    """Return (lat, lon, full_name) for the first geocoding result."""
    data, err = _get(f"{GEO}/direct", {"q": city, "limit": 1})
    if err or not data:
        return None, None, None
    item = data[0]
    name = item.get("name", city)
    state = item.get("state", "")
    country = item.get("country", "")
    full = ", ".join(filter(None, [name, state, country]))
    return item["lat"], item["lon"], full


# ─── Parsers ─────────────────────────────────────────────────────────────────

def _unit_symbols(units):
    if units == "metric":
        return "°C", "m/s", "km"
    elif units == "imperial":
        return "°F", "mph", "mi"
    else:  # standard (Kelvin)
        return "K", "m/s", "km"


def _parse_current(d, units):
    temp_sym, speed_sym, dist_sym = _unit_symbols(units)
    wind_spd = round(d["wind"]["speed"])
    uv_label, uv_color = _uv_label(0)  # OWM free tier doesn't include UV in current

    return {
        "city":        d["name"],
        "country":     d["sys"]["country"],
        "lat":         d["coord"]["lat"],
        "lon":         d["coord"]["lon"],
        "temp":        round(d["main"]["temp"]),
        "feels_like":  round(d["main"]["feels_like"]),
        "temp_min":    round(d["main"]["temp_min"]),
        "temp_max":    round(d["main"]["temp_max"]),
        "humidity":    d["main"]["humidity"],
        "pressure":    d["main"]["pressure"],
        "condition":   d["weather"][0]["main"],
        "description": d["weather"][0]["description"].title(),
        "icon":        d["weather"][0]["icon"],
        "icon_url":    f"https://openweathermap.org/img/wn/{d['weather'][0]['icon']}@2x.png",
        "wind_speed":  wind_spd,
        "wind_dir":    _wind_dir(d["wind"].get("deg", 0)),
        "wind_gust":   round(d["wind"].get("gust", wind_spd)),
        "visibility":  round(d.get("visibility", 10000) / (1609 if units=="imperial" else 1000), 1),
        "clouds":      d["clouds"]["all"],
        "sunrise":     d["sys"]["sunrise"],
        "sunset":      d["sys"]["sunset"],
        "timezone":    d["timezone"],
        "temp_sym":    temp_sym,
        "speed_sym":   speed_sym,
        "dist_sym":    dist_sym,
        "units":       units,
    }


def _parse_forecast(data, units):
    from datetime import datetime, timezone, timedelta
    temp_sym, _, _ = _unit_symbols(units)

    # Group by day
    days = {}
    for item in data["list"]:
        dt = datetime.fromtimestamp(item["dt"], tz=timezone.utc)
        day_key = dt.strftime("%Y-%m-%d")
        if day_key not in days:
            days[day_key] = {
                "date":      dt,
                "day_name":  dt.strftime("%A"),
                "short_day": dt.strftime("%a"),
                "date_str":  dt.strftime("%b %d"),
                "temps":     [],
                "icons":     [],
                "descs":     [],
                "humidity":  [],
                "wind":      [],
                "pop":       [],
            }
        days[day_key]["temps"].append(item["main"]["temp"])
        days[day_key]["icons"].append(item["weather"][0]["icon"])
        days[day_key]["descs"].append(item["weather"][0]["description"].title())
        days[day_key]["humidity"].append(item["main"]["humidity"])
        days[day_key]["wind"].append(item["wind"]["speed"])
        days[day_key]["pop"].append(item.get("pop", 0) * 100)

    result = []
    for key, d in list(days.items())[:7]:
        # pick most common icon
        from collections import Counter
        icon = Counter(d["icons"]).most_common(1)[0][0]
        desc = Counter(d["descs"]).most_common(1)[0][0]
        result.append({
            "day_name":  d["day_name"],
            "short_day": d["short_day"],
            "date_str":  d["date_str"],
            "temp_max":  round(max(d["temps"])),
            "temp_min":  round(min(d["temps"])),
            "icon":      icon,
            "icon_url":  f"https://openweathermap.org/img/wn/{icon}@2x.png",
            "description": desc,
            "humidity":  round(sum(d["humidity"]) / len(d["humidity"])),
            "wind":      round(sum(d["wind"]) / len(d["wind"])),
            "pop":       round(max(d["pop"])),
            "temp_sym":  temp_sym,
        })

    # Hourly (next 24 h = 8 × 3h slots)
    hourly = []
    for item in data["list"][:8]:
        from datetime import datetime, timezone
        dt = datetime.fromtimestamp(item["dt"], tz=timezone.utc)
        hourly.append({
            "time":    dt.strftime("%-I %p"),
            "temp":    round(item["main"]["temp"]),
            "icon":    item["weather"][0]["icon"],
            "icon_url": f"https://openweathermap.org/img/wn/{item['weather'][0]['icon']}@2x.png",
            "pop":     round(item.get("pop", 0) * 100),
            "temp_sym": temp_sym,
        })

    return {"daily": result, "hourly": hourly}
