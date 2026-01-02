#!/usr/bin/env sh
set -e

DOMAIN="helloworld.devops.buzzerboysites.com"
EMAIL="info@buzzerboy.com"

# Run from the repo root so docker compose can find docker-compose.yml
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(dirname -- "$SCRIPT_DIR")
cd "$REPO_ROOT"

docker compose up -d nginx hello-world

docker compose run --rm certbot certonly --webroot \
  -w /var/www/certbot \
  -d "$DOMAIN" \
  --email "$EMAIL" \
  --agree-tos --no-eff-email

docker compose exec nginx nginx -s reload
