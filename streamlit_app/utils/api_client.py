"""Typed-by-convention HTTP client for the FastAPI backend."""

import os

import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
TIMEOUT_SECONDS = 60


class ApiError(Exception):
    """A readable error returned by the application API."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _request(method: str, path: str, token: str | None = None, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        response = requests.request(
            method,
            f"{API_BASE_URL}{path}",
            headers=headers,
            timeout=TIMEOUT_SECONDS,
            **kwargs,
        )
    except requests.RequestException as exc:
        raise ApiError("Cannot reach the API. Check that the backend is running.") from exc

    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", "The request could not be completed.")
        except ValueError:
            detail = "The request could not be completed."
        if response.status_code == 401:
            detail = "Your session expired. Please sign in again."
        raise ApiError(str(detail), response.status_code)
    if response.status_code == 204:
        return None
    try:
        return response.json()
    except ValueError as exc:
        raise ApiError("The API returned an invalid response.", response.status_code) from exc


def register(username: str, password: str) -> dict:
    return _request("POST", "/auth/register", json={"username": username, "password": password})


def login(username: str, password: str) -> dict:
    return _request("POST", "/auth/login", json={"username": username, "password": password})


def create_guest_session() -> dict:
    return _request("POST", "/auth/guest")


def get_current_user(token: str) -> dict:
    return _request("GET", "/auth/me", token)


def logout(token: str) -> None:
    _request("POST", "/auth/logout", token)


def list_conversations(token: str, search: str = "") -> list[dict]:
    params = {"search": search} if search else None
    return _request("GET", "/conversations", token, params=params)


def create_conversation(token: str, title: str = "New chat") -> dict:
    return _request("POST", "/conversations", token, json={"title": title})


def load_conversation(token: str, conversation_id: str) -> dict:
    return _request("GET", f"/conversations/{conversation_id}", token)


def rename_conversation(token: str, conversation_id: str, title: str) -> dict:
    return _request("PATCH", f"/conversations/{conversation_id}", token, json={"title": title})


def delete_conversation(token: str, conversation_id: str) -> dict:
    return _request("DELETE", f"/conversations/{conversation_id}", token)


def send_query(token: str, conversation_id: str, query: str) -> dict:
    return _request(
        "POST",
        "/rag/query",
        token,
        json={"conversation_id": conversation_id, "query": query},
    )


def upload_document(token: str, file, description: str) -> dict:
    return _request(
        "POST",
        "/rag/documents/upload",
        token,
        headers={"X-Description": description},
        files={"file": (file.name, file.getvalue(), file.type or "application/octet-stream")},
    )


def list_documents(token: str) -> list[dict]:
    return _request("GET", "/rag/documents", token)
