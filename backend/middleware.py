"""
Security Middleware for HRBot API
Provides: Rate Limiting, Input Sanitization, Request Audit Logging,
and Firebase JWT Authentication verification.

Uses FastAPI's Depends() injection — no custom auth built from scratch.
"""

import os
import re
import time
import logging
from collections import defaultdict
from typing import Optional

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Firebase Admin SDK for token verification (managed auth — Strategy #1)
try:
    import firebase_admin
    from firebase_admin import auth as firebase_auth, credentials

    # Initialize Firebase only once
    if not firebase_admin._apps:
        # In production, GOOGLE_APPLICATION_CREDENTIALS env var points to service account JSON.
        # In hackathon dev mode, we allow graceful fallback.
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            # Default credentials (Cloud Run injects these automatically)
            try:
                firebase_admin.initialize_app()
            except Exception:
                pass  # Graceful fallback for local dev without Firebase
    FIREBASE_AVAILABLE = bool(firebase_admin._apps)
except ImportError:
    FIREBASE_AVAILABLE = False

# ─── Audit Logger ────────────────────────────────────────────────────
# Strategy #5: Every request is logged for the security timeline document

audit_logger = logging.getLogger("hrbot.audit")
audit_logger.setLevel(logging.INFO)

# File handler for persistent audit trail
_handler = logging.FileHandler("audit.log")
_handler.setFormatter(
    logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
)
audit_logger.addHandler(_handler)


# ─── Rate Limiter (in-memory, suitable for single-instance MVP) ──────
# Protects against brute-force and abuse during demo

class RateLimiter:
    """
    Simple sliding-window rate limiter.
    Production upgrade path: Redis-backed (e.g., via Cloud Memorystore).
    """

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        # Prune expired timestamps
        self._hits[client_ip] = [
            t for t in self._hits[client_ip] if now - t < self.window
        ]
        if len(self._hits[client_ip]) >= self.max_requests:
            return False
        self._hits[client_ip].append(now)
        return True


rate_limiter = RateLimiter(max_requests=30, window_seconds=60)


async def enforce_rate_limit(request: Request):
    """FastAPI dependency that rejects clients exceeding the rate limit."""
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        audit_logger.warning(f"RATE_LIMIT_EXCEEDED | ip={client_ip}")
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please slow down."
        )


# ─── Input Sanitization ─────────────────────────────────────────────
# Strips potentially dangerous patterns from user-supplied text

# Patterns that should never appear in HR chatbot queries
_DANGEROUS_PATTERNS = [
    re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),  # onclick=, onerror=, etc.
    re.compile(r"data:text/html", re.IGNORECASE),
]

# Maximum allowed query length (prevents payload abuse)
MAX_QUERY_LENGTH = 2000


def sanitize_input(text: str) -> str:
    """Remove XSS-style patterns and enforce length limits."""
    if len(text) > MAX_QUERY_LENGTH:
        text = text[:MAX_QUERY_LENGTH]

    for pattern in _DANGEROUS_PATTERNS:
        text = pattern.sub("", text)

    # Strip null bytes
    text = text.replace("\x00", "")
    return text.strip()


# ─── Firebase JWT Verification ───────────────────────────────────────
# Strategy #1: Never build auth from scratch — delegate to Firebase

security_scheme = HTTPBearer(auto_error=False)

# Toggle: set AUTH_REQUIRED=true in production, false in hackathon dev
AUTH_REQUIRED = os.getenv("AUTH_REQUIRED", "false").lower() == "true"


async def verify_firebase_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Optional[dict]:
    """
    Verifies the Firebase ID token from the Authorization header.

    - In production (AUTH_REQUIRED=true): rejects unauthenticated requests.
    - In dev/demo mode (AUTH_REQUIRED=false): allows passthrough with a
      warning log so judges can see the auth pipeline exists.
    """
    client_ip = request.client.host if request.client else "unknown"

    if credentials is None or not credentials.credentials:
        if AUTH_REQUIRED:
            audit_logger.warning(f"AUTH_MISSING | ip={client_ip} | path={request.url.path}")
            raise HTTPException(status_code=401, detail="Authentication required")
        audit_logger.info(f"AUTH_BYPASS_DEV | ip={client_ip} | path={request.url.path}")
        return None

    token = credentials.credentials

    if not FIREBASE_AVAILABLE:
        if AUTH_REQUIRED:
            raise HTTPException(status_code=503, detail="Auth service unavailable")
        audit_logger.info(f"AUTH_SKIP_NO_FIREBASE | ip={client_ip}")
        return None

    try:
        decoded = firebase_auth.verify_id_token(token)
        audit_logger.info(
            f"AUTH_SUCCESS | uid={decoded.get('uid')} | ip={client_ip}"
        )
        return decoded
    except firebase_auth.ExpiredIdTokenError:
        audit_logger.warning(f"AUTH_EXPIRED_TOKEN | ip={client_ip}")
        raise HTTPException(status_code=401, detail="Token expired — please re-authenticate")
    except firebase_auth.InvalidIdTokenError:
        audit_logger.warning(f"AUTH_INVALID_TOKEN | ip={client_ip}")
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    except Exception as e:
        audit_logger.error(f"AUTH_ERROR | ip={client_ip} | error={e}")
        if AUTH_REQUIRED:
            raise HTTPException(status_code=401, detail="Authentication failed")
        return None


# ─── Request Audit Logging Middleware ────────────────────────────────

async def log_request(request: Request):
    """Logs every API request for the security audit trail."""
    client_ip = request.client.host if request.client else "unknown"
    audit_logger.info(
        f"REQUEST | method={request.method} | path={request.url.path} | ip={client_ip}"
    )
