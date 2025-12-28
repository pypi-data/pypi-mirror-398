from __future__ import annotations

import os
import re
import time
import warnings
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    retry_if_result,
    stop_after_attempt,
    wait_exponential,
)

from .auth import api_key_headers, bearer_headers
from .config import Config
from .errors import DorcAuthError, DorcError
from .models import (
    TENANT_SLUG_REGEX,
    Candidate,
    ChunkResult,
    ChunkResultsResponse,
    RunStateResponse,
    ValidateOptions,
    ValidateRequest,
    ValidateResponse,
)

_TENANT_RE = re.compile(TENANT_SLUG_REGEX)


def _is_transient_exc(exc: BaseException) -> bool:
    return isinstance(exc, httpx.TimeoutException | httpx.NetworkError)


def _is_transient_response(resp: httpx.Response) -> bool:
    return resp.status_code in (429, 500, 502, 503, 504)


def _retry_get():
    return retry(
        retry=(
            retry_if_exception(_is_transient_exc)
            | retry_if_result(_is_transient_response)
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        reraise=True,
    )


class DorcClient:
    """Python SDK for DORC capability-based authentication.

    Accepts a Bearer token (API key or JWT) and forwards it to MCP.
    The SDK does NOT generate tokens - tokens must be provided by the caller.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        token: str | None = None,
        timeout_s: float = 30.0,
        validate_timeout_s: float = 300.0,
        config: Config | None = None,
        request_id: str | None = None,
    ):
        if config is None:
            if base_url is None and token is None:
                config = Config.from_env()
            else:
                # MCP mode: token is a Bearer token (API key or JWT)
                config = Config(
                    base_url=(base_url or "").rstrip("/"),
                    mode="mcp",
                    token=token,
                )

        self.config = config
        self._default_request_id = (
            (request_id or os.getenv("DORC_REQUEST_ID") or "").strip() or None
        )
        self._timeout = httpx.Timeout(timeout_s)
        self._validate_timeout = httpx.Timeout(validate_timeout_s)
        self._client = httpx.Client(
            base_url=self.config.base_url,
            headers={},  # auth headers are per-request
        )

    def _require_token(self) -> str:
        """Get Bearer token, raising clear error if missing."""
        if self.config.mode != "mcp":
            raise DorcError(
                status_code=500,
                code="CONFIG_ERROR",
                message="Token is only required in MCP mode",
            )
        token = (self.config.token or "").strip() or None
        if not token:
            raise DorcAuthError(
                status_code=401,
                code="UNAUTHENTICATED",
                message=(
                    "Bearer token is required. "
                    "Set token parameter or DORC_TOKEN environment variable."
                ),
            )
        return token

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> DorcClient:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    @classmethod
    def for_mcp(
        cls,
        base_url: str,
        *,
        token: str,
        timeout_s: float = 30.0,
        validate_timeout_s: float = 300.0,
    ) -> DorcClient:
        """Create client for MCP mode with Bearer token.

        Args:
            base_url: MCP service URL
            token: Bearer token (API key or JWT) - required
            timeout_s: Request timeout in seconds
            validate_timeout_s: Validation request timeout in seconds
        """
        cfg = Config(
            base_url=base_url.rstrip("/"),
            mode="mcp",
            token=token.strip() if token else None,
        )
        return cls(
            config=cfg,
            timeout_s=timeout_s,
            validate_timeout_s=validate_timeout_s,
        )

    @classmethod
    def for_engine(
        cls,
        base_url: str,
        *,
        api_key: str,
        tenant_slug: str,
        timeout_s: float = 30.0,
        validate_timeout_s: float = 300.0,
    ) -> DorcClient:
        tenant_slug = tenant_slug.strip()
        if not _TENANT_RE.fullmatch(tenant_slug):
            raise ValueError(f"invalid tenant_slug (must match {TENANT_SLUG_REGEX})")
        cfg = Config(
            base_url=base_url.rstrip("/"),
            mode="engine",
            tenant_slug=tenant_slug,
            api_key=api_key,
        )
        return cls(config=cfg, timeout_s=timeout_s, validate_timeout_s=validate_timeout_s)

    def _auth_headers(
        self, require_auth: bool = True, request_id: str | None = None
    ) -> dict[str, str]:
        """Get auth headers. require_auth=False for health endpoints."""
        headers: dict[str, str] = {}
        req_id = (request_id or self._default_request_id or "").strip() or None
        if req_id:
            headers["X-Request-Id"] = req_id
        if not require_auth:
            return headers
        if self.config.mode == "mcp":
            token = self._require_token()
            headers.update(bearer_headers(token))
            return headers
        # engine-direct (legacy) - not part of contract but kept for compatibility
        headers.update(api_key_headers(self.config.api_key))
        return headers

    def _raise_for_status(self, resp: httpx.Response) -> None:
        if 200 <= resp.status_code < 300:
            return

        text: str | None
        try:
            text = resp.text
        except Exception:
            text = None

        # Prefer contract error envelope.
        code = "HTTP_ERROR"
        message = "request failed"
        request_id = None
        try:
            payload = resp.json()
            if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
                err = payload["error"]
                code = str(err.get("code") or code)
                message = str(err.get("message") or message)
                request_id = str(err.get("request_id")) if err.get("request_id") else None
        except Exception:
            pass

        if resp.status_code in (401, 403):
            raise DorcAuthError(
                resp.status_code,
                code=code,
                message=message,
                request_id=request_id,
                response_text=text,
            )

        raise DorcError(
            resp.status_code,
            code=code,
            message=message,
            request_id=request_id,
            response_text=text,
        )

    @_retry_get()
    def _get(self, path: str) -> httpx.Response:
        resp = self._client.get(path, timeout=self._timeout, headers=self._auth_headers())
        if _is_transient_response(resp):
            return resp
        self._raise_for_status(resp)
        return resp

    def health(self) -> dict[str, Any]:
        """GET /health - Returns health status (no auth required)."""
        r = self._client.get(
            "/health",
            timeout=self._timeout,
            headers=self._auth_headers(require_auth=False),
        )
        self._raise_for_status(r)
        return r.json()

    def healthz(self) -> dict[str, Any]:
        """GET /healthz - Returns health status (no auth required)."""
        r = self._client.get(
            "/healthz",
            timeout=self._timeout,
            headers=self._auth_headers(require_auth=False),
        )
        self._raise_for_status(r)
        return r.json()

    def validate(
        self,
        *,
        candidate_content: str | None = None,
        content_type: str = "text/markdown",
        mode: str = "audit",
        title: str | None = None,
        metadata: dict[str, str] | None = None,
        options: dict[str, Any] | None = None,
        request_id: str | None = None,
        # legacy args (deprecated)
        content: str | None = None,
        candidate_text: str | None = None,
        candidate_id: str | None = None,
        candidate_title: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> ValidateResponse:
        """POST /v1/validate (contract-native).

        In MCP mode, tenant is derived by MCP from the JWT.
        In engine-direct mode, tenant is required.
        """
        # Deprecation adapter: old callers used content=/candidate_text=
        # and candidate_id/title/context.
        if candidate_content is None and (content is not None or candidate_text is not None):
            warnings.warn(
                (
                    "validate(content=...)/validate(candidate_text=...) is deprecated; "
                    "use validate(candidate_content=...)."
                ),
                DeprecationWarning,
                stacklevel=2,
            )
            candidate_content = content or candidate_text
            title = title or candidate_title
            if metadata is None and context is not None and isinstance(context, dict):
                # Best-effort: map context.tags into labels
                metadata = {k: str(v) for k, v in context.items() if isinstance(k, str)}

        if candidate_content is None or not str(candidate_content).strip():
            raise ValueError("validate() requires candidate_content=... (non-empty)")

        validate_options = ValidateOptions(**(options or {}))
        req = ValidateRequest(
            request_id=request_id,
            mode=mode,  # type: ignore[arg-type]
            candidate=Candidate(
                content=str(candidate_content),
                content_type=content_type,  # type: ignore[arg-type]
                title=title,
                labels=metadata,
                cce_id=candidate_id,
            ),
            options=validate_options,
        )

        payload = req.model_dump(exclude_none=True)
        if not payload.get("request_id") and self._default_request_id:
            payload["request_id"] = self._default_request_id

        # Engine-direct requires tenant_slug; MCP must not include it.
        if self.config.mode == "engine":
            tenant = (self.config.tenant_slug or "").strip()
            if not tenant:
                raise ValueError("tenant_slug is required for engine-direct client")
            if not _TENANT_RE.fullmatch(tenant):
                raise ValueError(f"invalid tenant_slug (must match {TENANT_SLUG_REGEX})")
            payload["tenant_slug"] = tenant
            payload["actor"] = {"subject": "sdk"}

        resp = self._client.post(
            "/v1/validate",
            json=payload,
            timeout=self._validate_timeout,
            headers=self._auth_headers(require_auth=True, request_id=payload.get("request_id")),
        )
        self._raise_for_status(resp)
        return ValidateResponse.model_validate(resp.json())

    def get_run(self, run_id: str) -> RunStateResponse:
        resp = self._get(f"/v1/runs/{run_id}")
        return RunStateResponse.model_validate(resp.json())

    def list_chunks(self, run_id: str) -> list[ChunkResult]:
        resp = self._get(f"/v1/runs/{run_id}/chunks")
        parsed = ChunkResultsResponse.model_validate(resp.json())
        return parsed.chunks

    def wait_for_completion(
        self,
        run_id: str,
        *,
        poll_interval_s: float = 2.0,
        timeout_s: float = 60.0,
    ) -> RunStateResponse:
        """Poll /v1/runs/{run_id} until pipeline_status != RUNNING (best-effort helper).

        Args:
            run_id: Run identifier
            poll_interval_s: Polling interval in seconds
            timeout_s: Timeout in seconds

        Note: In MCP mode, tenant is extracted from the Bearer token by MCP.
        Note: engine currently exposes `pipeline_status` not contract `status`.
        """
        deadline = time.time() + timeout_s
        while True:
            r = self.get_run(run_id)
            if str(r.pipeline_status).upper() != "RUNNING":
                return r
            if time.time() >= deadline:
                raise TimeoutError(f"timeout waiting for run {run_id}")
            time.sleep(poll_interval_s)


