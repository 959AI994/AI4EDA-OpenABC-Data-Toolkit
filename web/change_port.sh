#!/bin/bash
# Persist a Gunicorn port in ignored .env; restart explicitly when convenient.
set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
python3 - "$@" <<'PY'
import os
import sys
from pathlib import Path
from dotenv import dotenv_values, set_key
if len(sys.argv) != 2 or not sys.argv[1].isdigit() or not 1024 <= int(sys.argv[1]) <= 65535:
    raise SystemExit('Usage: ./change_port.sh <port 1024-65535>')
path = Path('.env')
existing = dotenv_values(path)
bind = existing.get('AI4EDA_BIND') or '127.0.0.1:8080'
host = bind.rpartition(':')[0]
if not host or bind.startswith('unix:'):
    raise SystemExit('Set AI4EDA_BIND manually for a non-TCP bind.')
set_key(str(path), 'AI4EDA_BIND', f'{host}:{int(sys.argv[1])}')
os.chmod(path, 0o600)
print('Updated .env. Restart Gunicorn to use the new port; exported AI4EDA_BIND takes precedence.')
PY
