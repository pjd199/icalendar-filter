import requests
import icalendar
from flask import Flask, request, Response

from apig_wsgi import make_lambda_handler
from flask_cors import cross_origin

app = Flask(__name__)
lambda_handler = make_lambda_handler(app)

@app.route('/', methods=['GET'])
@cross_origin()
def filter_events():
    url = request.args.get('url')
    words = request.args.getlist('words')
    ics_data = requests.get(url).text
    calendar = icalendar.Calendar.from_ical(ics_data)
    filtered_events = []
    for event in calendar.walk('VEVENT'):
        if all(word not in str(event.get('SUMMARY')) and word not in str(event.get('DESCRIPTION')) for word in words):
            filtered_events.append(event)
    calendar.subcomponents = filtered_events
    response = Response(calendar.to_ical(), mimetype='text/calendar')
    return response
