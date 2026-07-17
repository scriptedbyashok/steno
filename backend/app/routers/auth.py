from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import create_access_token, get_current_user, verify_password
from ..db import supabase
from ..models import LoginRequest, LoginResponse, UserPublic

router = APIRouter(prefix="/api/auth", tags=["auth"])


class UpdateMeRequest(BaseModel):
    display_name: str


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    rows = (
        supabase.table("users")
        .select("id, username, display_name, role, created_at, password_hash")
        .eq("username", body.username)
        .execute()
        .data
    )
    if not rows or not verify_password(body.password, rows[0]["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    user = rows[0]
    token = create_access_token(user)
    return LoginResponse(access_token=token, user=UserPublic(**user))


@router.get("/me", response_model=UserPublic)
def me(user: dict = Depends(get_current_user)):
    return UserPublic(**user)


@router.patch("/me", response_model=UserPublic)
def update_me(body: UpdateMeRequest, user: dict = Depends(get_current_user)):
    display_name = body.display_name.strip()
    if not display_name:
        raise HTTPException(status_code=422, detail="Display name cannot be empty")

    supabase.table("users").update({"display_name": display_name}).eq(
        "id", user["id"]
    ).execute()

    return UserPublic(**{**user, "display_name": display_name})
