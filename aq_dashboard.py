"""OpenAQ Air Quality Dashboard with Flask."""
import sqlalchemy
from sqlalchemy.orm import exc
import openaq
import os
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

# Access environment variables
db_config = os.getenv('DB_CONFIG')

APP = Flask(__name__)
APP.config['SQLALCHEMY_DATABASE_URI'] = db_config
DB = SQLAlchemy(APP)
API = openaq.OpenAQ()


class Record(DB.Model):
    """Defines the schema for a record of air-quality data."""
    id = DB.Column(DB.Integer, primary_key=True)
    datetime = DB.Column(DB.String(25), nullable=False)
    value = DB.Column(DB.Float, nullable=False)

    def __repr__(self):
        return f"{(self.datetime, self.value)}"


class Location(DB.Model):
    """Defines the schema for a location record, with city name and coordinates."""
    id = DB.Column('id', DB.Integer, primary_key=True)
    city = DB.Column('city', DB.String(25))
    country = DB.Column('country', DB.String(25))
    lat = DB.Column('lat', DB.Float)
    long = DB.Column('long', DB.Float)
    count = DB.Column('count', DB.Integer)

    def __repr__(self):
        return f"{self.city}, {self.country}: lattitude = {self.lat}, Longitude = {self.long}, count = {self.count}"


def get_la_measurements():
    """Display the latest raw datetime/measurement data from the API for Los Angeles."""
    try:
        DB.create_all()
        status, body = API.measurements(city='Los Angeles', parameter='pm25')

        if status == 200:
            results = body['results']

            for r in results:
                utc = r['date']['utc']
                val = r['value']
                record = Record(datetime=utc, value=val)
                DB.session.add(record)

            DB.session.commit()
            return Record.query.all()

        else:
            return "Something went wrong!"

    except (Exception, sqlalchemy.exc) as err:
        print(err)


def get_locations():
    """Displays a list of locations and their coordinates."""
    try:
        DB.create_all()
        status, body = API.locations()

        if status == 200:
            results = body['results']

            for r in results:
                city = r['city']
                country = r['country']
                lat = r['coordinates']['latitude']
                long = r['coordinates']['longitude']
                count = r['count']
                loc = Location(
                    city=city, country=country, lat=lat, long=long, count=count
                )
                DB.session.add(loc)

            DB.session.commit()
            return Location.query.all()

        else:
            return "Something went wrong!"

    except (Exception, sqlalchemy.exc) as err:
        print(err)


@APP.route('/')
def index():
    """Renders the homepage and displays datetime/value tuples."""
    results = get_la_measurements()
    return render_template('home.html', results=results)


@APP.route('/locations')
def locations():
    """Displays a list of locations and other measurements."""
    results = get_locations()
    return render_template('locations.html', results=results)


@APP.route('/refresh')
def refresh():
    """Pull fresh data from Open AQ and replace existing data."""
    DB.drop_all()
    DB.create_all()
    DB.session.commit()
    results = get_results()
    return f"""Data refreshed!
    {results}
    """
