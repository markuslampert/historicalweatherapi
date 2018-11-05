from historical_weather_app.api.db.mysql import MySqlDBAccess
from collections import OrderedDict
from math import ceil
from datetime import datetime
from copy import deepcopy
from historical_weather_app.api.exceptions import *


class Database:

    def __init__(self, server, username, password, database_name):
        self.db = MySqlDBAccess(server, username, password, database_name)

    def _select_one_line(self, statement):
        cursor = self.db.cursor
        cursor.execute(statement)
        return cursor.fetchone()

    def get_weather_station_list(self, page, page_size=500):

        # total amount of rows in table weather_station
        amount_of_rows = self._select_one_line("Select count(weather_station_id) From weather_station;")[0]

        cursor = self.db.cursor

        statement = """
        Select 
            weather_station.weather_station_id,
            weather_station.name,
            group_concat(parameter_type.parameter_name)
        From
            weather_station
            join weather_station_station_type
                on weather_station.weather_station_id = weather_station_station_type.weather_station_id
            join station_type
                on weather_station_station_type.station_type_id = station_type.station_type_id
            join parameter_type
                on station_type.station_type_id = parameter_type.station_type_id
            Group by weather_station.weather_station_id
            Limit %s,%s;
        """
        cursor.execute(statement, ((page - 1) * page_size, page_size))
        n = cursor.rowcount
        weather_stations = []
        for k in range(n):  # iterate table
            od = OrderedDict()
            dict_keys = ["weather_station_id", "name", "available_parameters"]
            row = cursor.fetchone()
            row_length = len(row)
            for m in range(row_length):  # iterate one row
                if m == 2:  # if available_parameters
                    available_parameters = row[m]  # parameters as comma separated str
                    available_parameters = available_parameters.split(",")  # parameters as list of str
                    od[dict_keys[m]] = available_parameters  # sets attribute available_parameters
                else:
                    od[dict_keys[m]] = row[m]  # sets attributes weather_station_id and name
            weather_stations.append(od)

        od = OrderedDict()
        od["page"] = page
        od["total_pages"] = ceil(amount_of_rows / page_size)
        od["weather_station_list"] = weather_stations
        return od

    def get_weather_station_information_by_id(self, weather_station_ids):

        if len(weather_station_ids) > 10:  # not more than 10 weather stations shell be requested
            raise MoreThan10WeatherStationsException400()

        cursor = self.db.cursor
        statement = """
        Select
            weather_station_id, name, latitude, longitude, county
        From
            weather_station
        Where
            weather_station_id in (""" + \
            ",".join(["%s" for k in weather_station_ids]) + \
            """)"""

        cursor.execute(statement, weather_station_ids)

        n = cursor.rowcount
        weather_stations = []
        for k in range(n):  # iterate table
            od = OrderedDict()
            dict_keys = ["weather_station_id", "name", "latitude", "longitude", "county"]
            row = cursor.fetchone()
            row_length = len(row)
            for m in range(row_length):  # iterate one row
                od[dict_keys[m]] = row[m]
            weather_stations.append(od)

        od = OrderedDict()
        od["weather_stations"] = weather_stations
        return od

    def get_whole_time_table_as_dict(self):
        """maps database table time as dict"""

        cursor = self.db.cursor
        statement = """
                Select * From time;
                """
        cursor.execute(statement)
        # columns: time_id, measurement_time
        time_table = {}
        n = cursor.rowcount
        for k in range(n):
            row = cursor.fetchone()
            time_table[row[0]] = row[1]
        # dict time_table's structure: int time_id: datetime measurement_time
        return time_table

    def _select_as_2d_list(self, statement):
        cursor = self.db.cursor
        cursor.execute(statement)
        return cursor.fetchall()

    def get_min_max_time_of_requested_weather_station_group(self, weather_station_ids):

        """ This function gets a amount of weather stations.
        The aim is to determine the absolute min and max datetime of this amount of weather stations.
        Returns tuple(datetime min, datetime max).
        """

        # In the inner select command the min and max datetime for each weather station is determined.
        # In the outer select command the absolute min and max datetime of the amount of min and max times
        # is determined. A datetime is represented by its time'id.
        cursor = self.db.cursor
        statement = """
        Select min(min_times), max(max_times) into @x ,@y
        From
            (
            Select
                weather_station_time.weather_station_id,
                min(weather_station_time.time_id) as min_times,
                max(weather_station_time.time_id) as max_times
            From
                weather_station_time
            Where
                weather_station_time.weather_station_id in (""" + \
                    ",".join(["%s" for k in weather_station_ids]) + \
                """)""" + \
        """
            group by weather_station_time.weather_station_id
            )
            as table_one;
        """
        cursor.execute(statement, weather_station_ids)

        # The following select command translates the time ids of the absolute min and max time
        # of the weather station group into datetime values.
        statement = """
        Select
            measurement_time
        From
            time
        Where time_id in (@x,@y);
        """
        min_max_time = self._select_as_2d_list(statement)

        # absolute min and max datetime of the weather station group is returned
        return min_max_time[0][0], min_max_time[1][0]

    def get_measurements_data(self, weather_station_ids, intersection_time_tuple,
                              parameters, page, page_size):
        cursor = self.db.cursor

        statement = """
        set @start_time = (Select time_id from time where measurement_time = %s);
        """
        cursor.execute(statement, (intersection_time_tuple[0],))
        statement = """
        set @end_time = (Select time_id from time where measurement_time = %s);
        """
        cursor.execute(statement, (intersection_time_tuple[1],))

        start_row = (page - 1) * page_size * 24
        amount_of_rows = page_size*24
        statement = """        
        Select
            measurement.parameter_type_id,
            table_one.weather_station_id,
            table_one.time_id,
            measurement.measurement_value
        From
            (
            """ + \
            "Union".join(
                ["""(Select * From weather_station_time Where weather_station_id = %s
                     and time_id between @start_time and @end_time Limit %s,%s)
                 """ for k in weather_station_ids]
            ) + \
            """
            ) as table_one
            join measurement
                on table_one.weather_station_time_id = measurement.weather_station_time_id
        Where measurement.parameter_type_id in (""" + \
            ",".join(["%s" for k in parameters]) + \
        """)""" + \
        """
        Order by
            measurement.parameter_type_id,
            table_one.weather_station_id,
            table_one.time_id;
        """
        # generate Sequence for prepared statement
        sequence = []
        for weather_station_id in weather_station_ids:
            sequence.append(weather_station_id)
            sequence.append(start_row)
            sequence.append(amount_of_rows)

        cursor.execute(statement, sequence+parameters)

    def fetchall(self):
        return self.db.cursor.fetchall()

    def close(self):
        self.db.close()
        self.db = None


