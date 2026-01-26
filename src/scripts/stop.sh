#!/usr/bin/env bash
set -euo pipefail

########################################
### load input paths
########################################
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

CONF_FILE="${SCRIPT_DIR}/../../paths.conf"

get_conf() {
  local key="$1"
  local file="$2"
  local val
  val="$(grep -E "^${key}=" "$file" | tail -n 1 | cut -d= -f2-)"
  if [[ -z "${val}" ]]; then
    echo "ERROR: ${key} not found in ${file}" >&2
    exit 1
  fi
  printf '%s' "$val"
}

ROOT="$(get_conf ROOT "$CONF_FILE")"
WEBCTL_DIR="$(get_conf WEBCTL_DIR "$CONF_FILE")"

SAMDAQ_DIR="${ROOT}/SAM_DAQ"
DATA_DIR="${WEBCTL_DIR}/data"
SCRIPT_OUT="${SAMDAQ_DIR}/scripts/hh015.txt"
WAIT_SH="${WEBCTL_DIR}/scripts/wait.sh"

read_dat() {
  local f="$1"
  [[ -f "$f" ]] || { echo "Missing file: $f" >&2; exit 1; }
  tr -d '\r\n' < "$f"
}

########################################
### load samidare setting
########################################
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
COMMENT="$(read_dat "${DATA_DIR}/comment.dat")"

OUTPUT_FILE="${OUT_DIR}/${FILE_NAME}_${RUN_NAME}_${RUN_NUMBER}.bin"
echo "${OUTPUT_FILE}" > "${DATA_DIR}/current_output_path.dat"

if [[ "$CLOCK_TYPE" == "external" ]]; then
    CLOCKFLAG=""
else
    CLOCKFLAG="#"
fi

LOG="/mnt/getdaq02-data/samidare/log/dump.log"
RSLOG="${OUT_DIR}/samidare/run_sammary.log"

########################################
### kill samdaq using PID
########################################
echo "[stop.sh] wait finished, stopping samdaq..."

PIDFILE="/home/daq/Work/daqui/src/data/samdaq.pgid"
[[ -f "$PIDFILE" ]] || { echo "no pidfile: $PIDFILE"; exit 0; }

PGID="$(tr -d '\r\n' < "$PIDFILE")"
[[ -n "$PGID" ]] || { echo "empty pgid"; exit 0; }

echo "killing PGID=$PGID"
kill -TERM -"${PGID}" 2>/dev/null || true
sleep 1
kill -KILL -"${PGID}" 2>/dev/null || true

########################################
### write log
########################################
echo "Stop Time: $(date '+%Y-%m-%d %H:%M:%S %Z')" >> "${LOG}"
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

########################################
### run summary
########################################
echo "${RUN_NUMBER} ${RUN_NAME} ${TRIG_TYPE} \
${OUT_DIR} ${FILE_NAME} ${POLARITY} ${GAIN} \
${NUM_SAMPLE} ${PRE_SAMPLE} ${CLOCK_TYPE} ${LOG}" >> "${RSLOG}"

echo "[stop.sh] finished"
