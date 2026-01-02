#!/bin/bash
set -euo pipefail

echo "[INFO] Starting application build..."

run_cmd() {
    "$@"
}

if ! command -v docker &> /dev/null; then
    echo "[ERROR] docker is not installed" >&2
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "[ERROR] docker-compose is not installed" >&2
    exit 1
fi

COMPOSE_FILE="docker-compose.yaml"
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "[ERROR] $COMPOSE_FILE not found in the current directory. Checking to see .yml" >&2
    COMPOSE_FILE="docker-compose.yml"
    if [ ! -f "$COMPOSE_FILE" ]; then
        echo "[ERROR] $COMPOSE_FILE not found in the current directory." >&2
        exit 1
    fi
fi

echo "[INFO] Authenticating to ECR..."
run_cmd aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY"


BUILD_PLATFORMS="linux/amd64,linux/arm64"
echo "[INFO] Building multi-arch Docker images..."
run_cmd docker buildx bake -f "$COMPOSE_FILE" --set "*.platform=$BUILD_PLATFORMS" --push

echo "[INFO] Build and Push complete."

echo "[INFO] Uploading docker-compose.yml to deployment bucket..."
run_cmd aws s3 cp "$COMPOSE_FILE" "s3://$DEPLOYMENT_BUCKET/$PROJECT_NAME/compose/docker-compose.yml"

echo "[INFO] Push complete."
