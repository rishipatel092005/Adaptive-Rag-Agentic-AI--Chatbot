"""Backward-compatible proxy to the application's authenticated API."""

import os

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Adaptive RAG Auth Compatibility Proxy")
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


class UserCredentials(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=256)


def _forward(path: str, credentials: UserCredentials) -> dict:
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/{path}",
            json=credentials.model_dump(),
            timeout=10,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=503, detail="The application API is unavailable.") from exc
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", "Authentication request failed.")
        except ValueError:
            detail = "Authentication request failed."
        raise HTTPException(status_code=response.status_code, detail=detail)
    try:
        return response.json()
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="The application API returned an invalid response.") from exc


@app.post("/api/create_user")
def create_user(credentials: UserCredentials):
    _forward("register", credentials)
    return {"message": "Account created successfully.", "status": "success"}


@app.post("/api/login")
def login(credentials: UserCredentials):
    result = _forward("login", credentials)
    return {"jwt": result["access_token"], "username": result["username"]}


@app.post("/api/init")
def initialize_legacy_api_token():
    raise HTTPException(
        status_code=410,
        detail="API tokens are no longer used; sign in through the application API.",
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "auth-compatibility-proxy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8080)
