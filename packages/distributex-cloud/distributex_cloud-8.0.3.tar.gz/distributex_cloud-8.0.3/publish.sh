#!/bin/bash
# publish.sh - Publish all DistributeX packages and frontend

set -e

echo "🚀 DistributeX Publishing Script"
echo "=================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Parse arguments
PUBLISH_PYTHON=false
PUBLISH_NPM=false
PUBLISH_DOCKER=false
PUBLISH_FRONTEND=false
UNPUBLISH_OLD=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --python) PUBLISH_PYTHON=true ;;
    --npm) PUBLISH_NPM=true ;;
    --docker) PUBLISH_DOCKER=true ;;
    --frontend) PUBLISH_FRONTEND=true ;;
    --unpublish-old) UNPUBLISH_OLD=true ;;
    --all)
      PUBLISH_PYTHON=true
      PUBLISH_NPM=true
      PUBLISH_DOCKER=true
      PUBLISH_FRONTEND=true
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: ./publish.sh [--python] [--npm] [--docker] [--frontend] [--all] [--unpublish-old]"
      exit 1
      ;;
  esac
  shift
done

# Check if no options provided
if ! $PUBLISH_PYTHON && ! $PUBLISH_NPM && ! $PUBLISH_DOCKER && ! $PUBLISH_FRONTEND; then
  echo "Usage: ./publish.sh [--python] [--npm] [--docker] [--frontend] [--all] [--unpublish-old]"
  exit 1
fi

# ============================================
# Unpublish Old Packages
# ============================================
if $UNPUBLISH_OLD; then
  echo -e "\n${YELLOW}📦 Unpublishing old packages...${NC}"
  
  # Unpublish old npm package (requires confirmation)
  if command -v npm &> /dev/null; then
    echo "To unpublish old npm packages, run manually:"
    echo "  npm unpublish distributex-js@<version> --force"
    echo "  npm deprecate distributex-js 'Package deprecated, use @distributex/sdk instead'"
  fi
  
  # Note: PyPI doesn't allow deletion, only yanking
  echo "To yank old Python packages, visit: https://pypi.org/manage/project/distributex-old/"
  echo "Or run: pip install pkginfo twine && twine yank distributex-old <version>"
fi

# ============================================
# 1. Publish Python Package to PyPI
# ============================================
if $PUBLISH_PYTHON; then
  echo -e "\n${GREEN}🐍 Publishing Python package to PyPI...${NC}"
  
  # Check for required tools
  if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
  fi
  
  # Install build tools
  echo "Installing build dependencies..."
  python3 -m pip install --upgrade pip build twine
  
  # Clean old builds
  echo "Cleaning old builds..."
  rm -rf dist/ build/ *.egg-info/
  
  # Build package
  echo "Building package..."
  python3 -m build
  
  # Check package
  echo "Checking package..."
  python3 -m twine check dist/*
  
  # Upload to PyPI (requires credentials)
  echo -e "${YELLOW}Uploading to PyPI...${NC}"
  echo "You'll need your PyPI API token"
  python3 -m twine upload dist/*
  
  echo -e "${GREEN}✓ Python package published!${NC}"
  echo "Install with: pip install distributex-cloud"
fi

# ============================================
# 2. Publish NPM Package
# ============================================
if $PUBLISH_NPM; then
  echo -e "\n${GREEN}📦 Publishing NPM package...${NC}"
  
  # Check for npm
  if ! command -v npm &> /dev/null; then
    echo -e "${RED}✗ npm not found${NC}"
    exit 1
  fi
  
  # Check if logged in
  if ! npm whoami &> /dev/null; then
    echo -e "${YELLOW}Not logged into npm. Run: npm login${NC}"
    exit 1
  fi
  
  # Build TypeScript package
  echo "Building TypeScript package..."
  npm run build
  
  # Publish to npm
  echo "Publishing to npm..."
  cd src
  npm publish --access public
  cd ..
  
  echo -e "${GREEN}✓ NPM package published!${NC}"
  echo "Install with: npm install distributex-cloud"
fi

# ============================================
# 3. Build & Push Docker Image
# ============================================
if $PUBLISH_DOCKER; then
  echo -e "\n${GREEN}🐳 Building and pushing Docker image...${NC}"
  
  # Check for Docker
  if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found${NC}"
    exit 1
  fi
  
  # Check if logged in
  if ! docker info &> /dev/null; then
    echo -e "${YELLOW}Docker daemon not running${NC}"
    exit 1
  fi
  
  # Build worker image
  echo "Building worker Docker image..."
  cd worker
  docker build -t distributexcloud/worker:latest -t distributexcloud/worker:1.0.0 .
  cd ..
  
  # Push to Docker Hub
  echo "Pushing to Docker Hub..."
  echo "Make sure you're logged in: docker login"
  
  docker push distributexcloud/worker:latest
  docker push distributexcloud/worker:1.0.0
  
  echo -e "${GREEN}✓ Docker image published!${NC}"
  echo "Pull with: docker pull distributexcloud/worker:latest"
fi

# ============================================
# 4. Deploy Frontend to Cloudflare Pages
# ============================================
if $PUBLISH_FRONTEND; then
  echo -e "\n${GREEN}☁️  Deploying frontend to Cloudflare Pages...${NC}"
  
  # Check for wrangler
  if ! command -v wrangler &> /dev/null; then
    echo "Installing Wrangler CLI..."
    npm install -g wrangler
  fi
  
  # Check auth
  if ! wrangler whoami &> /dev/null; then
    echo -e "${YELLOW}Not logged into Cloudflare. Run: wrangler login${NC}"
    exit 1
  fi
  
  # Build frontend
  echo "Building frontend..."
  npm run build
  
  # Deploy to Cloudflare Pages
  echo "Deploying to Cloudflare Pages..."
  wrangler pages deploy dist/public --project-name=distributex --branch=main
  
  echo -e "${GREEN}✓ Frontend deployed!${NC}"
  echo "Visit: https://distributex.pages.dev"
fi

echo -e "\n${GREEN}🎉 Publishing complete!${NC}"
echo ""
echo "Next steps:"
echo "  • Test Python SDK: pip install distributex"
echo "  • Test NPM SDK: npm install distributex"
echo "  • Pull Docker worker: docker pull distributex/worker:latest"
echo "  • Visit frontend: https://distributex.pages.dev"
echo ""
