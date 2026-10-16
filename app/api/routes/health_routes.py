import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health Check"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Simple health check endpoint to verify:
    - API is responding
    - Database connection is working
    - Current timestamp
    """
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        logger.exception("Health check: database unreachable")
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.now(UTC).isoformat(),
        "database": db_status,
        "version": settings.APP_VERSION,
    }


@router.get("/health/live")
def liveness():
    """Liveness probe: process is up. Does not touch dependencies."""
    return {"status": "alive"}


@router.get("/health/ready")
def readiness(response: Response, db: Session = Depends(get_db)):
    """Readiness probe: 503 when the database is unreachable."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Readiness check: database unreachable")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable"}
    return {"status": "ready"}


@router.get("/")
def root():
    """API root endpoint providing basic information."""
    return {
        "message": "Welcome to FastAPI Boilerplate",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
