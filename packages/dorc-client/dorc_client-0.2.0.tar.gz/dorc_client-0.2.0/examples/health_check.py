import argparse
import os

from dorc_client import DorcClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Health check against MCP")
    parser.add_argument("--base-url", default=os.getenv("DORC_BASE_URL", "http://localhost:8080"))
    parser.add_argument("--token", default=os.getenv("DORC_TOKEN") or os.getenv("DORC_JWT"))
    parser.add_argument("--request-id", default=os.getenv("DORC_REQUEST_ID"))
    args = parser.parse_args()

    with DorcClient(base_url=args.base_url, token=args.token, request_id=args.request_id) as c:
        ok = c.health()
        print(f"health={ok}")


if __name__ == "__main__":
    main()
