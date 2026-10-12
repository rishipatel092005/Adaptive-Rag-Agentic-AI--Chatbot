"""Authentication helpers for signed bearer tokens."""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from uuid import uuid4

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.db.mongo_client import db

users = db["users"]
bearer_scheme = HTTPBearer(auto_error=False)
TOKEN_TTL_SECONDS = 60 * 60 * 12


def _secret() -> bytes:
    secret = os.getenv("JWT_SECRET_KEY", "")
    if len(secret) < 32:
        raise HTTPException(
            status_code=503,
            detail="Authentication is not configured. Set JWT_SECRET_KEY to a random value of at least 32 characters.",
        )
    return secret.encode("utf-8")


def _encode_segment(value: dict) -> str:
    raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def create_access_token(
    username: str,
    token_version: int = 0,
    guest: bool = False,
) -> str:
    header = _encode_segment({"alg": "HS256", "typ": "JWT"})
    payload = _encode_segment(
        {
            "sub": username,
            "ver": token_version,
            "guest": guest,
            "exp": int(time.time()) + TOKEN_TTL_SECONDS,
        }
    )
    signing_input = f"{header}.{payload}".encode()
    signature = hmac.new(_secret(), signing_input, hashlib.sha256).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()
    return f"{header}.{payload}.{encoded_signature}"


def _decode_access_token(token: str) -> tuple[str, int, bool]:
    try:
        header, payload, signature = token.split(".")
        signing_input = f"{header}.{payload}".encode()
        expected = hmac.new(_secret(), signing_input, hashlib.sha256).digest()
        supplied = base64.urlsafe_b64decode(signature + "=" * (-len(signature) % 4))
        if not hmac.compare_digest(expected, supplied):
            raise ValueError("invalid signature")

        decoded_header = json.loads(
            base64.urlsafe_b64decode(header + "=" * (-len(header) % 4))
        )
        claims = json.loads(
            base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
        )
        if decoded_header != {"alg": "HS256", "typ": "JWT"}:
            raise ValueError("invalid token header")
        if (
            not isinstance(claims.get("sub"), str)
            or not isinstance(claims.get("ver"), int)
            or not isinstance(claims.get("guest"), bool)
            or claims.get("exp", 0) <= time.time()
        ):
            raise ValueError("expired or invalid token")
        return claims["sub"], claims["ver"], claims["guest"]
    except HTTPException:
        raise
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired access token.") from exc


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=32,
    )
    return "scrypt${}${}".format(
        base64.urlsafe_b64encode(salt).decode(),
        base64.urlsafe_b64encode(digest).decode(),
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, salt, expected = encoded.split("$")
        if algorithm != "scrypt":
            return False
        salt_bytes = base64.urlsafe_b64decode(salt.encode())
        expected_bytes = base64.urlsafe_b64decode(expected.encode())
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt_bytes,
            n=2**14,
            r=8,
            p=1,
            dklen=32,
        )
        return hmac.compare_digest(actual, expected_bytes)
    except (ValueError, TypeError):
        return False


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Sign in to continue.")
    username, token_version, guest = _decode_access_token(credentials.credentials)
    if guest:
        if not username.startswith("guest:"):
            raise HTTPException(status_code=401, detail="Invalid guest session.")
        return {"username": username, "is_guest": True}
    try:
        user = await users.find_one({"username": username}, {"_id": 0, "password_hash": 0})
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "MongoDB is unavailable. Set MONGODB_URL in the project .env "
                "to a reachable database (or start local MongoDB), then restart the API."
            ),
        ) from exc
    if user is None:
        raise HTTPException(status_code=401, detail="This account no longer exists.")
    if user.get("token_version", 0) != token_version:
        raise HTTPException(status_code=401, detail="This session has been signed out.")
    return user


def create_guest_session() -> dict[str, str]:
    guest_id = str(uuid4())
    subject = f"guest:{guest_id}"
    return {
        "access_token": create_access_token(subject, guest=True),
        "token_type": "bearer",
        "username": "Guest",
        "guest_id": guest_id,
    }
