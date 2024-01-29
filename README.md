# iCalendar Filter

An AWS lambda function for filtering events
from a calendar file in ICS format. If any 
calendar event contains the any of the
exclude words in the title or description
the event will be filtered out. The
remaining events will be output in ICS
format. 

## URL Parameters
* url - the URL of the ics file
* exclude - the filter words (may be specified multiple times)

## Output
The filtered ICS

## License
Licensed under MIT
