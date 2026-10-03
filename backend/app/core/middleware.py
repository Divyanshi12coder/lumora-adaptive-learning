"""HTTP middleware: secure headers, request-size limits and rate limiting.

The rate limiter is an in-process sliding window. It is intentionally simple and
documented as single-instance only; a multi-instance deployment should swap it
for a Redis-backed limiter (same interface).
"""

import time
from collections import defaultdict, deque
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for key, value in SECURITY_HEADERS.items():
            response.headers.setdefault(key, value)
        # The Swagger UI needs inline scripts from a CDN; everything else is JSON.
        if not request.url.path.startswith(("/docs", "/redoc")):
            response.headers.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
        if get_settings().environment == "production":
            response.headers.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains")
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        limit = get_settings().max_request_bytes
        length = request.headers.get("content-length")
        if length is not None:
            try:
                if int(length) > limit:
                    return JSONResponse({"detail": "Request is too large."}, status_code=413)
            except ValueError:
                return JSONResponse({"detail": "Invalid Content-Length header."}, status_code=400)
        return await call_next(request)


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, limit: int, window_seconds: float) -> bool:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > window_seconds:
                hits.popleft()
            if len(hits) >= limit:
                return False
            hits.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = SlidingWindowLimiter()

# (path prefix, method) -> (max requests, window seconds)
RATE_RULES: list[tuple[str, str, int, float]] = [
    ("/api/auth/login", "POST", 10, 60),
    ("/api/auth/register", "POST", 5, 60),
    ("/api/tutor/chat", "POST", 30, 60),
    ("/api/demo/", "POST", 40, 60),
    ("/api/adaptive/preview", "POST", 120, 60),
    ("/api/quiz/generate", "POST", 30, 60),
    ("/api/documents", "POST", 10, 60),
]


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if get_settings().rate_limit_enabled:
            client_ip = request.client.host if request.client else "unknown"
            for prefix, method, limit, window in RATE_RULES:
                if request.method == method and request.url.path.startswith(prefix):
                    if not limiter.allow(f"{client_ip}:{prefix}", limit, window):
                        return JSONResponse(
                            {"detail": "Too many requests - please slow down and try again in a minute."},
                            status_code=429,
                            headers={"Retry-After": str(int(window))},
                        )
                    break
        return await call_next(request)
