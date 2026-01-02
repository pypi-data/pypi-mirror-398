#!/usr/bin/env sh
# Issue/renew a Let's Encrypt certificate using the HTTP-01 challenge.
# This script expects DNS for the domain to resolve to the instance and port 80 to be reachable.
set -e

log() {
  echo "[ISSUE-CERT] $*"
}

die() {
  echo "[ISSUE-CERT][ERROR] $*" >&2
  exit 1
}

DOMAIN="{{primary_domain}}"
EMAIL="{{author_email}}"
SERVICE="{{container_name}}"

COMPOSE_FILE="/home/ec2-user/docker-compose.yml"

if [ ! -f "$COMPOSE_FILE" ]; then
  die "$COMPOSE_FILE not found. Run loader or copy the compose file first."
fi

if ! command -v docker >/dev/null 2>&1; then
  die "docker is not installed or not on PATH."
fi

if ! docker-compose version >/dev/null 2>&1; then
  die "docker-compose is not available."
fi

log "Starting nginx and application container..."
docker-compose -f "$COMPOSE_FILE" up -d nginx "$SERVICE"

log "Requesting certificate for $DOMAIN..."
docker-compose -f "$COMPOSE_FILE" run --rm certbot certonly --webroot \
  -w /var/www/certbot \
  -d "$DOMAIN" \
  --email "$EMAIL" \
  --agree-tos --no-eff-email --keep-until-expiring

HTTPS_DISABLED="/home/ec2-user/nginx/conf.d/10-https.conf.disabled"
HTTPS_ENABLED="/home/ec2-user/nginx/conf.d/10-https.conf"
if [ -f "$HTTPS_DISABLED" ]; then
  log "Enabling HTTPS nginx config..."
  mv "$HTTPS_DISABLED" "$HTTPS_ENABLED"
else
  die "Expected disabled HTTPS config not found at $HTTPS_DISABLED"
fi

log "Reloading nginx configuration..."
docker-compose -f "$COMPOSE_FILE" exec nginx nginx -s reload

if ! grep -q '"443:443"' "$COMPOSE_FILE"; then
  log "Enabling port 443 mapping in docker-compose.yml..."
  sed -i '/"80:80"/a\      - "443:443"' "$COMPOSE_FILE"
  docker-compose -f "$COMPOSE_FILE" up -d nginx
fi

log "Certificate issuance complete."
