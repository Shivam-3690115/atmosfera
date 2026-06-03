from django.urls import path
from . import views

urlpatterns = [
    path('',               views.index,           name='index'),
    path('weather/',       views.weather_city,    name='weather_city'),
    path('weather/geo/',   views.geo_result,      name='geo_result'),
    path('api/geo/',       views.api_geo_weather, name='api_geo'),
    path('api/search/',    views.api_search,      name='api_search'),
]
