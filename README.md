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

`Availability_requests`] needs columns:

-   `Key`: (text) Used as part of the link to the personalized
    calendar.
-   `Message`: (text) A message shown to the user on their
    personalized calendar.
-   `Responded`: (bool, output) To record whether the user has responded to
    this request.
-   `Response`: (text, output) To record the user\'s textual response.

`Request_timespans` needs columns:

-   `Request`: (reference to `Availability_requests`)
-   `Start`: (datetime)
-   `End`: (datetime)
-   `Allow partial`: (bool) If yes, will draw a timespan in the background,
    allowing the user to draw their availability over it. If no, only allows
    the user to say yes/no to each timespan.

### Output

`Availability`:

-   `Start`: (datetime)
-   `End`: (datetime)
-   `Available`: (bool)
-   `Request_timespan`: (reference to `Request_timespan`)
    Added if `Allow partial` is false for a given span.
