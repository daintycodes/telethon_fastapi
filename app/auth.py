from fastapi import Depends, HTTPException
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED

from .config import ADMIN_API_KEY
from .auth_jwt import oauth2_scheme, get_current_user

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str = Depends(api_key_header)):
    """Backward-compatible API key dependency (keeps previous behavior)."""
    if not ADMIN_API_KEY:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Admin API key not configured on server",
        )

    if not api_key or api_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )

    return True


def require_admin(token: str = Depends(oauth2_scheme)):
    """Primary admin dependency: prefers JWT bearer; falls back to API key if no token."""
    # If token provided, validate JWT and admin status
    if token:
        from .auth_jwt import get_current_user
        from .database import SessionLocal
        db = SessionLocal()
        try:
            user = get_current_user(token, db)
            if not user.is_admin:
                raise HTTPException(status_code=403, detail="Admin privileges required")
            return user
        finally:
            db.close()

    # No bearer token, try API key header
    return require_api_key()
