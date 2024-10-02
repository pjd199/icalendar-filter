"""iCalendar Filter."""

from re import findall

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
    tag_travel = "tag_travel" in request.args
    tag_decompress = "tag_decompress" in request.args
    ics_data = requests.get(url, timeout=60).text
    calendar = icalendar.Calendar.from_ical(ics_data)

    # handle the start and end dates
    events = (
        recurring_ical_events.of(calendar).between(start_date, end_date)
        if (start_date is not None and end_date is not None)
        else calendar.walk("VEVENT")
    )

    # tag travel events
    if tag_travel:
        # list all the travel event
        travel_events = [
            event
            for event in events
            if "travel" in event.get("SUMMARY", "").lower()
            and "this event was created by" in event.get("DESCRIPTION", "").lower()
        ]
        # create a mapping for all the start and end times for each travel event
        travel_time_starts = {e["DTSTART"].dt: e for e in travel_events}
        travel_time_ends = {e["DTEND"].dt: e for e in travel_events}
        for event in events:
            # extract the tags in the event
            tags = findall(r"#\w+", event.get("SUMMARY", ""))
            if tags and len(findall(r",", event.get("LOCATION", ""))) >= 2:
                # event has tags and location, so look for a travel event
                # that directly preceeds this event
                if event["DTSTART"].dt in travel_time_ends:
                    travel_event = travel_time_ends[event["DTSTART"].dt]
                    travel_event["SUMMARY"] += " " + " ".join(tags)
                    # pop travel_event to avoid duplicate processing
                    travel_time_starts.pop(travel_event["DTSTART"].dt, None)
                    travel_time_ends.pop(travel_event["DTEND"].dt, None)
                # look for a travel event that directly follows this event
                if event["DTEND"].dt in travel_time_starts:
                    travel_event = travel_time_starts[event["DTEND"].dt]
                    travel_event["SUMMARY"] += " " + " ".join(tags)
                    # pop travel_event to avoid duplicate processing
                    travel_time_starts.pop(travel_event["DTSTART"].dt, None)
                    travel_time_ends.pop(travel_event["DTEND"].dt, None)

    # tag decompress events
    if tag_decompress:
        # list all the decompress event
        decompress_events = [
            event
            for event in events
            if "decompress" in event.get("SUMMARY", "").lower()
            and "this event was created by" in event.get("DESCRIPTION", "").lower()
        ]
        # create a mapping for all the start times for each decompress event
        decompress_time_starts = {e["DTSTART"].dt: e for e in decompress_events}
        for event in events:
            # extract the tags in the event
            tags = findall(r"#\w+", event.get("SUMMARY", ""))
            # look for a decompress event that directly follows this event
            if tags and event["DTEND"].dt in decompress_time_starts:
                decompress_event = decompress_time_starts[event["DTEND"].dt]
                decompress_event["SUMMARY"] += " " + " ".join(tags)
                # pop travel_event to avoid duplicate processing
                decompress_time_starts.pop(travel_event["DTSTART"].dt, None)

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
