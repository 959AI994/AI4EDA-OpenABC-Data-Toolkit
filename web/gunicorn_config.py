# Gunicorn Configuration for AI4EDA Web Interface

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name('.env'))

# Server Socket
bind = os.getenv("AI4EDA_BIND", "127.0.0.1:8080")
backlog = 2048

# Worker Processes
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 180
keepalive = 5

# Logging
Path("logs").mkdir(exist_ok=True)
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Process Naming
proc_name = "ai4eda_web"

# Server Mechanics
daemon = False
pidfile = "gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (uncomment if using HTTPS directly)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
