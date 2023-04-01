from geopy.distance import geodesic
from pydantic import PositiveInt

# from modules.accessories import otp_dict
# from modules.database import db
from helpers.weather import get_coordinates


def find_distance(zipcode1: PositiveInt, zipcode2: PositiveInt):
    location1 = get_coordinates(zipcode1)
    location2 = get_coordinates(zipcode2)
    return geodesic(location1, location2).miles
