#!/bin/bash
# DistributeX Worker Installer
# Usage: curl https://distributex.cloud/install-worker.sh | bash

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║         DistributeX Worker Installer v1.0.0              ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found${NC}"
    echo ""
    echo "Install Docker:"
    echo "  macOS/Windows: https://docker.com/products/docker-desktop"
    echo "  Linux: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

echo -e "${GREEN}✓ Docker found${NC}"

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker daemon not running${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker running${NC}"
echo ""

# Get API key
echo -e "${YELLOW}Get your API key from: https://distributex.cloud/dashboard${NC}"
echo ""
read -p "Enter API Key: " API_KEY

if [ -z "$API_KEY" ]; then
    echo -e "${RED}❌ API key required${NC}"
    exit 1
fi

# Optional settings
read -p "API URL [https://distributex-production-7fd2.up.railway.app]: " API_URL
API_URL=${API_URL:-https://distributex-production-7fd2.up.railway.app}

read -p "Max CPU % [50]: " MAX_CPU
MAX_CPU=${MAX_CPU:-50}

read -p "Max Memory GB [2]: " MAX_MEM
MAX_MEM=${MAX_MEM:-2}

echo ""
echo "🛑 Stopping existing worker..."
docker stop distributex-worker 2>/dev/null || true
docker rm distributex-worker 2>/dev/null || true

echo "📦 Pulling latest image..."
docker pull distributexcloud/worker:latest

echo "🚀 Starting worker..."
docker run -d \
  --name distributex-worker \
  --restart unless-stopped \
  -e API_KEY="${API_KEY}" \
  -e API_URL="${API_URL}" \
  -e MAX_CPU_PERCENT="${MAX_CPU}" \
  -e MAX_MEMORY_GB="${MAX_MEM}" \
  -v /var/run/docker.sock:/var/run/docker.sock \
  distributexcloud/worker:latest

echo ""
echo -e "${GREEN}✅ Worker installed and running!${NC}"
echo ""
echo "Commands:"
echo "  View logs:    docker logs -f distributex-worker"
echo "  Stop:         docker stop distributex-worker"
echo "  Start:        docker start distributex-worker"
echo "  Remove:       docker rm -f distributex-worker"
echo ""
echo "Dashboard: https://distributex.cloud/dashboard"
