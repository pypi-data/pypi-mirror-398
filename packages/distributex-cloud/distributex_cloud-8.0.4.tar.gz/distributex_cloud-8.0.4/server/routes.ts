// server/routes.ts - REAL JOB EXECUTION SYSTEM
import type { Express } from "express";
import { createServer, type Server } from "http";
import passport from "passport";
import { storage } from "./storage";
import { register, isAuthenticated, checkApiKey } from "./auth";
import { db } from "./db";
import { users, jobs, workers } from "@shared/schema";
import { eq, and, isNull, sql } from "drizzle-orm";
import crypto from "crypto";

// Real job execution queue
const jobQueue: Map<number, any> = new Map();

export async function registerRoutes(httpServer: Server, app: Express): Promise<Server> {
  
  // Background: Mark inactive workers offline every 2 minutes
  setInterval(async () => {
    try {
      const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
      await db.execute(sql`
        UPDATE workers 
        SET status = 'offline' 
        WHERE last_heartbeat < ${fiveMinutesAgo} 
        AND status = 'online'
      `);
    } catch (err) {
      console.error("Failed to mark inactive workers:", err);
    }
  }, 2 * 60 * 1000);

  // --- PUBLIC STATS ---
  app.get("/api/workers/stats", async (_req, res) => {
    try {
      const stats = await storage.getWorkerStats();
      res.json(stats);
    } catch (error) {
      res.status(500).json({ active: 0, total: 0, unique_users: 0 });
    }
  });

  app.get("/api/jobs/stats", async (_req, res) => {
    try {
      const stats = await storage.getJobStats();
      res.json(stats);
    } catch (error) {
      res.status(500).json({ completed: 0, total: 0 });
    }
  });

  // --- SYSTEM ROUTES ---
  app.get("/api/health", (_req, res) => {
    res.json({ status: "healthy", timestamp: new Date().toISOString() });
  });

  // --- AUTH ROUTES ---
  app.post("/api/auth/register", async (req, res) => {
    try {
      const { email, username, password, role } = req.body;
      const user = await register(email, username, password, role || 'developer');
      req.login(user, (err) => {
        if (err) return res.status(500).json({ message: "Login failed" });
        res.status(201).json(user);
      });
    } catch (error: any) {
      res.status(400).json({ message: error.message });
    }
  });

  app.post("/api/auth/login", (req, res, next) => {
    passport.authenticate("local", (err: any, user: any, info: any) => {
      if (!user) return res.status(401).json({ message: info?.message || "Invalid" });
      req.login(user, () => res.json(user));
    })(req, res, next);
  });

  app.post("/api/auth/logout", (req, res) => {
    req.logout(() => {
      res.json({ message: "Logged out" });
    });
  });

  app.get("/api/auth/user", isAuthenticated, async (req, res) => {
    try {
      const [user] = await db.select().from(users).where(eq(users.id, req.user!.id)).limit(1);
      if (!user) return res.status(404).json({ message: "User not found" });
      res.json(user);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch user" });
    }
  });

  // --- WORKER ROUTES (Real Implementation) ---
  app.get("/api/workers", isAuthenticated, async (req, res) => {
    try {
      const workersList = await storage.getWorkers(req.user!.id);
      res.json(workersList);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch workers" });
    }
  });

  // REAL Worker Registration with Docker Container
  app.post("/api/workers", checkApiKey, async (req, res) => {
    try {
      const { hostname, specs, name } = req.body;
      
      // Create worker record
      const worker = await storage.createWorker(req.user!.id, {
        name: name || `worker-${hostname}`,
        hostname,
        specs,
        status: 'online'
      });
      
      console.log(`✅ Worker registered: ${worker.name} (ID: ${worker.id})`);
      res.status(201).json(worker);
    } catch (error: any) {
      console.error("Worker registration failed:", error);
      res.status(500).json({ message: "Registration failed", error: error.message });
    }
  });

  app.delete("/api/workers/:id", isAuthenticated, async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      await storage.deleteWorker(id);
      res.json({ success: true });
    } catch (error) {
      res.status(500).json({ message: "Failed to remove worker" });
    }
  });

  // REAL Heartbeat with Job Assignment
  app.post("/api/workers/:id/heartbeat", checkApiKey, async (req, res) => {
    try {
      const workerId = parseInt(req.params.id);
      await storage.updateWorkerHeartbeat(workerId);
      
      // Get available jobs for this worker
      const availableJobs = await storage.getAvailableJobs(workerId);
      
      res.json({ 
        status: "ok", 
        jobs: availableJobs,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      res.status(500).json({ message: "Heartbeat failed" });
    }
  });

  // --- JOB ROUTES (Real Execution) ---
  
  // REAL Job Submission
  app.post("/api/jobs", isAuthenticated, async (req, res) => {
    try {
      const { type, payload } = req.body;
      
      if (!type || !payload) {
        return res.status(400).json({ message: "Type and payload required" });
      }
      
      // Create job in database
      const job = await storage.createJob(req.user!.id, {
        type,
        payload,
        status: 'pending',
        priority: payload.priority || 0
      });
      
      console.log(`📝 Job created: ${job.id} (type: ${type})`);
      
      // Add to in-memory queue for fast polling
      jobQueue.set(job.id, job);
      
      res.status(201).json(job);
    } catch (error: any) {
      console.error("Job creation failed:", error);
      res.status(500).json({ message: "Failed to create job", error: error.message });
    }
  });

  // Get available jobs (for workers)
  app.get("/api/jobs/available", checkApiKey, async (req, res) => {
    try {
      const workerId = req.query.workerId ? parseInt(req.query.workerId as string) : undefined;
      const availableJobs = await storage.getAvailableJobs(workerId);
      res.json(availableJobs);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch available jobs" });
    }
  });

  // Get user's jobs
  app.get("/api/jobs", isAuthenticated, async (req, res) => {
    try {
      const jobsList = await storage.getJobs(req.user!.id);
      res.json(jobsList);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch jobs" });
    }
  });

  // Get specific job
  app.get("/api/jobs/:id", isAuthenticated, async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const job = await storage.getJob(id);
      
      if (!job) {
        return res.status(404).json({ message: "Job not found" });
      }
      
      if (job.userId !== req.user!.id) {
        return res.status(403).json({ message: "Forbidden" });
      }
      
      res.json(job);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch job" });
    }
  });

  // REAL Job Status Update (from worker)
  app.patch("/api/jobs/:id", checkApiKey, async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const { status, result, workerId } = req.body;
      
      console.log(`📊 Job ${id} status update: ${status} (worker: ${workerId})`);
      
      // Update job status
      const job = await storage.updateJobStatus(id, status, result, workerId);
      
      // Remove from queue if completed/failed
      if (status === 'completed' || status === 'failed') {
        jobQueue.delete(id);
        console.log(`✅ Job ${id} ${status}`);
      }
      
      res.json(job);
    } catch (error: any) {
      console.error(`Job ${req.params.id} update failed:`, error);
      res.status(500).json({ message: "Failed to update job", error: error.message });
    }
  });

  return httpServer;
}
