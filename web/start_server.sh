#!/bin/bash
# Start the local development server in the active Python environment.
set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
if ! python3 -c 'import flask, requests, dotenv' 2>/dev/null; then
    echo "Install Web dependencies first: python3 -m pip install -r requirements.txt"
    exit 1
fi
exec python3 app.py
