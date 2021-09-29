from geopy.geocoders import Nominatim
from geopy import distance
import math


def get_city_lat_and_lon(city):
    """
    get the city longitude and latitude from city name using Nominatim
    :param city: the city name
    :return: lat,lon if valid, None else
    """
    geolocator = Nominatim(user_agent='myapplication')
    location = geolocator.geocode(city)
    if location is None:
        return None, None
    lat = location.raw['lat']
    lon = location.raw['lon']
    return float(lat), float(lon)


def get_distance_between_cities(source, destination):
    """
    the distance between two cities
    :param source: the source city
    :param destination: the destination city
    :return: the distance, -1 if a city is invalid
    """
    lat1, lon1 = get_city_lat_and_lon(source)
    lat2, lon2 = get_city_lat_and_lon(destination)
    if lat1 is None or lat2 is None:
        return -1
    radius = 6371  # km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c

    return d

