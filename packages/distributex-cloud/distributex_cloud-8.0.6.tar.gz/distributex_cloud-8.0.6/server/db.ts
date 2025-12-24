import { Pool, neonConfig } from '@neondatabase/serverless';
import { drizzle } from 'drizzle-orm/neon-serverless';
import ws from "ws";
import * as schema from "@shared/schema";

// Required for serverless WebSocket support in Node.js
neonConfig.webSocketConstructor = ws;

const connectionString = process.env.DATABASE_URL;

if (!connectionString && process.env.NODE_ENV === 'production') {
  throw new Error("DATABASE_URL must be set in production");
}

export const pool = new Pool({ 
  connectionString: connectionString || "postgres://localhost/db_dummy" 
});

// FIX: Initializing drizzle by passing the pool directly as the first argument
export const db = drizzle(pool, { schema });
