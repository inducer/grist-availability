import dataclasses
import datetime
import json
import os
from time import time
from typing import (
    Any, Dict, Hashable, Optional, Sequence, Type, TypeVar, Union, cast, get_args,
    get_origin)

from flask import Flask, Response, flash, request, url_for
from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape
from pygrist_mini import GristClient


app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

JINJA_ENV = Environment(
    loader=PackageLoader("availability"),
    autoescape=select_autoescape(),
    undefined=StrictUndefined)


GRIST_ROOT_URL = os.environ["GRIST_ROOT_URL"]
with open(os.environ["GRIST_API_KEY_FILE"], "r") as inf:
    GRIST_API_KEY = inf.read().strip()
GRIST_DOC_ID = os.environ["GRIST_DOC_ID"]
NOTIFY_FROM = os.environ.get("NOTIFY_FROM")
NOTIFY_TO = os.environ.get("NOTIFY_TO")


CLIENT = GristClient(GRIST_ROOT_URL, GRIST_API_KEY, GRIST_DOC_ID)


def div_ceil(nr, dr):
    return -(-nr // dr)


# {{{ dataclasses

@dataclasses.dataclass(frozen=True)
class AvailabilityRequest:
    id: int
    request_group: Hashable
    key: str
    person: Any
    name: str
    allow_maybe: Optional[bool]
    message: str
    min_span_minutes: Optional[float]
    responded: Optional[float]  # unix timestamp
    response: str


@dataclasses.dataclass(frozen=True)
class RequestTimespan:
    id: int
    request_group: Hashable
    start: float
    end: float
    allow_partial: bool


@dataclasses.dataclass(frozen=True)
class TimeSlot:
    rspan_id: int
    start: datetime.datetime
    end: datetime.datetime
    available: Optional[bool]


@dataclasses.dataclass(frozen=True)
class TimeSpan:
    start: datetime.datetime
    end: datetime.datetime
    maybe: bool


def span_props_equal(sa: TimeSpan, sb: TimeSpan) -> bool:
    return sa.maybe == sb.maybe

# }}}


class ValidationError(Exception):
    pass


# {{{ json_to_dataclass

T = TypeVar("T")


def cast_to_type(t: Type[T], val: Any) -> Any:
    if t is datetime.datetime and isinstance(val, str):
        return datetime.datetime.fromisoformat(val)
    elif type(t).__module__ != "typing":
        return t(val)  # type: ignore[call-arg]
    else:
        return val


def json_to_dataclass(kv: Dict[str, Any], dataclass_type: Type[T]) -> T:
    kwargs = {}
    assert dataclasses.is_dataclass(dataclass_type)

    for f in dataclasses.fields(dataclass_type):
        if (get_origin(f.type) is Union
                and len(get_args(f.type)) == 2
                and type(None) in get_args(f.type)):
            tp, = [t for t in get_args(f.type) if t is not type(None)]
            val = kv.get(f.name)
            if val is not None:
                val = cast_to_type(tp, val)

            kwargs[f.name] = val
        else:
            kwargs[f.name] = cast_to_type(f.type, kv[f.name])

    return cast(T, dataclass_type(**kwargs))


def grist_json_to_dataclass(kv: Dict[str, Any], dataclass_type: Type[T]) -> T:
    fields = {n.lower(): v for n, v in kv["fields"].items()}
    fields["id"] = kv["id"]
    return json_to_dataclass(fields, dataclass_type)

# }}}


# {{{ normalization/validation

def check_start_after_end(ss: Sequence[Union[TimeSpan, TimeSlot]]):
    for s in ss:
        if not s.start < s.end:
            raise ValidationError("start must come before end")


def merge_adjacent_spans(spans: Sequence[TimeSpan]) -> Sequence[TimeSpan]:
    # assumes spans are sorted
    if not spans:
        return []

    result = [spans[0]]
    for s in spans[1:]:
        if result[-1].end == s.start and span_props_equal(result[-1], s):
            result[-1] = dataclasses.replace(result[-1], end=s.end)
        else:
            result.append(s)

    return result


def check_nonoverlapping(spans: Sequence[TimeSpan]) -> None:
    # assumes spans are sorted

    last_end: Optional[datetime.datetime] = None
    for s in spans:
        if last_end is not None:
            if last_end > s.start:
                raise ValidationError("Some time spans overlap.")

        last_end = s.end


def check_slots_responded(slots: Sequence[TimeSlot]) -> None:
    for s in slots:
        if s.available is None:
            raise ValidationError(
                "Not all time slots have availability responses.")


def check_spans_within_requested(
        req_timespans: Sequence[RequestTimespan],
        spans: Sequence[TimeSpan]) -> None:
    for s in spans:
        start = s.start.timestamp()
        end = s.end.timestamp()

        if not any(
                rtspan.start <= start and end <= rtspan.end
                for rtspan in req_timespans):
            raise ValidationError(
                "Not all time spans fall within the requested times.")


def check_min_span_minutes(
        min_span_minutes: float, spans: Sequence[TimeSpan]) -> None:
    for s in spans:
        if (s.end - s.start).total_seconds() / 60 < min_span_minutes:
            raise ValidationError(
                "Not all time slots have the required "
                f"length of at least {min_span_minutes} minutes.")

# }}}


def get_request_timespans(req_group: Any):
    return [
        grist_json_to_dataclass(rtspan, RequestTimespan)
        for rtspan in CLIENT.get_records(
            "Request_timespans",
            filter={"Request_group": [req_group]})]


MSG_CAT_TO_BOOTSTRAP = {
    "error": "danger",
    "message": "primary",
    "warning": "warning",
}


def get_flashed_messages():
    from flask import get_flashed_messages
    msgs = {
        (MSG_CAT_TO_BOOTSTRAP.get(cat, "primary"), msg)
        for cat, msg in get_flashed_messages(with_categories=True)
    }

    return msgs


def render_calendar(
        av_request: AvailabilityRequest,
        req_timespans: Sequence[RequestTimespan],
        spans: Optional[Sequence[TimeSpan]] = None,
        slots: Optional[Sequence[TimeSlot]] = None):
    if spans is None:
        spans = []
    if slots is None:
        slots = []

    initial_date = None
    last_date = None
    events = []

    has_slots = False
    has_spans = False

    id_to_slot = {s.rspan_id: s for s in slots}

    for rtspan in req_timespans:
        if initial_date is None:
            initial_date = rtspan.start*1000
        else:
            initial_date = min(initial_date, rtspan.start*1000)
        if last_date is None:
            last_date = rtspan.end*1000
        else:
            last_date = max(last_date, rtspan.end*1000)

        if rtspan.allow_partial:
            events.append({
                        "id": rtspan.id,
                        "start": rtspan.start*1000,
                        "end": rtspan.end*1000,
                        "display": "background",
                        })
            has_spans = True
        else:
            old_slot = id_to_slot.get(rtspan.id)
            events.append({
                        "start": rtspan.start*1000,
                        "end": rtspan.end*1000,
                        "extendedProps": {
                            "type": "slot",
                            "available": old_slot.available if old_slot else None,
                            "rspan_id": rtspan.id,
                            },
                        })
            has_slots = True

    if has_spans:
        for span in spans:
            events.append({
                "start": span.start.isoformat(),
                "end": span.end.isoformat(),
                "editable": True,
                "extendedProps": {
                    "type": "span",
                    "maybe": span.maybe,
                }
            })

    if req_timespans:
        assert initial_date is not None
        assert last_date is not None
        number_of_days = div_ceil(
            last_date - initial_date,
            1000 * 3600 * 24)
    else:
        number_of_days = 1

    template = JINJA_ENV.get_template("index.html")
    return template.render(
        messages=get_flashed_messages(),
        av_request=av_request,
        events=events,
        initial_date=initial_date,
        number_of_days=number_of_days,
        js_url=url_for("static", filename="availability.js"),
        has_slots=has_slots,
        allow_maybe=av_request.allow_maybe,
        has_spans=has_spans)


def send_notify(av_request: AvailabilityRequest, text_response: str,
                span_duration: float, slot_count: int) -> None:
    import smtplib
    import socket
    from email.message import EmailMessage

    summary = (
            f"{av_request.name} has responded for "
            f"request group {av_request.request_group}"
    )
    notification_template = JINJA_ENV.get_template("notification-email.txt")
    msg = EmailMessage()
    msg.set_content(notification_template.render(
                    summary=summary,
                    span_duration=span_duration,
                    slot_count=slot_count,
                    text_response=text_response,
                    hostname=socket.gethostname()))

    msg["Subject"] = f"[grist-av] {summary}"

    msg["From"] = NOTIFY_FROM
    msg["To"] = NOTIFY_TO

    s = smtplib.SMTP("localhost")
    s.send_message(msg)
    s.quit()


def respond_with_message(msg: str, category="message", status: Optional[int] = None):
    flash(msg, category)
    resp_text = (JINJA_ENV
            .get_template("base.html")
            .render(messages=get_flashed_messages()))
    return Response(resp_text, status)


@app.route("/availability/<key>", methods=["GET", "POST"])
def availabilit(key: str):
    av_requests = CLIENT.get_records("Availability_requests", filter={"Key": [key]})
    if not av_requests:
        return respond_with_message("Not found", "error", status=404)
    if len(av_requests) > 1:
        return respond_with_message(
            "More than one record found for request key", "error", status=500)

    av_request = grist_json_to_dataclass(av_requests[0], AvailabilityRequest)

    req_timespans = get_request_timespans(av_request.request_group)

    if request.method == "GET":
        if av_request.responded is not None:
            return respond_with_message(
                "Your availability has previously been submitted. ", "error")

        return render_calendar(av_request, req_timespans)
    else:
        if av_request.responded is not None:
            return respond_with_message(
                "Your availability has previously been submitted. "
                "The present response has not been recorded.", "error")

        cal_data = json.loads(request.form["calendarState"])
        cal_slots = [json_to_dataclass(s, TimeSlot) for s in cal_data["slots"]]
        cal_spans: Sequence[TimeSpan] = sorted(
            [json_to_dataclass(s, TimeSpan) for s in cal_data["spans"]],
            key=lambda span: span.start)

        text_response = request.form["response"]

        cal_spans = merge_adjacent_spans(cal_spans)

        try:
            check_start_after_end(cal_spans)
            check_start_after_end(cal_slots)
            check_nonoverlapping(cal_spans)
            check_slots_responded(cal_slots)
            check_spans_within_requested(req_timespans, cal_spans)
            if av_request.min_span_minutes is not None:
                check_min_span_minutes(av_request.min_span_minutes, cal_spans)

        except ValidationError as e:
            flash(f"Error: {e}", "error")
            return render_calendar(av_request, req_timespans,
                                   spans=cal_spans, slots=cal_slots)

        # {{{ save to database

        CLIENT.patch_records("Availability_requests", [
            (av_request.id, {
                "Responded": time(),
                "Response": text_response,
            })
        ])

        CLIENT.add_records("Availability", [{
                "Request_group": av_request.request_group,
                "Person": av_request.person,
                "Start": span.start.timestamp(),
                "End": span.end.timestamp(),
                "Available": True,
                } | ({"Maybe": span.maybe} if av_request.allow_maybe else {})
            for span in cal_spans])

        CLIENT.add_records("Availability", [{
                "Request_group": av_request.request_group,
                "Person": av_request.person,
                "Request_timespan": slot.rspan_id,
                "Start": slot.start.timestamp(),
                "End": slot.end.timestamp(),
                "Available": slot.available,
                }
            for slot in cal_slots])

        # }}}

        # {{{ notification email

        if NOTIFY_TO is not None and NOTIFY_FROM is not None:
            span_duration = sum(
                (span.end - span.start).total_seconds()
                for span in cal_spans)

            slot_count = sum(1 for slot in cal_slots if slot.available)

            send_notify(av_request, text_response, span_duration, slot_count)

        # }}}

        return respond_with_message("Thank you for submitting your availability!")


# vim: foldmethod=marker
