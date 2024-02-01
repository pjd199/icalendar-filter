"""iCalendar Filter."""
import icalendar  # type: ignore
import requests
from apig_wsgi import make_lambda_handler
from flask import Flask, Response, abort, request
from flask_cors import cross_origin

app = Flask(__name__)
lambda_handler = make_lambda_handler(app)


@app.route("/", methods=["GET"])
@cross_origin()
def filter_events() -> Response:
    """Handle the root path."""
    return Response("Hello", mimetype="text/plain")
    url = request.args.get("url")
    if url is None:
        abort(401)
    words = request.args.getlist("words")
    ics_data = requests.get(url, timeout=60).text
    calendar = icalendar.Calendar.from_ical(ics_data)
    filtered_events = [
        event
        for event in calendar.walk("VEVENT")
        if all(
            word not in str(event.get("SUMMARY"))
            and word not in str(event.get("DESCRIPTION"))
            for word in words
        )
    ]
    calendar.subcomponents = filtered_events
    return Response(calendar.to_ical(), mimetype="text/calendar")
