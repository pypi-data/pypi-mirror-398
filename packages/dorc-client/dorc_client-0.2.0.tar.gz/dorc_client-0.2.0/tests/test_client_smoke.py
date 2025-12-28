"""Tests for dorc-client SDK using mocked HTTP responses."""

import os
from unittest.mock import patch

import httpx
import pytest

from dorc_client import Config, DorcClient
from dorc_client.errors import DorcError
from dorc_client.models import ChunkResult, RunStateResponse, ValidateResponse


@pytest.fixture
def config():
    """Create a test MCP configuration."""
    return Config(
        base_url="https://test-mcp.run.app",
        mode="mcp",
        token="test-jwt-token",
    )


@pytest.fixture
def client(config):
    """Create a test MCP client."""
    c = DorcClient(config=config)
    return c


def _with_transport(client: DorcClient, handler):
    client._client.close()
    client._client = httpx.Client(  # type: ignore[attr-defined]
        base_url=client.config.base_url,
        transport=httpx.MockTransport(handler),
    )


def test_health_success(client):
    """Test successful health check."""
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url) == "https://test-mcp.run.app/health"
        return httpx.Response(
            status_code=200,
            json={"status": "ok", "service": "dorc-mcp", "version": "0.1.0"},
        )

    _with_transport(client, handler)
    result = client.health()
    assert result["status"] == "ok"


def test_validate_cce_success(client):
    """Test successful validate request."""
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
        assert request.headers.get("Authorization") == "Bearer test-jwt-token"
        return httpx.Response(status_code=200, json=mock_response)

    _with_transport(client, handler)
    response = client.validate(candidate_content="Test content")
    
    assert isinstance(response, ValidateResponse)
    assert response.run_id == "run-test-123"
    assert response.status == "COMPLETE"


def test_get_run_success(client):
    """Test successful get_run request."""
    mock_response = {
        "run_id": "run-test-123",
        "tenant_slug": "test-tenant",
        "pipeline_status": "COMPLETE",
        "content_summary": {
            "pass": 2,
            "fail": 0,
            "warn": 0,
            "error": 0,
        },
        "inserted_at": "2024-01-15T10:30:00Z",
        "meta": {},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url) == "https://test-mcp.run.app/v1/runs/run-test-123"
        assert request.headers.get("Authorization") == "Bearer test-jwt-token"
        return httpx.Response(status_code=200, json=mock_response)

    _with_transport(client, handler)
    response = client.get_run(run_id="run-test-123")
    
    assert isinstance(response, RunStateResponse)
    assert response.run_id == "run-test-123"
    assert response.pipeline_status == "COMPLETE"


def test_get_run_not_found(client):
    """Test get_run with 404 error."""
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url) == "https://test-mcp.run.app/v1/runs/nonexistent"
        assert request.headers.get("Authorization") == "Bearer test-jwt-token"
        return httpx.Response(
            status_code=404,
            json={"error": {"code": "NOT_FOUND", "message": "run not found"}},
        )

    _with_transport(client, handler)
    
    with pytest.raises(DorcError):
        client.get_run(run_id="nonexistent")


def test_list_chunks_success(client):
    """Test successful list_chunks request."""
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
            {
                "chunk_id": "ch-1-def",
                "index": 1,
                "status": "FAIL",
                "model_used": "gemini-2.5-pro",
                "finding_count": 2,
                "message": "Found contradictions",
                "evidence": [
                    {
                        "source": "canon_v2/section.md",
                        "excerpt": "Existing content...",
                        "note": "Contradiction",
                    }
                ],
                "details": {"confidence": 0.85},
            },
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url) == "https://test-mcp.run.app/v1/runs/run-test-123/chunks"
        assert request.headers.get("Authorization") == "Bearer test-jwt-token"
        return httpx.Response(status_code=200, json=mock_response)

    _with_transport(client, handler)
    chunks = client.list_chunks(run_id="run-test-123")
    
    assert len(chunks) == 2
    assert isinstance(chunks[0], ChunkResult)
    assert chunks[0].status == "PASS"
    assert chunks[1].status == "FAIL"
    assert chunks[1].finding_count == 2


def test_request_id_header_sent(config):
    """Ensure X-Request-Id is sent when provided."""
    c = DorcClient(config=config, request_id="req-abc123")

    mock_response = {
        "request_id": "req-abc123",
        "run_id": "run-test-123",
        "status": "COMPLETE",
        "result": "PASS",
        "counts": {"PASS": 1, "FAIL": 0, "WARN": 0, "ERROR": 0, "total_chunks": 1},
        "links": {"run": "/v1/runs/run-test-123", "chunks": "/v1/runs/run-test-123/chunks"},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("X-Request-Id") == "req-abc123"
        return httpx.Response(status_code=200, json=mock_response)

    _with_transport(c, handler)
    resp = c.validate(
        candidate_content="hello",
        candidate_id="c-1",
        candidate_title="t",
    )
    assert resp.request_id == "req-abc123"


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


def test_config_strips_trailing_slash():
    """Test Config.from_env strips trailing slash from base_url."""
    with patch.dict(
        os.environ,
        {
            "DORC_MCP_URL": "https://test-mcp.run.app/",
            "DORC_JWT": "test-jwt",
        },
        clear=True,
    ):
        config = Config.from_env()
        assert config.base_url == "https://test-mcp.run.app"

