// functions/api/[[path]].ts - FULL SCRIPT WITH INTEGRATED FIXES
import { neon } from '@neondatabase/serverless';

interface Env {
  DATABASE_URL: string;
  JWT_SECRET: string;
  SESSION_SECRET: string;
  SESSIONS: KVNamespace;
  RATE_LIMIT: KVNamespace;
}

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

// ============================================
// HELPER FUNCTIONS
// ============================================

// FIXED: More reasonable rate limiting (1000 requests per minute)
async function checkRateLimit(env: Env, ip: string): Promise<boolean> {
  const key = `rate_limit:${ip}`;
  const count = await env.RATE_LIMIT.get(key);
  
  if (count && parseInt(count) > 1000) {
    return false;
  }
  
  await env.RATE_LIMIT.put(key, String((parseInt(count || '0') + 1)), {
    expirationTtl: 60
  });
  
  return true;
}

function base64UrlEncode(str: string): string {
  return btoa(str).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

function base64UrlDecode(str: string): string {
  str = str.replace(/-/g, '+').replace(/_/g, '/');
  while (str.length % 4) { str += '='; }
  return atob(str);
}

async function generateJWT(payload: any, secret: string): Promise<string> {
  const header = { alg: 'HS256', typ: 'JWT' };
  const now = Math.floor(Date.now() / 1000);
  const claims = { ...payload, iat: now, exp: now + (7 * 24 * 60 * 60) };
  const headerEncoded = base64UrlEncode(JSON.stringify(header));
  const payloadEncoded = base64UrlEncode(JSON.stringify(claims));
  const message = `${headerEncoded}.${payloadEncoded}`;
  const encoder = new TextEncoder();
  const data = encoder.encode(message);
  const keyData = encoder.encode(secret);
  const cryptoKey = await crypto.subtle.importKey('raw', keyData, { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const signature = await crypto.subtle.sign('HMAC', cryptoKey, data);
  const signatureBase64 = base64UrlEncode(String.fromCharCode(...new Uint8Array(signature)));
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
    const cryptoKey = await crypto.subtle.importKey('raw', keyData, { name: 'HMAC', hash: 'SHA-256' }, false, ['verify']);
    const signatureBytes = Uint8Array.from(base64UrlDecode(signatureB64).split('').map(c => c.charCodeAt(0)));
    const valid = await crypto.subtle.verify('HMAC', cryptoKey, signatureBytes, data);
    if (!valid) return null;
    const payload = JSON.parse(base64UrlDecode(payloadB64));
    if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) return null;
    return payload;
  } catch (e) { return null; }
}

async function hashPassword(password: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(password);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

function generateApiKey(): string {
  const uuid = crypto.randomUUID().replace(/-/g, '');
  return `dsx_${uuid}`;
}

// ============================================
// MAIN REQUEST HANDLER
// ============================================

export async function onRequest(context: any): Promise<Response> {
  const { request, env } = context;
  const url = new URL(request.url);
  const path = url.pathname;
  const method = request.method;

  console.log(`[${method}] ${path}`);

  // 1. Handle CORS preflight
  if (method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: corsHeaders });
  }

  // 2. Auth Detection (for Rate Limiting Bypass)
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
  const cookieHeader = request.headers.get('Cookie') || '';
  const hasSession = cookieHeader.includes('sessionId=');

  // FIXED: Apply rate limiting only to non-authenticated users
  if (!hasSession) {
    const allowed = await checkRateLimit(env, ip);
    if (!allowed) {
      console.log(`⚠️ Rate limited IP: ${ip}`);
      return new Response(JSON.stringify({ error: 'Rate limit exceeded' }), {
        status: 429,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
  }

  const sql = neon(env.DATABASE_URL);

  try {
    // ============================================
    // PUBLIC / STATS ENDPOINTS
    // ============================================
    
    if (path === '/api/health' && method === 'GET') {
      return new Response(JSON.stringify({ status: "healthy", timestamp: new Date().toISOString() }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    if (path === '/api/workers/stats' && method === 'GET') {
      const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
      const activeWorkers = await sql`SELECT COUNT(*) as count FROM workers WHERE last_heartbeat > ${fiveMinutesAgo}`;
      const totalWorkers = await sql`SELECT COUNT(*) as count FROM workers`;
      const uniqueUsers = await sql`SELECT COUNT(DISTINCT user_id) as count FROM workers`;

      return new Response(JSON.stringify({
        active: Number(activeWorkers[0]?.count || 0),
        total: Number(totalWorkers[0]?.count || 0),
        unique_users: Number(uniqueUsers[0]?.count || 0),
      }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
    }

    if (path === '/api/jobs/stats' && method === 'GET') {
      const completed = await sql`SELECT COUNT(*) as count FROM jobs WHERE status = 'completed'`;
      const total = await sql`SELECT COUNT(*) as count FROM jobs`;
      return new Response(JSON.stringify({
        completed: Number(completed[0]?.count || 0),
        total: Number(total[0]?.count || 0),
      }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
    }

    // ============================================
    // AUTH ENDPOINTS
    // ============================================
    
    if (path === '/api/auth/register' && method === 'POST') {
      const { email, username, password, role } = await request.json();
      if (!email || !username || !password || password.length < 8) {
        return new Response(JSON.stringify({ message: 'Missing fields or password too short' }), { status: 400, headers: corsHeaders });
      }

      const existing = await sql`SELECT id FROM users WHERE email = ${email} OR username = ${username}`;
      if (existing.length > 0) {
        return new Response(JSON.stringify({ message: 'User already exists' }), { status: 400, headers: corsHeaders });
      }

      const passwordHash = await hashPassword(password);
      const apiKey = generateApiKey();

      const [user] = await sql`
        INSERT INTO users (email, username, password_hash, role, api_key, is_active)
        VALUES (${email}, ${username}, ${passwordHash}, ${role || 'developer'}, ${apiKey}, true)
        RETURNING id, email, username, role, api_key as "apiKey"
      `;

      const sessionId = crypto.randomUUID();
      await env.SESSIONS.put(`session:${sessionId}`, JSON.stringify({ userId: user.id, email: user.email }), { expirationTtl: 604800 });
      const token = await generateJWT({ userId: user.id }, env.JWT_SECRET);

      return new Response(JSON.stringify({ ...user, token }), {
        status: 201,
        headers: { 
          ...corsHeaders, 
          'Content-Type': 'application/json',
          'Set-Cookie': `sessionId=${sessionId}; Path=/; HttpOnly; SameSite=None; Secure; Max-Age=604800`
        }
      });
    }

    if (path === '/api/auth/login' && method === 'POST') {
      const { email, password } = await request.json();
      const passwordHash = await hashPassword(password);
      const [user] = await sql`SELECT id, email, username, role, api_key as "apiKey" FROM users WHERE email = ${email} AND password_hash = ${passwordHash}`;

      if (!user) return new Response(JSON.stringify({ message: 'Invalid credentials' }), { status: 401, headers: corsHeaders });

      const sessionId = crypto.randomUUID();
      await env.SESSIONS.put(`session:${sessionId}`, JSON.stringify({ userId: user.id, email: user.email }), { expirationTtl: 604800 });
      const token = await generateJWT({ userId: user.id }, env.JWT_SECRET);

      return new Response(JSON.stringify({ ...user, token }), {
        status: 200,
        headers: { 
          ...corsHeaders, 
          'Content-Type': 'application/json',
          'Set-Cookie': `sessionId=${sessionId}; Path=/; HttpOnly; SameSite=None; Secure; Max-Age=604800`
        }
      });
    }

    if (path === '/api/auth/logout' && method === 'POST') {
      const sid = cookieHeader.split('sessionId=')[1]?.split(';')[0];
      if (sid) await env.SESSIONS.delete(`session:${sid}`);
      return new Response(JSON.stringify({ message: 'Logged out' }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json', 'Set-Cookie': 'sessionId=; Path=/; HttpOnly; Max-Age=0' }
      });
    }

    // ============================================
    // PROTECTED ENDPOINTS - AUTH REQUIRED
    // ============================================
    
    let userId: string | null = null;
    const authHeader = request.headers.get('Authorization');
    
    // Check JWT First
    if (authHeader?.startsWith('Bearer ')) {
      const payload = await verifyJWT(authHeader.substring(7), env.JWT_SECRET);
      if (payload) userId = payload.userId;
    }

    // Check Session Cookie Second
    if (!userId && hasSession) {
      const sessionId = cookieHeader.split('sessionId=')[1]?.split(';')[0];
      const session = await env.SESSIONS.get(`session:${sessionId}`);
      if (session) userId = JSON.parse(session).userId;
    }

    if (!userId) {
      return new Response(JSON.stringify({ message: 'Unauthorized' }), { status: 401, headers: corsHeaders });
    }

    // USER PROFILE (Auto-fix missing API Key)
    if (path === '/api/auth/user' && method === 'GET') {
      const [user] = await sql`SELECT id, email, username, role, api_key as "apiKey" FROM users WHERE id = ${userId}`;
      if (!user) return new Response(JSON.stringify({ message: 'Not found' }), { status: 404, headers: corsHeaders });

      if (!user.apiKey) {
        const newKey = generateApiKey();
        await sql`UPDATE users SET api_key = ${newKey} WHERE id = ${userId}`;
        user.apiKey = newKey;
      }
      return new Response(JSON.stringify(user), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
    }

    // WORKERS
    if (path === '/api/workers') {
      if (method === 'GET') {
        const workers = await sql`SELECT * FROM workers WHERE user_id = ${userId} ORDER BY created_at DESC`;
        return new Response(JSON.stringify(workers), { headers: corsHeaders });
      }
      if (method === 'POST') {
        const { name, specs } = await request.json();
        const [worker] = await sql`
          INSERT INTO workers (user_id, name, specs, status, last_heartbeat)
          VALUES (${userId}, ${name}, ${JSON.stringify(specs || {})}, 'offline', NOW())
          RETURNING *
        `;
        return new Response(JSON.stringify(worker), { status: 201, headers: corsHeaders });
      }
    }

    // Worker Heartbeat
    if (path.match(/^\/api\/workers\/\d+\/heartbeat$/) && method === 'POST') {
      const workerId = parseInt(path.split('/')[3]);
      await sql`UPDATE workers SET last_heartbeat = NOW(), status = 'online' WHERE id = ${workerId}`;
      return new Response(JSON.stringify({ status: 'ok' }), { headers: corsHeaders });
    }

    // JOBS
    if (path === '/api/jobs') {
      if (method === 'GET') {
        const jobs = await sql`SELECT * FROM jobs WHERE user_id = ${userId} ORDER BY created_at DESC LIMIT 100`;
        return new Response(JSON.stringify(jobs), { headers: corsHeaders });
      }
      if (method === 'POST') {
        const { type, payload } = await request.json();
        const [job] = await sql`
          INSERT INTO jobs (user_id, type, payload, status)
          VALUES (${userId}, ${type}, ${JSON.stringify(payload)}, 'pending')
          RETURNING *
        `;
        return new Response(JSON.stringify(job), { status: 201, headers: corsHeaders });
      }
    }

    // Specific Job ID
    if (path.match(/^\/api\/jobs\/\d+$/) && method === 'GET') {
      const jobId = parseInt(path.split('/')[3]);
      const [job] = await sql`SELECT * FROM jobs WHERE id = ${jobId} AND user_id = ${userId}`;
      if (!job) return new Response(JSON.stringify({ message: 'Job not found' }), { status: 404, headers: corsHeaders });
      return new Response(JSON.stringify(job), { headers: corsHeaders });
    }

    return new Response(JSON.stringify({ error: 'Not found' }), { status: 404, headers: corsHeaders });

  } catch (error: any) {
    console.error('API Error:', error);
    return new Response(JSON.stringify({ error: 'Internal server error', message: error.message }), { 
      status: 500, 
      headers: corsHeaders 
    });
  }
}

export default { fetch: onRequest };
