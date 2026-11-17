#!/bin/bash
# Run the published Gunicorn configuration in the active Python environment.
set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
if ! python3 -c 'import flask, requests, dotenv, gunicorn' 2>/dev/null; then
    echo "Install Web dependencies first: python3 -m pip install -r requirements.txt"
    exit 1
fi
mkdir -p logs uploads outputs
if [ -f gunicorn.pid ] && kill -0 "$(cat gunicorn.pid)" 2>/dev/null; then
    echo "Gunicorn is already running; stop it before starting another instance."
    exit 1
fi
python3 -c 'import gunicorn_config as c; print(f"Gunicorn: {c.bind}, workers={c.workers}")'
exec python3 -m gunicorn -c gunicorn_config.py app:app
