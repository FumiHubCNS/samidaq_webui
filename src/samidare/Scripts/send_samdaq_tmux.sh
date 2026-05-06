#!/usr/bin/env bash
set -euo pipefail

SESSION="${SAMDAQ_SESSION:-samdaq:0.0}"

# 実行した場所にログを出す
LOG_FILE="${SAMDAQ_LOG_FILE:-$PWD/samdaq_tmux.log}"

WAIT_TIMEOUT="${SAMDAQ_WAIT_TIMEOUT:-2}"
POLL_SEC="${SAMDAQ_POLL_SEC:-0.05}"

if [ "$#" -eq 0 ]; then
    echo "Usage: $0 <samdaq command> [args...]" >&2
    exit 1
fi

CMD="$*"
SESSION_NAME="${SESSION%%:*}"

if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "ERROR: tmux session '$SESSION_NAME' not found" >&2
    exit 2
fi

touch "$LOG_FILE"

# pipe-pane が張られていなければ、このスクリプト実行場所のログへ出力
PIPE_STATE="$(
    tmux list-panes \
        -t "$SESSION" \
        -F '#{pane_pipe}' \
        | head -n 1
)"

if [ "$PIPE_STATE" != "1" ]; then
    tmux pipe-pane -t "$SESSION" "cat >> '$LOG_FILE'"
fi

START_SIZE="$(stat -c%s "$LOG_FILE")"

# 入力途中の文字を消して送信
tmux send-keys -t "$SESSION" C-u
tmux send-keys -t "$SESSION" "$CMD" Enter

# ログが増えるまで待つ
elapsed="0"

while true; do
    END_SIZE="$(stat -c%s "$LOG_FILE")"

    if [ "$END_SIZE" -gt "$START_SIZE" ]; then
        break
    fi

    timeout_reached="$(
        awk \
            -v e="$elapsed" \
            -v t="$WAIT_TIMEOUT" \
            'BEGIN { print (e >= t) ? 1 : 0 }'
    )"

    if [ "$timeout_reached" = "1" ]; then
        exit 0
    fi

    sleep "$POLL_SEC"

    elapsed="$(
        awk \
            -v e="$elapsed" \
            -v p="$POLL_SEC" \
            'BEGIN { print e + p }'
    )"
done

# read 結果など、続きの行が入るのを少し待つ
sleep 0.2

END_SIZE="$(stat -c%s "$LOG_FILE")"
BYTES=$((END_SIZE - START_SIZE))

ESCAPED_CMD="$(
    printf '%s' "$CMD" \
        | sed 's/[.[\*^$()+?{}|]/\\&/g'
)"

# 今回増えたログだけ出す
tail -c "$BYTES" "$LOG_FILE" \
    | tr -d '\r' \
    | sed '/^[[:space:]]*$/d' \
    | sed 's/^SAM_DAQ> //' \
    | sed "/^${ESCAPED_CMD}$/d"