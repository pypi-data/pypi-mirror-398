# worker/Dockerfile - OPTIMIZED WITH DNS FIX
FROM node:20-alpine

# Install dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    docker-cli \
    bind-tools \
    curl

WORKDIR /app

# Copy package files
COPY package.json ./
RUN npm install --production

# Copy worker code
COPY index.js .

# Environment defaults
ENV MAX_CPU_PERCENT=50
ENV MAX_MEMORY_GB=2
ENV HEARTBEAT_INTERVAL=30000

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

CMD ["node", "index.js"]
