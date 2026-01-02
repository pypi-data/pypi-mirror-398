#!/bin/bash
set -euo pipefail

echo "[INFO] Starting application deploy..."

run_cmd() {
    "$@"
}


BUILD_SCRIPT="appBuild.sh"
PUSH_SCRIPT="./appPush.sh"
LOAD_SCRIPT="./appLoad.sh"

if [ ! -f "$BUILD_SCRIPT" ] || [ ! -f "$PUSH_SCRIPT" ] || [ ! -f "$LOAD_SCRIPT" ]; then
    echo "[ERROR] One or more deploy scripts are missing in $SCRIPT_DIR" >&2
    exit 1
fi

run_cmd "$BUILD_SCRIPT"
run_cmd "$PUSH_SCRIPT"
run_cmd "$LOAD_SCRIPT"

echo "[INFO] Deploy complete."
