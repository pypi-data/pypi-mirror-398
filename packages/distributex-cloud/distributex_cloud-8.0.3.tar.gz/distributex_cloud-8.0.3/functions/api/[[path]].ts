// functions/api/[[path]].ts - FIXED Cloudflare Worker for DistributeX
import { neon } from '@neondatabase/serverless';

interface Env {
  DATABASE_URL: string;
  JWT_SECRET: string;
  SESSION_SECRET: string;
  SESSIONS: KVNamespace;
  RATE_LIMIT: KVNamespace;
}

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

// Rate limiting
async function checkRateLimit(env: Env, ip: string): Promise<boolean> {
  const key = `rate_limit:${ip}`;
  const count = await env.RATE_LIMIT.get(key);
  
  if (count && parseInt(count) > 100) {
    return false;
  }
  
  await env.RATE_LIMIT.put(key, String((parseInt(count || '0') + 1)), {
    expirationTtl: 60 // 1 minute
  });
  
  return true;
}

// JWT helper functions
function base64UrlEncode(str: string): string {
  return btoa(str)
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}

function base64UrlDecode(str: string): string {
  str = str.replace(/-/g, '+').replace(/_/g, '/');
  while (str.length % 4) {
    str += '=';
  }
  return atob(str);
}

async function generateJWT(payload: any, secret: string): Promise<string> {
  const header = {
    alg: 'HS256',
    typ: 'JWT'
  };

  const now = Math.floor(Date.now() / 1000);
  const claims = {
    ...payload,
    iat: now,
    exp: now + (7 * 24 * 60 * 60) // 7 days
  };

  const headerEncoded = base64UrlEncode(JSON.stringify(header));
  const payloadEncoded = base64UrlEncode(JSON.stringify(claims));
  const message = `${headerEncoded}.${payloadEncoded}`;

  const encoder = new TextEncoder();
  const data = encoder.encode(message);
  const keyData = encoder.encode(secret);

  const cryptoKey = await crypto.subtle.importKey(
    'raw',
    keyData,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );

  const signature = await crypto.subtle.sign('HMAC', cryptoKey, data);
  const signatureArray = new Uint8Array(signature);
  const signatureBase64 = base64UrlEncode(String.fromCharCode(...signatureArray));

  return `${message}.${signatureBase64}`;
}

async function verifyJWT(token: string, secret: string): Promise<any> {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;

    const [headerB64, payloadB64, signatureB64] = parts;
    const message = `${headerB64}.${payloadB64}`;

    const encoder = new TextEncoder();
    const data = encoder.encode(message);
    const keyData = encoder.encode(secret);

    const cryptoKey = await crypto.subtle.importKey(
      'raw',
      keyData,
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['verify']
    );

    const signatureBytes = Uint8Array.from(
      base64UrlDecode(signatureB64).split('').map(c => c.charCodeAt(0))
    );

    const valid = await crypto.subtle.verify('HMAC', cryptoKey, signatureBytes, data);

    if (!valid) return null;

    const payload = JSON.parse(base64UrlDecode(payloadB64));
    
    // Check expiration
    if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) {
      return null;
    }

    return payload;
  } catch (e) {
    console.error('JWT verification error:', e);
    return null;
  }
}

