import time
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware

rate_limit_store = {}
RATE_LIMIT = 5
RATE_WINDOW = 60

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        exempt_paths = ["/docs", "/openapi.json", "/redoc"]
        if not any(request.url.path.startswith(path) for path in exempt_paths):
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["X-Request-ID"] = request.headers.get("X-Request-ID", str(time.time()))
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting if TESTING environment variable is set
        if os.environ.get("TESTING"):
            return await call_next(request)

        exempt_paths = ["/docs", "/openapi.json", "/redoc"]
        if any(request.url.path.startswith(path) for path in exempt_paths):
            return await call_next(request)

        client_ip = request.client.host
        now = time.time()
        timestamps = rate_limit_store.get(client_ip, [])
        timestamps = [t for t in timestamps if now - t < RATE_WINDOW]
        if len(timestamps) >= RATE_LIMIT:
            retry_after = RATE_WINDOW - int(now - timestamps[0])
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Try again later."},
                headers={"Retry-After": str(max(1, retry_after))}
            )
        timestamps.append(now)
        rate_limit_store[client_ip] = timestamps
        response = await call_next(request)
        return response

def setup_gateway(app: FastAPI):
    app.add_middleware(GZipMiddleware, minimum_size=500)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)