#!/usr/bin/env bash
set -euo pipefail

MODE="${SAMDAQ_EXEC_MODE:-host}"

HOST_SCRIPT="${SAMDAQ_HOST_SCRIPT:-scripts/send_samdaq_tmux.sh}"
CONTAINER_SCRIPT="${SAMDAQ_CONTAINER_SCRIPT:-/work/scripts/send_samdaq_tmux.sh}"

DOCKER_CONTAINER="${SAMDAQ_DOCKER_CONTAINER:-}"
APPTAINER_IMAGE="${SAMDAQ_APPTAINER_IMAGE:-}"

SESSION="${SAMDAQ_SESSION:-samdaq:0.0}"
LOG_FILE="${SAMDAQ_LOG_FILE:-$PWD/samdaq_tmux.log}"
WAIT_TIMEOUT="${SAMDAQ_WAIT_TIMEOUT:-2}"
POLL_SEC="${SAMDAQ_POLL_SEC:-0.05}"

if [ "$#" -eq 0 ]; then
    echo "Usage: $0 <samdaq command> [args...]" >&2
    exit 1
fi

CMD=( "$@" )

case "$MODE" in
    host)
        exec "$HOST_SCRIPT" "${CMD[@]}"
        ;;

    docker)
        if [ -z "$DOCKER_CONTAINER" ]; then
            echo "ERROR: SAMDAQ_DOCKER_CONTAINER is not set" >&2
            exit 10
        fi

        exec docker exec \
            -e SAMDAQ_SESSION="$SESSION" \
            -e SAMDAQ_LOG_FILE="$LOG_FILE" \
            -e SAMDAQ_WAIT_TIMEOUT="$WAIT_TIMEOUT" \
            -e SAMDAQ_POLL_SEC="$POLL_SEC" \
            "$DOCKER_CONTAINER" \
            "$CONTAINER_SCRIPT" "${CMD[@]}"
        ;;

    apptainer|singularity)
        if [ -z "$APPTAINER_IMAGE" ]; then
            echo "ERROR: SAMDAQ_APPTAINER_IMAGE is not set" >&2
            exit 11
        fi

        exec apptainer exec \
            --env SAMDAQ_SESSION="$SESSION" \
            --env SAMDAQ_LOG_FILE="$LOG_FILE" \
            --env SAMDAQ_WAIT_TIMEOUT="$WAIT_TIMEOUT" \
            --env SAMDAQ_POLL_SEC="$POLL_SEC" \
            "$APPTAINER_IMAGE" \
            "$CONTAINER_SCRIPT" "${CMD[@]}"
        ;;

    *)
        echo "ERROR: unknown SAMDAQ_EXEC_MODE '$MODE'" >&2
        echo "Use one of: host, docker, apptainer" >&2
        exit 12
        ;;
esac