// Hash password using Web Crypto API
async function hashPassword(password: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(password);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

// Main request handler
export async function onRequest(context: any): Promise<Response> {
  const { request, env } = context;
  const url = new URL(request.url);
  const path = url.pathname;
  const method = request.method;

  console.log(`[${method}] ${path}`);

  // Handle CORS preflight
  if (method === 'OPTIONS') {
    return new Response(null, { 
      status: 204,
      headers: corsHeaders 
    });
  }

  // Rate limiting
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
  const allowed = await checkRateLimit(env, ip);
  if (!allowed) {
    return new Response(JSON.stringify({ error: 'Rate limit exceeded' }), {
      status: 429,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }

  // Database connection
  const sql = neon(env.DATABASE_URL);

  try {
    // ============================================
    // AUTH ENDPOINTS
    // ============================================
    
    // REGISTER
    if (path === '/api/auth/register' && method === 'POST') {
      const body = await request.json();
      const { email, username, password } = body;
      
      // Validate input
      if (!email || !username || !password) {
        return new Response(JSON.stringify({ 
          message: 'Email, username, and password are required' 
        }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }

      if (password.length < 8) {
        return new Response(JSON.stringify({ 
          message: 'Password must be at least 8 characters' 
        }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }

      // Check if user exists
      const existing = await sql`
        SELECT id FROM users 
        WHERE email = ${email} OR username = ${username}
      `;
      
      if (existing.length > 0) {
        return new Response(JSON.stringify({ 
          message: 'User with this email or username already exists' 
        }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }

      // Hash password
      const passwordHash = await hashPassword(password);

      // Create user
      const [user] = await sql`
        INSERT INTO users (email, username, password_hash, credits)
        VALUES (${email}, ${username}, ${passwordHash}, 100)
        RETURNING id, email, username, credits
      `;

      // Generate JWT
      const token = await generateJWT({ userId: user.id }, env.JWT_SECRET);

      // Store session in KV
      const sessionId = crypto.randomUUID();
      await env.SESSIONS.put(
        `session:${sessionId}`,
        JSON.stringify({ userId: user.id, email: user.email }),
        { expirationTtl: 7 * 24 * 60 * 60 }
      );

      return new Response(JSON.stringify({ 
        ...user, 
        token,
        sessionId 
      }), {
        status: 201,
        headers: { 
          ...corsHeaders, 
          'Content-Type': 'application/json',
          'Set-Cookie': `sessionId=${sessionId}; Path=/; HttpOnly; SameSite=None; Secure; Max-Age=${7 * 24 * 60 * 60}`
        }
      });
    }

    // LOGIN
    if (path === '/api/auth/login' && method === 'POST') {
      const body = await request.json();
      const { email, password } = body;

      if (!email || !password) {
        return new Response(JSON.stringify({ 
          message: 'Email and password are required' 
        }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }

      // Hash password
      const passwordHash = await hashPassword(password);

      // Find user
      const [user] = await sql`
        SELECT id, email, username, credits
        FROM users
        WHERE email = ${email} AND password_hash = ${passwordHash}
      `;

      if (!user) {
        return new Response(JSON.stringify({ 
          message: 'Invalid email or password' 
        }), {
          status: 401,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }

      // Generate JWT
      const token = await generateJWT({ userId: user.id }, env.JWT_SECRET);

      // Store session
      const sessionId = crypto.randomUUID();
      await env.SESSIONS.put(
        `session:${sessionId}`,
        JSON.stringify({ userId: user.id, email: user.email }),
        { expirationTtl: 7 * 24 * 60 * 60 }
      );

      return new Response(JSON.stringify({ 
        ...user, 
        token,
        sessionId 
      }), {
        status: 200,
        headers: { 
          ...corsHeaders, 
          'Content-Type': 'application/json',
          'Set-Cookie': `sessionId=${sessionId}; Path=/; HttpOnly; SameSite=None; Secure; Max-Age=${7 * 24 * 60 * 60}`
        }
      });
    }

    // LOGOUT
    if (path === '/api/auth/logout' && method === 'POST') {
      const cookieHeader = request.headers.get('Cookie');
      if (cookieHeader) {
        const sessionId = cookieHeader.split('sessionId=')[1]?.split(';')[0];
        if (sessionId) {
          await env.SESSIONS.delete(`session:${sessionId}`);
        }
      }

      return new Response(JSON.stringify({ message: 'Logged out' }), {
        headers: { 
          ...corsHeaders, 
          'Content-Type': 'application/json',
          'Set-Cookie': 'sessionId=; Path=/; HttpOnly; Max-Age=0'
        }
      });
    }

    // ============================================
    // PROTECTED ENDPOINTS
    // ============================================

    // Get auth from header or cookie
    let userId: string | null = null;

    // Try Authorization header first
    const authHeader = request.headers.get('Authorization');
    if (authHeader?.startsWith('Bearer ')) {
      const token = authHeader.substring(7);
      const payload = await verifyJWT(token, env.JWT_SECRET);
      if (payload) {
        userId = payload.userId;
      }
    }

    // Try cookie as fallback
    if (!userId) {
      const cookieHeader = request.headers.get('Cookie');
      if (cookieHeader) {
        const sessionId = cookieHeader.split('sessionId=')[1]?.split(';')[0];
        if (sessionId) {
          const session = await env.SESSIONS.get(`session:${sessionId}`);
          if (session) {
            const data = JSON.parse(session);
            userId = data.userId;
          }
        }
      }
    }

    // Get user info
    if (path === '/api/auth/user' && method === 'GET') {
      if (!userId) {
        return new Response(JSON.stringify({ message: 'Unauthorized' }), {
          status: 401,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }

      const [user] = await sql`
        SELECT id, email, username, credits
        FROM users WHERE id = ${userId}
      `;

      if (!user) {
        return new Response(JSON.stringify({ message: 'User not found' }), {
          status: 404,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
      
      return new Response(JSON.stringify(user), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Require auth for remaining endpoints
    if (!userId) {
      return new Response(JSON.stringify({ message: 'Unauthorized' }), {
        status: 401,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // ============================================
    // WORKERS ENDPOINTS
    // ============================================

    if (path === '/api/workers' && method === 'GET') {
      const workers = await sql`
        SELECT * FROM workers WHERE user_id = ${userId}
        ORDER BY created_at DESC
      `;
      
      return new Response(JSON.stringify(workers), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    if (path === '/api/workers' && method === 'POST') {
      const body = await request.json();
      const { name, specs } = body;
      
      const [worker] = await sql`
        INSERT INTO workers (user_id, name, specs, status, last_heartbeat)
        VALUES (${userId}, ${name}, ${JSON.stringify(specs || {})}, 'offline', NOW())
        RETURNING *
      `;
      
      return new Response(JSON.stringify(worker), {
        status: 201,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Heartbeat (no auth required, uses worker token)
    if (path.match(/^\/api\/workers\/\d+\/heartbeat$/) && method === 'POST') {
      const workerId = parseInt(path.split('/')[3]);
      
      await sql`
        UPDATE workers
        SET last_heartbeat = NOW(), status = 'online'
        WHERE id = ${workerId}
      `;
      
      return new Response(JSON.stringify({ status: 'ok' }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // ============================================
    // JOBS ENDPOINTS
    // ============================================

    if (path === '/api/jobs' && method === 'GET') {
      const jobs = await sql`
        SELECT * FROM jobs
        WHERE user_id = ${userId}
        ORDER BY created_at DESC
        LIMIT 100
      `;
      
      return new Response(JSON.stringify(jobs), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    if (path === '/api/jobs' && method === 'POST') {
      const body = await request.json();
      const { type, payload, price } = body;
      
      // Check credits
      const [user] = await sql`
        SELECT credits FROM users WHERE id = ${userId}
      `;
      
      if (!user || user.credits < price) {
        return new Response(JSON.stringify({ message: 'Insufficient credits' }), {
          status: 402,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }

      // Create job
      const [job] = await sql`
        INSERT INTO jobs (user_id, type, payload, price, status)
        VALUES (${userId}, ${type}, ${JSON.stringify(payload)}, ${price}, 'pending')
        RETURNING *
      `;

      // Deduct credits
      await sql`
        UPDATE users SET credits = credits - ${price}
        WHERE id = ${userId}
      `;

      return new Response(JSON.stringify(job), {
        status: 201,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    if (path.match(/^\/api\/jobs\/\d+$/) && method === 'GET') {
      const jobId = parseInt(path.split('/')[3]);
      
      const [job] = await sql`
        SELECT * FROM jobs
        WHERE id = ${jobId} AND user_id = ${userId}
      `;
      
      if (!job) {
        return new Response(JSON.stringify({ message: 'Job not found' }), {
          status: 404,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
      
      return new Response(JSON.stringify(job), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Not found
    return new Response(JSON.stringify({ error: 'Not found', path, method }), {
      status: 404,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });

  } catch (error: any) {
    console.error('Error:', error);
    return new Response(JSON.stringify({ 
      error: 'Internal server error',
      message: error.message || String(error)
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
}

export default {
  fetch: onRequest,
};
