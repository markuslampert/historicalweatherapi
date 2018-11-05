from flask import Flask

app = Flask(__name__)
app.config["DEBUG"] = False
app.config["JSON_SORT_KEYS"] = False

from historical_weather_app.api import api_bp

app.register_blueprint(api_bp)
