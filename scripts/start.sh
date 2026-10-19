#!/bin/bash
# Start the ElevenLabs OpenAI Proxy Server

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_DIR/.server.pid"
LOG_FILE="$PROJECT_DIR/server.log"

# Load environment variables from .env if it exists
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
fi

# Check if server is already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Server is already running (PID: $PID)"
        echo "Use 'make stop' to stop it first"
        exit 1
    fi
    rm -f "$PID_FILE"
fi

# Activate virtual environment
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "Error: Virtual environment not found. Run 'make install' first."
    exit 1
fi

source "$PROJECT_DIR/venv/bin/activate"

# Start server in background
echo "Starting ElevenLabs OpenAI Proxy Server..."
cd "$PROJECT_DIR"
nohup python server.py > "$LOG_FILE" 2>&1 &
SERVER_PID=$!

# Save PID
echo $SERVER_PID > "$PID_FILE"

# Wait a moment and check if it started successfully
sleep 2
if ps -p $SERVER_PID > /dev/null 2>&1; then
    PORT=${PORT:-8000}
    echo "✓ Server started successfully (PID: $SERVER_PID)"
    echo "✓ Listening on http://localhost:$PORT"
    echo "✓ API docs: http://localhost:$PORT/docs"
    echo "✓ Logs: tail -f $LOG_FILE"
else
    echo "✗ Server failed to start. Check $LOG_FILE for details"
    rm -f "$PID_FILE"
    exit 1
fi
