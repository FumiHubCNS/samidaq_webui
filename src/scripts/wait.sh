#!/usr/bin/env bash
set -euo pipefail

FILE="status.txt"
TARGET="STOP"
INTERVAL=1

echo "Waiting for $FILE to become '$TARGET'..."

while true; do
    if [[ -f "$FILE" ]]; then
        value=$(<"$FILE")
        if [[ "$value" == "$TARGET" ]]; then
            echo "Detected target value: $TARGET"
            break
        fi
    fi
    sleep "$INTERVAL"
done
