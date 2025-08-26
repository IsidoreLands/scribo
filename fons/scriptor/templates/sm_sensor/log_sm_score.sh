#!/bin/bash
# --- Configuration ---
LOG_FILE="$HOME/.sm_history.log"
STATUS_FILE="/tmp/sm_status.json"
TMP_FILE="/tmp/sm_history.log.tmp"
MAX_LINES=10080
SENSOR_SCRIPT="/home/isidore/system_maneuverability/get_sm_score.py"
ERROR_LOG="/tmp/sm_score_error.log"

# --- Create log file if it doesn't exist ---
touch "$LOG_FILE"
chmod 644 "$LOG_FILE"

# --- Get Current Score with Lock ---
(
    flock -w 5 9 || { echo "$(date): Lock failed after 5s, skipping" >> "$ERROR_LOG"; exit 1; }
    CURRENT_SCORE=$($SENSOR_SCRIPT 2>> "$ERROR_LOG")
    if [[ ! "$CURRENT_SCORE" =~ ^[0-9]+$ ]]; then
        echo "$(date): Invalid score from $SENSOR_SCRIPT: $CURRENT_SCORE" >> "$ERROR_LOG"
        EXTRACTED_SCORE=$(echo "$CURRENT_SCORE" | grep -oE '^[0-9]+$' || echo "0")
        CURRENT_SCORE=$EXTRACTED_SCORE
    fi
    TIMESTAMP=$(date +%s)
    echo "$TIMESTAMP,$CURRENT_SCORE" >> "$LOG_FILE"
    tail -n "$MAX_LINES" "$LOG_FILE" > "$TMP_FILE" 2>> "$ERROR_LOG"
    mv "$TMP_FILE" "$LOG_FILE" 2>> "$ERROR_LOG"
    if [[ -s "$LOG_FILE" ]]; then
        SUM=$(awk -F',' '{sum+=$2} END {print sum}' "$LOG_FILE" 2>> "$ERROR_LOG")
        COUNT=$(wc -l < "$LOG_FILE")
        if [[ "$COUNT" -gt 0 ]]; then
            AVERAGE_SCORE=$(echo "scale=0; $SUM / $COUNT" | bc 2>> "$ERROR_LOG")
        else
            AVERAGE_SCORE=0
            echo "$(date): Empty log file or count is zero" >> "$ERROR_LOG"
        fi
    else
        AVERAGE_SCORE=0
        echo "$(date): Log file is empty or missing" >> "$ERROR_LOG"
    fi
    echo "{\"current\": \"$CURRENT_SCORE\", \"average\": \"$AVERAGE_SCORE\"}" > "$STATUS_FILE"
    chmod 644 "$STATUS_FILE"
) 9>/tmp/sm_status.lock
