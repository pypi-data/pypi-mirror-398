// src/index.ts
import axios, { AxiosInstance } from 'axios';

export interface JobOptions {
  type: string;
  code: string;
  timeout?: number;
  bidPrice?: number;
  requirements?: string[];
  gpu?: boolean;
  memory?: string;
}

export interface Job {
  id: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  type: string;
  payload: any;
  result?: any;
  createdAt: string;
  completedAt?: string;
}

export class DistributeXClient {
  private client: AxiosInstance;

  constructor(config: { apiKey: string; baseUrl?: string }) {
    this.client = axios.create({
      baseURL: config.baseUrl || 'https://api.distributex.cloud',
      headers: {
        'Authorization': `Bearer ${config.apiKey}`,
        'Content-Type': 'application/json'
      }
    });
  }

  async submit(options: JobOptions): Promise<Job> {
    const response = await this.client.post('/api/jobs', {
      type: options.type,
      payload: {
        code: options.code,
        requirements: options.requirements || [],
        timeout: options.timeout || 300,
        gpu: options.gpu || false,
        memory: options.memory || '2GB'
      },
      price: options.bidPrice || 10
    });

    return response.data;
  }

  async getJob(jobId: number): Promise<Job> {
    const response = await this.client.get(`/api/jobs/${jobId}`);
    return response.data;
  }

  async waitForJob(jobId: number, timeout: number = 600): Promise<Job> {
    const startTime = Date.now();
    const pollInterval = 5000;

    while (Date.now() - startTime < timeout * 1000) {
      const job = await this.getJob(jobId);

      if (job.status === 'completed' || job.status === 'failed') {
        return job;
      }

      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }

    throw new Error(`Job ${jobId} did not complete within ${timeout} seconds`);
  }

  async cancelJob(jobId: number): Promise<boolean> {
    try {
      await this.client.delete(`/api/jobs/${jobId}`);
      return true;
    } catch {
      return false;
    }
  }

  async getBalance(): Promise<number> {
    const response = await this.client.get('/api/auth/me');
    return response.data.credits;
  }
}
