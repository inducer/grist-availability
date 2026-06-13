# Collect availability responses (mini-Doodle/WhenIsGood), backed by Grist

Users arrive via a personalized link (`/availability/<key>`),
created in a table of "Availability requests" in
[Grist](https://github.com/gristlabs/grist-core).  Users are shown a calendar,
allowing them to

-   draw their availability over a shown set of ranges,
-   select yes/no for predefined time slots, and
-   submit a textual response.

Data from their response is once again recorded in Grist.

Needed configuration: see the [dev script](dev.sh) for needed
environment variables.

To run, first run `poetry install` (see [poetry
docs](https://python-poetry.org/docs/)), then run `dev.sh`. Generalize/deploy
from there.

## Schema assumptions

### Input (mostly)

`Availability_requests` needs columns:

-   `Request_group`: (int/any) Used to find request timespans.
    In my case, a reference to another table, `Availability_request_groups`, but
    it need not be.
-   `Key`: (text) Used as part of the link to the personalized
    calendar.
-   `Person`: (any) Identifier of person to whom the request is addressed.
    Copied verbatim into `Availability`.
-   `Name`: (text) Name of the person or entity whose availability
    is being requested.
-   `Allow_maybe`: (bool, optional) Whether timespans may be marked as 'If I must'.
-   `Message`: (text) A message shown to the user on their
    personalized calendar.
-   `Min_span_minutes`: (number, optional) The minimum number of minutes required
    in each time span supplied by a respondent.
-   `Responded`: (unix timestamp, input/output) To record whether (and when)
    the user has responded to this request.
-   `Response`: (text, output) To record the user's textual response.

`Request_timespans` needs columns:

-   `Request_group`: (int/any) Identifier of the group of requests, matches
    `Availability_requests.Request_group`.
-   `Start`: (unix timestamp)
-   `End`: (unix timestamp)
-   `Allow partial`: (bool) If yes, will draw a timespan in the background,
    allowing the user to draw their availability over it. If no, only allows
    the user to say yes/no to each timespan.

`Contextual_availability_requests` (optional) has columns:

-   `Request`: Reference to `Availability_requests`. The request for which
    context is being provided.
-   `Description`: A description of the contextual relationship
    (e.g. "student"/"instructor").
-   `Contextual_request`:  Reference to `Availability_requests`.
    The request from which contextual data should be shown.

### Output

`Availability`:

-   `Request_group`: (int/any) Identifier of the group of requests, matches
    `Availability_requests.Request_group`.
-   `Person`: (any)
-   `Start`: (unix timestamp)
-   `End`: (unix timestamp)
-   `Available`: (bool)
-   `Maybe`: (bool) (only used if `Allow_maybe` is present and truthy)
-   `Request_timespan`: (reference to `Request_timespan`)
    Added if `Allow partial` is false for a given span.

## Systemd service file for deployment

```
[Unit]
Description=Grist Availability via Granian
After=network.target

[Service]
User={{ user }}
Group={{ user }}

WorkingDirectory={{ home_dir }}/grist-availability

Environment="GRANIAN_HOST=127.0.0.1"
Environment="GRANIAN_PORT=8123"
Environment="GRANIAN_WORKERS=1"
Environment="GRANIAN_WORKERS_MAX_RSS=500"
Environment="GRANIAN_INTERFACE=wsgi"
Environment="GRANIAN_RESPAWN_FAILED_WORKERS=true"

Environment=GRIST_ROOT_URL=https://scicomp-grist.cs.illinois.edu
Environment=GRIST_API_KEY_FILE={{ home_dir }}/.grist-api-key
Environment=GRIST_DOC_ID={{ grist_doc_id }}
Environment=NOTIFY_FROM=andreask@illinois.edu
Environment=NOTIFY_TO=andreask@illinois.edu
Environment=SECRET_KEY={{ flask_secret_key }}

Environment=CAL_TIMEZONES=America/Chicago,local,UTC

ExecStart={{ home_dir }}/grist-availability/.venv/bin/granian availability.app:app

[Install]
WantedBy=multi-user.target
```
