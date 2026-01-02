#!/bin/bash

# Bootstrap steps:
# 1) Install Docker and enable the daemon.
# 2) Install Docker Compose.
# 3) Download loader.sh from S3 to /tmp and make it executable.
# 4) Download the systemd unit from S3 and substitute the loader path.
# 5) Reload systemd, enable, and start the loader service.

# Function to run a command and log errors but continue
run_cmd() {
    "$@"
    local status=$?
    if [ $status -ne 0 ]; then
        echo "[SETUP][ERROR] Command failed: $* (exit code $status)" >&2
    fi
    return $status
}

echo "[SETUP] Starting EC2 instance setup..."

# Prepare nginx/certbot directories and config.
echo "[SETUP] Preparing nginx and certbot directories..."
run_cmd mkdir -p /home/ec2-user/nginx/conf.d
run_cmd mkdir -p /home/ec2-user/certbot/www
run_cmd mkdir -p /home/ec2-user/certbot/conf

# Download nginx assets from S3.
echo "[SETUP] Downloading nginx assets..."
run_cmd aws s3 sync s3://{{deployment_bucket}}/{{project_name}}/nginx/conf.d/ /home/ec2-user/nginx/conf.d/
run_cmd aws s3 cp s3://{{deployment_bucket}}/{{project_name}}/nginx/issue-cert.sh /home/ec2-user/nginx/issue-cert.sh
run_cmd chmod +x /home/ec2-user/nginx/issue-cert.sh

# Install Docker if not already installed.
if ! command -v docker &> /dev/null; then
    echo "[SETUP] Installing Docker..."
    run_cmd yum update -y
    run_cmd yum install -y docker
    run_cmd systemctl start docker
    run_cmd systemctl enable docker
    run_cmd usermod -aG docker ec2-user
else
    echo "[SETUP] Docker already installed"
fi

# Install Docker Compose if not already installed.
if ! command -v docker-compose &> /dev/null; then
    echo "[SETUP] Installing Docker Compose..."
    run_cmd curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    run_cmd chmod +x /usr/local/bin/docker-compose
else
    echo "[SETUP] Docker Compose already installed"
fi

# Download loader.sh from S3.
echo "[SETUP] Downloading loader.sh..."
run_cmd aws s3 cp s3://{{deployment_bucket}}/{{project_name}}/loader/loader.sh /tmp/loader.sh
run_cmd chmod +x /tmp/loader.sh

# Setup loader.sh to run as a systemd service on boot.
SERVICE_FILE="/etc/systemd/system/awsec2-app.service"

echo "[SETUP] Creating systemd service for setup script..."
# Get systemd service template.
run_cmd aws s3 cp s3://{{deployment_bucket}}/{{project_name}}/systemd/awsec2-app.service $SERVICE_FILE
run_cmd sed -i "s|{{setup_script_path}}|/tmp/loader.sh|g" $SERVICE_FILE
run_cmd sudo systemctl daemon-reload
run_cmd sudo systemctl enable --now awsec2-app.service


# Ensure ec2-user owns its home directory contents.
run_cmd chown -R ec2-user:ec2-user /home/ec2-user/

echo "[SETUP] Setup complete! Loader service is installed and running."
