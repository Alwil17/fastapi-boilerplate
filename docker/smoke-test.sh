#!/bin/sh
# Boot the image against a throwaway Postgres and check it end to end:
# migrations applied, container healthy, /health/ready OK, not running as root.
# Usage: docker/smoke-test.sh [image]   (default: fastapi-boilerplate:latest)
set -eu

IMAGE="${1:-fastapi-boilerplate:latest}"
SUFFIX="$$"
NETWORK="smoke-net-$SUFFIX"
DB="smoke-db-$SUFFIX"
API="smoke-api-$SUFFIX"
PORT="${SMOKE_PORT:-18080}"

cleanup() {
    docker logs "$API" 2>&1 | tail -n 40 || true
    docker rm -f "$API" "$DB" >/dev/null 2>&1 || true
    docker network rm "$NETWORK" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker network create "$NETWORK" >/dev/null
docker run -d --name "$DB" --network "$NETWORK" \
    -e POSTGRES_DB=app -e POSTGRES_USER=app -e POSTGRES_PASSWORD=smoke-password-1 \
    postgres:16-alpine >/dev/null

# Production settings: also proves the app boots with a valid production config.
docker run -d --name "$API" --network "$NETWORK" -p "$PORT:8000" \
    -e APP_ENV=production \
    -e APP_SECRET_KEY="smoke-test-secret-key-0123456789-abcdefghij" \
    -e DB_HOST="$DB" -e DB_NAME=app -e DB_USER=app \
    -e DB_PASSWORD=smoke-password-1 -e DB_SSLMODE=disable \
    -e CORS_ORIGINS=https://app.example.com \
    "$IMAGE" >/dev/null

echo "waiting for the container to become healthy..."
i=0
until [ "$(docker inspect -f '{{.State.Health.Status}}' "$API")" = "healthy" ]; do
    i=$((i + 1))
    if [ "$i" -gt 60 ]; then
        echo "container never became healthy" >&2
        exit 1
    fi
    sleep 2
done

curl -fsS "http://127.0.0.1:$PORT/health/ready" | grep -q '"ready"'
echo "ready: ok"

uid="$(docker exec "$API" id -u)"
if [ "$uid" = "0" ]; then
    echo "container runs as root" >&2
    exit 1
fi
echo "user: uid $uid (non-root)"

trap - EXIT
cleanup >/dev/null
echo "smoke test passed"
