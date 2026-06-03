"""
Atmosfera Django Settings
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-change-this-in-production-atmosfera-2026'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'weather',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'atmosfera.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'atmosfera.wsgi.application'

STATIC_URL = '/static/'
STATICFILES_DIRS = []

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── Weather API ─────────────────────────────────────────────────────────────
# Sign up free at https://openweathermap.org/api
# Then replace the value below with your key, OR set the env variable:
#   export OPENWEATHER_API_KEY="your_key_here"
OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', 'YOUR_API_KEY_HERE')

# Optional: OpenCage for reverse geocoding (free tier at opencagedata.com)
OPENCAGE_API_KEY = os.environ.get('OPENCAGE_API_KEY', '')
