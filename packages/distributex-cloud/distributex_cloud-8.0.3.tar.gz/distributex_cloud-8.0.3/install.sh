#!/bin/bash
# install.sh - installer for local worker (starts the distributex-worker container)

set -euo pipefail

echo "🚀 DistributeX Worker Installer"
echo "================================"

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✓ Docker found"

# Get worker token
read -r -p "Enter your worker token (from dashboard): " WORKER_TOKEN

if [ -z "$WORKER_TOKEN" ]; then
    echo "❌ Worker token required"
    exit 1
fi

# Pull latest worker image
echo "📥 Pulling latest worker image..."
docker pull distributex/worker:latest || true

# Stop existing worker if running
docker stop distributex-worker 2>/dev/null || true
docker rm distributex-worker 2>/dev/null || true

# Start worker
echo "🎬 Starting worker..."
docker run -d \
  --name distributex-worker \
  --restart unless-stopped \
  -e WORKER_TOKEN="$WORKER_TOKEN" \
  -e API_URL="https://api.distributex.cloud" \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --memory="2g" \
  --cpus="2" \
  distributex/worker:latest

echo ""
echo "✅ Worker installed and running!"
echo ""
echo "Commands:"
echo "  View logs: docker logs -f distributex-worker"
echo "  Stop worker: docker stop distributex-worker"
echo "  Start worker: docker start distributex-worker"
echo "  Uninstall: docker rm -f distributex-worker"
echo ""
echo "Dashboard: https://distributex.cloud/dashboard"
