// shared/schema.ts - FINAL: All credits removed with Fix Applied
import { 
  pgTable, 
  text, 
  serial, 
  integer, 
  timestamp, 
  jsonb, 
  varchar, 
  index,
  boolean,
  bigint,
} from "drizzle-orm/pg-core";
import { createInsertSchema, createSelectSchema } from "drizzle-zod";
import { sql } from "drizzle-orm";
import { z } from "zod";

// ============================================
// SESSIONS TABLE
// ============================================
export const sessions = pgTable(
  "sessions",
  {
    sid: varchar("sid").primaryKey(),
    sess: jsonb("sess").notNull(),
    expire: timestamp("expire").notNull(),
  },
  (table) => ({
    expireIdx: index("IDX_session_expire").on(table.expire),
  })
);

// ============================================
// USERS TABLE - NO CREDITS
// ============================================
export const users = pgTable(
  "users",
  {
    // Fix applied: Explicit ID with random UUID default
    id: varchar("id").primaryKey().default(sql`gen_random_uuid()::text`),
    email: varchar("email", { length: 255 }).unique().notNull(),
    username: varchar("username", { length: 255 }).unique().notNull(),
    passwordHash: varchar("password_hash", { length: 255 }).notNull(),
    
    // CRITICAL FIX: Explicit column name mapping for role and apiKey
    role: varchar("role", { length: 50 }).default("developer").notNull(),
    apiKey: varchar("api_key", { length: 255 }).unique(), // Maps api_key -> apiKey
    
    createdAt: timestamp("created_at").defaultNow().notNull(),
    updatedAt: timestamp("updated_at").defaultNow().notNull(),
    lastLogin: timestamp("last_login"),
    isActive: boolean("is_active").default(true).notNull(),
  },
  (table) => ({
    emailIdx: index("idx_users_email").on(table.email),
    usernameIdx: index("idx_users_username").on(table.username),
    apiKeyIdx: index("idx_users_api_key").on(table.apiKey),
  })
);

// ============================================
// WORKERS TABLE
// ============================================
export const workers = pgTable(
  "workers",
  {
    id: serial("id").primaryKey(),
    userId: varchar("user_id").references(() => users.id, { onDelete: "cascade" }).notNull(),
    
    // Worker identification
    name: text("name").notNull(),
    hostname: varchar("hostname", { length: 255 }),
    
    // Worker status
    status: varchar("status", { length: 50 }).default("offline").notNull(),
    
    // System specifications (JSONB)
    specs: jsonb("specs").default(sql`'{}'::jsonb`),
    
    // Statistics
    jobsCompleted: integer("jobs_completed").default(0).notNull(),
    jobsFailed: integer("jobs_failed").default(0).notNull(),
    totalComputeTimeSeconds: bigint("total_compute_time_seconds", { mode: "number" }).default(0).notNull(),
    
    // Timestamps
    lastHeartbeat: timestamp("last_heartbeat").defaultNow(),
    createdAt: timestamp("created_at").defaultNow().notNull(),
  },
  (table) => ({
    userIdIdx: index("idx_workers_user_id").on(table.userId),
    statusIdx: index("idx_workers_status").on(table.status),
    lastHeartbeatIdx: index("idx_workers_last_heartbeat").on(table.lastHeartbeat),
  })
);

// ============================================
// JOBS TABLE - NO PRICE/CREDITS
// ============================================
export const jobs = pgTable(
  "jobs",
  {
    id: serial("id").primaryKey(),
    userId: varchar("user_id").references(() => users.id, { onDelete: "cascade" }).notNull(),
    workerId: integer("worker_id").references(() => workers.id, { onDelete: "set null" }),
    
    // Job details
    type: varchar("type", { length: 50 }).notNull(),
    status: varchar("status", { length: 50 }).default("pending").notNull(),
    
    // Job data (JSONB)
    payload: jsonb("payload").notNull(),
    result: jsonb("result"),
    
    // Execution details
    startedAt: timestamp("started_at"),
    completedAt: timestamp("completed_at"),
    durationSeconds: integer("duration_seconds"),
    
    // Job priority
    priority: integer("priority").default(0).notNull(),
    
    // Retry logic
    retryCount: integer("retry_count").default(0).notNull(),
    maxRetries: integer("max_retries").default(3).notNull(),
    
    // Timestamps
    createdAt: timestamp("created_at").defaultNow().notNull(),
    updatedAt: timestamp("updated_at").defaultNow().notNull(),
  },
  (table) => ({
    userIdIdx: index("idx_jobs_user_id").on(table.userId),
    workerIdIdx: index("idx_jobs_worker_id").on(table.workerId),
    statusIdx: index("idx_jobs_status").on(table.status),
    createdAtIdx: index("idx_jobs_created_at").on(table.createdAt),
  })
);

// ============================================
// ZOD SCHEMAS
// ============================================

export const insertUserSchema = createInsertSchema(users, {
  email: z.string().email("Invalid email address"),
  username: z.string().min(3, "Username must be at least 3 characters").max(50),
  passwordHash: z.string().min(1, "Password hash is required"),
  role: z.enum(["contributor", "developer"]).default("developer"),
}).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
  apiKey: true,
  lastLogin: true,
});

export const insertWorkerSchema = createInsertSchema(workers, {
  name: z.string().min(1, "Worker name is required"),
  status: z.enum(["online", "offline", "busy", "error"]).default("offline"),
  specs: z.record(z.any()).optional(),
}).omit({
  id: true,
  userId: true,
  lastHeartbeat: true,
  createdAt: true,
  jobsCompleted: true,
  jobsFailed: true,
  totalComputeTimeSeconds: true,
});

export const insertJobSchema = createInsertSchema(jobs, {
  type: z.enum(["script", "render", "compute", "ml", "custom"]),
  status: z.enum(["pending", "assigned", "processing", "completed", "failed", "cancelled"]).default("pending"),
  payload: z.object({
    script: z.string().optional(),
    code: z.string().optional(),
    runtime: z.string().default("node"),
    timeout: z.number().int().default(300),
    requirements: z.array(z.string()).default([]),
  }),
  priority: z.number().int().default(0),
}).omit({
  id: true,
  userId: true,
  workerId: true,
  result: true,
  startedAt: true,
  completedAt: true,
  durationSeconds: true,
  createdAt: true,
  updatedAt: true,
  retryCount: true,
});

// ============================================
// TYPESCRIPT TYPES
// ============================================

export type User = typeof users.$inferSelect;
export type InsertUser = z.infer<typeof insertUserSchema>;

export type Worker = typeof workers.$inferSelect;
export type InsertWorker = z.infer<typeof insertWorkerSchema>;

export type Job = typeof jobs.$inferSelect;
export type InsertJob = z.infer<typeof insertJobSchema>;

export type UserRole = "contributor" | "developer";
export type WorkerStatus = "online" | "offline" | "busy" | "error";
export type JobStatus = "pending" | "assigned" | "processing" | "completed" | "failed" | "cancelled";
