"""Interactive helpers for acquiring Firebase ID tokens for Kumiho tests."""
from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import requests

CONFIG_ENV = "KUMIHO_CONFIG_DIR"
API_KEY_ENV = "KUMIHO_FIREBASE_API_KEY"
PROJECT_ENV = "KUMIHO_FIREBASE_PROJECT_ID"
# Legacy env var for token file is removed
REPO_ROOT_ENV = "KUMIHO_WORKSPACE_ROOT"
ENV_FILE_ENV = "KUMIHO_ENV_FILE"
TOKEN_GRACE_ENV = "KUMIHO_AUTH_TOKEN_GRACE_SECONDS"
CONTROL_PLANE_API_ENV = "KUMIHO_CONTROL_PLANE_API_URL"
DEFAULT_TOKEN_GRACE_SECONDS = 300
DEFAULT_CONTROL_PLANE_API_URL = "https://control.kumiho.cloud"
DEFAULT_FIREBASE_API_KEY = "AIzaSyBFAo7Nv48xAvbN18rL-3W41Dqheporh8E"


class TokenAcquisitionError(RuntimeError):
    """Raised when we cannot obtain or refresh a Firebase ID token."""


@dataclass
class Credentials:
    api_key: str
    email: str
    refresh_token: str
    id_token: str
    expires_at: int
    project_id: Optional[str] = None
    control_plane_token: Optional[str] = None
    cp_expires_at: Optional[int] = None

    def is_valid(self) -> bool:
        remaining = self.expires_at - int(time.time())
        grace = int(os.getenv(TOKEN_GRACE_ENV, DEFAULT_TOKEN_GRACE_SECONDS))
        return bool(self.id_token) and remaining > grace

    def is_cp_valid(self) -> bool:
        if not self.control_plane_token or not self.cp_expires_at:
            return False
        remaining = self.cp_expires_at - int(time.time())
        grace = int(os.getenv(TOKEN_GRACE_ENV, DEFAULT_TOKEN_GRACE_SECONDS))
        return remaining > grace


def _config_dir() -> Path:
    base = os.getenv(CONFIG_ENV)
    if base:
        return Path(base).expanduser()
    return Path.home() / ".kumiho"


def _credentials_path() -> Path:
    return _config_dir() / "kumiho_authentication.json"


def _default_repo_root() -> Path:
    env_root = os.getenv(REPO_ROOT_ENV)
    if env_root:
        return Path(env_root).expanduser()

    search_paths = [Path.cwd(), Path(__file__).resolve()]
    visited = set()
    for origin in search_paths:
        for candidate in [origin, *origin.parents]:
            if candidate in visited:
                continue
            visited.add(candidate)
            if (candidate / ".env.local").exists() and (candidate / "kumiho-python").exists():
                return candidate
            if (candidate / "Cargo.toml").exists() and (candidate / "kumiho-python").exists():
                return candidate
    return Path.cwd()


def _load_credentials() -> Optional[Credentials]:
    try:
        data = json.loads(_credentials_path().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None

    try:
        return Credentials(
            api_key=data["api_key"],
            email=data["email"],
            refresh_token=data["refresh_token"],
            id_token=data["id_token"],
            expires_at=int(data["expires_at"]),
            project_id=data.get("project_id"),
            control_plane_token=data.get("control_plane_token"),
            cp_expires_at=int(data.get("cp_expires_at")) if data.get("cp_expires_at") else None,
        )
    except KeyError:
        return None


def _save_credentials(creds: Credentials) -> None:
    path = _credentials_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "api_key": creds.api_key,
        "email": creds.email,
        "refresh_token": creds.refresh_token,
        "id_token": creds.id_token,
        "expires_at": creds.expires_at,
        "project_id": creds.project_id,
        "control_plane_token": creds.control_plane_token,
        "cp_expires_at": creds.cp_expires_at,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.chmod(path, 0o600)


def _token_preview(token: str) -> str:
    if not token:
        return "<empty>"
    if len(token) <= 16:
        return f"{token} (len={len(token)})"
    return f"{token[:8]}...{token[-6:]} (len={len(token)})"


def _log_token(token: str, source: str) -> None:
    # Do not log tokens in production
    pass


def _fetch_with_password(api_key: str, email: str, password: str) -> Tuple[str, str, int]:
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True,
    }
    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data["idToken"], data["refreshToken"], int(data.get("expiresIn", "3600"))


