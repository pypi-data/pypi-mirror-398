from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from .errors import DorcConfigError


@dataclass(frozen=True)
class Config:
    """Configuration for the DORC client.

    MCP mode uses Bearer token authentication (capability-based).
    Engine-direct mode is legacy and not part of the contract.
    """

    base_url: str
    mode: Literal["mcp", "engine"] = "mcp"

    # MCP auth: Bearer token (API key or JWT) - required for MCP mode
    token: str | None = None

    # Engine-direct auth (X-API-Key) + tenancy (legacy, not contract-compliant)
    tenant_slug: str | None = None
    api_key: str | None = None

    @classmethod
    def from_env(cls) -> Config:
        # MCP mode (primary, contract-compliant)
        mcp_url = (os.getenv("DORC_MCP_URL") or "").strip().rstrip("/")
        if mcp_url:
            token = (os.getenv("DORC_TOKEN") or os.getenv("DORC_JWT") or "").strip() or None
            return cls(base_url=mcp_url, mode="mcp", token=token)

        # Engine-direct fallback (legacy).
        base_url = os.getenv("DORC_BASE_URL") or os.getenv("DORC_ENGINE_URL")
        if not base_url:
            raise DorcConfigError(
                "Missing base URL. Set DORC_MCP_URL for MCP (recommended) or set "
                "DORC_BASE_URL to your dorc-engine URL "
                "(example: https://dorc-engine-xxxxx.us-east1.run.app)."
            )
        base_url = base_url.rstrip("/")

        tenant_slug = (os.getenv("DORC_TENANT_SLUG") or "").strip() or None
        if not tenant_slug:
            raise DorcConfigError(
                "Missing DORC_TENANT_SLUG for engine-direct mode "
                "(tenant is required for direct engine calls)."
            )

        api_key = (os.getenv("DORC_API_KEY") or "").strip() or None
        return cls(base_url=base_url, mode="engine", tenant_slug=tenant_slug, api_key=api_key)


