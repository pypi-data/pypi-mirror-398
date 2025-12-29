"""HTTP client for Zen API."""
import httpx
from typing import Any
from config import API_BASE_URL, session


class APIError(Exception):
    """API error with status code and message."""
    def __init__(self, status_code: int, error: str, message: str):
        self.status_code = status_code
        self.error = error
        self.message = message
        super().__init__(f"{error}: {message}")


def _get_headers() -> dict[str, str]:
    """Get headers with auth token if available."""
    headers = {"Content-Type": "application/json"}
    if session.id_token:
        headers["Authorization"] = f"Bearer {session.id_token}"
    return headers


def _handle_response(response: httpx.Response) -> dict[str, Any]:
    """Handle API response, raising APIError on failure."""
    if response.status_code >= 400:
        try:
            data = response.json()
            raise APIError(
                response.status_code,
                data.get("error", "unknown_error"),
                data.get("message", "Unknown error occurred")
            )
        except (ValueError, KeyError):
            raise APIError(response.status_code, "request_failed", response.text)
    
    if response.status_code == 204:
        return {}
    
    return response.json()


# ─────────────────────────────────────────────────────────────────────────────
# Auth API
# ─────────────────────────────────────────────────────────────────────────────

def login(email: str, password: str) -> dict[str, Any]:
    """Login and get tokens."""
    with httpx.Client(base_url=API_BASE_URL, timeout=30) as client:
        response = client.post("/auth/login", json={"email": email, "password": password})
        return _handle_response(response)


def signup(email: str, password: str, display_name: str = "") -> dict[str, Any]:
    """Create a new account."""
    with httpx.Client(base_url=API_BASE_URL, timeout=30) as client:
        payload = {"email": email, "password": password}
        if display_name:
            payload["displayName"] = display_name
        response = client.post("/auth/signup", json=payload)
        return _handle_response(response)


# ─────────────────────────────────────────────────────────────────────────────
# Chats API
# ─────────────────────────────────────────────────────────────────────────────

def list_chats() -> list[dict[str, Any]]:
    """List all chats for current user."""
    with httpx.Client(base_url=API_BASE_URL, timeout=30, headers=_get_headers()) as client:
        response = client.get("/chats", params={"uid": session.uid})
        data = _handle_response(response)
        return data.get("items", [])


def get_chat(chat_id: str) -> dict[str, Any]:
    """Get a chat with messages."""
    with httpx.Client(base_url=API_BASE_URL, timeout=30, headers=_get_headers()) as client:
        response = client.get(f"/chats/{chat_id}", params={"uid": session.uid})
        return _handle_response(response)


def create_chat(title: str = "", system_prompt: str = "") -> dict[str, Any]:
    """Create a new chat."""
    with httpx.Client(base_url=API_BASE_URL, timeout=30, headers=_get_headers()) as client:
        payload = {"uid": session.uid}
        if title:
            payload["title"] = title
        if system_prompt:
            payload["systemPrompt"] = system_prompt
        response = client.post("/chats", json=payload)
        return _handle_response(response)


def delete_chat(chat_id: str) -> None:
    """Delete a chat."""
    with httpx.Client(base_url=API_BASE_URL, timeout=30, headers=_get_headers()) as client:
        response = client.request("DELETE", f"/chats/{chat_id}", json={"uid": session.uid})
        _handle_response(response)


def send_message(chat_id: str, content: str) -> dict[str, Any]:
    """Send a message and get AI response."""
    with httpx.Client(base_url=API_BASE_URL, timeout=120, headers=_get_headers()) as client:
        response = client.post(
            f"/chats/{chat_id}/messages",
            json={"uid": session.uid, "content": content, "role": "user"}
        )
        return _handle_response(response)


# ─────────────────────────────────────────────────────────────────────────────
# Notes API
# ─────────────────────────────────────────────────────────────────────────────

def list_notes(limit: int = 50) -> list[dict[str, Any]]:
    """List all notes for current user."""
    with httpx.Client(base_url=API_BASE_URL, timeout=30, headers=_get_headers()) as client:
        response = client.get("/notes", params={"uid": session.uid, "limit": limit})
        data = _handle_response(response)
        return data.get("items", [])


def get_note(note_id: str) -> dict[str, Any]:
    """Get a single note."""
    with httpx.Client(base_url=API_BASE_URL, timeout=30, headers=_get_headers()) as client:
        response = client.get(f"/notes/{note_id}", params={"uid": session.uid})
        return _handle_response(response)


def create_note(title: str, content: str = "", keywords: list[str] = None, 
                trigger_words: list[str] = None) -> dict[str, Any]:
    """Create a new note."""
    with httpx.Client(base_url=API_BASE_URL, timeout=30, headers=_get_headers()) as client:
        payload = {"uid": session.uid, "title": title, "content": content}
        if keywords:
            payload["keywords"] = keywords
        if trigger_words:
            payload["triggerWords"] = trigger_words
        response = client.post("/notes", json=payload)
        return _handle_response(response)


def update_note(note_id: str, title: str = None, content: str = None,
                keywords: list[str] = None, trigger_words: list[str] = None) -> dict[str, Any]:
    """Update a note."""
    with httpx.Client(base_url=API_BASE_URL, timeout=30, headers=_get_headers()) as client:
        payload = {"uid": session.uid}
        if title is not None:
            payload["title"] = title
        if content is not None:
            payload["content"] = content
        if keywords is not None:
            payload["keywords"] = keywords
        if trigger_words is not None:
            payload["triggerWords"] = trigger_words
        response = client.patch(f"/notes/{note_id}", json=payload)
        return _handle_response(response)


def delete_note(note_id: str) -> None:
    """Delete a note."""
    with httpx.Client(base_url=API_BASE_URL, timeout=30, headers=_get_headers()) as client:
        response = client.request("DELETE", f"/notes/{note_id}", json={"uid": session.uid})
        _handle_response(response)


def search_notes(query: str = "", keywords: list[str] = None, 
                 trigger_words: list[str] = None, limit: int = 50) -> list[dict[str, Any]]:
    """Search notes."""
    with httpx.Client(base_url=API_BASE_URL, timeout=30, headers=_get_headers()) as client:
        params = {"uid": session.uid, "limit": limit}
        if query:
            params["q"] = query
        if keywords:
            params["keywords"] = keywords
        if trigger_words:
            params["triggerWords"] = trigger_words
        response = client.get("/notes/search", params=params)
        data = _handle_response(response)
        return data.get("items", [])
