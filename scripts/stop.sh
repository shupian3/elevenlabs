#!/bin/bash
# Stop the ElevenLabs OpenAI Proxy Server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_DIR/.server.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "No PID file found. Server may not be running."
    # Try to kill any running server.py processes anyway
    pkill -f "python server.py" && echo "✓ Stopped orphaned server process" || echo "No server process found"
    exit 0
fi

PID=$(cat "$PID_FILE")

if ps -p "$PID" > /dev/null 2>&1; then
    echo "Stopping server (PID: $PID)..."
    kill "$PID"

    # Wait for graceful shutdown
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            echo "✓ Server stopped successfully"
            rm -f "$PID_FILE"
            exit 0
        fi
        sleep 0.5
    done

    # Force kill if still running
    echo "Force killing server..."
    kill -9 "$PID" 2>/dev/null || true
    echo "✓ Server stopped (forced)"
else
    echo "Server not running (stale PID file)"
fi

rm -f "$PID_FILE"
