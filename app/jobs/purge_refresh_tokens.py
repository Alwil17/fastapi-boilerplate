"""Delete expired refresh tokens. Run periodically (cron / k8s CronJob):

python -m app.jobs.purge_refresh_tokens
"""

from datetime import UTC, datetime

from app.db.base import SessionLocal
from app.repositories.refresh_token_repository import RefreshTokenRepository


def main() -> int:
    with SessionLocal() as db:
        deleted = RefreshTokenRepository(db).delete_expired(datetime.now(UTC))
    print(f"Deleted {deleted} expired refresh token(s)")
    return deleted


if __name__ == "__main__":
    main()
