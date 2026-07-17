import pytest
from fastapi import HTTPException

from app.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("Welcome@123")
    assert hashed != "Welcome@123"
    assert verify_password("Welcome@123", hashed)


def test_password_hash_rejects_wrong_password():
    hashed = hash_password("Welcome@123")
    assert not verify_password("wrong-password", hashed)


def test_access_token_roundtrip():
    user = {"id": "11111111-1111-1111-1111-111111111111", "username": "ashok"}
    token = create_access_token(user)
    payload = decode_access_token(token)
    assert payload["sub"] == user["id"]
    assert payload["username"] == "ashok"


def test_decode_rejects_garbage_token():
    with pytest.raises(HTTPException):
        decode_access_token("not-a-real-token")
