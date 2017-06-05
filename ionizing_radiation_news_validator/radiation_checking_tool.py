from nlp_news_checker import NLPNewsChecker
from geocoding import Geocoding
from exceptions import Not200Code, InvalidArgument, NLPNewsCheckerNotValid
import re
import requests
import numpy
import time
import datetime
import matplotlib.pyplot as plt


class RadiationCheckingTool:
    def __init__(self, nlp_news_checker=None):
        self.__geocoding = Geocoding()
        if nlp_news_checker:
            if not isinstance(nlp_news_checker, NLPNewsChecker):
                raise InvalidArgument(
                    "RadiationCheckingTool() or RadiationCheckingTool("
                    "instance_of_nlp_news_checker)")
            try:
                self.__date = nlp_news_checker.date
                self.__cities = self.__map_list_of_countries_to_capital_cities(
                    nlp_news_checker.enumerated_countries)
                self.__countries = nlp_news_checker.enumerated_countries
            except:
                raise NLPNewsCheckerNotValid()
        else:
            d = datetime.datetime.now()
            self.__date = str(d.year) + "-" + str(d.month) + "-" + str(d.day)
            self.__countries = list()
            self.__cities = list()
        self.__get_list_of_active_sensors_and_reactors()

    # Setting up date in format YYYY-MM-DD
    def set_up_date(self, given_date):
        if not re.match("^[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}$", given_date):
            print("Date is not valid, please type date in formay YYYY-MM-DD")
        else:
            self.__date = given_date

    # Setting up list of countries. Only european
    def set_up_list_of_countries(self, countries):
        if not isinstance(countries, list):
            print("Please provide countries in list")
        else:
            self.__cities = self.__map_list_of_countries_to_capital_cities(
                countries)
            self.__countries = countries

    # Take list of countries and map it to its capital cities
    def __map_list_of_countries_to_capital_cities(self, countries_list):
        result = list()
        for country in countries_list:
            try:
                result.append(Geocoding.get_capital_city_by_country(country))
            except Not200Code:
                print("Capital of " + country + " not found")
                countries_list.remove(country)
        return result

    # Setting reactors and sensors
    def __get_list_of_active_sensors_and_reactors(self):
        r = requests.get("http://radioactiveathome.org/map/")
        if (not r.status_code == 200):
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
        (self.__reactors_names,
         self.__reactors_coords) = self.__get_array_tuple_of_reactors(
            reactors_raw)
        self.__sensors_numpy = self.__get_array_of_sensors(sensors_raw)

    # Converts list of string to numpy array with structure [id, latitude,
    # longitude]
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
            line = line[end + 2:]
            (end, _) = patteren_comma.search(line).span()
            result[i][0] = int(line[0:end])
        return result

    # Converts list of string to (list with name, numpy array with structure
    #  [latitude, longitude])
    def __get_array_tuple_of_reactors(self, reactors_raw):
        result_names = list()
        result_coords = numpy.empty((len(reactors_raw), 2))
        pattern_createMarker = re.compile(
            "\(createReactorMarker\(new GLatLng\(")
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

    def __get_list_of_sensors_in_range_km(self, coords, range_km):
        list_of_sensors = list()
        for sensor in self.__sensors_numpy:
            if Geocoding.compute_distance_between_two_coordinates(coords, (
                    sensor[1], sensor[2])) < range_km:
                list_of_sensors.append((sensor[0], sensor[1], sensor[2]))
        return list_of_sensors

    def __get_list_of_reactors_in_range_km(self, coords, range_km):
        list_of_reactors = list()
        for i, reactor in enumerate(self.__reactors_coords):
            if Geocoding.compute_distance_between_two_coordinates(coords, (
                    reactor[0], reactor[1])) < range_km:
                list_of_reactors.append(
                    (self.__reactors_names[i], reactor[0], reactor[1]))
        return list_of_reactors

    # Scrape pages, download data and return data from one particular day
    # sensor_id - int, date format YYYY-MM-DD - string
    # Result is returned in numpy array format [timestamp, measurement]
    def __get_sensor_data_from_day(self, sensor_id, date):
        url_1 = "http://radioactiveathome.org/boinc/gettrickledata.php?start="
        url_2 = "&hostid="
        searched_date = self.__convert_date_to_timestamp(date)
        current_measurement_id = 0
        results = list()
        while True:
            r = requests.get(
                url_1 + str(current_measurement_id) + url_2 + str(sensor_id))
            if (not r.status_code == 200):
                raise Not200Code()
            str_content = str(r.content)

            if re.search("NO DATA", str_content):  # reached end of data
                break
            # Split by line, remove first line
            splitted_data = str_content[2:len(str_content) - 3].split("\\n")[
                            1:]
            # Extract next page pointer
            current_measurement_id = int(
                splitted_data[len(splitted_data) - 1].split(",")[0])
            (first_record_date, _, _,
             _) = self.__extract_data_time_counts_timescale_from_line(
                splitted_data[1])
            if self.__convert_date_to_timestamp(
                    first_record_date) > searched_date:
                break  # current data is newer than searched

            (last_record_date, _, _,
             _) = self.__extract_data_time_counts_timescale_from_line(
                splitted_data[len(splitted_data) - 1])
            if self.__convert_date_to_timestamp(
                    last_record_date) < searched_date:
                continue  # current data too old

            for line in splitted_data:
                (date, hours, counts,
                 timescale) = \
                    self.__extract_data_time_counts_timescale_from_line(
                        line)
                if self.__convert_date_to_timestamp(date) == searched_date:
                    results.append(
                        (self.__convert_date_time_to_timestamp(date, hours),
                         self.__convert_counts_per_time_to_uSv(counts,
                                                               timescale)))
        return numpy.array(results)

    # line example
    # 287000059,6,80,2017-04-30 23:46:29,51.803020,19.753744,3.993,n,0,513
    # returns (date, time, counts, duration of measurement)
    def __extract_data_time_counts_timescale_from_line(self, line):
        splitted_line = line.split(",")
        splitted_date_time = splitted_line[3].split(" ")
        return (
            splitted_date_time[0], splitted_date_time[1],
            int(splitted_line[2]),
            float(splitted_line[6]))

    def __convert_date_time_to_timestamp(self, date, hours=""):
        return time.mktime(datetime.datetime.strptime(date + " " + hours,
                                                      "%Y-%m-%d "
                                                      "%H:%M:%S").timetuple())

    def __convert_date_to_timestamp(self, date):
        return time.mktime(
            datetime.datetime.strptime(date, "%Y-%m-%d").timetuple())

    # Equation source:
    # http://radioactiveathome.org/boinc/forum_thread.php?id=60&nowrap=true#716
    def __convert_counts_per_time_to_uSv(self, counts, timescale):
        return counts / timescale / 171.232876

    # Take not analysed sensor data in two dimensional numpy array with
    # format [timestamp, measurement]
    # Return numpy array 24 rows, 3 cols, format [mininum value, maximum
    # value, average hour value]
    def __get_min_max_avg_per_hour(sensor_data):
        result = numpy.zeros((24, 3))
        timestamp = int(sensor_data[0][0])
        delta = datetime.timedelta(hours=1)
        daytime = datetime.datetime.fromtimestamp(timestamp) + delta
        timestamp = daytime.timestamp()

        i = 0
        for j in range(24):
            avg = count = 0
            if i < len(sensor_data):
                min_v = max_v = sensor_data[i][1]
            while i < len(sensor_data) and sensor_data[i][0] < timestamp:
                data = sensor_data[i][1]
                avg += data
                count += 1
                if min_v > data:
                    min_v = data
                if max_v < data:
                    max_v = data
                i += 1
            if count > 0:
                result[j][0] = min_v
                result[j][1] = max_v
                result[j][2] = avg / count
            daytime = daytime + delta
            timestamp = daytime.timestamp()
        return result

    # Prints graph
    def __create_min_max_avg_graph(prepared_data, coords, extra_info=''):
        (c1, c2) = coords
        fig, ax = plt.subplots(figsize=(15, 5))
        width = 1
        min_v = ax.bar([x * 4 for x in range(24)], prepared_data[:, 0], width,
                       color='g')
        max_v = ax.bar([x * 4 + 1 for x in range(24)], prepared_data[:, 1],
                       width, color='r')
        avg_v = ax.bar([x * 4 + 2 for x in range(24)], prepared_data[:, 2],
                       width, color='b')
        ax.set_ylabel('Radiation [uSv]')
        ax.set_title(
            'Minimum, maximum, average radiation per hour - sensor position '
            '' + str(
                c1) + '° ' + str(
                c2) + '°' + extra_info)
        ax.set_xticks([x * 4 for x in range(24)])
        ax.set_xticklabels([x for x in range(24)])
        ax.legend((min_v[0], max_v[0], avg_v[0]), ('min', 'max', 'avg'))
        plt.show()

    def __is_any_raised_avg_measurement(prepared_data):
        for measurement in prepared_data:
            if measurement[2] > 0.3:
                return True
        return False

    def __get_percentage_of_raised_measurements(raw_data):
        count = 0
        for measurement in raw_data:
            if measurement[1] > 0.3:
                count += 1
        return count * 100 / len(raw_data)

    # Return closes sensor (id, coord1, coord2)
    def __find_closest_sensor(self, coords):
        closest_sensor_distance = \
            Geocoding.compute_distance_between_two_coordinates(
                coords, (
                    self.__sensors_numpy[0][1], self.__sensors_numpy[0][2]))
        for sensor in self.__sensors_numpy:
            distance = Geocoding.compute_distance_between_two_coordinates(
                coords, (sensor[1], sensor[2]))
            if distance < closest_sensor_distance:
                closest_sensor_distance = distance
                closest_sensor = sensor
        return closest_sensor

    # Download data from sensors in range x km from city, analyse it and
    # print results
    def check_radiation_in_city_day(self, city, day, range_km=100):
        city_coords = self.__geocoding.get_city_coords(city)
        sensors_list = self.__get_list_of_sensors_in_range_km(city_coords,
                                                              range_km)
        for i, sensor in enumerate(sensors_list):
            self.__download_data_for_sensor_and_analyse_it(sensor, day,
                                                           city_coords)

    # Download data from one nearest sensor from city setted earlier,
    # analyse it and print results
    def check_radiation_in_countries(self):
        for i, city in enumerate(self.__cities):
            city_coords = self.__geocoding.get_city_coords(city)
            closest_sensor = self.__find_closest_sensor(city_coords)
            print("\nData for %s:" % self.__countries[i])
            self.__download_data_for_sensor_and_analyse_it(closest_sensor,
                                                           self.__date,
                                                           city_coords)

    # Download data for one sensor, one day, for one city, and visualise it
    def __download_data_for_sensor_and_analyse_it(self, sensor, day,
                                                  city_coords):
        raw_data = self.__get_sensor_data_from_day(sensor[0], day)
        if raw_data.any():
            prepared_data = RadiationCheckingTool.__get_min_max_avg_per_hour(
                raw_data)
            distance_tmp = Geocoding.compute_distance_between_two_coordinates(
                city_coords, (sensor[1], sensor[2]))
            RadiationCheckingTool.__create_min_max_avg_graph(prepared_data, (
                sensor[1], sensor[2]), " Distance from  city: %.2f km."
                 % distance_tmp)
            if RadiationCheckingTool.__is_any_raised_avg_measurement(
                    prepared_data):
                print("Warning: At least one average measurement is raised.\
                    (> 0.3 uSv/h)")
            else:
                print("All average measurements are in quota")
            percentage_of_raised_measurements = RadiationCheckingTool. \
                __get_percentage_of_raised_measurements(raw_data)
            print("This sensor has %2.2f%% measurements above 0.3 uSv/h" %
                  percentage_of_raised_measurements)
        else:
            print("There is no data from this day - sensor sensor position " +
                  str(sensor[1]) + '° ' + str(sensor[1]) + '°')

    # Print reactors in range of x km
    def print_reactors_in_range(self, city, range_km=100):
        city_coords = self.__geocoding.get_city_coords(city)
        reactor_list = self.__get_list_of_reactors_in_range_km(city_coords,
                                                               range_km)
        if len(reactor_list) == 0:
            print("No reactors in range %d" % range_km)
        else:
            print("Reactors in range %d" % range_km)
        for reactor in reactor_list:
            print(('{0:} {1:.3f} {2:.3f}'.format(reactor[0], reactor[1],
                                                 reactor[2])))
