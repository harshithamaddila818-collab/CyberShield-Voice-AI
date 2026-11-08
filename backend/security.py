"""Small safety limits for a public demo: per-IP rate limit on the expensive endpoints.

RATE_LIMIT_PER_MIN (default 30) = max POST requests per minute per visitor to the
analyze/speak endpoints. Set to 0 to switch the limit off (local development).
In-memory only, which is enough for a single-instance demo.
"""
import os
import time
from collections import defaultdict, deque

from fastapi.responses import JSONResponse

LIMITED_PATHS = ("/api/analyze-text", "/api/analyze-audio", "/api/speak")
WINDOW_SECONDS = 60


def client_ip(request):
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()

    if forwarded:
        return forwarded

    return request.client.host if request.client else "unknown"


def install_rate_limit(app):
    try:
        limit = int(os.environ.get("RATE_LIMIT_PER_MIN", "30"))
    except ValueError:
        limit = 30

    if limit <= 0:
        return

    hits = defaultdict(deque)

    @app.middleware("http")
    async def rate_limit(request, call_next):
        if request.method == "POST" and request.url.path in LIMITED_PATHS:
            now = time.time()
            ip = client_ip(request)
            recent = hits[ip]

            while recent and now - recent[0] > WINDOW_SECONDS:
                recent.popleft()

            if len(recent) >= limit:
                return JSONResponse(
                    status_code=429,
                    headers={"Retry-After": "30"},
                    content={
                        "detail": (
                            "Too many requests. Please wait a minute and try again."
                        )
                    }
                )

            recent.append(now)

            if len(hits) > 5000:  # forget visitors that went quiet
                for key in [k for k, v in hits.items() if not v or now - v[-1] > WINDOW_SECONDS]:
                    hits.pop(key, None)

        return await call_next(request)
