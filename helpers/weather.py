import requests
from pydantic import PositiveInt

from helpers.location import get_coordinates
from helpers.log import logger
from modules.accessories import env

url = "https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={apikey}&units=imperial"


def get_weather(zipcode: PositiveInt):
    if location_details := get_coordinates(zipcode):
        latitude, longitude = location_details
    else:
        logger.error("Failed to get location co-ordinations for the zipcode %s", zipcode)
        return
    weather_url = url.format(lat=latitude, lon=longitude, apikey=env.weather_api)
    response = requests.get(url=weather_url)
    if response.ok:
        return response.json()
    response.raise_for_status()