class MeasurementsAccess:
    """
    An Object of this class is used by function get_measurements to retrieve weather data from database and generate the
    corresponding JSON response.
    """

    def __init__(self, db):
        self.db = db
        self.time_table = self.db.get_whole_time_table_as_dict()
        self.parameter_names = {8:  'soil_temp_5cm_dep_cel',
                                9:  'wind_spe_m_per_s',
                                10: 'wind_dir_deg',
                                11: 'precip_hei_mm',
                                12: 'sun_dur_min_of_h',
                                13: 'air_temp_2m_hei_cel',
                                14: 'rel_humid_2m_hei_percent'}
        self.measurements = []  # result lists; out of them the JSON response will be generated
        self.weather_stations = []
        self.parameters = []

    @staticmethod
    def _get_intersection_time_tuple(requested_time_tuple, db_available_time_tuple):
        """return intersection of user requested time range and in database available time range"""

        # if request start and end_time not touches the database start and end_time (no intersection)
        if requested_time_tuple[1] < db_available_time_tuple[0] \
                or requested_time_tuple[0] > db_available_time_tuple[1]:
            return []
        # else build the intersection_time_tuple
        intersection_time_tuple = deepcopy(requested_time_tuple)
        if requested_time_tuple[0] <= db_available_time_tuple[0]:
            intersection_time_tuple[0] = db_available_time_tuple[0]
        if requested_time_tuple[1] >= db_available_time_tuple[1]:
            intersection_time_tuple[1] = db_available_time_tuple[1]
        return intersection_time_tuple

    @staticmethod
    def _calculate_total_amount_of_pages(intersection_time_tuple, page_size):
        total_amount_of_pages = 1  # at least 1 page, also if there is no intersection
        if intersection_time_tuple:
            tmp_time_delta = (intersection_time_tuple[1] - intersection_time_tuple[0])
            total_amount_of_pages = ceil(
                (tmp_time_delta.days*24 + tmp_time_delta.seconds/3600) / (page_size * 24))
            total_amount_of_pages = 1 if total_amount_of_pages == 0 else total_amount_of_pages
            # at least 1, also if intersection_time_tuple[1] - intersection_time_tuple[0] is 0:00:00
        return total_amount_of_pages

    @staticmethod
    def _convert_parameters_into_parameter_ids(parameters):
        """
        returns str of comma separated parameter_ids corresponding to given parameter names
        returns "" if there is given a wrong parameter name
        """
        parameter_ids = {'soil_temp_5cm_dep_cel': 8,
                         'wind_spe_m_per_s': 9,
                         'wind_dir_deg': 10,
                         'precip_hei_mm': 11,
                         'sun_dur_min_of_h': 12,
                         'air_temp_2m_hei_cel': 13,
                         'rel_humid_2m_hei_percent': 14}
        parameter_ids = [parameter_ids.get(parameter, None) for parameter in parameters]
        return "" if None in parameter_ids else parameter_ids

    def _convert_cursor_rows_into_dict(self, row, next_weather_station_id_other,
                                       next_parameter_type_id_other, is_last_row):
        # 4 possible request-cases: weather_station:parameter, 1:1, 1:n, n:1, n:n
        parameter_type_id, weather_station_id, time_id, measurement_value = \
            row  # columns: parameter_type_id, weather_station_id, time_id, measurement_value

        measurement = OrderedDict()
        measurement["time"] = datetime.strftime(self.time_table.get(time_id), "%Y-%m-%dT%H:%M")
        measurement["value"] = measurement_value
        self.measurements.append(measurement)

        if next_weather_station_id_other or is_last_row:
            weather_station = OrderedDict()
            weather_station["weather_station_id"] = weather_station_id
            weather_station["measurements"] = self.measurements
            self.weather_stations.append(weather_station)
            self.measurements = []

        if next_parameter_type_id_other or is_last_row:
            if not self.weather_stations:  # if weather_stations is empty create and append a new weather_station
                weather_station = OrderedDict()  # its the case if there is a request for only one weather_station
                weather_station["weather_station_id"] = weather_station_id
                weather_station["measurements"] = self.measurements
                self.weather_stations.append(weather_station)
                self.measurements = []
            parameter = OrderedDict()
            parameter["parameter_name"] = self.parameter_names.get(parameter_type_id)
            parameter["weather_stations"] = self.weather_stations
            self.parameters.append(parameter)
            self.weather_stations = []

    def _create_measurements_dict_from_cursor(self, requested_time_tuple, intersection_time_tuple,
                                              page, total_amount_of_pages):

        measurements_table = self.db.fetchall()
        n = len(measurements_table)
        for k in range(n):
            row = measurements_table[k]
            is_last_row = k == n-1
            next_weather_station_id_other = None  # None for last row
            next_parameter_type_id_other = None
            if not is_last_row:
                next_row = measurements_table[k+1]
                next_weather_station_id_other = next_row[1] != row[1]
                next_parameter_type_id_other = next_row[0] != row[0]
            self._convert_cursor_rows_into_dict(
                row, next_weather_station_id_other, next_parameter_type_id_other, is_last_row)

        request_info = OrderedDict()
        request_info["requested_start_time"] = datetime.strftime(requested_time_tuple[0], "%Y-%m-%dT%H:%M")
        request_info["requested_end_time"] = datetime.strftime(requested_time_tuple[1], "%Y-%m-%dT%H:%M")
        request_info["available_start_time"] = datetime.strftime(intersection_time_tuple[0], "%Y-%m-%dT%H:%M")
        request_info["available_end_time"] = datetime.strftime(intersection_time_tuple[1], "%Y-%m-%dT%H:%M")
        data = OrderedDict()
        data["request_info"] = request_info
        data["page"] = page
        data["total_pages"] = total_amount_of_pages
        data["parameters"] = self.parameters
        return data

    def get_measurements_dict(self, parameter_identifiers, weather_station_ids,
                              requested_time_tuple, page, page_size=31):
        start_date, end_date = requested_time_tuple

        if end_date < start_date:  # exception handling
            raise StartDateAfterEndDateException400()
        if len(weather_station_ids) > 10:
            raise MoreThan10WeatherStationsException400()

        # handle given time range; determine intersection between user requested time range and database available
        # time range
        db_available_time_tuple = self.db.get_min_max_time_of_requested_weather_station_group(weather_station_ids)
        intersection_time_tuple = \
            self._get_intersection_time_tuple(requested_time_tuple, db_available_time_tuple)
        if not intersection_time_tuple:  # not found if user requested time range is not in database available
            raise NoDbEntriesForRequestException404()

        # concerning paging; calculate how many pages are needed to cover the intersection time range
        total_amount_of_pages = self._calculate_total_amount_of_pages(intersection_time_tuple, page_size)

        # convert parameter names into parameter_ids; they are needed to ease the communication with the database
        parameter_identifiers = self._convert_parameters_into_parameter_ids(parameter_identifiers)

        if not parameter_identifiers:  # parameter_identifiers now holds str of parameter_ids or empty str in error case
            raise WrongParameterException400()

        # build select command to retrieve desired weather data from data base and fire it
        self.db.get_measurements_data(weather_station_ids, intersection_time_tuple, parameter_identifiers,
                                      page, page_size)

        # make an ordered dict out of data stored in the cursor and return it
        return self._create_measurements_dict_from_cursor(requested_time_tuple, intersection_time_tuple,
                                                          page, total_amount_of_pages)
