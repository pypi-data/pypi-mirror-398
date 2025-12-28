def api_key_headers(api_key: str | None) -> dict[str, str]:
    """Return headers for API key authentication.

    The engine is expected to accept `X-API-Key`. If api_key is None, returns {}.
    """

    if not api_key:
        return {}
    return {"X-API-Key": api_key}


def bearer_headers(token: str | None) -> dict[str, str]:
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


