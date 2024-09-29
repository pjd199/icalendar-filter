"""iCalendar Filter."""
import icalendar  # type: ignore
import recurring_ical_events  # type: ignore
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
    url = request.args.get("ics")
    if url is None:
        abort(400, description="URL Parameter 'ics' is missing")
    exclude = request.args.getlist("exclude")
    start_date = request.args.get("start")
    end_date = request.args.get("end")
    merge_travel = (
        request.args.get("travel") is not None
        and str(request.args.get("travel")).lower() == "true"
    )
    ics_data = requests.get(url, timeout=60).text
    calendar = icalendar.Calendar.from_ical(ics_data)

    # handle the start and end dates
    events = (
        recurring_ical_events.of(calendar).between(start_date, end_date)
        if (start_date is not None and end_date is not None)
        else calendar.walk("VEVENT")
    )

    # merge travel events
    if merge_travel:
        travel_events = [
            event
            for event in events
            if event.get("SUMMARY") is not None
            and "travel" in str(event.get("SUMMARY")).lower()
            and event.get("DESCRIPTION") is not None
            and "this event was created by" in event.get("DESCRIPTION").lower()
        ]
        travel_ends = {event.get("DTEND").dt: event for event in travel_events}
        travel_starts = {event.get("DTSTART").dt: event for event in travel_events}
        for event in events:
            if event["DTSTART"].dt in travel_ends:
                event["DTSTART"] = (travel_ends[event["DTSTART"].dt])["DTSTART"]
            if event["DTEND"].dt in travel_starts:
                event["DTEND"] = (travel_starts[event["DTEND"].dt])["DTEND"]
        events = [
            event
            for event in events
            if not (
                event.get("SUMMARY") is not None
                and "travel" in str(event.get("SUMMARY")).lower()
                and event.get("DESCRIPTION") is not None
                and "this event was created by" in event.get("DESCRIPTION").lower()
            )
        ]

    # filter the keywords
    events = [
        event
        for event in events
        if all(
            word.lower() not in str(event.get("SUMMARY")).lower()
            and word.lower() not in str(event.get("DESCRIPTION")).lower()
            for word in exclude
        )
    ]

    # update the calendar and send response
    calendar.subcomponents = events
    return Response(calendar.to_ical(), mimetype="text/calendar")
