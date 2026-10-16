# Runbook

How to operate the service. Commands assume the compose stack; with plain `docker` or
Kubernetes, run the same commands inside the `api` container.

## Quick reference

| What | Where |
| --- | --- |
| Is the process up? | `GET /health/live` |
| Can it serve traffic (DB reachable)? | `GET /health/ready` (503 when not) |
| Logs | stdout, JSON, one object per line (`LOG_FORMAT=json`) |
| Metrics | `GET /metrics` when `PROMETHEUS_ENABLED=true` (Bearer `METRICS_TOKEN` if set) |
| Errors | Sentry when `SENTRY_DSN` is set |
| Request id | `X-Request-ID` response header, `request_id` in every log line and error body |

## Deploy

```bash
git pull
docker compose -f docker-compose.yml up -d --build
docker compose -f docker-compose.yml ps        # api must become "healthy"
```

On start the entrypoint runs `alembic upgrade head` (retrying while the database comes
up), then gunicorn. The old container gets SIGTERM and has `GUNICORN_GRACEFUL_TIMEOUT`
(30 s) to finish in-flight requests; `stop_grace_period` is 40 s.

Released images come from GHCR (`ghcr.io/<owner>/<repo>:X.Y.Z`), published when a tag
`vX.Y.Z` matching `app.__version__` is pushed. To run one instead of building on the host,
pull it, give it the name the compose file expects, and skip the build:

```bash
docker pull ghcr.io/<owner>/<repo>:X.Y.Z
docker tag ghcr.io/<owner>/<repo>:X.Y.Z fastapi-boilerplate:X.Y.Z
IMAGE_TAG=X.Y.Z docker compose -f docker-compose.yml up -d --no-build
```

**Several replicas:** set `RUN_MIGRATIONS=false` on them and run the migration once
before rolling out, otherwise replicas can race:

```bash
docker compose -f docker-compose.yml run --rm -e RUN_MIGRATIONS=true api alembic upgrade head
```

## Roll back

1. Redeploy the previous image tag (`IMAGE_TAG=<previous>`, as above).
2. If the release added a migration the old code cannot run against, downgrade first,
   using the **new** image (it knows the migration):

   ```bash
   docker compose -f docker-compose.yml run --rm api alembic downgrade -1
   ```

   Downgrades can drop columns and data. Take a backup first (see below).

## Trace a request

A client reporting a failure gives the `request_id` (from the `X-Request-ID` header or the
`error.request_id` field of the error body).

```bash
docker compose logs api | grep '"request_id": "<id>"'
```

The access line has `method`, `path` (no query string), `status`, `duration_ms` and
`client_ip`. A 500 also has an `Unhandled exception` line with the traceback and, with
Sentry on, an event tagged with the same id.

## Incidents

**`/health/ready` returns 503, API otherwise up.** The database is unreachable. Check
`docker compose ps db`, the DB logs, `DB_HOST`/`DB_PORT`/credentials and `DB_SSLMODE`.
The `Readiness check: database unreachable` log line has the driver error. The API
recovers by itself once the database is back (`pool_pre_ping` discards dead connections).

**Container `unhealthy` right after a config change.** If `ALLOWED_HOSTS` was restricted,
the image healthcheck sends the first non-wildcard host; make sure that value, or
`healthcheck.<domain>` for a `*.domain` entry, is allowed. Orchestrator probes must send
an allowed `Host` header too. Symptom of a mismatch: 400 on `/health/live`.

**Container exits at startup.** `docker compose logs api`. Either
`Unsafe configuration for APP_ENV=production: ...` (fix the listed settings; see
SECURITY.md) or `alembic upgrade head failed after N attempts` (database or migration
problem).

**Spike of 429.** Rate limits are per client IP. Behind a proxy, if every request shares
one IP, `FORWARDED_ALLOW_IPS` does not include the proxy and everyone is counted as the
proxy. With several workers the real limit is multiplied by `WEB_CONCURRENCY` unless
`RATE_LIMIT_STORAGE_URI` points to a shared store.

**Users suddenly logged out / `Refresh token reuse detected` warnings.** A refresh token
that was already used was presented again, so its whole session family was revoked. One or
two are normal (a client retrying after a timeout). Many for one `user_id` means a stolen
token or a buggy client: revoke that user's sessions with `POST /auth/logout-all` (as the
user) or by setting `revoked` on their `refresh_tokens` rows, and reset the password.

**High latency / timeouts.** Check `http_request_duration_seconds` by `path` and
`http_requests_in_progress`. Raise `WEB_CONCURRENCY` if CPU allows, or `DB_POOL_SIZE` /
`DB_MAX_OVERFLOW` if requests wait for a connection (`QueuePool limit ... reached` in
logs; keep `workers x (pool + overflow)` under PostgreSQL's `max_connections`). bcrypt
(login/register) is CPU-bound by design.

**Worker killed / restarted.** Gunicorn restarts workers that exceed `GUNICORN_TIMEOUT`.
Set `GUNICORN_MAX_REQUESTS` to recycle workers periodically if memory grows.

## Routine jobs

```bash
# Delete expired refresh tokens; run daily (cron, k8s CronJob, ...)
docker compose exec api python -m app.jobs.purge_refresh_tokens

# Create or promote an admin; password from ADMIN_PASSWORD or a prompt, never argv
docker compose exec -e ADMIN_PASSWORD='...' api python -m app.jobs.create_admin admin@example.com
```

## Backups

The compose stack stores data in the `postgres_data` volume. The volume is not a backup.

```bash
# Dump
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > backup.sql

# Restore into an empty database
docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"' < backup.sql
```

Schedule the dump, ship it off the host, and test a restore. With a managed PostgreSQL,
use its point-in-time recovery instead.

## Rotate secrets

- `APP_SECRET_KEY`: changing it invalidates every access token (at most
  `ACCESS_TOKEN_EXPIRE_MINUTES`, 15 by default, of disruption: clients refresh). Refresh
  tokens are opaque and stored hashed, so they survive.
- `DB_PASSWORD`: change it in PostgreSQL and `.env`, then restart `api`.
- `METRICS_TOKEN`: change it here and in the scraper.

Restart with `docker compose -f docker-compose.yml up -d` so the new `.env` is read.
