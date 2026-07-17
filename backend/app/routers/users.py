from fastapi import APIRouter, Depends, HTTPException

from ..auth import hash_password, require_admin
from ..db import supabase
from ..models import UserCreate, UserPublic, UserUpdate

router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])


@router.get("", response_model=list[UserPublic])
def list_users(_admin: dict = Depends(require_admin)):
    rows = (
        supabase.table("users")
        .select("id, username, display_name, role, created_at")
        .order("created_at")
        .execute()
        .data
    )
    return rows


@router.post("", response_model=UserPublic, status_code=201)
def create_user(body: UserCreate, _admin: dict = Depends(require_admin)):
    existing = (
        supabase.table("users")
        .select("id")
        .eq("username", body.username)
        .execute()
        .data
    )
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")

    row = (
        supabase.table("users")
        .insert(
            {
                "username": body.username,
                "display_name": body.display_name,
                "password_hash": hash_password(body.password),
                "role": body.role,
            }
        )
        .execute()
        .data[0]
    )
    return UserPublic(**row)


@router.patch("/{user_id}", response_model=UserPublic)
def update_user(
    user_id: str, body: UserUpdate, _admin: dict = Depends(require_admin)
):
    existing = supabase.table("users").select("id").eq("id", user_id).execute().data
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")

    updates: dict = {}
    if body.username is not None:
        conflict = (
            supabase.table("users")
            .select("id")
            .eq("username", body.username)
            .neq("id", user_id)
            .execute()
            .data
        )
        if conflict:
            raise HTTPException(status_code=409, detail="Username already exists")
        updates["username"] = body.username
    if body.display_name is not None:
        updates["display_name"] = body.display_name
    if body.role is not None:
        updates["role"] = body.role
    if body.password:
        updates["password_hash"] = hash_password(body.password)

    if updates:
        supabase.table("users").update(updates).eq("id", user_id).execute()

    row = (
        supabase.table("users")
        .select("id, username, display_name, role, created_at")
        .eq("id", user_id)
        .execute()
        .data[0]
    )
    return UserPublic(**row)


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: str, admin: dict = Depends(require_admin)):
    if user_id == admin["id"]:
        raise HTTPException(
            status_code=400, detail="You cannot delete your own account"
        )

    existing = supabase.table("users").select("id").eq("id", user_id).execute().data
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")

    # Cascades to that user's attempts (attempts.user_id has ON DELETE CASCADE) —
    # their personal practice history has no meaning once the account is gone.
    supabase.table("users").delete().eq("id", user_id).execute()
