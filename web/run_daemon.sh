#!/bin/bash
# AI4EDA Data Toolkit - Web Interface Daemon Script
# Usage: ./run_daemon.sh {start|stop|restart|status}

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PID_FILE="$SCRIPT_DIR/web_server.pid"
LOG_FILE="$SCRIPT_DIR/web_server.log"

start() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "Web server is already running (PID: $(cat "$PID_FILE"))"
        return 1
    fi

    echo "Starting AI4EDA Web Interface..."
    cd "$SCRIPT_DIR"

    # Check dependencies
    if ! python3 -c "import flask, requests, dotenv" 2>/dev/null; then
        echo "Installing dependencies..."
        python3 -m pip install -q -r requirements.txt
    fi

    # Start server in background
    nohup python3 app.py > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    sleep 2

    if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "✓ Web server started successfully (PID: $(cat "$PID_FILE"))"
        echo "✓ Access at: http://localhost:5000"
        echo "✓ Logs: $LOG_FILE"
        return 0
    else
        echo "✗ Failed to start web server"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "Web server is not running"
        return 1
    fi

    PID=$(cat "$PID_FILE")
    echo "Stopping web server (PID: $PID)..."

    if kill -0 $PID 2>/dev/null; then
        kill $PID
        sleep 2

        # Force kill if still running
        if kill -0 $PID 2>/dev/null; then
            kill -9 $PID
        fi

        rm -f "$PID_FILE"
        echo "✓ Web server stopped"
        return 0
    else
        echo "✗ Process not found"
        rm -f "$PID_FILE"
        return 1
    fi
}

status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 $PID 2>/dev/null; then
            echo "✓ Web server is running (PID: $PID)"
            echo "  Access at: http://localhost:5000"
            return 0
        else
            echo "✗ PID file exists but process is not running"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        echo "✗ Web server is not running"
        return 1
    fi
}

restart() {
    echo "Restarting web server..."
    stop
    sleep 1
    start
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit $?
