import { db } from "./db";
import { users, workers, jobs, type User, type Worker, type Job } from "@shared/schema";
import { eq, desc, and, isNull, or } from "drizzle-orm";

export interface IStorage {
  getUser(id: string): Promise<User | undefined>;
  deductCredits(userId: string, amount: number): Promise<void>;

  getWorkers(userId: string): Promise<Worker[]>;
  createWorker(userId: string, worker: any): Promise<Worker>;
  updateWorkerHeartbeat(id: number): Promise<void>;

  getJobs(userId: string): Promise<Job[]>;
  getJob(id: number): Promise<Job | undefined>;
  createJob(userId: string, job: any): Promise<Job>;
  updateJobStatus(id: number, status: string, result?: any): Promise<Job>;
  getAvailableJobs(workerId?: number): Promise<Job[]>;
}

export class DatabaseStorage implements IStorage {
  async getUser(id: string): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.id, id));
    return user;
  }

  async deductCredits(userId: string, amount: number): Promise<void> {
    await db
      .update(users)
      .set({
        credits: db.$with('user_credits').select({credits: users.credits}).from(users).where(eq(users.id, userId)),
        updatedAt: new Date()
      })
      .where(eq(users.id, userId));
  }

  async getWorkers(userId: string): Promise<Worker[]> {
    return await db.select().from(workers).where(eq(workers.userId, userId));
  }

  async createWorker(userId: string, worker: any): Promise<Worker> {
    const [newWorker] = await db.insert(workers).values({ ...worker, userId }).returning();
    return newWorker;
  }

  async updateWorkerHeartbeat(id: number): Promise<void> {
    await db.update(workers)
      .set({ lastHeartbeat: new Date(), status: 'online' })
      .where(eq(workers.id, id));
  }

  async getJobs(userId: string): Promise<Job[]> {
    return await db.select().from(jobs)
      .where(eq(jobs.userId, userId))
      .orderBy(desc(jobs.createdAt));
  }

  async getJob(id: number): Promise<Job | undefined> {
    const [job] = await db.select().from(jobs).where(eq(jobs.id, id));
    return job;
  }

  async createJob(userId: string, job: any): Promise<Job> {
    const [newJob] = await db.insert(jobs).values({ ...job, userId }).returning();
    return newJob;
  }

  async updateJobStatus(id: number, status: string, result?: any): Promise<Job> {
    const [updatedJob] = await db.update(jobs)
      .set({
        status,
        result,
        completedAt: status === 'completed' || status === 'failed' ? new Date() : undefined
      })
      .where(eq(jobs.id, id))
      .returning();
    return updatedJob;
  }

  async getAvailableJobs(workerId?: number): Promise<Job[]> {
    const query = workerId
      ? db.select()
          .from(jobs)
          .where(
            and(
              eq(jobs.status, 'pending'),
              or(isNull(jobs.workerId), eq(jobs.workerId, workerId))
            )
          )
          .orderBy(desc(jobs.price), jobs.createdAt)
          .limit(5)
      : db.select()
          .from(jobs)
          .where(
            and(
              eq(jobs.status, 'pending'),
              isNull(jobs.workerId)
            )
          )
          .orderBy(desc(jobs.price), jobs.createdAt)
          .limit(5);

    return await query;
  }
}

export const storage = new DatabaseStorage();
