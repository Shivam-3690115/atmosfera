"""
Views for the Atmosfera weather app.

Routes:
  GET  /                   → index (search + optional geo)
  GET  /weather/?city=...  → city weather page
  POST /api/geo/           → receive lat/lon from browser, return weather JSON
  GET  /api/search/        → JSON city autocomplete (optional, uses geocoding)
"""

import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from . import services


def _units_from_request(request):
    return request.GET.get("units", request.session.get("units", "imperial"))


def index(request):
    """Landing page — shows search form and geolocation prompt."""
    return render(request, "weather/index.html", {
        "page": "home",
    })


def weather_city(request):
    """Show weather for a searched city."""
    city = request.GET.get("city", "").strip()
    units = _units_from_request(request)

    if not city:
        return render(request, "weather/index.html", {"error": "Please enter a city name."})

    # Save unit preference in session
    request.session["units"] = units

    # Geocode first so we get precise lat/lon
    lat, lon, full_name = services.geocode_city(city)
    if lat is None:
        return render(request, "weather/index.html", {
            "error": f'City "{city}" not found. Try a different spelling.',
            "query": city,
        })

    current, err = services.get_weather_by_coords(lat, lon, units)
    if err:
        return render(request, "weather/index.html", {"error": err, "query": city})

    forecast, _ = services.get_forecast_by_coords(lat, lon, units)
    air = services.get_air_quality(lat, lon)

    # Override city name with the more complete geocoded one if available
    if full_name:
        current["display_name"] = full_name

    return render(request, "weather/weather.html", {
        "current":  current,
        "forecast": forecast,
        "air":      air,
        "units":    units,
        "query":    city,
        "page":     "weather",
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_geo_weather(request):
    """
    Called by the browser when user grants geolocation.
    Body: { "lat": 40.7, "lon": -74.0, "units": "imperial" }
    Returns full weather JSON.
    """
    try:
        body = json.loads(request.body)
        lat = float(body["lat"])
        lon = float(body["lon"])
        units = body.get("units", "imperial")
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        return JsonResponse({"error": f"Bad request: {e}"}, status=400)

    current, err = services.get_weather_by_coords(lat, lon, units)
    if err:
        return JsonResponse({"error": err}, status=502)

    forecast, _ = services.get_forecast_by_coords(lat, lon, units)
    air = services.get_air_quality(lat, lon)

    return JsonResponse({
        "current":  current,
        "forecast": forecast,
        "air":      air,
        "units":    units,
    })


def geo_result(request):
    """Page that reads geoWeather from sessionStorage and redirects."""
    return render(request, "weather/geo_result.html")


def api_search(request):
    """
    Optional JSON endpoint for city search suggestions.
    GET /api/search/?q=Lon
    """
    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})

    # Use OWM geocoding to find up to 5 matches
    from django.conf import settings
    import requests as req
    try:
        r = req.get(
            "https://api.openweathermap.org/geo/1.0/direct",
            params={"q": q, "limit": 5, "appid": settings.OPENWEATHER_API_KEY},
            timeout=5,
        )
        r.raise_for_status()
        items = r.json()
        results = []
        for item in items:
            name = item.get("name", "")
            state = item.get("state", "")
            country = item.get("country", "")
            label = ", ".join(filter(None, [name, state, country]))
            results.append({"label": label, "lat": item["lat"], "lon": item["lon"]})
        return JsonResponse({"results": results})
    except Exception:
        return JsonResponse({"results": []})
