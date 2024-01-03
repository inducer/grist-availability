import json
import os

from flask import Flask, request, url_for
from jinja2 import Environment, PackageLoader, select_autoescape
from pygrist_mini import GristClient
from time import time


app = Flask(__name__)

jinja_env = Environment(
        loader=PackageLoader("availability"),
        autoescape=select_autoescape()
        )


GRIST_ROOT_URL = os.environ["GRIST_ROOT_URL"]
with open(os.environ["GRIST_API_KEY_FILE"], "r") as inf:
    GRIST_API_KEY = inf.read().strip()
GRIST_DOC_ID = os.environ["GRIST_DOC_ID"]


CLIENT = GristClient(GRIST_ROOT_URL, GRIST_API_KEY, GRIST_DOC_ID)


def div_ceil(nr, dr):
    return -(-nr // dr)


@app.get("/availability/<key>")
def availability(key: str):
    avrequests = CLIENT.get_records("Availability_requests", filter={"Key": [key]})
    if not avrequests:
        return "Not found", 404
    if len(avrequests) > 1:
        return "More than one record found for request key", 500
    avrequest, = avrequests
    req_group = avrequest["fields"]["Request_group"]

    if avrequest["fields"]["Responded"]:
        template = jinja_env.get_template("thanks.html")
        return template.render()

    timespans = CLIENT.get_records(
            "Request_timespans",
            filter={"Request_group": [req_group]})

    has_slots = False
    has_spans = False

    initial_date = None
    last_date = None
    events = []
    for tspan in timespans:
        fields = tspan["fields"]
        if initial_date is None:
            initial_date = fields["Start"]*1000
        else:
            initial_date = min(initial_date, fields["Start"]*1000)
        if last_date is None:
            last_date = fields["End"]*1000
        else:
            last_date = max(last_date, fields["End"]*1000)

        if fields["Allow_partial"]:
            events.append({
                        "id": tspan["id"],
                        "start": fields["Start"]*1000,
                        "end": fields["End"]*1000,
                        "display": "background",
                        })
            has_spans = True
        else:
            events.append({
                        "start": fields["Start"]*1000,
                        "end": fields["End"]*1000,
                        "title": "No Answer",
                        "extendedProps": {
                            "type": "slot",
                            "available": None,
                            "rspan_id": tspan["id"],
                            },
                        })
            has_slots = True

    if timespans:
        assert initial_date is not None
        assert last_date is not None
        number_of_days = div_ceil(
            last_date - initial_date,
            1000 * 3600 * 24)
    else:
        number_of_days = 1
    template = jinja_env.get_template("index.html")
    return template.render(
            avrequest=avrequest,
            events=events,
            initial_date=initial_date,
            number_of_days=number_of_days,
            js_url=url_for("static", filename="availability.js"),
            has_slots=has_slots,
            has_spans=has_spans)


@app.post("/availability/<key>")
def post_availability(key: str):
    cal_data = json.loads(request.form["calendarState"])
    cal_slots = cal_data["slots"]
    cal_spans = cal_data["spans"]

    avrequest, = CLIENT.get_records("Availability_requests", filter={"Key": [key]})
    req_group = avrequest["fields"]["Request_group"]

    CLIENT.patch_records("Availability_requests", [
        (avrequest["id"], {
            "Responded": time(),
            "Response": request.form["response"],
        })
    ])

    CLIENT.add_records("Availability", [{
            "Request_group": req_group,
            "Person": avrequest["fields"]["Person"],
            "Start": span["start"],
            "End": span["end"],
            "Available": True,
            }
        for span in cal_spans])

    CLIENT.add_records("Availability", [{
            "Request_group": req_group,
            "Person": avrequest["fields"]["Person"],
            "Request_timespan": slot["rspan_id"],
            "Start": slot["start"],
            "End": slot["end"],
            "Available": slot["available"],
            }
        for slot in cal_slots])

    template = jinja_env.get_template("thanks.html")
    return template.render()


# vim: foldmethod=marker
