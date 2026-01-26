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
COMMENT="$(read_dat "${DATA_DIR}/comment.dat")"

OUTPUT_FILE="${OUT_DIR}/${FILE_NAME}_${RUN_NAME}_${RUN_NUMBER}.bin"
echo "${OUTPUT_FILE}" > "${DATA_DIR}/current_output_path.dat"


if [[ "$CLOCK_TYPE" == "external" ]]; then
    CLOCKFLAG=""
else
    CLOCKFLAG="#"
fi

LOG="/mnt/getdaq02-data/samidare/log/${RUN_NAME}_${RUN_NUMBER}.log"

# --- 3) samdaq 用スクリプトを書き出し
# ※ hh015.txt のコマンド形式はあなたの SAM_DAQ の仕様に合わせて書き換えてください。
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

# --- 4) pixi をバックグラウンド起動（新しいプロセスグループで起動）

echo "Start Time: $(date '+%Y-%m-%d %H:%M:%S %Z')" >> "${LOG}"
cd "${ROOT}"
source ./clean-env.sh
cd "${SAMDAQ_DIR}"

PIDFILE="${DATA_DIR}/samdaq.pgid"

setsid bash -lc 'pixi run samdaq --script "scripts/'"$(basename "${SCRIPT_OUT}")"'"' \
	  >> "${LOG}" 2>&1 &
SAMDAQ_PGID=$!

echo "${SAMDAQ_PGID}" > "${PIDFILE}"
echo "[run.sh] wrote PGID to ${PIDFILE}: ${SAMDAQ_PGID}"


exit 0
