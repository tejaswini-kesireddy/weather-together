import os
from datetime import datetime, timezone
import requests
from geopy.geocoders import Nominatim
from pydantic import PositiveInt

#from helpers.log import logger

url = "https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&appid={apikey}"


def get_coordinates(zipcode: PositiveInt):
    geolocator = Nominatim(user_agent="WeatherTogether")
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
            'timezone': -18000, 'id': 4409896, 'name': 'Springfield', 'cod': 200, }
    if location_details := get_coordinates(zipcode):
        latitude, longitude = location_details
    else:
        #logger.error("Failed to get location co-ordinations for the zipcode %s", zipcode)
        return
    weather_url = url.format(lat=latitude, lon=longitude, apikey=os.environ.get("APIKEY"))
    
    response = requests.get(url=weather_url)
    #if response.ok:
    #    print(response.json())

    w = response.json()
    #print(w)
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    todays_weather = next((d for d in w["daily"] if datetime.utcfromtimestamp(d["dt"]).strftime('%Y-%m-%d') == today), None)
    #print(todays_weather)
    todays_description = todays_weather["weather"][0]["description"]
    todays_high= round((float(todays_weather["temp"]["max"])-273.15)*(9/5) + 32)#kelvin to faren
    todays_low= round((float(todays_weather["temp"]["min"])-273.15)*(9/5) + 32)#kelvin to faren
    
    #print(todays_description, todays_high, todays_low)
    
    current_temperature = w["current"]["temp"]
    current_pressure = w["current"]["pressure"]
    current_humidity = w["current"]["humidity"]
    
    feels_like= w["current"]["feels_like"]

    z = w["current"]["weather"]
    weather_description = z[0]["description"]
    current_temperatureF=round((float(current_temperature)-273.15)*(9/5) + 32)#kelvin to faren


    hourly = w["hourly"]
    hourly_weather=[]
    weather=[]
    for entry in hourly:
        temp = entry["temp"]
        tempf= round((float(temp)-273.15)*(9/5) + 32)#kelvin to faren
        dt= datetime.fromtimestamp( int(entry["dt"]))
        dt = str(dt.strftime("%I:%M %p"))
        h_weather_description= entry["weather"][0]["description"]
        weather = [dt, tempf,"°F with", h_weather_description]
        hourly_weather.append(weather)
    
    
    weather_alerts = w.get("alerts")
    
    
    
    #print(weather_alerts)
    #print( hourly_weather)
    #print( current_temperatureF, weather_description)
    return (hourly_weather, todays_description, todays_low, todays_high,weather_alerts)


    
    





get_weather("65807", mock=False)



