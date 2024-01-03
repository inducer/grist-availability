#! /bin/bash

export GRIST_ROOT_URL="https://grist.tiker.net"
export GRIST_API_KEY_FILE="$HOME/.grist-api-key"
export GRIST_DOC_ID="isSNVL12chULhkfCZkRbus"

poetry run flask --app=availability.app run --debug
