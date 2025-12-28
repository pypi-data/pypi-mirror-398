#!/usr/bin/env python3
"""Check JWT configuration in deployed Cloud Run service.

This script uses gcloud to check what JWT configuration is set in your
deployed dorc-mcp Cloud Run service.

Usage:
    python scripts/check_jwt_config.py
"""

import json
import os
import subprocess
import sys


def run_gcloud_command(args):
    """Run a gcloud command and return the output."""
    try:
        result = subprocess.run(
            ["gcloud"] + args,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"ERROR: gcloud command failed: {e.stderr}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("ERROR: gcloud CLI not found. Install it from https://cloud.google.com/sdk", file=sys.stderr)
        return None


def get_service_env_vars(project_id, region, service_name):
    """Get environment variables from Cloud Run service."""
    args = [
        "run",
        "services",
        "describe",
        service_name,
        "--region",
        region,
        "--project",
        project_id,
        "--format",
        "json",
    ]
    
    output = run_gcloud_command(args)
    if not output:
        return None
    
    try:
        service_data = json.loads(output)
        containers = service_data.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
        if not containers:
            return None
        
        env_vars = {}
        for env in containers[0].get("env", []):
            name = env.get("name")
            value = env.get("value")
            if name and value:
                env_vars[name] = value
            elif name:
                # Might be a secret reference
                secret_ref = env.get("valueSource", {}).get("secretKeyRef", {})
                if secret_ref:
                    secret_name = secret_ref.get("secret")
                    env_vars[name] = f"[Secret: {secret_name}]"
        
        return env_vars
    except json.JSONDecodeError:
        print("ERROR: Failed to parse gcloud output", file=sys.stderr)
        return None


def main():
    project_id = os.getenv("PROJECT_ID", "dorc-481715")
    region = os.getenv("REGION", "us-east1")
    service_name = os.getenv("SERVICE", "dorc-mcp")
    
    print("=" * 60)
    print(f"Checking JWT Configuration")
    print("=" * 60)
    print(f"Project: {project_id}")
    print(f"Region: {region}")
    print(f"Service: {service_name}")
    print()
    
    env_vars = get_service_env_vars(project_id, region, service_name)
    
    if not env_vars:
        print("ERROR: Could not retrieve service configuration.")
        print()
        print("Troubleshooting:")
        print("  1. Make sure you're authenticated: gcloud auth login")
        print("  2. Make sure you have permission to view Cloud Run services")
        print("  3. Check that the service name is correct")
        return 1
    
    # Check for JWT-related variables
    jwt_secret = env_vars.get("DORC_JWT_SECRET") or env_vars.get("JWT_SECRET")
    jwt_issuer = env_vars.get("DORC_JWT_ISSUER") or env_vars.get("JWT_ISSUER")
    jwt_audience = env_vars.get("DORC_JWT_AUDIENCE") or env_vars.get("JWT_AUDIENCE")
    auth_mode = env_vars.get("AUTH_MODE", "jwt")
    
    print("JWT Configuration:")
    print("-" * 60)
    
    if auth_mode == "none":
        print("✅ AUTH_MODE=none - No JWT required!")
        print()
        print("You can test without a JWT token:")
        print("  export DORC_MCP_URL=\"https://your-service.run.app\"")
        print("  python test_integration_standalone.py")
        return 0
    
    if jwt_secret:
        if jwt_secret.startswith("[Secret:"):
            print(f"  DORC_JWT_SECRET: {jwt_secret}")
            print("    ⚠️  This is stored in Secret Manager")
            print("    Get it with: gcloud secrets versions access latest --secret=<secret-name>")
        else:
            print(f"  DORC_JWT_SECRET: {jwt_secret[:20]}... (truncated)")
    else:
        print("  DORC_JWT_SECRET: ❌ NOT SET")
    
    if jwt_issuer:
        print(f"  DORC_JWT_ISSUER: {jwt_issuer}")
    else:
        print("  DORC_JWT_ISSUER: ❌ NOT SET")
    
    if jwt_audience:
        print(f"  DORC_JWT_AUDIENCE: {jwt_audience}")
    else:
        print("  DORC_JWT_AUDIENCE: ❌ NOT SET")
    
    print()
    print("AUTH_MODE:", auth_mode)
    print()
    
    if jwt_secret and jwt_issuer and jwt_audience:
        print("=" * 60)
        print("✅ All JWT values found!")
        print("=" * 60)
        print()
        print("To generate a token, run:")
        print()
        if not jwt_secret.startswith("[Secret:"):
            print(f"  export DORC_JWT_SECRET=\"{jwt_secret}\"")
        print(f"  export DORC_JWT_ISSUER=\"{jwt_issuer}\"")
        print(f"  export DORC_JWT_AUDIENCE=\"{jwt_audience}\"")
        print("  python scripts/generate_jwt.py --tenant scott")
        print()
    else:
        print("=" * 60)
        print("⚠️  JWT configuration incomplete")
        print("=" * 60)
        print()
        print("Missing values need to be set in Cloud Run.")
        print("Check your Terraform variables or deployment configuration.")
        print()
        print("If values are in Secret Manager, retrieve them with:")
        print("  gcloud secrets list --project", project_id)
        print("  gcloud secrets versions access latest --secret=<secret-name>")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

