#!/bin/bash
# Check JWT configuration in deployed Cloud Run service

PROJECT_ID="${PROJECT_ID:-dorc-481715}"
REGION="${REGION:-us-east1}"
SERVICE="${SERVICE:-dorc-mcp}"

echo "Checking JWT configuration for $SERVICE in $REGION..."
echo ""

# Get the service configuration
gcloud run services describe "$SERVICE" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --format="get(spec.template.spec.containers[0].env)" 2>/dev/null | \
  grep -E "(DORC_JWT|AUTH_MODE)" || {
    echo "ERROR: Could not get service configuration."
    echo "Make sure you're authenticated: gcloud auth login"
    echo "And have permission to view Cloud Run services."
    exit 1
  }

echo ""
echo "If you see the values above, copy them and use:"
echo "  export DORC_JWT_SECRET=\"<value>\""
echo "  export DORC_JWT_ISSUER=\"<value>\""
echo "  export DORC_JWT_AUDIENCE=\"<value>\""
echo ""
echo "Then generate a token with:"
echo "  python scripts/generate_jwt.py --tenant scott"

