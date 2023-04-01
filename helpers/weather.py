import os

import requests
from geopy.geocoders import Nominatim
from pydantic import PositiveInt

from helpers.log import logger

url = "https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={apikey}"
geolocator = Nominatim(user_agent="WeatherTogether")


def get_coordinates(zipcode: PositiveInt):
    location = geolocator.geocode(str(zipcode), country_codes="us")
    if location:
        return location.latitude, location.longitude


def get_weather(zipcode: PositiveInt, mock: bool = False):
    if mock:
        return {
            'coord':
                {'lon': -93.3141, 'lat': 37.1653},
            'weather': [{'id': 802, 'main': 'Clouds', 'description': 'scattered clouds', 'icon': '03d'}],
            'base': 'stations', 'main': {'temp': 285.82, 'feels_like': 284.34, 'temp_min': 284.28, 'temp_max': 287.11,
                                         'pressure': 1016, 'humidity': 46}, 'visibility': 10000,
            'wind': {'speed': 4.63, 'deg': 30, 'gust': 8.23},
            'clouds': {'all': 40}, 'dt': 1679952325,
            'sys': {'type': 2, 'id': 2080868, 'country': 'US', 'sunrise': 1679918794, 'sunset': 1679963434},
            'timezone': -18000, 'id': 4409896, 'name': 'Springfield', 'cod': 200
        }
    if location_details := get_coordinates(zipcode):
        latitude, longitude = location_details
    else:
        logger.error("Failed to get location co-ordinations for the zipcode %s", zipcode)
        return
    weather_url = url.format(lat=latitude, lon=longitude, apikey=os.environ.get("APIKEY"))
    response = requests.get(url=weather_url)
    if response.ok:
        print(response.json())

# get_weather(65807, mock=True)
