from historical_weather_app.api import api_bp
from historical_weather_app.api import db
from historical_weather_app.api.db.database import MeasurementsAccess
from flask import jsonify
from flask import render_template
from datetime import datetime


@api_bp.route('/weather-station-list', methods=['GET'])
@api_bp.route('/weather-station-list/pages/<int:page>', methods=['GET'])
def get_weather_station_list(page=1):
    return jsonify(db.get_weather_station_list(page))


def convert_comma_separated_str_into_list(comma_separated_str, get_type="str"):
    tmp_list = comma_separated_str.split(",")
    if get_type == "str":
        return list(map(lambda x: x.strip(), tmp_list))
    if get_type == "int":
        return list(map(lambda x: int(x.strip()), tmp_list))
    if get_type == "datetime":
        return list(map(lambda x: datetime.strptime(x.strip(), "%Y-%m-%dT%H:%M").replace(minute=0), tmp_list))


@api_bp.route('/weather-stations/<weather_station_ids>', methods=['GET'])
def get_weather_stations(weather_station_ids):
    weather_station_dict = db.get_weather_station_information_by_id(
        convert_comma_separated_str_into_list(weather_station_ids)
    )
    return jsonify(weather_station_dict)


@api_bp.route('/measurements/<parameters>/<weather_station_ids>/<duration>', methods=['GET'])
@api_bp.route('/measurements/<parameters>/<weather_station_ids>/<duration>/pages/<int:page>', methods=['GET'])
def get_measurements(parameters, weather_station_ids, duration, page=1):

    measurements_access = MeasurementsAccess(db)

    return jsonify(
        measurements_access.get_measurements_dict(
            convert_comma_separated_str_into_list(parameters),
            convert_comma_separated_str_into_list(weather_station_ids, "int"),
            convert_comma_separated_str_into_list(duration, "datetime"),
            page
        )
    )


@api_bp.route('/', methods=['GET'])
def index():
    return render_template("index.html")
