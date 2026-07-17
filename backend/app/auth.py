from fastapi import Header, HTTPException

from .db import supabase


def require_admin(authorization: str | None = Header(default=None)):
    """Verify the Supabase Auth JWT in the Authorization header.

    Any successfully authenticated Supabase user counts as an admin —
    there's a single admin account for now (multi-admin roles are a
    later enhancement, not required by the current spec).
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        response = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if not response or not response.user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return response.user
