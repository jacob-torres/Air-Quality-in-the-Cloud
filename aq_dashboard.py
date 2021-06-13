"""OpenAQ Air Quality Dashboard with Flask."""
import openaq
import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Access environment variables
db_config = os.getenv('DB_CONFIG')

APP = Flask(__name__)
APP.config['SQLALCHEMY_DATABASE_URI'] = db_config
DB = SQLAlchemy(APP)


class Record(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    datetime = DB.Column(DB.String(25), nullable=False)
    value = DB.Column(DB.Float, nullable=False)

    def __repr__(self):
        return f"""
        UTC: {self.datetime}, Value: {self.value}
    """


def get_results():
    """Display raw data from the API."""
    DB.create_all()
    API = openaq.OpenAQ()
    status, body = API.measurements(city='Los Angeles', parameter='pm25')

    if (status == 200):
        results = body['results']

        for i in range(len(results)):
            utc = results[i]['date']['utc']
            val = results[i]['value']
            record = Record(datetime=utc, value=val)
            DB.session.add(record)

        DB.session.commit()
        return Record.query.all()

    else:
        return 'Something went wrong!'


@APP.route('/')
def root():
    """Base view."""
    return str(get_results())


@APP.route('/refresh')
def refresh():
    """Pull fresh data from Open AQ and replace existing data."""
    DB.drop_all()
    DB.create_all()
    get_results()
    DB.session.commit()
    return 'Data refreshed!'
