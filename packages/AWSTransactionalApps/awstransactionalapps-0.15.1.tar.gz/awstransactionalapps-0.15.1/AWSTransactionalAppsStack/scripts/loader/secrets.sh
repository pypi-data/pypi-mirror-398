#!/bin/bash
echo "[INFO] Starting secrets loader..."

# Function to run a command and log errors but continue
run_cmd() {
    "$@"
    local status=$?
    if [ $status -ne 0 ]; then
        echo "[ERROR] Command failed: $* (exit code $status)" >&2
    fi
    return $status
}


PROJECT_NAME="{{project_name}}"
SECRET_NAME="{{secret_name}}"
ENV_PATH="/home/ec2-user/.env"

if ! command -v aws &> /dev/null; then
    echo "[ERROR] aws CLI is not installed" >&2
fi

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 is not installed" >&2
fi

REGION="{{region}}"
if [ -z "$REGION" ]; then
    echo "[ERROR] Unable to determine AWS" >&2
fi

SECRET_JSON=$(aws secretsmanager get-secret-value \
    --secret-id "$SECRET_NAME" \
    --region "$REGION" \
    --query SecretString \
    --output text)

if [ -z "$SECRET_JSON" ] || [ "$SECRET_JSON" = "None" ]; then
    echo "[ERROR] Secret $SECRET_NAME has no SecretString" >&2
fi

run_cmd install -o ec2-user -g ec2-user -m 600 /dev/null "$ENV_PATH"

python3 - "$ENV_PATH" "$SECRET_JSON" <<'PY'
import json
import sys

env_path = sys.argv[1]
secret_raw = sys.argv[2]

try:
    data = json.loads(secret_raw)
except json.JSONDecodeError as exc:
    raise SystemExit(f"[ERROR] SecretString is not valid JSON: {exc}")

if not isinstance(data, dict):
    raise SystemExit("[ERROR] SecretString must be a JSON object of key/value pairs")

def _escape_value(value: str) -> str:
    value = value.replace("\\", "\\\\")
    value = value.replace("\"", "\\\"")
    value = value.replace("\n", "\\n")
    return value

with open(env_path, "w", encoding="utf-8") as handle:
    for key, value in data.items():
        if value is None:
            value = ""
        value = _escape_value(str(value))
        handle.write(f'{key}="{value}"\n')
PY

run_cmd chown ec2-user:ec2-user "$ENV_PATH"
run_cmd chmod 600 "$ENV_PATH"
echo "[INFO] Wrote secrets to $ENV_PATH"
