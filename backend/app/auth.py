import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, Header, HTTPException

from .db import supabase

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_DAYS = 7


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(user: dict) -> str:
    payload = {
        "sub": user["id"],
        "username": user["username"],
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRES_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    """Resolve the bearer token to a live user row.

    Re-fetching from the DB (rather than trusting the JWT payload's role)
    means a role change or account deletion takes effect on the very next
    request, not just after the token expires.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)

    rows = (
        supabase.table("users")
        .select("id, username, display_name, role, created_at")
        .eq("id", payload["sub"])
        .execute()
        .data
    )
    if not rows:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return rows[0]


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
