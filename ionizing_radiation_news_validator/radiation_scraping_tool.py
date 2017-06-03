from nlp_news_checker import NLPNewsChecker
from geocoding import Geocoding
import re
import requests
import numpy
import time
import datetime

class RadiationScrapingTool:
    def __init__(self, nlp_news_checker = None):
        print
        a = self.get_sensor_data_from_day(6, "2017-05-01")
        print(a)
        print(len(a))

        self.__geocoding = Geocoding()
        if not nlp_news_checker == None:
            if not isinstance(nlp_news_checker, NLPNewsChecker):
                raise InvalidArgument()
            try:
                self.date = nlp_news_checker.date
                self.countries = nlp_news_checker.enumerated_countries
            except:
                raise NLPNewsCheckerNotValid()


    def __get_list_of_active_sensors_and_reactors(self):
        r = requests.get("http://radioactiveathome.org/map/")
        if(not r.status_code == 200):
            raise Not200Code()
        (_, end) = re.search("map.addOverlay", str(r.content)).span()
        text = str(r.content)[end:]
        splitted_text = text.split("map.addOverlay")
        regex_reactor = re.compile("createReactorMarker")
        regex_sensor = re.compile("createMarker")
        reactors_raw = list()
        sensors_raw = list()
        for line in splitted_text:
            if regex_sensor.search(line):
                sensors_raw.append(line)
            if regex_reactor.search(line):
                reactors_raw.append(line)
        (self.__reactors_names, self.__reactors_coords) = self.__get_dict_of_reactors(reactors_raw)
        self.__sensors_numpy = self.__get_dict_of_sensors(sensors_raw)

    # Converts list of string to numpy array with structure id, latitude, longitude
    def __get_array_of_sensors(self, sensors_raw):
        result = numpy.empty((len(sensors_raw), 3))
        pattern_createMarker = re.compile("\(createMarker\(new GLatLng\(")
        patteren_comma = re.compile(",")
        pattern_bracket_comma = re.compile("\),")
        for i, line in enumerate(sensors_raw):
            (_, start) = pattern_createMarker.search(line).span()
            line = line[start:]
            (end, _) = patteren_comma.search(line).span()
            result[i][1] = float(line[0:end])
            line = line[end + 1:]
            (end, _) = pattern_bracket_comma.search(line).span()
            result[i][2] = float(line[0:end])
            line = line[end+2:]
            (end, _) = patteren_comma.search(line).span()
            result[i][0] = int(line[0:end])
        return result

    # Converts list of string to (list with name, numpy array with structure latitude, longitude)
    def __get_array_tuple_of_reactors(self, reactors_raw):
        result_names = list()
        result_coords = numpy.empty((len(reactors_raw), 2))
        pattern_createMarker = re.compile("\(createReactorMarker\(new GLatLng\(")
        patteren_comma = re.compile(",")
        pattern_bracket_comma = re.compile("\),")
        pattern_name = re.compile("Name: ")
        pattern_netto = re.compile("<br>Capacity")
        for i, line in enumerate(reactors_raw):
            (_, start) = pattern_createMarker.search(line).span()
            line = line[start:]
            (end, _) = patteren_comma.search(line).span()
            result_coords[i][0] = float(line[0:end])
            line = line[end + 1:]
            (end, _) = pattern_bracket_comma.search(line).span()
            result_coords[i][1] = float(line[0:end])
            (_, start) = pattern_name.search(line).span()
            (end, _) = pattern_netto.search(line).span()
            result_names.append(line[start:end])
        return (result_names, result_coords)

    def get_list_of_sensors_in_range_km(self, coords, range_km):
        list_of_sensors = list()
        for sensor in self.__sensors_numpy:
            if self.__geocoding.compute_distance_between_two_coordinates(coords, (sensor[1], sensor[2])) < range_km:
                list_of_sensors.append((sensor[0], sensor[1], sensor[2]))
        return list_of_sensors

    def get_list_of_reactors_in_range_km(self, coords, range_km):
        list_of_reactors = list()
        for i, reactor in enumerate(self.__reactors_coords):
            if self.__geocoding.compute_distance_between_two_coordinates(coords, reactor[0], reactor[1]) < range_km:
                list_of_reactors.append((self.__reactors_names[i], reactor[0], reactor[1]))

    # Scrape pages, download data and return data from one particular day
    # sensor_id - int, date format YYYY-MM-DD - string
    # Result is returned in numpy array format timestamp, measurement
    def __get_sensor_data_from_day(self, sensor_id, date):
        url_1 = "http://radioactiveathome.org/boinc/gettrickledata.php?start="
        url_2 = "&hostid="
        searched_date = self.__convert_date_to_timestamp(date)
        current_measurement_id = 0
        results = list()

        while True:
            print(url_1 + str(current_measurement_id) + url_2 + str(sensor_id))
            r = requests.get(url_1 + str(current_measurement_id) + url_2 + str(sensor_id))
            if(not r.status_code == 200):
                raise Not200Code()
            str_content = str(r.content)

            if re.search("NO DATA", str_content): # reached end of data
                break;
            # Split by line, remove first line
            splitted_data = str_content[2:len(str_content)-3].split("\\n")[1:]
            # Extract next page pointer
            current_measurement_id = int(splitted_data[len(splitted_data) - 1].split(",")[0])
            (first_record_date, _, _, _) = self.__extract_data_time_counts_timescale_from_line(splitted_data[1])
            if self.__convert_date_to_timestamp(first_record_date) > searched_date:
                break; # current data is newer than searched
            print(len(splitted_data))

            (last_record_date, _, _, _) = self.__extract_data_time_counts_timescale_from_line(splitted_data[len(splitted_data) - 1])
            if self.__convert_date_to_timestamp(last_record_date) < searched_date:
                continue; # current data too old

            for line in splitted_data:
                (date, hours, counts, timescale) = self.__extract_data_time_counts_timescale_from_line(line)
                if self.__convert_date_to_timestamp(date) == searched_date:
                    results.append((self.__convert_date_time_to_timestamp(date, hours), self.__convert_counts_per_time_to_uSv(counts, timescale)))
        return numpy.array(results)

    # line example
    # 287000059,6,80,2017-04-30 23:46:29,51.803020,19.753744,3.993,n,0,513
    def __extract_data_time_counts_timescale_from_line(self, line):
        splitted_line = line.split(",")
        splitted_date_time = splitted_line[3].split(" ")
        print(splitted_line)
        print()
        print(splitted_date_time)
        return (splitted_date_time[0], splitted_date_time[1], int(splitted_line[2]), float(splitted_line[6]))

    def __convert_date_time_to_timestamp(self, date, hours=""):
        return time.mktime(datetime.datetime.strptime(date + " " + hours, "%Y-%m-%d %H:%M:%S").timetuple())

    def __convert_date_to_timestamp(self, date):
        return time.mktime(datetime.datetime.strptime(date, "%Y-%m-%d").timetuple())

    def __convert_counts_per_time_to_uSv(self, counts, timescale):
        return counts / timescale / 171.232876

class InvalidArgument(Exception):
    def __init__(self, value="Invalid argument. RadiationScrapingTool() or RadiationScrapingTool(instance_of_nlp_news_checker)"):
            self.value = value

    def __str__(self):
        return repr(self.value)

class NLPNewsCheckerNotValid(Exception):
    def __init__(self, value="Given instance of NLPNewsChecker is not valid, please check if you found date and countries in article"):
            self.value = value

    def __str__(self):
        return repr(self.value)

class Not200Code(Exception):
    def __init__(self, value="Returned http code is not 200"):
            self.value = value

    def __str__(self):
        return repr(self.value)

'''class DataRelatedToDateNotFound(Exception):
    def __init__(self, value="Data not found. Please be aware that data is limited to maximum 2 months backwards")
            self.value = value

    def __str__(self):
        return repr(self.value)
'''
if __name__ == '__main__':
    RadiationScrapingTool()
