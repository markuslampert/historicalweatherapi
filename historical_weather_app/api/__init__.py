from flask import Blueprint
import configparser
from historical_weather_app.api.db.database import Database

config = configparser.ConfigParser()
config.read("config.ini")
sctn = config["database"]
db = Database(sctn.get("server"), sctn.get("username"), sctn.get("password"), sctn.get("database_name"))

api_bp = Blueprint('api', __name__)
from historical_weather_app.api import weather_stations, error_messages
