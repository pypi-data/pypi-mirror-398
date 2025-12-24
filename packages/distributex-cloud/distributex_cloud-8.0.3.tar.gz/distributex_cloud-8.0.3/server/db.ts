import { Pool, neonConfig } from '@neondatabase/serverless';
import { drizzle } from 'drizzle-orm/neon-serverless';
import ws from "ws";
import * as schema from "@shared/schema";

// This is required for the serverless pool to work over WebSockets in Node.js
neonConfig.webSocketConstructor = ws;

const connectionString = process.env.DATABASE_URL;

if (!connectionString && process.env.NODE_ENV === 'production') {
  throw new Error("DATABASE_URL must be set in production.");
}

// Create the pool with a fallback for build-time safety
export const pool = new Pool({ 
  connectionString: connectionString || "postgres://localhost/db_dummy" 
});

export const db = drizzle({ client: pool, schema });
