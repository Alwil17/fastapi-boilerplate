#!/bin/sh
# Container entrypoint: apply pending migrations, then run the given command.
#
# RUN_MIGRATIONS=false skips them. Do that (and run `alembic upgrade head` as a
# one-off job instead) when several replicas start at the same time.
set -eu

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    attempt=1
    # The database may still be starting: retry before giving up.
    until alembic upgrade head; do
        if [ "$attempt" -ge "${MIGRATION_ATTEMPTS:-10}" ]; then
            echo "alembic upgrade head failed after $attempt attempts" >&2
            exit 1
        fi
        attempt=$((attempt + 1))
        sleep "${MIGRATION_RETRY_DELAY:-3}"
    done
fi

exec "$@"
