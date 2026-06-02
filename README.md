# 🌤️ Atmosfera — Full-Stack Django Weather App

A polished weather web app built with Django + OpenWeatherMap API.

## Features

- 🔍 **City search** with autocomplete (geocoding API)
- 📍 **Browser geolocation** — one click to get your local weather
- 🌡️ **Current conditions** — temp, feels like, humidity, wind, pressure, visibility
- ⏱️ **Hourly forecast** (next 24 hours)
- 📅 **7-day forecast** with high/low temp bars
- 🌫️ **Air quality index** (PM2.5, PM10, O₃, NO₂)
- 🌅 **Sunrise & sunset** times
- °F / °C toggle (persisted in session)
- Responsive, glassmorphism design

---

## Quick Start

### 1. Get a free API key

Sign up at **https://openweathermap.org/api** (free tier covers all endpoints used here).

After signing up, go to *API Keys* in your account dashboard and copy your key.

### 2. Clone / unzip the project

```bash
unzip atmosfera.zip
cd atmosfera
```

### 3. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Set your API key

**Option A — environment variable (recommended):**
```bash
export OPENWEATHER_API_KEY="your_key_here"
```

**Option B — edit settings directly:**
Open `atmosfera/settings.py` and replace:
```python
OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', 'YOUR_API_KEY_HERE')
```

### 6. Run the development server

```bash
python manage.py runserver
```

Open **http://127.0.0.1:8000** in your browser.

---

## Project Structure

```
atmosfera/
├── manage.py
├── requirements.txt
├── atmosfera/                  # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── weather/                    # Main app
    ├── views.py                # Request handlers
    ├── services.py             # OpenWeatherMap API calls
    ├── urls.py                 # URL routing
    └── templates/weather/
        ├── base.html           # Shared layout & CSS
        ├── index.html          # Home / search page
        ├── weather.html        # Weather results page
        └── geo_result.html     # Geolocation redirect page
```

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/` | Home page |
| GET | `/weather/?city=London&units=metric` | Weather for a city |
| POST | `/api/geo/` | Submit lat/lon, get weather JSON |
| GET | `/api/search/?q=Tok` | City autocomplete suggestions |
| GET | `/weather/geo/` | Geo redirect page |

## OpenWeatherMap APIs Used

- `GET /data/2.5/weather` — current conditions
- `GET /data/2.5/forecast` — 5-day/3-hour forecast
- `GET /data/2.5/air_pollution` — AQI & pollutants
- `GET /geo/1.0/direct` — geocoding (city → lat/lon)

All are available on the **free tier** (60 calls/min limit).

## Deployment Notes

For production:
1. Set `DEBUG = False` in `settings.py`
2. Set a real `SECRET_KEY` via environment variable
3. Add your domain to `ALLOWED_HOSTS`
4. Use `whitenoise` or a CDN for static files
5. Use `gunicorn` as the WSGI server

```bash
pip install gunicorn whitenoise
gunicorn atmosfera.wsgi:application
```
