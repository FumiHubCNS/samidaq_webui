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
SAMDAQ_DIR="$(get_conf SAMDAQ_DIR "$CONF_FILE")"
PIXI_SKIP="$(get_conf PIXI_SKIP "$CONF_FILE")"

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

LOG="${OUT_DIR}/../log/${RUN_NAME}_${RUN_NUMBER}.log"
RSLOG="${OUT_DIR}/../run_sammary.log"

########################################
### write script
########################################
cat > "${SCRIPT_OUT}" <<EOF
connect

refresh

power off

power on

refresh

trigger ${TRIG_TYPE}

trigger-threshold ${TRIG_VALUE}

output-dir ${OUT_DIR}

output-file ${FILE_NAME}_${RUN_NAME}_${RUN_NUMBER}

${CLOCKFLAG}external-clk on

polarity ${POLARITY}

#positive

gain ${GAIN}

samples ${NUM_SAMPLE}

pretrigger ${PRE_SAMPLE}

stat

start
sleep 3600
sleep 3600
sleep 3600
sleep 3600
sleep 3600
sleep 3600
sleep 3600
sleep 3600

stop

sleep 1

power off

disconnect

quit
# start
EOF

echo "[run.sh] Generated ${SCRIPT_OUT}"


########################################
### write log
########################################
START_TIME="$(date '+%Y-%m-%d_%H:%M:%S_%Z')"
echo "Start Time: ${START_TIME}" >> "${LOG}"
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
echo "${COMMENT}" >> "${LOG}"

########################################
### run summary
########################################
printf '%s %s %s %s %s %s %s %s %s %s %s %s %s %s ' \
"$START_TIME" "$RUN_NUMBER" "$RUN_NAME" "$TRIG_TYPE" \
"$OUT_DIR" "$FILE_NAME" "$POLARITY" "$GAIN" \
"$NUM_SAMPLE" "$PRE_SAMPLE" "$CLOCK_TYPE" \
"$TRIG_VALUE" "$COMMENT" "$LOG" >> "$RSLOG"

########################################
### run samfaq uing pixi with background
########################################
cd "${ROOT}"

if [[ "${PIXI_SKIP}" == "true" ]]; then
    echo "[run.sh] PIXI_SKIP is set to true"
    echo "[run.sh] PIXI_SKIP is set to true" >> "${LOG}" 2>&1 &
else
    source ./clean-env.sh
    cd "${SAMDAQ_DIR}"

    PIDFILE="${DATA_DIR}/samdaq.pgid"

    setsid bash -lc 'pixi run samdaq --script "scripts/'"$(basename "${SCRIPT_OUT}")"'"' \
        >> "${LOG}" 2>&1 &
    SAMDAQ_PGID=$!

    echo "${SAMDAQ_PGID}" > "${PIDFILE}"
    echo "[run.sh] wrote PGID to ${PIDFILE}: ${SAMDAQ_PGID}"
fi

exit 0
