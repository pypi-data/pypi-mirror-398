"""Helpers for locating bearer tokens used by the Python client."""
from __future__ import annotations

import json
import os
import stat
import warnings
from pathlib import Path
from typing import Optional, Tuple

_TOKEN_ENV = "KUMIHO_AUTH_TOKEN"
_FIREBASE_TOKEN_ENV = "KUMIHO_FIREBASE_ID_TOKEN"
_CREDENTIALS_FILENAME = "kumiho_authentication.json"
_USE_CP_TOKEN_ENV = "KUMIHO_USE_CONTROL_PLANE_TOKEN"


def _normalize(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _env_flag(name: str) -> bool:
    value = os.getenv(name)
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes"}


def _config_dir() -> Path:
    base = os.getenv("KUMIHO_CONFIG_DIR")
    if base:
        return Path(base).expanduser()
    return Path.home() / ".kumiho"


def _credentials_path() -> Path:
    return _config_dir() / _CREDENTIALS_FILENAME


def _check_file_permissions(path: Path) -> None:
    """Warn if credential file has insecure permissions (Unix only)."""
    if os.name == "nt":  # Skip on Windows
        return
    try:
        mode = path.stat().st_mode
        # Check if group or world readable/writable/executable
        if mode & (stat.S_IRWXG | stat.S_IRWXO):
            warnings.warn(
                f"Credential file {path} has insecure permissions (mode: {oct(mode)}). "
                f"Other users may be able to read your credentials. "
                f"Run: chmod 600 {path}",
                UserWarning,
                stacklevel=3,
            )
    except OSError:
        pass  # Ignore errors checking permissions


def _read_credentials() -> Optional[dict]:
    path = _credentials_path()
    if not path.exists():
        return None
    
    # Security: Check file permissions before reading
    _check_file_permissions(path)
    
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _credentials_tokens() -> Tuple[Optional[str], Optional[str]]:
    data = _read_credentials()
    if not data:
        return None, None
    return _normalize(data.get("control_plane_token")), _normalize(data.get("id_token"))


def validate_token_format(token: Optional[str], source: str = "token") -> Optional[str]:
    """Validate that a token has valid JWT structure.
    
    Args:
        token: The token string to validate
        source: Description of token source for error messages
        
    Returns:
        The validated token, or None if token was None/empty
        
    Raises:
        ValueError: If the token is not in valid JWT format (3 base64 parts)
    """
    if token is None or not token.strip():
        return None
    
    token = token.strip()
    parts = token.split(".")
    
    if len(parts) != 3:
        raise ValueError(
            f"Invalid {source} format: expected JWT with 3 parts (header.payload.signature), "
            f"but got {len(parts)} part(s). "
            f"Did you accidentally use an API key instead of a JWT token? "
            f"Use 'kumiho-cli login' to obtain a valid token."
        )
    
    # Basic check that each part is non-empty
    for i, part in enumerate(parts):
        if not part:
            raise ValueError(
                f"Invalid {source} format: JWT part {i + 1} is empty. "
                f"The token may be corrupted or incomplete."
            )
    
    return token


def load_bearer_token() -> Optional[str]:
    """Return the preferred bearer token for gRPC calls.
    
    Raises:
        ValueError: If a token is found but has invalid JWT format
    """

    env_token = _normalize(os.getenv(_TOKEN_ENV))
    if env_token:
        return validate_token_format(env_token, "KUMIHO_AUTH_TOKEN")

    prefer_control_plane = _env_flag(_USE_CP_TOKEN_ENV)
    control_plane_token, firebase_token = _credentials_tokens()
    
    if prefer_control_plane and control_plane_token:
        return validate_token_format(control_plane_token, "control_plane_token")
    if firebase_token:
        return validate_token_format(firebase_token, "id_token")
    if control_plane_token:
        return validate_token_format(control_plane_token, "control_plane_token")

    return None


def load_firebase_token() -> Optional[str]:
    """Return a Firebase ID token for control-plane interactions."""

    env_token = _normalize(os.getenv(_FIREBASE_TOKEN_ENV))
    if env_token:
        return env_token

    _, firebase_token = _credentials_tokens()
    return firebase_token
