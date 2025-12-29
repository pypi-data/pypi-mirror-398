"""
Centralized configuration for FastAPI and all services.
Loads environment variables and provides a single source of truth for app settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# PostgreSQL Configuration
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "lazy_crawler")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "lazy_crawler")

# ============================================================================
# FASTAPI CONFIGURATION
# ============================================================================

APP_TITLE = "Crawlio Intelligence App"
API_DESCRIPTION = (
    "API for premium market intelligence and automated business data extraction"
)
API_VERSION = "1.0.0"

# CORS Configuration
CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "*")
CORS_ORIGINS = (
    [origin.strip() for origin in CORS_ORIGINS_STR.split(",")]
    if CORS_ORIGINS_STR != "*"
    else ["*"]
)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# GZip Middleware Configuration
GZIP_MIN_SIZE = 1000

# ============================================================================
# EMAIL CONFIGURATION
# ============================================================================

EMAIL_HOST = os.getenv("EMAIL_HOST", "email-smtp.ap-south-1.amazonaws.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT") or os.getenv("SMTP_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAILS_FROM_NAME = os.getenv("EMAILS_FROM_NAME", "Lazy Crawler Support")
EMAILS_FROM_EMAIL = os.getenv("EMAILS_FROM_EMAIL") or EMAIL_HOST_USER
CONTACT_RECIPIENT_EMAIL = os.getenv("CONTACT_RECIPIENT_EMAIL")

# ============================================================================
# AUTHENTICATION CONFIGURATION
# ============================================================================

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback"
)

# ============================================================================
# FILE UPLOAD CONFIGURATION
# ============================================================================

ALLOWED_UPLOAD_EXTENSIONS = [".csv", ".xlsx", ".xls"]
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")

# ============================================================================
# APPLICATION PATHS
# ============================================================================

APP_DIR = os.path.dirname(__file__)
TEMPLATES_DIR = os.path.join(APP_DIR, "templates")
STATIC_DIR = os.path.join(APP_DIR, "static")

# Create directories if they don't exist
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
