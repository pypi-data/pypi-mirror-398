## dorc-client (Python)

Python SDK for DORC MCP service with capability-based Bearer token authentication.

**Per CONTRACT.md**: The SDK accepts a Bearer token (API key or JWT) and forwards it. The SDK does NOT generate tokens.

### Install

```bash
pip install dorc-client
```

### Quick Start

```python
from dorc_client import DorcClient

# Create client with Bearer token (API key or JWT)
client = DorcClient(
    base_url="https://dorc-mcp-xxxxx.run.app",
    token="your-bearer-token-here",  # API key or JWT
)

# Health check (no auth required)
health = client.health()
print(health)  # {"status": "ok", "service": "dorc-mcp", "version": "0.1.0"}

# Validate content (Bearer token required)
result = client.validate(
    candidate_content="# My Canon Entry\n\nContent here...",
    content_type="text/markdown",
)
print(f"Run ID: {result.run_id}, Status: {result.pipeline_status}")

# Get run details
run = client.get_run(run_id=result.run_id)

# List chunks
chunks = client.list_chunks(run_id=result.run_id)
```

### Environment Variables

- **`DORC_MCP_URL`**: base URL of dorc-mcp (example: `https://dorc-mcp-xxxxx.us-east1.run.app`)
- **`DORC_TOKEN`** (or `DORC_JWT` for backward compat): Bearer token (API key or JWT)

### API Methods

- `health()` → `GET /health` (no auth)
- `healthz()` → `GET /healthz` (no auth)
- `validate(candidate_content, ...)` → `POST /v1/validate` (Bearer token required)
- `get_run(run_id)` → `GET /v1/runs/{run_id}` (Bearer token required)
- `list_chunks(run_id)` → `GET /v1/runs/{run_id}/chunks` (Bearer token required)

**Note**: Tenant is extracted from the token by MCP. You do NOT pass tenant_slug to these methods in MCP mode.


