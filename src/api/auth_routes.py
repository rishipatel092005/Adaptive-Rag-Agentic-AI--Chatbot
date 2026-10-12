"""Registration and login endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError

from src.auth import (
    create_access_token,
    create_guest_session,
    get_current_user,
    hash_password,
    users,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=256)


@router.post("/guest")
async def guest_session():
    return create_guest_session()


@router.post("/register", status_code=201)
async def register(credentials: Credentials):
    username = credentials.username.strip().lower()
    try:
        await users.create_index("username", unique=True)
        await users.insert_one(
            {
                "username": username,
                "password_hash": hash_password(credentials.password),
                "token_version": 0,
                "created_at": datetime.now(timezone.utc),
            }
        )
    except DuplicateKeyError as exc:
        raise HTTPException(status_code=409, detail="An account with this username already exists.") from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "MongoDB is unavailable. Set MONGODB_URL in the project .env "
                "to a reachable database (or start local MongoDB), then restart the API."
            ),
        ) from exc
    return {"message": "Account created. You can now sign in."}


@router.post("/login")
async def login(credentials: Credentials):
    username = credentials.username.strip().lower()
    try:
        user = await users.find_one({"username": username})
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "MongoDB is unavailable. Set MONGODB_URL in the project .env "
                "to a reachable database (or start local MongoDB), then restart the API."
            ),
        ) from exc
    if user is None or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    return {
        "access_token": create_access_token(
            username,
            user.get("token_version", 0),
        ),
        "token_type": "bearer",
        "username": username,
    }


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    if user.get("is_guest"):
        return {"username": "Guest", "is_guest": True}
    return {"username": user["username"]}


@router.post("/logout", status_code=204)
async def logout(user: dict = Depends(get_current_user)):
    if user.get("is_guest"):
        return None
    try:
        await users.update_one(
            {"username": user["username"]},
            {"$inc": {"token_version": 1}},
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="The session could not be revoked.") from exc
