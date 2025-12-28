"""Integration tests for dorc-client SDK against a real deployed service.

These tests make actual HTTP calls to a deployed dorc-mcp service.
Set DORC_MCP_URL and DORC_JWT environment variables to run these tests.

To run:
    export DORC_MCP_URL="https://your-mcp-service.run.app"
    export DORC_JWT="your-jwt-token"
    pytest tests/test_integration.py -v

Or skip if env vars not set:
    pytest tests/test_integration.py -v -m "not integration"
Integration tests for DorcClient
"""
import os

import pytest

from dorc_client import DorcClient
from dorc_client.errors import DorcAuthError, DorcError

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def client():
    """Create a client from environment variables."""
    mcp_url = os.getenv("DORC_MCP_URL")
    jwt = os.getenv("DORC_JWT") or os.getenv("DORC_TOKEN")
    
    if not mcp_url or not jwt:
        pytest.skip("DORC_MCP_URL and DORC_JWT must be set for integration tests")
    
    return DorcClient()


def test_health_endpoint(client: DorcClient):
    """Test /health endpoint (no auth required)."""
    result = client.health()
    assert result["status"] == "ok"
    assert "service" in result
    assert result["service"] == "dorc-mcp"


def test_healthz_endpoint(client: DorcClient):
    """Test /healthz endpoint (no auth required)."""
    result = client.healthz()
    assert result["status"] == "ok"
    assert "service" in result


def test_validate_basic(client: DorcClient):
    """Test basic validation with simple content."""
    response = client.validate(
        candidate_content="# Test Document\n\nThis is a simple test.",
        content_type="text/markdown",
        mode="audit",
    )
    
    assert response.run_id is not None
    assert response.pipeline_status in ("COMPLETE", "RUNNING", "ERROR")
    assert response.content_summary is not None
    assert hasattr(response.content_summary, "pass")
    assert hasattr(response.content_summary, "fail")


def test_validate_with_title(client: DorcClient):
    """Test validation with title and metadata."""
    response = client.validate(
        candidate_content="# My Test Document\n\nContent here.",
        content_type="text/markdown",
        mode="audit",
        title="My Test Document",
        metadata={"source": "test", "version": "1.0"},
    )
    
    assert response.run_id is not None
    assert response.pipeline_status in ("COMPLETE", "RUNNING", "ERROR")


def test_get_run(client: DorcClient):
    """Test getting run status."""
    # First create a run
    validate_response = client.validate(
        candidate_content="# Test for get_run\n\nContent.",
    )
    run_id = validate_response.run_id
    
    # Now get the run status
    run_state = client.get_run(run_id)
    assert run_state.run_id == run_id
    assert run_state.pipeline_status is not None
    assert run_state.content_summary is not None


def test_list_chunks(client: DorcClient):
    """Test listing chunks for a run."""
    # First create a run
    validate_response = client.validate(
        candidate_content="# Test for list_chunks\n\nContent here.",
    )
    run_id = validate_response.run_id
    
    # Get chunks
    chunks = client.list_chunks(run_id)
    assert isinstance(chunks, list)
    # Chunks might be empty for very small content, but should be a list
    for chunk in chunks:
        assert hasattr(chunk, "chunk_id")
        assert hasattr(chunk, "index")
        assert hasattr(chunk, "status")


def test_validate_without_jwt():
    """Test that validation fails without JWT."""
    mcp_url = os.getenv("DORC_MCP_URL")
    if not mcp_url:
        pytest.skip("DORC_MCP_URL must be set")
    
    # Create client without JWT
    client = DorcClient.for_mcp(mcp_url, token=None)
    
    with pytest.raises(DorcAuthError) as exc_info:
        client.validate(candidate_content="# Test")
    
    assert "JWT token is required" in str(exc_info.value) or exc_info.value.status_code == 401


def test_validate_invalid_jwt():
    """Test that validation fails with invalid JWT."""
    mcp_url = os.getenv("DORC_MCP_URL")
    if not mcp_url:
        pytest.skip("DORC_MCP_URL must be set")
    
    # Create client with invalid JWT
    client = DorcClient.for_mcp(mcp_url, token="invalid-token")
    
    with pytest.raises((DorcAuthError, DorcError)) as exc_info:
        client.validate(candidate_content="# Test")
    
    # Should get 401 or 403
    assert exc_info.value.status_code in (401, 403)


def test_validate_empty_content(client: DorcClient):
    """Test that validation fails with empty content."""
    with pytest.raises(ValueError, match="candidate_content"):
        client.validate(candidate_content="")


def test_validate_large_content(client: DorcClient):
    """Test validation with larger content."""
    large_content = "# Large Document\n\n" + "This is a test paragraph. " * 100
    
    response = client.validate(
        candidate_content=large_content,
        content_type="text/markdown",
    )
    
    assert response.run_id is not None
    assert response.pipeline_status is not None

