from exceptions import CityNotFound
import re
import requests
import math
class Geocoding:

    # Prepare to use
    def __init__(self):
        r = requests.get("https://en.wikipedia.org/wiki/List_of_cities_by_longitude")
        if(not r.status_code == 200):
            print("Can't download page")
        else:
            self.page = str(r.content)

    # Simple extraction of city coordinates from url given in contructor
    def get_city_coords(self, city):
        if(city == "Chernobyl"):
            return (51.275,30.186)
        try:
            city = re.search(city, self.page)
            (start, _) = city.span()
            substring = self.page[start - 200:start]
            (cut, start) = re.search("data-sort-value=\"", substring).span()
            substring = substring[cut:]
            start -= cut
            (end, _) = re.search("\">", substring).span()
            coord1 = float(substring[start:end])
            substring = substring[end:]
            (cut, start) = re.search("data-sort-value=\"", substring).span()
            substring = substring[cut:]
            start -= cut
            (end, _) = re.search("\">", substring).span()
            coord2 = float(substring[start:end])
            return (coord1, coord2)
        except Exception:
            raise CityNotFound()

    # Computing distance according to formula from
    # https://pl.wikibooks.org/wiki/Astronomiczne_podstawy_geografii/Odleg%C5%82o%C5%9Bci
    @staticmethod
    def compute_distance_between_two_coordinates(coord1, coord2):
        try:
            (long1, lat1) = coord1
            (long2, lat2) = coord2
        except Exception:
            raise InvalidArgument("compute_distance_between_two_coordinates((x1, y1), (x2, y2))")
        longitude_component = (long2 - long1) ** 2
        latitude_component =  (math.cos(long1 * math.pi / 180) * (lat2 - lat1)) ** 2
        return (longitude_component + latitude_component) ** 0.5 * 40075.704 / 360

    def compute_distance_between_two_cities(self, city1, city2):
        coord1 = self.get_city_coords(city1)
        coord2 = self.get_city_coords(city2)
        return Geocoding.compute_distance_between_two_coordinates(coord1, coord2)

    @staticmethod
    def get_capital_city_by_country(country):
        r = requests.get("https://restcountries.eu/rest/v2/name/" + country)
        if(not r.status_code == 200):
            print("Can't download page")
        else:
            json_data = json.loads(r.text)
