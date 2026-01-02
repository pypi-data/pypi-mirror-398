"""Internal helpers for bootstrapping the default Kumiho client."""
from __future__ import annotations

import logging

from .client import _Client
from .auth_cli import ensure_token, TokenAcquisitionError

_LOGGER = logging.getLogger("kumiho.bootstrap")


def bootstrap_default_client(*, force_refresh: bool = False) -> _Client:
    """Return a Client that delegates discovery to the public constructor."""

    refresh_flag = True if force_refresh else None
    
    # Ensure we have a valid token before creating the client
    # We use interactive=False by default to avoid EOFError in non-interactive environments (like Cloud Run)
    try:
        token, _ = ensure_token(interactive=False)
    except TokenAcquisitionError:
        # If we can't get a token, we'll proceed without one and let the client fail later if needed,
        # or rely on environment variables. But typically ensure_token raises if interactive fails.
        # We'll log and continue.
        _LOGGER.warning("Failed to acquire Firebase token interactively.")
        token = None

    try:
        return _Client(force_discovery_refresh=refresh_flag, auth_token=token)
    except Exception:  # pragma: no cover - defensive logging
        _LOGGER.exception("Falling back to direct Client initialisation")
        return _Client(target=None, force_discovery_refresh=None)


__all__ = ["bootstrap_default_client"]
