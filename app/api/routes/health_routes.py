from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.base import get_db

router = APIRouter(tags=["Health Check"])

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Simple health check endpoint to verify:
    - API is responding
    - Database connection is working
    - Current timestamp
    """
    try:
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
        "version": "1.0.0",
    }

@router.get("/")
async def root():
    """API root endpoint providing basic information."""
    return {
        "message": "Welcome to FastAPI Boilerplate",
        "version": "1.0.0",
        "docs": "/docs",
    }
