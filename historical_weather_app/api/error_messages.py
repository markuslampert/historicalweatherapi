from flask import Response
from historical_weather_app.api import api_bp
from historical_weather_app.api.exceptions import *


def error_return(content, status):
    """content must be str containing JSON; status is HTTP status code and must be int"""
    content = '{' + '"status":{},"message":"{}"'.format(status, content) + '}'
    return Response(content, status=status, mimetype='application/json')


@api_bp.errorhandler(NoDbEntriesForRequestException404)
def handle_no_db_entries_for_request_exception_404(error):
    return error_return("No DB entries for requested start time and end time.", 404)


@api_bp.errorhandler(StartDateAfterEndDateException400)
def handle_start_date_for_end_date_exception_400(error):
    return error_return("Given start time must be before given end time.", 400)


@api_bp.errorhandler(MoreThan10WeatherStationsException400)
def handle_more_than_10_weather_station_exception_400(error):
    return error_return("More than 10 weather stations given.", 400)


@api_bp.errorhandler(WrongParameterException400)
def handle_wrong_parameter_exception_400(error):
    return error_return("At least one wrong parameter name given.", 400)
