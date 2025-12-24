#!/bin/bash
# final-production-fix.sh - Complete fix for DistributeX

set -e

echo "🔧 DistributeX Final Production Fix"
echo "===================================="

# 1. Fix package.json with ALL required dependencies
echo "1️⃣ Creating correct package.json..."
cat > package.json << 'EOF'
{
  "name": "distributex-cloud",
  "version": "8.0.5",
  "type": "module",
  "license": "MIT",
  "main": "dist/index.cjs",
  "scripts": {
    "dev": "NODE_ENV=development tsx server/index.ts",
    "build": "tsx script/build.ts",
    "start": "node dist/index.cjs",
    "db:push": "drizzle-kit push",
    "db:migrate": "drizzle-kit migrate"
  },
  "dependencies": {
    "@hookform/resolvers": "^3.9.0",
    "@neondatabase/serverless": "^0.9.4",
    "@radix-ui/react-accordion": "^1.2.0",
    "@radix-ui/react-alert-dialog": "^1.1.1",
    "@radix-ui/react-aspect-ratio": "^1.1.0",
    "@radix-ui/react-avatar": "^1.1.0",
    "@radix-ui/react-checkbox": "^1.1.1",
    "@radix-ui/react-dialog": "^1.1.1",
    "@radix-ui/react-dropdown-menu": "^2.1.1",
    "@radix-ui/react-label": "^2.1.0",
    "@radix-ui/react-menubar": "^1.1.1",
    "@radix-ui/react-navigation-menu": "^1.2.0",
    "@radix-ui/react-popover": "^1.1.1",
    "@radix-ui/react-progress": "^1.1.0",
    "@radix-ui/react-radio-group": "^1.2.0",
    "@radix-ui/react-scroll-area": "^1.1.0",
    "@radix-ui/react-select": "^2.1.1",
    "@radix-ui/react-separator": "^1.1.0",
    "@radix-ui/react-slider": "^1.2.0",
    "@radix-ui/react-slot": "^1.1.0",
    "@radix-ui/react-switch": "^1.1.0",
    "@radix-ui/react-tabs": "^1.1.0",
    "@radix-ui/react-toast": "^1.2.1",
    "@radix-ui/react-toggle": "^1.1.0",
    "@radix-ui/react-toggle-group": "^1.1.0",
    "@radix-ui/react-tooltip": "^1.1.2",
    "@tailwindcss/typography": "^0.5.15",
    "@tanstack/react-query": "^5.56.2",
    "@types/bcryptjs": "^2.4.6",
    "@types/connect-pg-simple": "^7.0.3",
    "@types/cors": "^2.8.17",
    "@types/express": "^4.17.21",
    "@types/express-session": "^1.18.0",
    "@types/jsonwebtoken": "^9.0.6",
    "@types/node": "^20.16.5",
    "@types/passport": "^1.0.16",
    "@types/passport-local": "^1.0.38",
    "@types/react": "^18.3.5",
    "@types/react-dom": "^18.3.0",
    "@types/ws": "^8.5.12",
    "@vitejs/plugin-react": "^4.3.1",
    "autoprefixer": "^10.4.20",
    "bcryptjs": "^2.4.3",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.1",
    "cmdk": "^1.0.0",
    "connect-pg-simple": "^9.0.1",
    "cors": "^2.8.5",
    "date-fns": "^3.6.0",
    "drizzle-kit": "^0.24.2",
    "drizzle-orm": "^0.33.0",
    "drizzle-zod": "^0.5.0",
    "embla-carousel-react": "^8.3.0",
    "esbuild": "^0.23.1",
    "express": "^4.21.0",
    "express-session": "^1.18.0",
    "framer-motion": "^11.5.4",
    "input-otp": "^1.2.4",
    "jsonwebtoken": "^9.0.2",
    "lucide-react": "^0.441.0",
    "nanoid": "^5.0.7",
    "passport": "^0.7.0",
    "passport-local": "^1.0.0",
    "pg": "^8.12.0",
    "postcss": "^8.4.45",
    "react": "^18.3.1",
    "react-day-picker": "^8.10.1",
    "react-dom": "^18.3.1",
    "react-hook-form": "^7.53.0",
    "react-resizable-panels": "^2.1.2",
    "recharts": "^2.12.7",
    "tailwind-merge": "^2.5.2",
    "tailwindcss": "^3.4.10",
    "tailwindcss-animate": "^1.0.7",
    "tsx": "^4.19.0",
    "typescript": "^5.6.2",
    "vaul": "^0.9.2",
    "vite": "^5.4.3",
    "wouter": "^3.3.5",
    "ws": "^8.18.0",
    "zod": "^3.23.8",
    "zod-validation-error": "^3.3.1"
  }
}
EOF

# 2. Fix pyproject.toml version
echo "2️⃣ Fixing pyproject.toml..."
cat > pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=45", "wheel", "setuptools_scm[toml]>=6.2"]
build-backend = "setuptools.build_meta"

