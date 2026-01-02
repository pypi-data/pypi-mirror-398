#!/bin/bash
set -euo pipefail

echo "[INFO] Starting application reload..."

run_cmd() {
    "$@"
}

REGION="{{region}}"
INSTANCE_ID="{{ec2_instance_id}}"

if [ -z "$REGION" ] || [ -z "$INSTANCE_ID" ]; then
    echo "[ERROR] region or ec2_instance_id is not set" >&2
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo "[ERROR] aws CLI is not installed" >&2
    exit 1
fi

echo "[INFO] Restarting EC2 instance..."
run_cmd aws ec2 reboot-instances --region "$REGION" --instance-ids "$INSTANCE_ID"

echo "[INFO] Reload complete."
