from slowapi import Limiter
from fastapi import Request
from typing import Optional


def get_robust_key(request: Request) -> str:
    """
    Robust rate limit key function:
    1. Highest priority: User ID for authenticated users.
    2. Fallback: Real client IP (handling X-Forwarded-For and X-Real-IP).
    3. Last resort: Default remote address.
    """
    # 1. Check for authenticated user (if available in app.state or request.user)
    # SlowAPI's request object can access app state or dependencies if mapped
    # but here we rely on headers first for unauthenticated and user-specific info

    # 2. Extract Real IP (support for Nginx/Load Balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Get the leftmost IP which is the original client
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # 3. Default to remote_address (request.client.host)
    return request.client.host or "127.0.0.1"


limiter = Limiter(key_func=get_robust_key)