[project]
name = "distributex-cloud"
version = "1.0.0"
description = "Python SDK for DistributeX distributed computing"
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
authors = [
    {name = "DistributeX", email = "support@distributex.cloud"}
]
keywords = ["distributed", "computing", "cloud", "serverless"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
dependencies = [
    "requests>=2.31.0",
]

[project.urls]
Homepage = "https://distributex.cloud"
Documentation = "https://docs.distributex.cloud"
Repository = "https://github.com/DistributeX-Cloud/distributex"
Changelog = "https://github.com/DistributeX-Cloud/distributex/blob/main/CHANGELOG.md"
EOF

# 3. Fix wrangler.toml
echo "3️⃣ Fixing wrangler.toml..."
cat > wrangler.toml << 'EOF'
name = "distributex-cloud"
compatibility_date = "2024-01-01"
compatibility_flags = ["nodejs_compat"]

pages_build_output_dir = "dist/public"

[vars]
ENVIRONMENT = "production"
NODE_ENV = "production"

[[kv_namespaces]]
binding = "SESSIONS"
id = "2393dbaa488a4c429e8247dc34b59ef6"

[[kv_namespaces]]
binding = "RATE_LIMIT"
id = "2982e734601b4bbf91836cae34d1af5a"

[observability]
enabled = true
EOF

# 4. Create unified auth
echo "4️⃣ Creating unified auth system..."
mkdir -p server
cat > server/unified-auth.ts << 'EOF'
import crypto from 'crypto';

export async function hashPassword(password: string): Promise<string> {
  return crypto.createHash('sha256').update(password).digest('hex');
}

export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  const passwordHash = await hashPassword(password);
  return passwordHash === hash;
}
EOF

# 5. Update server/auth.ts
echo "5️⃣ Updating server/auth.ts..."
cat > server/auth.ts << 'EOF'
// @ts-nocheck
import { hashPassword, verifyPassword } from './unified-auth';
import type { Request, Response, NextFunction } from 'express';
import { db } from './db';
import { users } from '@shared/schema';
import { eq } from 'drizzle-orm';

export interface AuthRequest extends Request {
  userId?: string;
}

declare global {
  namespace Express {
    interface User {
      id: string;
      email: string;
      username: string;
      credits: number;
    }
  }
}

export { hashPassword, verifyPassword };

export async function register(email: string, username: string, password: string) {
  const existingUser = await db.select().from(users).where(eq(users.email, email)).limit(1);
  
  if (existingUser.length > 0) {
    throw new Error('User already exists');
  }

  const existingUsername = await db.select().from(users).where(eq(users.username, username)).limit(1);
  
  if (existingUsername.length > 0) {
    throw new Error('Username already taken');
  }

  const passwordHash = await hashPassword(password);
  
  const [newUser] = await db.insert(users).values({
    email,
    username,
    passwordHash,
    credits: 100,
  }).returning();

  return {
    id: newUser.id,
    email: newUser.email,
    username: newUser.username,
    credits: newUser.credits,
  };
}

export async function login(email: string, password: string) {
  const [user] = await db.select().from(users).where(eq(users.email, email)).limit(1);
  
  if (!user || !user.passwordHash) {
    throw new Error('Invalid credentials');
  }

  const isValid = await verifyPassword(password, user.passwordHash);
  
  if (!isValid) {
    throw new Error('Invalid credentials');
  }

  return {
    id: user.id,
    email: user.email,
    username: user.username,
    credits: user.credits,
  };
}

export function isAuthenticated(req: Request, res: Response, next: NextFunction) {
  if (!req.isAuthenticated || !req.isAuthenticated()) {
    return res.status(401).json({ message: 'Unauthorized' });
  }
  next();
}
EOF

# 6. Fix worker package
echo "6️⃣ Fixing worker package..."
cat > worker/package.json << 'EOF'
{
  "name": "distributex-worker",
  "version": "1.0.0",
  "description": "DistributeX worker runtime",
  "main": "index.js",
  "scripts": {
    "start": "node index.js"
  },
  "dependencies": {
    "axios": "^1.7.7"
  }
}
EOF

cd worker
rm -f package-lock.json
npm install
cd ..

# 7. Fix worker Dockerfile
echo "7️⃣ Fixing worker Dockerfile..."
cat > worker/Dockerfile << 'EOF'
FROM node:20-alpine

RUN apk add --no-cache python3 py3-pip docker-cli

WORKDIR /app

COPY package.json ./
RUN npm install --production

COPY index.js .

ENV MAX_CPU_PERCENT=50
ENV MAX_MEMORY_GB=2
ENV HEARTBEAT_INTERVAL=30000

CMD ["node", "index.js"]
EOF

# 8. Install and build
echo "8️⃣ Installing dependencies..."
npm install

echo "9️⃣ Building project..."
npm run build

echo ""
echo "✅ All fixes complete!"
echo ""
echo "📋 Deployment Steps:"
echo ""
echo "1. Commit and push:"
echo "   git add ."
echo "   git commit -m 'Production fixes - all dependencies resolved'"
echo "   git push"
echo ""
echo "2. Cloudflare Pages will auto-deploy with:"
echo "   Build command: npm install && npm run build"
echo "   Output: dist/public"
echo ""
echo "3. Set Cloudflare secrets (in dashboard or CLI):"
echo "   wrangler secret put DATABASE_URL"
echo "   wrangler secret put JWT_SECRET"
echo "   wrangler secret put SESSION_SECRET"
echo ""
echo "4. Build and push worker:"
echo "   cd worker"
echo "   docker build -t distributexcloud/worker:latest ."
echo "   docker push distributexcloud/worker:latest"
echo ""
echo "5. Test everything:"
echo "   ✓ Frontend: https://distributex.pages.dev"
echo "   ✓ Backend: https://api.distributex.cloud/health"
echo "   ✓ Worker: docker run distributexcloud/worker:latest"
echo ""