def _refresh_with_token(api_key: str, refresh_token: str) -> Tuple[str, str, int]:
    url = f"https://securetoken.googleapis.com/v1/token?key={api_key}"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    resp = requests.post(url, data=payload, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data["id_token"], data["refresh_token"], int(data.get("expires_in", "3600"))


def _exchange_for_control_plane_token(firebase_token: str) -> Tuple[Optional[str], Optional[int]]:
    base_url = os.getenv(CONTROL_PLANE_API_ENV, DEFAULT_CONTROL_PLANE_API_URL).rstrip("/")
    url = f"{base_url}/api/control-plane/token"
    
    try:
        resp = requests.post(
            url, 
            headers={"Authorization": f"Bearer {firebase_token}"},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        return data["token"], int(data["expires_at"])
    except requests.RequestException as exc:
        # Fallback: if CP exchange fails, we just return empty (client will use Firebase token)
        # But we should log it.
        print(f"[kumiho-auth] Warning: Failed to exchange for Control Plane JWT: {exc}")
        return None, None


def _prompt(prompt_text: str) -> str:
    return input(prompt_text).strip()


def _prompt_password(prompt_text: str = "KumihoClouds password: ") -> str:
    return getpass.getpass(prompt_text)


def _resolve_api_key(existing: Optional[str]) -> str:
    if existing:
        return existing
    env_key = os.getenv(API_KEY_ENV)
    if env_key:
        return env_key
    return DEFAULT_FIREBASE_API_KEY


def _resolve_project_id(existing: Optional[str]) -> Optional[str]:
    return existing or os.getenv(PROJECT_ENV)


def _interactive_login(api_key: str, project_id: Optional[str]) -> Credentials:
    print("[kumiho-auth] No cached credentials found. Please log in with your KumihoClouds credentials.")
    email = _prompt("KumihoClouds email: ")
    if not email:
        raise TokenAcquisitionError("KumihoClouds email is required")
    password = _prompt_password()
    if not password:
        raise TokenAcquisitionError("KumihoClouds password is required")

    id_token, refresh_token, expires_in = _fetch_with_password(api_key, email, password)
    expires_at = int(time.time()) + expires_in
    return Credentials(
        api_key=api_key,
        email=email,
        refresh_token=refresh_token,
        id_token=id_token,
        expires_at=expires_at,
        project_id=project_id,
    )


def ensure_token(
    *,
    interactive: bool = True,
) -> Tuple[str, str]:
    """Ensure a usable Firebase ID token exists.

    Returns the token and a short description of the source.
    """

    creds = _load_credentials()
    if creds and creds.is_valid():
        _log_token(creds.id_token, "cached")
        
        # Check if we need to refresh CP token
        if not creds.is_cp_valid():
             cp_token, cp_exp = _exchange_for_control_plane_token(creds.id_token)
             if cp_token:
                 creds.control_plane_token = cp_token
                 creds.cp_expires_at = cp_exp
                 _save_credentials(creds)

        return creds.control_plane_token or creds.id_token, "cached credentials"

    if creds and creds.refresh_token:
        try:
            id_token, refresh_token, expires_in = _refresh_with_token(creds.api_key, creds.refresh_token)
            updated = Credentials(
                api_key=creds.api_key,
                email=creds.email,
                refresh_token=refresh_token,
                id_token=id_token,
                expires_at=int(time.time()) + expires_in,
                project_id=creds.project_id,
            )
            
            # Exchange for CP token
            cp_token, cp_exp = _exchange_for_control_plane_token(id_token)
            updated.control_plane_token = cp_token
            updated.cp_expires_at = cp_exp

            _save_credentials(updated)
            _log_token(updated.id_token, "refreshed")
            return updated.control_plane_token or updated.id_token, "refreshed credentials"
        except requests.HTTPError as exc:
            print(f"[kumiho-auth] Refresh failed: {exc}")

    if not interactive:
        raise TokenAcquisitionError("No KumihoClouds token available and interactive mode disabled")

    api_key = _resolve_api_key(creds.api_key if creds else None)
    project_id = _resolve_project_id(creds.project_id if creds else None)
    new_creds = _interactive_login(api_key, project_id)
    
    # Exchange for CP token
    cp_token, cp_exp = _exchange_for_control_plane_token(new_creds.id_token)
    new_creds.control_plane_token = cp_token
    new_creds.cp_expires_at = cp_exp
    
    _save_credentials(new_creds)
    _log_token(new_creds.id_token, "interactive")
    return new_creds.control_plane_token or new_creds.id_token, "interactive login"


def cmd_login(args: argparse.Namespace) -> None:
    api_key = args.api_key or _resolve_api_key(None)
    project_id = args.project_id or _resolve_project_id(None)

    creds = _interactive_login(api_key, project_id)
    
    # Exchange for CP token
    cp_token, cp_exp = _exchange_for_control_plane_token(creds.id_token)
    creds.control_plane_token = cp_token
    creds.cp_expires_at = cp_exp

    _save_credentials(creds)
    _log_token(creds.id_token, "login")
    print(f"[kumiho-auth] Credentials cached at {_credentials_path()}")


def cmd_refresh(args: argparse.Namespace) -> None:
    creds = _load_credentials()
    if not creds:
        raise TokenAcquisitionError("No cached credentials to refresh. Run 'kumiho-auth login' first.")
    id_token, refresh_token, expires_in = _refresh_with_token(creds.api_key, creds.refresh_token)
    updated = Credentials(
        api_key=creds.api_key,
        email=creds.email,
        refresh_token=refresh_token,
        id_token=id_token,
        expires_at=int(time.time()) + expires_in,
        project_id=creds.project_id,
    )
    _save_credentials(updated)
    _log_token(updated.id_token, "refresh")
    print("[kumiho-auth] Token refreshed.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="KumihoClouds token helper")
    sub = parser.add_subparsers(dest="command", required=True)

    login = sub.add_parser("login", help="Obtain and store a KumihoClouds ID token using email/password")
    login.add_argument("--api-key", help="KumihoClouds API key (defaults to KUMIHO_FIREBASE_API_KEY)")
    login.add_argument("--project-id", help="KumihoClouds project ID (optional)")
    login.set_defaults(func=cmd_login)

    refresh = sub.add_parser("refresh", help="Refresh the cached KumihoClouds ID token using the stored refresh token")
    refresh.set_defaults(func=cmd_refresh)
    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except TokenAcquisitionError as exc:
        parser.error(str(exc))
    except requests.HTTPError as exc:
        parser.error(f"KumihoClouds request failed: {exc}")


if __name__ == "__main__":
    main()
