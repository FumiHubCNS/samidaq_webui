#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/daq/samidare"
SAMDAQ_DIR="${ROOT}/SAM_DAQ"
WEBCTL_DIR="/home/daq/Work/daqui/src"
DATA_DIR="${WEBCTL_DIR}/data"          # send.sh の ../data が SAM_DAQ/data の想定
SCRIPT_OUT="${SAMDAQ_DIR}/scripts/hh015.txt"
WAIT_SH="${WEBCTL_DIR}/scripts/wait.sh"              # status.sh でもOK。実体のパスに合わせて下さい

# --- 1) send.sh 実行（.dat を更新）
#bash "${WEBCTL_DIR}/scripts/send.sh"

# --- 2) .dat を読み込み（改行除去して変数化）
read_dat() {
  local f="$1"
  [[ -f "$f" ]] || { echo "Missing file: $f" >&2; exit 1; }
  tr -d '\r\n' < "$f"
}

RUN_NUMBER="$(read_dat "${DATA_DIR}/run_number.dat")"
RUN_NAME="$(read_dat "${DATA_DIR}/run_name.dat")"
TRIG_TYPE="$(read_dat "${DATA_DIR}/trig_type.dat")"
OUT_DIR="$(read_dat "${DATA_DIR}/output_dir.dat")"
FILE_NAME="$(read_dat "${DATA_DIR}/file_name.dat")"
POLARITY="$(read_dat "${DATA_DIR}/polarity.dat")"
GAIN="$(read_dat "${DATA_DIR}/gain.dat")"
NUM_SAMPLE="$(read_dat "${DATA_DIR}/num_sample.dat")"
PRE_SAMPLE="$(read_dat "${DATA_DIR}/pre_sample.dat")"
CLOCK_TYPE="$(read_dat "${DATA_DIR}/clock_type.dat")"
TRIG_VALUE="$(read_dat "${DATA_DIR}/trig_value.dat")"

if [[ "$CLOCK_TYPE" == "external" ]]; then
    CLOCKFLAG=""
else
    CLOCKFLAG="#"
fi

LOG="/mnt/getdaq02-data/samidare/log/dump.log"
RSLOG="/mnt/getdaq02-data/samidare/run_sammary.log"

echo "[stop.sh] wait finished, stopping samdaq..."

PIDFILE="/home/daq/Work/daqui/src/data/samdaq.pgid"
[[ -f "$PIDFILE" ]] || { echo "no pidfile: $PIDFILE"; exit 0; }

PGID="$(tr -d '\r\n' < "$PIDFILE")"
[[ -n "$PGID" ]] || { echo "empty pgid"; exit 0; }

echo "killing PGID=$PGID"
kill -TERM -"${PGID}" 2>/dev/null || true
sleep 1
kill -KILL -"${PGID}" 2>/dev/null || true

echo "Stop Time: $(date '+%Y-%m-%d %H:%M:%S %Z')" >> "${LOG}"

# Log
echo "${RUN_NUMBER}" >> "${LOG}"
echo "${RUN_NAME}" >> "${LOG}"
echo "${TRIG_TYPE}" >> "${LOG}"
echo "${OUT_DIR}" >> "${LOG}"
echo "${FILE_NAME}" >> "${LOG}"
echo "${POLARITY}" >> "${LOG}"
echo "${GAIN}" >> "${LOG}"
echo "${NUM_SAMPLE}" >> "${LOG}"
echo "${PRE_SAMPLE}" >> "${LOG}"
echo "${CLOCK_TYPE}" >> "${LOG}"
echo "${TRIG_VALUE}" >> "${LOG}"

# Run Summary
echo "${RUN_NUMBER} ${RUN_NAME} ${TRIG_TYPE} \
${OUT_DIR} ${FILE_NAME} ${POLARITY} ${GAIN} \
${NUM_SAMPLE} ${PRE_SAMPLE} ${CLOCK_TYPE} ${LOG}" >> "${RSLOG}"

#cd "${ROOT}"
#source ./clean-env.sh
#cd "${SAMDAQ_DIR}"
#PIDFILE="${DATA_DIR}/samdaq.pgid"
#setsid bash -lc 'pixi run samdaq --script "scripts/clear.txt"'
echo "[stop.sh] finished"
