# todo: get weather reports for appropriate zipcodes and notify during report time
import json
import time
from datetime import datetime

from helpers.log import logger
from helpers.support import email_object
from helpers.weather import get_weather
from modules.database import get_existing_info


def store_weather():
    info = get_existing_info()
    weather_info = {"last_updated_time": datetime.now().strftime("%c")}
    for each in info:
        email_address = each[1]
        zipcode = each[3]
        current = get_weather(zipcode, True)
        if current.get("alerts"):
            response = email_object.send_email(recipient=email_address,
                                               subject=f"Welcome to WeatherTogether {datetime.now().strftime('%c')}",
                                               sender="WeatherTogether",
                                               body="Hi,\n\n"
                                                    "Currently you have a severe weather warning in your area\n\n"
                                                    f"{current['alerts']}")
            if response.ok:
                logger.info("weather warning has been sent to %s", email_address)
            else:
                logger.error(response.body)
    with open("weather_file.json", "w") as file:
        json.dump(weather_info, file, indent=4)


def background_task():
    start_time = time.time()
    store_weather()
    while True:
        if time.time() - start_time > 1800:
            start_time = time.time()
            store_weather()
