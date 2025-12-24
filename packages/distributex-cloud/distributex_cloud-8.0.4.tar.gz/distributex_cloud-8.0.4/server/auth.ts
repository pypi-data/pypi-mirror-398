// server/auth.ts - COMPLETE WITH checkApiKey
import { hashPassword, verifyPassword } from './unified-auth';
import crypto from 'crypto';
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
      role: string;
      apiKey: string | null;
    }
  }
}

export { hashPassword, verifyPassword };

// REGISTER - Generate API key on registration
export async function register(
  email: string, 
  username: string, 
  password: string, 
  role?: string
) {
  // Check existing user
  const existingUser = await db
    .select()
    .from(users)
    .where(eq(users.email, email))
    .limit(1);
  
  if (existingUser.length > 0) {
    throw new Error('User already exists');
  }

  const existingUsername = await db
    .select()
    .from(users)
    .where(eq(users.username, username))
    .limit(1);
  
  if (existingUsername.length > 0) {
    throw new Error('Username already taken');
  }

  // Hash password and generate API key
  const passwordHash = await hashPassword(password);
  const apiKey = `dsx_${crypto.randomUUID().replace(/-/g, '')}`;
  
  console.log('🔑 Generated API Key:', apiKey);
  
  // Insert and return with Drizzle ORM
  const [newUser] = await db
    .insert(users)
    .values({
      email,
      username,
      passwordHash,
      role: role || 'developer',
      apiKey, // This will be mapped to api_key in DB
      isActive: true,
    })
    .returning();

  console.log('✅ User created with API key:', {
    id: newUser.id,
    email: newUser.email,
    hasApiKey: !!newUser.apiKey,
    apiKeyPreview: newUser.apiKey ? `${newUser.apiKey.slice(0, 15)}...` : 'NONE'
  });

  return {
    id: newUser.id,
    email: newUser.email,
    username: newUser.username,
    role: newUser.role,
    apiKey: newUser.apiKey,
  };
}

// LOGIN
export async function login(email: string, password: string) {
  // Use Drizzle ORM select
  const [user] = await db
    .select({
      id: users.id,
      email: users.email,
      username: users.username,
      role: users.role,
      apiKey: users.apiKey, // Drizzle auto-maps api_key -> apiKey
      passwordHash: users.passwordHash,
    })
    .from(users)
    .where(eq(users.email, email))
    .limit(1);
  
  if (!user || !user.passwordHash) {
    throw new Error('Invalid credentials');
  }

  const isValid = await verifyPassword(password, user.passwordHash);
  
  if (!isValid) {
    throw new Error('Invalid credentials');
  }

  console.log('✅ Login successful:', {
    id: user.id,
    email: user.email,
    hasApiKey: !!user.apiKey,
    apiKeyPreview: user.apiKey ? `${user.apiKey.slice(0, 15)}...` : 'NONE'
  });

  return {
    id: user.id,
    email: user.email,
    username: user.username,
    role: user.role,
    apiKey: user.apiKey,
  };
}

// SESSION AUTHENTICATION MIDDLEWARE
export function isAuthenticated(req: Request, res: Response, next: NextFunction) {
  if (!req.isAuthenticated || !req.isAuthenticated()) {
    return res.status(401).json({ message: 'Unauthorized' });
  }
  next();
}

// API KEY AUTHENTICATION MIDDLEWARE (for workers)
export async function checkApiKey(req: Request, res: Response, next: NextFunction) {
  try {
    // 1. Extract API Key from various sources
    const headerKey = req.headers['x-api-key'] as string;
    const bearerKey = req.headers['authorization']?.startsWith('Bearer ') 
      ? req.headers['authorization'].split(' ')[1] 
      : null;
    const queryKey = req.query.api_key as string;

    const apiKey = headerKey || bearerKey || queryKey;
    
    // Log extraction source for debugging
    const source = headerKey ? 'X-API-KEY' : bearerKey ? 'Bearer' : queryKey ? 'Query' : 'None';
    console.log(`🔍 API Key Auth Attempt [Source: ${source}]`);

    if (!apiKey) {
      console.warn('⚠️ Access Denied: No API key provided');
      return res.status(401).json({ message: 'API key is required' });
    }

    // 2. Query User
    const [user] = await db
      .select({
        id: users.id,
        email: users.email,
        username: users.username,
        role: users.role,
        apiKey: users.apiKey,
      })
      .from(users)
      .where(eq(users.apiKey, apiKey))
      .limit(1);

    if (!user) {
      console.error(`❌ Access Denied: Invalid key (${apiKey.slice(0, 8)}...)`);
      return res.status(401).json({ message: 'Invalid API key' });
    }

    // 3. Success
    console.log(`✅ API Authenticated: ${user.username} (${user.role})`);

    // Attach user to request
    req.user = user;
    next();
  } catch (error) {
    console.error('💥 API Key Auth Error:', error);
    res.status(500).json({ message: 'Internal server error during authentication' });
  }
}
