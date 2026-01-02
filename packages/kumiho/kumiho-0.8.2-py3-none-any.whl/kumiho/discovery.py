"""Helpers for bootstrapping a Client via the control-plane discovery endpoint."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
import platform
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional, Sequence, Tuple, Type

import requests

from ._token_loader import load_bearer_token, load_firebase_token
if TYPE_CHECKING:
    from .client import _Client as ClientType
else:
    ClientType = Any

Client: Optional[Type[Any]] = None

DEFAULT_CONTROL_PLANE_URL = os.getenv("KUMIHO_CONTROL_PLANE_URL") or "https://control.kumiho.cloud"
DEFAULT_CACHE_PATH = Path(
    os.getenv("KUMIHO_DISCOVERY_CACHE_FILE")
    or (Path.home() / ".kumiho" / "discovery-cache.json")
)
_DEFAULT_TIMEOUT = float(os.getenv("KUMIHO_DISCOVERY_TIMEOUT_SECONDS", "10"))
_DEFAULT_CACHE_KEY = "__default__"


class DiscoveryError(RuntimeError):
    """Raised when the discovery endpoint cannot be reached or returns an error."""


@dataclass(frozen=True)
class RegionRouting:
    region_code: str
    server_url: str
    grpc_authority: Optional[str] = None

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RegionRouting":
        return cls(
            region_code=payload["region_code"],
            server_url=payload["server_url"],
            grpc_authority=payload.get("grpc_authority"),
        )

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "region_code": self.region_code,
            "server_url": self.server_url,
        }
        if self.grpc_authority:
            data["grpc_authority"] = self.grpc_authority
        return data


@dataclass(frozen=True)
class CacheControl:
    issued_at: datetime
    refresh_at: datetime
    expires_at: datetime
    expires_in_seconds: int
    refresh_after_seconds: int

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "CacheControl":
        issued_at = _parse_iso8601(payload.get("issued_at"))
        refresh_at = _parse_iso8601(payload.get("refresh_at"))
        expires_at = _parse_iso8601(payload.get("expires_at"))
        return cls(
            issued_at=issued_at,
            refresh_at=refresh_at,
            expires_at=expires_at,
            expires_in_seconds=int(payload.get("expires_in_seconds", 0)),
            refresh_after_seconds=int(payload.get("refresh_after_seconds", 0)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issued_at": self.issued_at.isoformat(),
            "refresh_at": self.refresh_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "expires_in_seconds": self.expires_in_seconds,
            "refresh_after_seconds": self.refresh_after_seconds,
        }

    def is_expired(self, *, now: Optional[datetime] = None) -> bool:
        moment = now or datetime.now(timezone.utc)
        return moment >= self.expires_at

    def should_refresh(self, *, now: Optional[datetime] = None) -> bool:
        moment = now or datetime.now(timezone.utc)
        return moment >= self.refresh_at


@dataclass(frozen=True)
class DiscoveryRecord:
    tenant_id: str
    tenant_name: Optional[str]
    roles: Sequence[str]
    guardrails: Optional[Dict[str, Any]]
    region: RegionRouting
    cache_control: CacheControl

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "DiscoveryRecord":
        cache_section = payload.get("cache_control")
        if not cache_section:
            raise DiscoveryError("Discovery payload is missing cache_control metadata")
        region_section = payload.get("region")
        if not region_section:
            raise DiscoveryError("Discovery payload is missing region metadata")
        return cls(
            tenant_id=payload["tenant_id"],
            tenant_name=payload.get("tenant_name"),
            roles=list(payload.get("roles", [])),
            guardrails=payload.get("guardrails"),
            region=RegionRouting.from_dict(region_section),
            cache_control=CacheControl.from_dict(cache_section),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "tenant_name": self.tenant_name,
            "roles": list(self.roles),
            "guardrails": self.guardrails,
            "region": self.region.to_dict(),
            "cache_control": self.cache_control.to_dict(),
        }


def _get_machine_id() -> str:
    """Get a stable machine identifier for deriving encryption keys.
    
    This provides defense-in-depth by making cache files non-portable
    between machines. Falls back to a random ID stored in config dir.
    """
    # Try platform-specific methods
    try:
        if platform.system() == "Linux":
            # Linux: use machine-id
            for path in ["/etc/machine-id", "/var/lib/dbus/machine-id"]:
                if os.path.exists(path):
                    with open(path, "r") as f:
                        return f.read().strip()
        elif platform.system() == "Darwin":
            # macOS: use hardware UUID
            import subprocess
            result = subprocess.run(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in result.stdout.split("\n"):
                if "IOPlatformUUID" in line:
                    return line.split('"')[-2]
        elif platform.system() == "Windows":
            # Windows: use machine GUID
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography",
            )
            value, _ = winreg.QueryValueEx(key, "MachineGuid")
            return str(value)
    except Exception:
        pass  # Fall through to file-based ID
    
    # Fallback: use a randomly generated ID stored in config dir
    from ._token_loader import _config_dir
    id_file = _config_dir() / ".machine_id"
    if id_file.exists():
        return id_file.read_text(encoding="utf-8").strip()
    
    # Generate and store new ID
    new_id = str(uuid.uuid4())
    id_file.parent.mkdir(parents=True, exist_ok=True)
    id_file.write_text(new_id, encoding="utf-8")
    return new_id


def _derive_cache_key() -> bytes:
    """Derive an encryption key from machine ID + user context."""
    machine_id = _get_machine_id()
    user_context = f"{os.getlogin() if hasattr(os, 'getlogin') else ''}{os.getuid() if hasattr(os, 'getuid') else ''}"
    key_material = f"kumiho-discovery-cache-v1:{machine_id}:{user_context}"
    return hashlib.sha256(key_material.encode()).digest()


def _encrypt_cache_data(plaintext: str) -> str:
    """Encrypt cache data using XOR cipher with HMAC authentication.
    
    This provides defense-in-depth, not cryptographic security against
    determined attackers. The goal is to prevent casual inspection and
    make cache files non-portable between machines.
    """
    key = _derive_cache_key()
    
    # Generate random IV
    iv = secrets.token_bytes(16)
    
    # XOR encryption (simple but effective for this use case)
    plaintext_bytes = plaintext.encode("utf-8")
    key_stream = hashlib.sha256(key + iv).digest()
    
    # Extend key stream for longer plaintexts
    while len(key_stream) < len(plaintext_bytes):
        key_stream += hashlib.sha256(key + key_stream[-32:]).digest()
    
    ciphertext = bytes(p ^ k for p, k in zip(plaintext_bytes, key_stream))
    
    # Add HMAC for integrity
    mac = hmac.new(key, iv + ciphertext, hashlib.sha256).digest()[:16]
    
    # Format: base64(iv + ciphertext + mac)
    encrypted = base64.b64encode(iv + ciphertext + mac).decode("ascii")
    return f"enc:v1:{encrypted}"


def _decrypt_cache_data(encrypted: str) -> Optional[str]:
    """Decrypt cache data. Returns None if decryption fails."""
    if not encrypted.startswith("enc:v1:"):
        # Unencrypted legacy format - migrate on next write
        return encrypted
    
    try:
        key = _derive_cache_key()
        raw = base64.b64decode(encrypted[7:])  # Skip "enc:v1:" prefix
        
        if len(raw) < 32:  # iv(16) + mac(16) minimum
            return None
        
        iv = raw[:16]
        mac = raw[-16:]
        ciphertext = raw[16:-16]
        
        # Verify HMAC
        expected_mac = hmac.new(key, iv + ciphertext, hashlib.sha256).digest()[:16]
        if not hmac.compare_digest(mac, expected_mac):
            return None  # Integrity check failed
        
        # Decrypt
        key_stream = hashlib.sha256(key + iv).digest()
        while len(key_stream) < len(ciphertext):
            key_stream += hashlib.sha256(key + key_stream[-32:]).digest()
        
        plaintext = bytes(c ^ k for c, k in zip(ciphertext, key_stream))
        return plaintext.decode("utf-8")
    except Exception:
        return None


class DiscoveryCache:
    """Encrypted JSON file cache keyed by tenant hint.
    
    Cache data is encrypted at rest using a machine-specific key,
    providing defense-in-depth protection for tenant metadata.
    """

    def __init__(self, path: Optional[Path] = None, *, encrypt: bool = True) -> None:
        self.path = path or DEFAULT_CACHE_PATH
        self._encrypt = encrypt

    def load(self, cache_key: str) -> Optional[DiscoveryRecord]:
        payload = self._read_all().get(cache_key)
        if not payload:
            return None
        try:
            return DiscoveryRecord.from_dict(payload)
        except DiscoveryError:
            return None

    def store(self, cache_key: str, record: DiscoveryRecord) -> None:
        data = self._read_all()
        data[cache_key] = record.to_dict()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(".tmp")
        
        # Serialize to JSON
        json_content = json.dumps(data, indent=2)
        
        # Encrypt if enabled
        if self._encrypt:
            content_to_write = _encrypt_cache_data(json_content)
        else:
            content_to_write = json_content
        
        with tmp_path.open("w", encoding="utf-8") as handle:
            handle.write(content_to_write)
        
        # Retry replacement to handle Windows file locking
        import time
        max_retries = 5
        for i in range(max_retries):
            try:
                tmp_path.replace(self.path)
                return
            except PermissionError:
                if i == max_retries - 1:
                    raise
                time.sleep(0.1)
            except OSError:
                if i == max_retries - 1:
                    raise
                time.sleep(0.1)

    def _read_all(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                content = handle.read()
            
            # Try to decrypt if encrypted
            decrypted = _decrypt_cache_data(content)
            if decrypted is None:
                # Decryption failed - cache may be from different machine
                return {}
            
            return json.loads(decrypted)
        except (json.JSONDecodeError, OSError):
            return {}


class DiscoveryManager:
    """Coordinates cache usage and remote discovery calls."""

    def __init__(
        self,
        *,
        control_plane_url: Optional[str] = None,
        cache_path: Optional[Path] = None,
        timeout: Optional[float] = None,
    ) -> None:
        self.base_url = control_plane_url or DEFAULT_CONTROL_PLANE_URL
        self.cache = DiscoveryCache(cache_path)
        self.timeout = timeout or _DEFAULT_TIMEOUT

    def resolve(
        self,
        *,
        id_token: str,
        tenant_hint: Optional[str] = None,
        force_refresh: bool = False,
    ) -> DiscoveryRecord:
        cache_key = tenant_hint or _DEFAULT_CACHE_KEY

        def fetch_fresh() -> DiscoveryRecord:
            firebase_token = _ensure_firebase_token(id_token)
            fresh = self._fetch_remote(id_token=firebase_token, tenant_hint=tenant_hint)
            self.cache.store(cache_key, fresh)
            return fresh

        if not force_refresh:
            cached = self.cache.load(cache_key)
            if cached and not cached.cache_control.is_expired():
                if cached.cache_control.should_refresh():
                    try:
                        return fetch_fresh()
                    except DiscoveryError:
                        if not cached.cache_control.is_expired():
                            return cached
                        raise
                return cached

        return fetch_fresh()

    def _fetch_remote(self, *, id_token: str, tenant_hint: Optional[str]) -> DiscoveryRecord:
        url = _build_discovery_url(self.base_url)
        headers = {"Authorization": f"Bearer {id_token}", "Content-Type": "application/json"}
        payload: Dict[str, Any] = {}
        if tenant_hint:
            payload["tenant_hint"] = tenant_hint

        response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        if response.status_code >= 400:
            raise DiscoveryError(
                f"Discovery endpoint returned {response.status_code}: {response.text[:200]}"
            )
        try:
            body = response.json()
        except ValueError as exc:
            raise DiscoveryError("Discovery endpoint returned invalid JSON") from exc
        return DiscoveryRecord.from_dict(body)


def client_from_discovery(
    *,
    id_token: Optional[str] = None,
    tenant_hint: Optional[str] = None,
    control_plane_url: Optional[str] = None,
    cache_path: Optional[str] = None,
    force_refresh: bool = False,
    default_metadata: Optional[Sequence[Tuple[str, str]]] = None,
) -> "ClientType":
    """Create a Client configured via the public discovery endpoint.

    The helper caches discovery payloads based on the tenant hint, respects the
    cache-control metadata emitted by the control plane, and refreshes the
    routing info once the `refresh_after_seconds` deadline passes.
    """

    token = id_token or load_bearer_token()
    if not token:
        raise DiscoveryError(
            "A bearer token is required. Set KUMIHO_AUTH_TOKEN or run kumiho-auth login."
        )

    manager = DiscoveryManager(
        control_plane_url=control_plane_url,
        cache_path=Path(cache_path) if cache_path else None,
    )
    record = manager.resolve(id_token=token, tenant_hint=tenant_hint, force_refresh=force_refresh)

    target = record.region.grpc_authority or record.region.server_url
    metadata: Iterable[Tuple[str, str]] = list(default_metadata or [])
    metadata = list(metadata)
    metadata.append(("x-tenant-id", record.tenant_id))

    client_cls = _get_client_class()
    return client_cls(target=target, auth_token=token, default_metadata=metadata)


def _parse_iso8601(raw: Optional[str]) -> datetime:
    if not raw:
        raise DiscoveryError("Discovery payload missing required timestamp")
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    value = datetime.fromisoformat(text)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _build_discovery_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/api/discovery/tenant"):
        return base
    if base.endswith("/api/discovery"):
        return f"{base}/tenant"
    if base.endswith("/api"):
        return f"{base}/discovery/tenant"
    return f"{base}/api/discovery/tenant"


def _ensure_firebase_token(candidate: str) -> str:
    if not _is_control_plane_token(candidate):
        return candidate

    firebase = load_firebase_token()
    if firebase:
        return firebase

    raise DiscoveryError(
        "Control Plane JWT detected but no Firebase ID token is available. "
        "Run 'kumiho-auth login' to refresh credentials."
    )


def _decode_claims(token: str) -> Dict[str, Any]:
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    payload = parts[1]
    padding = "=" * (-len(payload) % 4)
    try:
        data = base64.urlsafe_b64decode((payload + padding).encode("utf-8"))
    except (binascii.Error, ValueError):
        return {}
    try:
        obj = json.loads(data)
    except json.JSONDecodeError:
        return {}
    return obj if isinstance(obj, dict) else {}


def _is_control_plane_token(token: str) -> bool:
    claims = _decode_claims(token)
    if not claims:
        return False
    if isinstance(claims.get("tenant_id"), str):
        return True
    iss = claims.get("iss")
    if isinstance(iss, str) and iss.startswith("https://control.kumiho.cloud"):
        return True
    aud = claims.get("aud")
    if isinstance(aud, str) and aud.startswith("kumiho-server"):
        return True
    return False


def _get_client_class() -> Type[Any]:
    global Client
    if Client is None:
        from .client import _Client as RealClient

        Client = RealClient
    return Client
