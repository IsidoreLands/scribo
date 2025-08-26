#!/bin/bash
CONFIG_FILE="/tmp/sm_gpu_config.json"
ERROR_LOG="/tmp/sm_score_error.log"
LAST_CHECK_FILE="/tmp/sm_gpu_last_check.txt"

# Dependency checks
for cmd in jq date; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "$(date): Missing dependency: $cmd" >> "$ERROR_LOG"
        exit 1
    fi
done

# Check if last test was within 7 days
if [[ -f "$LAST_CHECK_FILE" ]]; then
    last_check=$(cat "$LAST_CHECK_FILE")
    current_time=$(date +%s)
    if [[ $((current_time - last_check)) -lt 604800 ]]; then
        exit 0
    fi
fi

# Test tools
gpu_tool="none"
for tool in "radeontop" "intel_gpu_top" "nvidia-smi"; do
    if [[ "$tool" == "nvidia-smi" ]]; then
        test_output=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader 2>&1)
        if [[ $? -eq 0 && $test_output =~ ^[0-9]+ ]]; then
            gpu_tool="nvidia-smi"
            break
        fi
    else
        test_output=$(sudo $tool -l 1 2>&1)
        if [[ $? -eq 0 && ($test_output == *"radeontop"* || $test_output == *"Render/3D"*) ]]; then
            gpu_tool=$tool
            break
        fi
    fi
done

# Update config if changed
old_tool=$(jq -r .gpu_tool "$CONFIG_FILE" 2>/dev/null || echo "none")
if [[ "$gpu_tool" != "$old_tool" ]]; then
    echo "{\"gpu_tool\": \"$gpu_tool\"}" > "$CONFIG_FILE"
    echo "$(date): GPU tool changed to $gpu_tool" >> "$ERROR_LOG"
fi

date +%s > "$LAST_CHECK_FILE"
