#! /bin/bash

export GRIST_ROOT_URL="https://grist.tiker.net"
export GRIST_API_KEY_FILE="$HOME/.grist-api-key"
export GRIST_DOC_ID="isSNVL12chULhkfCZkRbus"

# Optional. Only effective if both are provided.
export NOTIFY_FROM="inform@tiker.net"
export NOTIFY_TO="inform@tiker.net"

poetry run flask --app=availability.app run --debug
