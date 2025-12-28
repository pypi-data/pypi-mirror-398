"""Tests for dorc-client SDK MCP mode with JWT auth."""

import os
from unittest.mock import patch

import httpx
import pytest

from dorc_client import Config, DorcClient
from dorc_client.errors import DorcAuthError


@pytest.fixture
def mcp_config():
    """Create a test MCP configuration."""
    return Config(
        base_url="https://test-mcp.run.app",
        mode="mcp",
        token="test-jwt-token-123",
    )


@pytest.fixture
def mcp_client(mcp_config):
    """Create a test MCP client."""
    c = DorcClient(config=mcp_config)
    return c


def _with_transport(client: DorcClient, handler):
    client._client.close()
    client._client = httpx.Client(  # type: ignore[attr-defined]
        base_url=client.config.base_url,
        transport=httpx.MockTransport(handler),
    )


def test_health_works_without_jwt(mcp_client):
    """Test health endpoint works without JWT (no auth required)."""
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url) == "https://test-mcp.run.app/health"
        # Health endpoint doesn't require Authorization header
        assert "Authorization" not in request.headers
        return httpx.Response(
            status_code=200,
            json={"status": "ok", "service": "dorc-mcp", "version": "0.1.0"},
        )

    _with_transport(mcp_client, handler)
    result = mcp_client.health()
    assert result["status"] == "ok"
    assert result["service"] == "dorc-mcp"


def test_healthz_works_without_jwt(mcp_client):
    """Test healthz endpoint works without JWT (no auth required)."""
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url) == "https://test-mcp.run.app/healthz"
        # Health endpoint doesn't require Authorization header
        assert "Authorization" not in request.headers
        return httpx.Response(
            status_code=200,
            json={"status": "ok", "service": "dorc-mcp", "version": "0.1.0"},
        )

    _with_transport(mcp_client, handler)
    result = mcp_client.healthz()
    assert result["status"] == "ok"
    assert result["service"] == "dorc-mcp"


def test_validate_cce_sends_authorization_header(mcp_client):
    """Test validate sends Authorization: Bearer <jwt> header."""
    mock_response = {
        "request_id": "req-test-123",
        "run_id": "run-test-123",
        "status": "COMPLETE",
        "result": "PASS",
        "counts": {"PASS": 1, "FAIL": 0, "WARN": 0, "ERROR": 0, "total_chunks": 1},
        "links": {"run": "/v1/runs/run-test-123", "chunks": "/v1/runs/run-test-123/chunks"},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert str(request.url) == "https://test-mcp.run.app/v1/validate"
        # Must have Authorization header with Bearer token
        auth_header = request.headers.get("Authorization")
        assert auth_header is not None
        assert auth_header == "Bearer test-jwt-token-123"
        # Verify payload does NOT include tenant_slug (MCP derives it from JWT)
        payload = request.read()
        import json
        data = json.loads(payload)
        assert "tenant_slug" not in data
        assert data["candidate"]["content"] == "# Test CCE\n\nContent here."
        return httpx.Response(status_code=200, json=mock_response)

    _with_transport(mcp_client, handler)
    response = mcp_client.validate(candidate_content="# Test CCE\n\nContent here.")
    assert response.run_id == "run-test-123"


def test_validate_cce_raises_error_without_jwt():
    """Test validate_cce raises error when JWT is missing."""
    config = Config(
        base_url="https://test-mcp.run.app",
        mode="mcp",
        token=None,  # No JWT
    )
    client = DorcClient(config=config)

    with pytest.raises(DorcAuthError) as exc_info:
        client.validate(candidate_content="# Test")
    assert "Bearer token is required" in str(exc_info.value) or exc_info.value.status_code == 401


def test_get_run_sends_authorization_header(mcp_client):
    """Test get_run sends Authorization: Bearer <jwt> header."""
    mock_response = {
        "run_id": "run-test-123",
        "tenant_slug": "test-tenant",
        "pipeline_status": "COMPLETE",
        "content_summary": {"pass": 1, "fail": 0, "warn": 0, "error": 0},
        "inserted_at": "2024-01-15T10:30:00Z",
        "meta": {},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url) == "https://test-mcp.run.app/v1/runs/run-test-123"
        # Must have Authorization header
        auth_header = request.headers.get("Authorization")
        assert auth_header is not None
        assert auth_header == "Bearer test-jwt-token-123"
        return httpx.Response(status_code=200, json=mock_response)

    _with_transport(mcp_client, handler)
    response = mcp_client.get_run(run_id="run-test-123")
    assert response.run_id == "run-test-123"


def test_list_chunks_sends_authorization_header(mcp_client):
    """Test list_chunks sends Authorization: Bearer <jwt> header."""
    mock_response = {
        "run_id": "run-test-123",
        "tenant_slug": "test-tenant",
        "chunks": [
            {
                "chunk_id": "ch-0-abc",
                "index": 0,
                "status": "PASS",
                "model_used": "gemini-2.5-pro",
                "finding_count": 0,
                "message": "No contradictions",
                "evidence": [],
                "details": None,
            },
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url) == "https://test-mcp.run.app/v1/runs/run-test-123/chunks"
        # Must have Authorization header
        auth_header = request.headers.get("Authorization")
        assert auth_header is not None
        assert auth_header == "Bearer test-jwt-token-123"
        return httpx.Response(status_code=200, json=mock_response)

    _with_transport(mcp_client, handler)
    chunks = mcp_client.list_chunks(run_id="run-test-123")
    assert len(chunks) == 1
    assert chunks[0].status == "PASS"


def test_config_from_env_mcp_mode():
    """Test Config.from_env loads MCP mode when DORC_MCP_URL is set."""
    with patch.dict(
        os.environ,
        {
            "DORC_MCP_URL": "https://test-mcp.run.app",
            "DORC_JWT": "test-jwt-token",
        },
        clear=True,
    ):
        config = Config.from_env()
        assert config.base_url == "https://test-mcp.run.app"
        assert config.mode == "mcp"
        assert config.token == "test-jwt-token"


def test_for_mcp_factory():
    """Test DorcClient.for_mcp factory method."""
    client = DorcClient.for_mcp(
        base_url="https://test-mcp.run.app",
        token="test-jwt",
    )
    assert client.config.base_url == "https://test-mcp.run.app"
    assert client.config.mode == "mcp"
    assert client.config.token == "test-jwt"

