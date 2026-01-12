#!/bin/bash
#
# Run University Contact Finder in Background
# Uses nohup and screen to allow monitoring and detaching
#

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "Starting University Contact Finder in Background"
echo "============================================================"

# Check if already running
if [ -f "logs/process.pid" ]; then
    PID=$(cat logs/process.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "[ERROR] Process already running with PID: $PID"
        echo "Use './check_status.sh' to check status"
        echo "Use 'kill $PID' to stop it first"
        exit 1
    else
        echo "[INFO] Removing stale PID file"
        rm logs/process.pid
    fi
fi

# Create logs directory
mkdir -p logs

# Get configuration from user
echo ""
echo "Configuration:"
echo "1. Test (10 universities)"
echo "2. Small batch (100 universities)"
echo "3. Medium batch (500 universities)"
echo "4. Large batch (1000 universities)"
echo "5. All remaining universities (~5,877)"
echo "6. Custom number"
echo ""
read -p "Select option [1-6]: " OPTION

case $OPTION in
    1)
        MAX_UNIS=10
        MODE="test"
        ;;
    2)
        MAX_UNIS=100
        MODE="small"
        ;;
    3)
        MAX_UNIS=500
        MODE="medium"
        ;;
    4)
        MAX_UNIS=1000
        MODE="large"
        ;;
    5)
        MAX_UNIS=""
        MODE="all"
        ;;
    6)
        read -p "Enter number of universities: " MAX_UNIS
        MODE="custom"
        ;;
    *)
        echo "[ERROR] Invalid option"
        exit 1
        ;;
esac

# Build command
CMD="source venv/bin/activate && cd scripts && python process_universities.py \
    --input ../data/universities_master_with_contacts.xlsx \
    --skip-existing \
    --no-confirm"

if [ ! -z "$MAX_UNIS" ]; then
    CMD="$CMD --max $MAX_UNIS"
else
    CMD="$CMD --all"
fi

# Create output log filename with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="logs/process_${MODE}_${TIMESTAMP}.log"
PID_FILE="logs/process.pid"

echo ""
echo "[INFO] Configuration:"
if [ -z "$MAX_UNIS" ]; then
    echo "  Mode: Process ALL remaining universities"
else
    echo "  Mode: Process $MAX_UNIS universities"
fi
echo "  Log file: $LOG_FILE"
echo "  PID file: $PID_FILE"
echo ""
echo "[STARTING] Process starting in background..."
echo "  You can close this terminal - process will continue running"
echo ""

# Run in background with nohup
nohup bash -c "$CMD" > "$LOG_FILE" 2>&1 &
PROCESS_PID=$!

# Save PID
echo $PROCESS_PID > "$PID_FILE"

echo "[SUCCESS] Process started!"
echo "  PID: $PROCESS_PID"
echo "  Log: $LOG_FILE"
echo ""
echo "Monitor with:"
echo "  ./monitor_progress.sh      - Live log tail"
echo "  ./check_status.sh          - Check if running"
echo "  tail -f $LOG_FILE          - Watch full log"
echo ""
echo "Stop with:"
echo "  kill $PROCESS_PID"
echo ""
