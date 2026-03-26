"""Health check endpoints for API status monitoring"""
import os
import requests
from fastapi import APIRouter
from app.core.logging import logger
from app.db.models import get_connection

router = APIRouter()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def check_api_key() -> bool:
    """Check if Gemini API key is valid by making a test request"""
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not found in environment")
        return False
    
    try:
        # Use Gemini's models endpoint to verify API key
        response = requests.get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}",
            timeout=5
        )
        is_valid = response.status_code == 200
        if is_valid:
            logger.info("API key validation successful")
        else:
            logger.warning(f"API key validation failed: {response.status_code}")
        return is_valid
    except Exception as e:
        logger.error(f"API key check failed: {e}")
        return False


def check_database() -> bool:
    """Check if database connection is working"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


@router.get("/")
def health_check():
    """
    Health check endpoint that verifies:
    - Gemini API key is valid
    - Database connection is working
    """
    api_status = "active" if check_api_key() else "inactive"
    db_status = "connected" if check_database() else "disconnected"
    
    logger.info(f"Health check: API={api_status}, DB={db_status}")
    
    return {
        "api_status": api_status,
        "db_status": db_status
    }
