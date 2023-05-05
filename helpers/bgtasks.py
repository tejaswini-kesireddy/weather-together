import json
import os
import string
import time
from datetime import datetime

from helpers.log import logger
from helpers.support import email_object
from helpers.weather import get_weather
from modules.database import get_existing_info


def send_alert():
    info = get_existing_info()
    if not info:
        logger.warning("No information in DB")
        return
    weather_info = {"last_updated_time": datetime.now().strftime("%c")}
    for each in info:
        email_address = each[1]
        zipcode = each[3]
        current = get_weather(zipcode)
        if current.get("alerts"):
            response = email_object.send_email(recipient=email_address,
                                               subject=f"Welcome to WeatherTogether {datetime.now().strftime('%c')}",
                                               sender="WeatherTogether",
                                               body="Hi,\n\n"
                                                    "Currently you have a severe weather warning near your area code: "
                                                    f"{zipcode}\n\n"
                                                    f"{current['alerts']}")
            if response.ok:
                logger.info("weather warning has been sent to %s", email_address)
            else:
                logger.error(response.body)
    with open("weather_file.json", "w") as file:
        json.dump(weather_info, file, indent=4)


def send_report():
    info = get_existing_info()
    if not info:
        logger.warning("No information in DB")
        return
    for each in info:
        email_address = each[1]
        zipcode = each[3]
        report_time = each[4]
        if report_time == datetime.now().strftime("%I:%M %p"):
            current_weather = None
            if os.path.isfile("weather_file.json"):
                with open("weather_file.json") as file:
                    existing_weather = json.load(file)
                if existing_weather.get(zipcode):
                    current_weather = existing_weather[zipcode]
            if current_weather is None:
                current_weather = get_weather(zipcode)
            city = current_weather.get('name', zipcode)
            desc = current_weather.get('weather', [{}])[0].get('description')
            temp = current_weather.get('main', {}).get('temp')
            temp_min = current_weather.get('main', {}).get('temp_min')
            temp_max = current_weather.get('main', {}).get('temp_max')
            feels_like = current_weather.get('main', {}).get('feels_like')
            text = f"Current weather forecast for {city}:\n\n{string.capwords(desc)} with " \
                   f"current temperature of {temp} \N{DEGREE SIGN}F. " \
                   f"The high is {temp_max} \N{DEGREE SIGN}F, and the low is {temp_min} \N{DEGREE SIGN}F." \
                   f" It currently feels like {feels_like} \N{DEGREE SIGN}F."
            response = email_object.send_email(recipient=email_address,
                                               subject=f"Weather Report - {datetime.now().strftime('%c')}",
                                               sender="WeatherTogether", body=text)
            if response.ok:
                logger.info("weather report email has been sent")
            else:
                logger.error(response.body)


def background_task():
    alert_start = time.time()
    report_start = time.time()
    send_alert()
    while True:
        if time.time() - alert_start > 1_800:
            alert_start = time.time()
            send_alert()
        if time.time() - report_start > 30:
            report_start = time.time()
            send_report()
