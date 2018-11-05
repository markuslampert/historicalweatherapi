historical_weather_api v1.0
===========================


Introduction
------------

The project "historical_weather_api" is a read only restful web API which is realized by a Flask application.
Weather data stored in an underlying MySQL database can be retrieved by this web API.


Requirements
------------

* MySQL database server
* WSGI server (e.g. gunicorn)
* python 3
* third party modules

    - flask
    - pymysql


Idea of the program
-------------------

Folder "historical_weather_api" contains the Flask application and the Flask application Object is called "app".
In "config.ini" login data for the database connection is stored.
Folder 'static' contains CSS files and folder 'templates' HTML files to render the main page of the API.
Flask application Object "app" has one blueprint (in Flask kind of module) named "api".
In "weather_stations.py" functions concerning the use cases are assigned to URLs. If a URL is called these functions are evoked.

In folder "db" functions for reading data out of database are stored. 
"mysql.py" contains a wrapper class for the pymysql module. Thereby the connection and disconnection to the database is outsourced from "database.py".

Wrong URL input by the user is handled by exceptions which are listed in "exceptions.py".
If an exception is thrown, the specific listening function in "error_messages.py" is called and an error message as output is made.

The API delivers JSON documents. Flask's jsonify function is used to convert OrderedDicts into JSON response. Therefore functions in "weather_stations.py" demand data structured in OrderedDicts from "database.py". Functions in "database.py" retrieve data from database and convert them to OrderedDicts. OrderedDicts must be used instead of Dicts because the order of attributes in a Dict is not fixed. If jsonify gets a Dict as input the output will be a JSON response where attributes are mixed up.

The use case to deliver weather data to specific place time and parameters (function "get_measurements") needs a longer program procedure. Because of that the extra class "Measurements_access" has been created which has the responsibility to handle the retrieval of data and creation of the OrderedDict concerning this use case only.
