import os

from flask import Flask, url_for
from jinja2 import Environment, PackageLoader, select_autoescape
from .grist_client import GristClient


app = Flask(__name__)

jinja_env = Environment(
        loader=PackageLoader("availability"),
        autoescape=select_autoescape()
        )


GRIST_ROOT_URL = os.environ["GRIST_ROOT_URL"]
with open(os.environ["GRIST_API_KEY_FILE"], "r") as inf:
    GRIST_API_KEY = inf.read().strip()
GRIST_DOC_ID = os.environ["GRIST_DOC_ID"]


@app.route("/availability/<key>", methods=("GET", "POST"))
def availability(key: str):
    client = GristClient(GRIST_ROOT_URL, GRIST_API_KEY, GRIST_DOC_ID)

    avrequest, = client.get_records("Availability_requests", filter={"Key": [key]})

    timespans = client.get_records(
            "Request_timespans",
            filter={"Request": [avrequest["id"]]})

    has_slots = False
    has_spans = False

    initial_date = None
    events = []
    for tspan in timespans:
        fields = tspan["fields"]
        if initial_date is None:
            initial_date = fields["Start"]*1000
        else:
            initial_date = min(initial_date, fields["Start"]*1000)

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
                        "id": tspan["id"],
                        "start": fields["Start"]*1000,
                        "end": fields["End"]*1000,
                        "classNames": "avr-unknown",
                        })
            has_slots = True

    template = jinja_env.get_template("index.html")
    return template.render(
            avrequest=avrequest,
            events=events,
            initial_date=initial_date,
            js_url=url_for("static", filename="availability.js"),
            has_slots=has_slots,
            has_spans=has_spans)

# vim: foldmethod=marker
