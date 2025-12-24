// server/storage.ts - REAL JOB STATUS UPDATES WITH WORKER ASSIGNMENT
import { db } from "./db";
import { users, workers, jobs, type User, type Worker, type Job } from "@shared/schema";
import { eq, desc, and, isNull, or, sql, lt } from "drizzle-orm";

export interface IStorage {
  getUser(id: string): Promise<User | undefined>;
  getWorkers(userId: string): Promise<Worker[]>;
  createWorker(userId: string, worker: any): Promise<Worker>;
  updateWorkerHeartbeat(id: number): Promise<void>;
  getWorkerStats(): Promise<{ active: number; total: number; unique_users: number }>;
  getJobs(userId: string): Promise<Job[]>;
  getJob(id: number): Promise<Job | undefined>;
  createJob(userId: string, job: any): Promise<Job>;
  updateJobStatus(id: number, status: string, result?: any, workerId?: number): Promise<Job>;
  getAvailableJobs(workerId?: number): Promise<Job[]>;
  getJobStats(): Promise<{ completed: number; total: number }>;
  pruneInactiveWorkers(): Promise<number>;
  deleteWorker(id: number): Promise<void>;
}

export class DatabaseStorage implements IStorage {
  async getUser(id: string): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.id, id));
    return user;
  }

  async getWorkers(userId: string): Promise<Worker[]> {
    const workerList = await db.select()
      .from(workers)
      .where(eq(workers.userId, userId))
      .orderBy(desc(workers.lastHeartbeat));
    
    const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
    return workerList.map(w => ({
      ...w,
      status: w.lastHeartbeat && new Date(w.lastHeartbeat) > fiveMinutesAgo ? w.status : 'offline'
    }));
  }

  async createWorker(userId: string, workerData: any): Promise<Worker> {
    const hostname = workerData.hostname || workerData.specs?.hostname || `worker-${Date.now()}`;
    const specs = workerData.specs || {
      cpu: workerData.cpu,
      memory: workerData.memory,
      arch: workerData.arch,
      platform: workerData.platform,
      limits: workerData.limits
    };

    try {
      const existing = await db.select()
        .from(workers)
        .where(and(eq(workers.userId, userId), eq(workers.hostname, hostname)))
        .limit(1);
      
      if (existing.length > 0) {
        console.log(`♻️ Reusing existing worker #${existing[0].id} for ${hostname}`);
        const [updated] = await db.update(workers)
          .set({ 
            lastHeartbeat: new Date(), 
            status: 'online',
            specs: specs
          })
          .where(eq(workers.id, existing[0].id))
          .returning();
        return updated;
      }

      const [newWorker] = await db.insert(workers).values({ 
        userId,
        name: workerData.name || `Worker-${hostname.substring(0, 8)}`,
        hostname: hostname,
        specs: specs,
        status: 'online',
        lastHeartbeat: new Date()
      }).returning();
      
      console.log(`🆕 Created new worker #${newWorker.id} for user ${userId}`);
      return newWorker;
    } catch (error) {
      console.error("❌ Database error in createWorker:", error);
      throw error;
    }
  }

  async deleteWorker(id: number): Promise<void> {
    await db.delete(workers).where(eq(workers.id, id));
    console.log(`🗑️  Deleted worker #${id}`);
  }

  async updateWorkerHeartbeat(id: number): Promise<void> {
    const now = new Date();
    await db.update(workers)
      .set({ lastHeartbeat: now, status: 'online' })
      .where(eq(workers.id, id));
  }

  async getWorkerStats(): Promise<{ active: number; total: number; unique_users: number }> {
    try {
      const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
      
      const [activeResult] = await db.select({ count: sql<number>`count(*)::int` })
        .from(workers).where(sql`${workers.lastHeartbeat} > ${fiveMinutesAgo}`);
      
      const [totalResult] = await db.select({ count: sql<number>`count(*)::int` })
        .from(workers);
      
      const uniqueUsersResult = await db.selectDistinctOn([workers.userId], { userId: workers.userId })
        .from(workers);

      return {
        active: activeResult?.count || 0,
        total: totalResult?.count || 0,
        unique_users: uniqueUsersResult.length || 0,
      };
    } catch (error) {
      return { active: 0, total: 0, unique_users: 0 };
    }
  }

  async pruneInactiveWorkers(): Promise<number> {
    try {
      const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
      
      const deleted = await db.delete(workers)
        .where(
          or(
            lt(workers.lastHeartbeat, sevenDaysAgo),
            and(
              isNull(workers.lastHeartbeat),
              lt(workers.createdAt, sevenDaysAgo)
            )
          )
        )
        .returning();

      if (deleted.length > 0) {
        console.log(`🧹 Pruned ${deleted.length} inactive workers.`);
      }
      return deleted.length;
    } catch (error) {
      console.error("❌ Pruning error:", error);
      return 0;
    }
  }

  async getJobs(userId: string): Promise<Job[]> {
    return await db.select().from(jobs)
      .where(eq(jobs.userId, userId))
      .orderBy(desc(jobs.createdAt))
      .limit(100);
  }

  async getJob(id: number): Promise<Job | undefined> {
    const [job] = await db.select().from(jobs).where(eq(jobs.id, id));
    return job;
  }

  async createJob(userId: string, job: any): Promise<Job> {
    const [newJob] = await db.insert(jobs).values({ 
      ...job, 
      userId,
      status: 'pending',
      createdAt: new Date()
    }).returning();
    return newJob;
  }

  // REAL Job Status Update with Worker Assignment
  async updateJobStatus(id: number, status: string, result?: any, workerId?: number): Promise<Job> {
    const updateData: any = { 
      status, 
      result, 
      updatedAt: new Date() 
    };
    
    // Assign worker if provided
    if (workerId !== undefined) {
      updateData.workerId = workerId;
    }
    
    // Set timestamps based on status
    if (status === 'completed' || status === 'failed') {
      updateData.completedAt = new Date();
    }
    
    if (status === 'processing' && !result) {
      updateData.startedAt = new Date();
    }
    
    const [updatedJob] = await db.update(jobs)
      .set(updateData)
      .where(eq(jobs.id, id))
      .returning();
    
    return updatedJob;
  }

  async getAvailableJobs(workerId?: number): Promise<Job[]> {
    const baseFilter = and(
      eq(jobs.status, 'pending'),
      workerId ? or(isNull(jobs.workerId), eq(jobs.workerId, workerId)) : isNull(jobs.workerId)
    );

    return await db.select().from(jobs)
      .where(baseFilter)
      .orderBy(desc(jobs.priority), jobs.createdAt)
      .limit(5);
  }

  async getJobStats(): Promise<{ completed: number; total: number }> {
    try {
      const [completedResult] = await db.select({ count: sql<number>`count(*)::int` })
        .from(jobs).where(eq(jobs.status, 'completed'));
      const [totalResult] = await db.select({ count: sql<number>`count(*)::int` })
        .from(jobs);
      return { completed: completedResult?.count || 0, total: totalResult?.count || 0 };
    } catch (error) {
      return { completed: 0, total: 0 };
    }
  }
}

export const storage = new DatabaseStorage();
