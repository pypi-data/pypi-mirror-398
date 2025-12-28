import json

import httpx
import pytest

from dorc_client import DorcClient
from dorc_client.errors import DorcError


def test_mcp_client_builds_contract_body_and_auth(monkeypatch: pytest.MonkeyPatch):
    c = DorcClient.for_mcp("https://mcp.example", token="t")

    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("Authorization")
        seen["json"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(
            status_code=200,
            json={
                "request_id": "req_1",
                "run_id": "run_1",
                "status": "COMPLETE",
                "result": "PASS",
                "counts": {"PASS": 1, "FAIL": 0, "WARN": 0, "ERROR": 0, "total_chunks": 1},
                "links": {"run": "/v1/runs/run_1", "chunks": "/v1/runs/run_1/chunks"},
            },
        )

    c._client.close()
    c._client = httpx.Client(base_url=c.config.base_url, transport=httpx.MockTransport(handler))  # type: ignore[attr-defined]

    r = c.validate(candidate_content="hi")
    assert r.request_id == "req_1"

    assert seen["auth"] == "Bearer t"
    payload = seen["json"]
    assert "tenant_slug" not in payload
    assert payload["candidate"]["content"] == "hi"


def test_engine_client_requires_valid_tenant_slug():
    with pytest.raises(ValueError, match="invalid tenant_slug"):
        DorcClient.for_engine("https://engine.example", api_key="k", tenant_slug="Bad Tenant")


def test_error_envelope_parsing():
    c = DorcClient.for_engine("https://engine.example", api_key="k", tenant_slug="acme")
    import httpx

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=400,
            json={"error": {"code": "BAD_REQUEST", "message": "nope", "request_id": "req_x"}},
        )

    c._client.close()
    c._client = httpx.Client(base_url=c.config.base_url, transport=httpx.MockTransport(handler))  # type: ignore[attr-defined]

    with pytest.raises(DorcError) as e:
        c.validate(candidate_content="hi")
    assert e.value.code == "BAD_REQUEST"
    assert e.value.request_id == "req_x"


