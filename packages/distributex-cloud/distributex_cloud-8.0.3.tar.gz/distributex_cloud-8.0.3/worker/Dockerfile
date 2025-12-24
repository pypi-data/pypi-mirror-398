FROM node:20-alpine

# System deps
RUN apk add --no-cache python3 py3-pip docker-cli

WORKDIR /app

# Install Node deps
COPY package.json package-lock.json ./
RUN npm ci --production

# Copy worker code
COPY index.js .

ENV MAX_CPU_PERCENT=50
ENV MAX_MEMORY_GB=2
ENV HEARTBEAT_INTERVAL=30000

CMD ["node", "index.js"]
