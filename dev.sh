#! /bin/bash

export GRIST_ROOT_URL="https://scicomp-grist.cs.illinois.edu"
export GRIST_API_KEY_FILE="$HOME/.grist-uiuc-api-key"
export GRIST_DOC_ID="s7VzXiAHXbwgivucYprb6z"

# Optional. Only effective if both are provided.
export NOTIFY_FROM="inform@tiker.net"
export NOTIFY_TO="inform@tiker.net"

export CAL_TIMEZONES="America/Chicago,local,UTC"

export SECRET_KEY="CHANGE_ME"

poetry run flask --app=availability.app run --debug
