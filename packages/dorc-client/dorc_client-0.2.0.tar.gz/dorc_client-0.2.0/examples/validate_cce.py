import argparse
import os

from dorc_client import DorcClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a sample CCE via MCP")
    parser.add_argument("--base-url", default=os.getenv("DORC_BASE_URL", "http://localhost:8080"))
    parser.add_argument("--token", default=os.getenv("DORC_TOKEN") or os.getenv("DORC_JWT"))
    parser.add_argument("--request-id", default=os.getenv("DORC_REQUEST_ID"))
    parser.add_argument("--title", default="Example CCE")
    parser.add_argument("--candidate-id", default="example-001")
    parser.add_argument("--file", help="Path to markdown content (optional)")
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = """# Example CCE

This is a tiny example payload.
"""

    with DorcClient(base_url=args.base_url, token=args.token, request_id=args.request_id) as c:
        r = c.validate(
            candidate_content=content,
            candidate_id=args.candidate_id,
            candidate_title=args.title,
            request_id=args.request_id,
        )
        print(f"run_id={r.run_id} pipeline_status={r.pipeline_status}")
        print(r.content_summary.model_dump(by_alias=True))


if __name__ == "__main__":
    main()
