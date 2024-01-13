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

## UWSGI config for deployment

```
[uwsgi]
plugins = python311
socket = /tmp/uwsgi-grist-av.sock

env = GRIST_ROOT_URL=https://grist.tiker.net
env = GRIST_API_KEY_FILE=/home/grist-av/.grist-api-key
env = GRIST_DOC_ID=rLJPGJ9RLJ4TRVx4AxT2tW
env = SECRET_KEY=CHANGE_ME

# Optional. Only effective if both are provided.
env = NOTIFY_FROM=andreask@illinois.edu
env = NOTIFY_TO=andreask@illinois.edu

chdir = /home/grist-av/grist-availability
module=availability.app:app
uid = grist-av
gid = grist-av
need-app = 1
workers = 1
virtualenv=/home/grist-av/grist-availability/.venv
buffer-size = 16384
```
