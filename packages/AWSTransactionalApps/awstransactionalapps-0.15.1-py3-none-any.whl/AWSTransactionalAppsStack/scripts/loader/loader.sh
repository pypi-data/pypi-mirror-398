#!/bin/bash
echo "[INFO] Starting application loader..."

# Function to run a command and log errors but continue
run_cmd() {
    "$@"
    local status=$?
    if [ $status -ne 0 ]; then
        echo "[ERROR] Command failed: $* (exit code $status)" >&2
    fi
    return $status
}

# Assumptions:
# - docker and docker-compose are installed and available on PATH.
# - aws CLI is installed and configured for access to the deployment bucket and ECR.
# - deployment_bucket and project_name placeholders are templated or set by the environment.

# Step 3: Load prerequisites and project name
DEPLOYMENT_BUCKET="{{deployment_bucket}}"
PROJECT_NAME="{{project_name}}"

if [ -z "$DEPLOYMENT_BUCKET" ] || [ -z "$PROJECT_NAME" ]; then
    echo "[ERROR] deployment_bucket or project_name is not set" >&2
fi

if ! command -v aws &> /dev/null; then
    echo "[ERROR] aws CLI is not installed" >&2
fi

if ! command -v docker-compose &> /dev/null; then
    echo "[ERROR] docker-compose is not installed" >&2
fi

# Step 4: Self update loader.sh and rerun if a newer version exists
echo "[INFO] Checking for loader.sh updates..."
if run_cmd aws s3 cp s3://{{deployment_bucket}}/{{project_name}}/loader/loader.sh /tmp/loader.sh; then
    run_cmd chmod +x /tmp/loader.sh
    if [ -z "$LOADER_SELF_UPDATED" ] && ! cmp -s /tmp/loader.sh "$0"; then
        echo "[INFO] New loader.sh found; re-running latest version..."
        exec env LOADER_SELF_UPDATED=1 /tmp/loader.sh "$@"
    fi
fi

# Step 5: Get region from instance metadata
REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region)
echo "[INFO] Region: $REGION"

# Step 6: Get the latest docker-compose.yml from the deployment bucket
echo "[INFO] Downloading docker-compose.yml..."
run_cmd aws s3 cp s3://{{deployment_bucket}}/{{project_name}}/compose/docker-compose.yml /home/ec2-user/docker-compose.yml

# Step 6.0: Download and run secrets loader
echo "[INFO] Downloading secrets loader..."
run_cmd aws s3 cp s3://{{deployment_bucket}}/{{project_name}}/loader/secrets.sh /home/ec2-user/secrets.sh
run_cmd chmod +x /home/ec2-user/secrets.sh
echo "[INFO] Running secrets loader..."
run_cmd /home/ec2-user/secrets.sh

# Step 6.1: Sync nginx assets from the deployment bucket
echo "[INFO] Syncing nginx assets..."
run_cmd mkdir -p /home/ec2-user/nginx/conf.d
run_cmd aws s3 sync s3://{{deployment_bucket}}/{{project_name}}/nginx/conf.d/ /home/ec2-user/nginx/conf.d/
run_cmd aws s3 cp s3://{{deployment_bucket}}/{{project_name}}/nginx/issue-cert.sh /home/ec2-user/nginx/issue-cert.sh
run_cmd chmod +x /home/ec2-user/nginx/issue-cert.sh

# Step 7: ECR authenticate
run_cmd aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin {{ecr_registry}}

# Step 8: Docker compose pull
echo "[INFO] Pulling Docker image..."
run_cmd cd /home/ec2-user
run_cmd docker-compose pull

# Step 9: Docker compose up
echo "[INFO] Starting application..."
run_cmd docker-compose up -d

echo "[INFO] Setup complete! Application is running."
