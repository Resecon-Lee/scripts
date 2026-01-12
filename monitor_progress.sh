#!/bin/bash
#
# Monitor University Contact Finder Progress
# Shows live updates and statistics
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "University Contact Finder - Progress Monitor"
echo "============================================================"

# Check if process is running
if [ ! -f "logs/process.pid" ]; then
    echo "[ERROR] No process running (no PID file found)"
    echo "Start with: ./run_background.sh"
    exit 1
fi

PID=$(cat logs/process.pid)
if ! ps -p $PID > /dev/null 2>&1; then
    echo "[WARNING] Process not running (PID $PID not found)"
    echo "It may have completed or crashed. Check logs:"
    ls -lt logs/*.log | head -5
    exit 1
fi

# Find most recent log file
LATEST_LOG=$(ls -t logs/process_*.log 2>/dev/null | head -1)

if [ -z "$LATEST_LOG" ]; then
    echo "[ERROR] No log file found"
    exit 1
fi

echo ""
echo "[STATUS] Process is running (PID: $PID)"
echo "[LOG] Monitoring: $LATEST_LOG"
echo ""
echo "Press Ctrl+C to stop monitoring (process will continue running)"
echo "============================================================"
echo ""

# Function to show summary statistics
show_stats() {
    echo ""
    echo "--- Current Statistics ---"

    # Extract stats from log
    if [ -f "$LATEST_LOG" ]; then
        echo "Last 10 lines of log:"
        tail -10 "$LATEST_LOG"
        echo ""

        # Count completed universities
        COMPLETED=$(grep -c "\[FOUND\]" "$LATEST_LOG" || echo "0")
        ERRORS=$(grep -c "\[ERROR\]" "$LATEST_LOG" || echo "0")

        echo "Universities processed: $COMPLETED"
        echo "Errors encountered: $ERRORS"

        # Show progress from log
        PROGRESS=$(grep -oP '\[\d+/\d+\]' "$LATEST_LOG" | tail -1 || echo "")
        if [ ! -z "$PROGRESS" ]; then
            echo "Current progress: $PROGRESS"
        fi
    fi
    echo "--------------------------"
    echo ""
}

# Show initial stats
show_stats

# Tail the log file with auto-refresh
echo "Live log updates (refreshing every 2 seconds):"
echo "============================================================"

# Use tail -f with timeout to allow periodic stats updates
while true; do
    # Show last 20 lines
    tail -20 "$LATEST_LOG"

    # Check if process still running
    if ! ps -p $PID > /dev/null 2>&1; then
        echo ""
        echo "============================================================"
        echo "[COMPLETED] Process has finished!"
        echo "============================================================"
        show_stats

        # Show final results
        echo ""
        echo "Final log file: $LATEST_LOG"
        echo ""
        echo "Check output file:"
        echo "  data/universities_master_with_contacts_with_contacts.xlsx"
        echo ""
        break
    fi

    sleep 2
    clear
    echo "============================================================"
    echo "University Contact Finder - Progress Monitor"
    echo "============================================================"
    echo "[STATUS] Process running (PID: $PID)"
    echo "[LOG] $LATEST_LOG"
    echo "Press Ctrl+C to stop monitoring (process continues running)"
    echo "============================================================"
    echo ""
done
