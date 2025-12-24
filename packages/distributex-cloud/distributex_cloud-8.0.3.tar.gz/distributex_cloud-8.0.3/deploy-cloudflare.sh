#!/bin/bash
# deploy-cloudflare.sh - Deploy fixed Cloudflare Worker

set -e

echo "🚀 Deploying Cloudflare Worker with JWT fix..."

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo "Installing wrangler..."
    npm install -g wrangler
fi

# Check auth
if ! wrangler whoami &> /dev/null; then
    echo "Please login to Cloudflare:"
    wrangler login
fi

# Deploy the worker
echo "Deploying worker..."
wrangler deploy functions/api/[[path]].ts

echo "✅ Cloudflare Worker deployed!"
echo ""
echo "Set environment variables in Cloudflare dashboard:"
echo "  - DATABASE_URL"
echo "  - JWT_SECRET"
echo "  - SESSION_SECRET"
echo ""
echo "Or use wrangler:"
echo "  wrangler secret put DATABASE_URL"
echo "  wrangler secret put JWT_SECRET"
echo "  wrangler secret put SESSION_SECRET"
echo ""
echo "Test the worker at: https://api.distributex.cloud/api/health"
