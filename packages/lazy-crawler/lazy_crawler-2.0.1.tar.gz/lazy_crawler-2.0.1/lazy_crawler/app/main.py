"""
FastAPI Application Entry Point
Minimal configuration - all routes and settings are modularized
"""

from lazy_crawler.app.database import init_db
from lazy_crawler.app import config
from lazy_crawler.app.routers import auth, ds, contact, pages, data, health, admin
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from lazy_crawler.app.limiter import limiter


from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on application startup"""
    await init_db()
    yield


# Initialize FastAPI app
app = FastAPI(
    title=config.APP_TITLE,
    description=config.API_DESCRIPTION,
    version=config.API_VERSION,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=config.CORS_ALLOW_CREDENTIALS,
    allow_methods=config.CORS_ALLOW_METHODS,
    allow_headers=config.CORS_ALLOW_HEADERS,
)

app.add_middleware(GZipMiddleware, minimum_size=config.GZIP_MIN_SIZE)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


# Include all Routers
app.include_router(auth.router)
app.include_router(ds.router)
app.include_router(contact.router)
app.include_router(pages.router)
app.include_router(data.router)
app.include_router(health.router)
app.include_router(admin.router)


# Mount Static Files
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
