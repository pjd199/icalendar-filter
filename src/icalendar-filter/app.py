import requests
import icalendar
from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['GET'])
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
    return calendar.to_ical().decode('utf-8')
