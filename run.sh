#! /bin/bash

export GRIST_ROOT_URL="https://grist.tiker.net"
export GRIST_API_KEY_FILE="$HOME/.grist-api-key"
export GRIST_DOC_ID="rLJPGJ9RLJ4TRVx4AxT2tW"

poetry run flask --app=availability.app run --debug
