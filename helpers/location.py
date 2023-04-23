from fastapi import HTTPException
from geopy.distance import geodesic
from geopy.exc import GeopyError
from geopy.geocoders import Nominatim
from pydantic import PositiveInt

from helpers.log import logger


def get_coordinates(zipcode: PositiveInt):
    geolocator = Nominatim(scheme="http", user_agent="test/1")
    location = geolocator.geocode(str(zipcode), country_codes="us")
    if location:
        return location.latitude, location.longitude
    raise HTTPException(status_code=400, detail='zipcode invalid or not in the US')


def find_distance(zipcode1: PositiveInt, zipcode2: PositiveInt):
    logger.info("zipcode1: %d", zipcode1)
    logger.info("zipcode2: %d", zipcode2)
    if zipcode1 == zipcode2:
        return 0
    try:
        location1 = get_coordinates(zipcode1)
        location2 = get_coordinates(zipcode2)
    except GeopyError as error:
        logger.error(error)
        return 0
    logger.info("coordinates1: %s", location1)
    logger.info("coordinates2: %s", location2)
    return geodesic(location1, location2).miles
