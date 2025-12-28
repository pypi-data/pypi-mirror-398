#!/usr/bin/env python3
"""Generate a test JWT token for testing dorc-mcp service.

This script helps you generate a JWT token that will work with your deployed
dorc-mcp service. You need to know the JWT configuration from your Cloud Run
service (secret, issuer, audience).

Usage:
    # Option 1: Use environment variables
    export DORC_JWT_SECRET="your-secret"
    export DORC_JWT_ISSUER="your-issuer"
    export DORC_JWT_AUDIENCE="your-audience"
    python scripts/generate_jwt.py --tenant scott

    # Option 2: Pass everything as arguments
    python scripts/generate_jwt.py \
        --secret "your-secret" \
        --issuer "your-issuer" \
        --audience "your-audience" \
        --tenant scott

    # Note: The SDK does NOT generate tokens per CONTRACT.md.
    # This script is for testing/dev only.
"""

import argparse
import os
import sys
from pathlib import Path

import time

try:
    import jwt as pyjwt
except ImportError:
    print("ERROR: PyJWT is required. Install with: pip install PyJWT", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a test JWT token for dorc-mcp service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use environment variables
  export DORC_JWT_SECRET="my-secret"
  export DORC_JWT_ISSUER="my-issuer"
  export DORC_JWT_AUDIENCE="my-audience"
  python scripts/generate_jwt.py --tenant scott

  # Pass everything as arguments
  python scripts/generate_jwt.py \\
      --secret "my-secret" \\
      --issuer "my-issuer" \\
      --audience "my-audience" \\
      --tenant scott \\
      --subject user-123

  # Copy the token to use it
  export DORC_JWT="$(python scripts/generate_jwt.py --tenant scott --quiet)"
        """
    )
    
    parser.add_argument(
        "--secret",
        default=os.getenv("DORC_JWT_SECRET") or os.getenv("JWT_SECRET"),
        help="JWT secret (or set DORC_JWT_SECRET env var)",
    )
    parser.add_argument(
        "--issuer",
        default=os.getenv("DORC_JWT_ISSUER") or os.getenv("JWT_ISSUER"),
        help="JWT issuer (or set DORC_JWT_ISSUER env var)",
    )
    parser.add_argument(
        "--audience",
        default=os.getenv("DORC_JWT_AUDIENCE") or os.getenv("JWT_AUDIENCE"),
        help="JWT audience (or set DORC_JWT_AUDIENCE env var)",
    )
    parser.add_argument(
        "--tenant",
        default="scott",
        help="Tenant slug (default: scott)",
    )
    parser.add_argument(
        "--subject",
        default="test-user",
        help="Subject/user ID (default: test-user)",
    )
    parser.add_argument(
        "--ttl",
        type=int,
        default=3600,
        help="Token lifetime in seconds (default: 3600 = 1 hour)",
    )
    parser.add_argument(
        "--scope",
        default="read write",
        help="Scope string (default: 'read write')",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only output the token (for use in scripts)",
    )
    
    args = parser.parse_args()
    
    # Validate required arguments
    if not args.secret:
        print("ERROR: --secret is required (or set DORC_JWT_SECRET env var)", file=sys.stderr)
        print("\nTo find your JWT configuration:", file=sys.stderr)
        print("  1. Check your Cloud Run service environment variables", file=sys.stderr)
        print("  2. Look for DORC_JWT_SECRET, DORC_JWT_ISSUER, DORC_JWT_AUDIENCE", file=sys.stderr)
        return 1
    
    if not args.issuer:
        print("ERROR: --issuer is required (or set DORC_JWT_ISSUER env var)", file=sys.stderr)
        return 1
    
    if not args.audience:
        print("ERROR: --audience is required (or set DORC_JWT_AUDIENCE env var)", file=sys.stderr)
        return 1
    
    # Generate token (test/dev script - not part of SDK per CONTRACT.md)
    try:
        now = int(time.time())
        exp = now + args.ttl
        
        # Contract: iss, sub, tenant, scope, iat, exp
        claims = {
            "iss": args.issuer,
            "aud": args.audience,
            "sub": args.subject,
            "tenant": args.tenant,  # Contract uses "tenant" not "tenant_slug"
            "iat": now,
            "exp": exp,
        }
        
        if args.scope:
            # Contract: scope is a list of allowed operations
            if isinstance(args.scope, str):
                claims["scope"] = [s.strip() for s in args.scope.split() if s.strip()]
            else:
                claims["scope"] = args.scope
        else:
            claims["scope"] = ["read", "write"]  # Default scope
        
        token = pyjwt.encode(claims, args.secret, algorithm="HS256")
    except Exception as e:
        print(f"ERROR: Failed to generate JWT: {e}", file=sys.stderr)
        return 1
    
    if args.quiet:
        # Just output the token for use in scripts
        print(token)
        return 0
    
    # Output token and info
    print("=" * 60)
    print("Generated JWT Token")
    print("=" * 60)
    print()
    print(token)
    print()
    print("=" * 60)
    print("Configuration")
    print("=" * 60)
    print(f"  Secret: {args.secret[:20]}... (truncated)")
    print(f"  Issuer: {args.issuer}")
    print(f"  Audience: {args.audience}")
    print()
    print("=" * 60)
    print("Token Claims")
    print("=" * 60)
    print(f"  tenant_slug: {args.tenant}")
    print(f"  subject: {args.subject}")
    print(f"  scope: {args.scope}")
    print(f"  TTL: {args.ttl} seconds ({args.ttl // 3600} hours)")
    print()
    print("=" * 60)
    print("Usage")
    print("=" * 60)
    print(f'  export DORC_JWT="{token}"')
    print()
    print("  # Or use it directly:")
    print(f'  python test_integration_standalone.py')
    print()
    print("  # Or with curl:")
    print(f'  curl -H "Authorization: Bearer {token}" \\')
    print(f'       https://your-mcp-url.run.app/v1/validate \\')
    print(f'       -d \'{{"mode":"audit","candidate":{{"content":"test"}}}}\'')
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

