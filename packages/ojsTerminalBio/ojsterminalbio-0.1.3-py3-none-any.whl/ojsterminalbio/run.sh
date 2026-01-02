#!/bin/bash
# ojsTerminalBio - Run Server Script

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start server
echo "Starting ojsTerminalBio..."
echo "Access: http://localhost:7777"
echo "Press Ctrl+C to stop"
echo ""

ojsterminalbio runserver
