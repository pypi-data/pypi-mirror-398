from __future__ import annotations

from dataclasses import dataclass


class DorcClientError(Exception):
    """Base error for dorc_client."""


class DorcConfigError(DorcClientError):
    """Configuration error (missing env vars, invalid base URL, etc.)."""


@dataclass
class DorcError(DorcClientError):
    """Normalized contract error (or best-effort fallback)."""

    status_code: int
    code: str
    message: str
    request_id: str | None = None
    response_text: str | None = None

    def __str__(self) -> str:
        rid = f" request_id={self.request_id}" if self.request_id else ""
        return f"HTTP {self.status_code} {self.code}:{rid} {self.message}"


class DorcHttpError(DorcError):
    """Legacy alias name for HTTP errors (kept for backwards compatibility)."""


class DorcAuthError(DorcError):
    """Authentication/authorization failure (401/403)."""


