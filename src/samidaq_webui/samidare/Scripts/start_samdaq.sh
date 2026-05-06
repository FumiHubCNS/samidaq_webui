#!/usr/bin/env bash
set -euo pipefail

SESSION="${SAMDAQ_SESSION:-samdaq}"
SAMDAQ_DIR="${1:-/home/daq/samidare/SAM_DAQ}"

# cactus severの環境設定を消す
CLEAN_ENV="${SAMDAQ_CLEAN_ENV:-$SAMDAQ_DIR/../clean-env.sh}"

if [ ! -d "$SAMDAQ_DIR" ]; then
  echo "[ERROR] SAMDAQ_DIR does not exist: $SAMDAQ_DIR" >&2
  exit 1
fi

if [ ! -f "$CLEAN_ENV" ]; then
  echo "[ERROR] CLEAN_ENV does not exist: $CLEAN_ENV" >&2
  exit 1
fi

# 既存tmuxセッションがあれば終了
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "[INFO] Existing tmux session '$SESSION' found. Killing it..."
  tmux kill-session -t "$SESSION"
fi

# 念のため、samdaqプロセスが残っていれば終了
if pgrep -f "pixi run samdaq -b|samdaq -b|SAMDAQ -b" >/dev/null; then
  echo "[INFO] Existing SAMDAQ process found. Killing it..."
  pkill -f "pixi run samdaq -b|samdaq -b|SAMDAQ -b" || true
  sleep 1
fi

# まだ残っていたら強制終了
if pgrep -f "pixi run samdaq -b|samdaq -b|SAMDAQ -b" >/dev/null; then
  echo "[WARN] SAMDAQ process still alive. Force killing..."
  pkill -9 -f "pixi run samdaq -b|samdaq -b|SAMDAQ -b" || true
fi

# ログ設定。指定がなければ SAMDAQ_DIR に出す
LOG_FILE="${SAMDAQ_LOG_FILE:-$SAMDAQ_DIR/samdaq_tmux.log}"
: > "$LOG_FILE"

echo "[INFO] Starting SAMDAQ tmux session '$SESSION'..."
echo "[INFO] SAMDAQ_DIR: $SAMDAQ_DIR"
echo "[INFO] CLEAN_ENV: $CLEAN_ENV"

tmux new-session -d -s "$SESSION" \
  "bash -lc 'cd \"$SAMDAQ_DIR\" && source \"$CLEAN_ENV\" && pixi run samdaq -b'"

# tmux出力をログへ流す
tmux pipe-pane -t "$SESSION:0.0" "cat >> '$LOG_FILE'"

echo "[INFO] Started."
echo "[INFO] Session: $SESSION"
echo "[INFO] Log: $LOG_FILE"