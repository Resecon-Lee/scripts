#!/bin/bash
#
# Check Status of University Contact Finder
# Quick status check without tailing logs
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "University Contact Finder - Status Check"
echo "============================================================"
echo ""

# Check if PID file exists
if [ ! -f "logs/process.pid" ]; then
    echo "[STATUS] Not running (no PID file)"
    echo ""
    echo "Recent log files:"
    ls -lth logs/process_*.log 2>/dev/null | head -5 || echo "  No logs found"
    echo ""
    echo "To start: ./run_background.sh"
    exit 0
fi

# Read PID
PID=$(cat logs/process.pid)

# Check if process is running
if ps -p $PID > /dev/null 2>&1; then
    echo "[STATUS] RUNNING"
    echo "  PID: $PID"

    # Get process info
    echo "  Started: $(ps -p $PID -o lstart= 2>/dev/null || echo 'Unknown')"
    echo "  CPU: $(ps -p $PID -o %cpu= 2>/dev/null || echo 'N/A')%"
    echo "  Memory: $(ps -p $PID -o %mem= 2>/dev/null || echo 'N/A')%"
    echo ""

    # Find latest log
    LATEST_LOG=$(ls -t logs/process_*.log 2>/dev/null | head -1)
    if [ ! -z "$LATEST_LOG" ]; then
        echo "Current log: $LATEST_LOG"
        echo "Log size: $(du -h "$LATEST_LOG" | cut -f1)"
        echo ""

        # Extract progress from log
        LAST_PROGRESS=$(grep -oP '\[\d+/\d+\]' "$LATEST_LOG" | tail -1 || echo "")
        if [ ! -z "$LAST_PROGRESS" ]; then
            echo "Progress: $LAST_PROGRESS"
        fi

        COMPLETED=$(grep -c "\[FOUND\]" "$LATEST_LOG" 2>/dev/null || echo "0")
        echo "Universities processed: $COMPLETED"

        echo ""
        echo "Last 5 log entries:"
        tail -5 "$LATEST_LOG"
    fi

    echo ""
    echo "Commands:"
    echo "  ./monitor_progress.sh  - Watch live progress"
    echo "  tail -f $LATEST_LOG - Follow log file"
    echo "  kill $PID             - Stop process"

else
    echo "[STATUS] NOT RUNNING"
    echo "  PID file exists but process $PID not found"
    echo "  Process may have completed or crashed"
    echo ""

    # Show last log
    LATEST_LOG=$(ls -t logs/process_*.log 2>/dev/null | head -1)
    if [ ! -z "$LATEST_LOG" ]; then
        echo "Last log file: $LATEST_LOG"
        echo "Last modified: $(ls -lh "$LATEST_LOG" | awk '{print $6, $7, $8}')"
        echo ""
        echo "Last 10 lines:"
        tail -10 "$LATEST_LOG"
        echo ""

        # Check if completed successfully
        if grep -q "PROCESSING SUMMARY" "$LATEST_LOG"; then
            echo "[INFO] Process appears to have completed successfully!"
        elif grep -q "\[ERROR\]" "$LATEST_LOG" | tail -1; then
            echo "[WARNING] Process may have ended with errors"
        fi
    fi

    # Clean up PID file
    rm logs/process.pid 2>/dev/null

    echo ""
    echo "To restart: ./run_background.sh"
fi

echo ""
echo "============================================================"
