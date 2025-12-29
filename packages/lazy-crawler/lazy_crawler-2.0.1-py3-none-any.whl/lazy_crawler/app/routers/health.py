"""
Health check and system monitoring endpoints
"""

from fastapi import APIRouter
from lazy_crawler.app.database import engine
from sqlalchemy import text
from pymongo import MongoClient
from lazy_crawler.app import config

router = APIRouter(tags=["health"])

# MongoDB Connection
client = MongoClient(config.MONGO_URI)


@router.get("/health")
async def health_check():
    """
    Health check endpoint for Docker and Nginx monitoring.

    Returns status of:
    - MongoDB connection
    - PostgreSQL connection
    """
    status = {"status": "healthy", "checks": {}}

    try:
        # Check MongoDB connection
        client.admin.command("ping")
        status["checks"]["mongodb"] = "connected"
    except Exception as e:
        status["status"] = "unhealthy"
        status["checks"]["mongodb"] = f"disconnected: {str(e)}"

    try:
        # Check Postgres connection
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        status["checks"]["postgres"] = "connected"
    except Exception as e:
        status["status"] = "unhealthy"
        status["checks"]["postgres"] = f"disconnected: {str(e)}"

    return status
