// src/index.ts - PRODUCTION READY
/**
 * DistributeX JavaScript/TypeScript SDK
 * Official client for the DistributeX distributed computing platform
 * @packageDocumentation
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

export const VERSION = '4.0.5';

/**
 * Base error class for DistributeX SDK
 */
export class DistributeXError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'DistributeXError';
  }
}

/**
 * Authentication error
 */
export class AuthenticationError extends DistributeXError {
  constructor(message: string) {
    super(message);
    this.name = 'AuthenticationError';
  }
}

/**
 * Job not found error
 */
export class JobNotFoundError extends DistributeXError {
  constructor(message: string) {
    super(message);
    this.name = 'JobNotFoundError';
  }
}

/**
 * Timeout error
 */
export class TimeoutError extends DistributeXError {
  constructor(message: string) {
    super(message);
    this.name = 'TimeoutError';
  }
}

/**
 * Configuration for DistributeX client
 */
export interface ClientConfig {
  /** Your DistributeX API key (starts with dsx_) */
  apiKey: string;
  /** API base URL (default: production) */
  baseUrl?: string;
  /** Request timeout in milliseconds (default: 30000) */
  timeout?: number;
}

/**
 * Options for submitting a job
 */
export interface JobOptions {
  /** Job type (default: "script") */
  type?: string;
  /** Code to execute */
  code: string;
  /** Runtime environment: "node" or "python" (default: "node") */
  runtime?: 'node' | 'python';
  /** Maximum execution time in seconds (default: 300) */
  timeout?: number;
  /** NPM packages to install (Node.js only) */
  requirements?: string[];
  /** Whether GPU is required (default: false) */
  gpu?: boolean;
  /** Memory limit, e.g., "2GB" (default: "2GB") */
  memory?: string;
}

/**
 * Job status
 */
export type JobStatus = 'pending' | 'assigned' | 'processing' | 'completed' | 'failed' | 'cancelled';

/**
 * Job result
 */
export interface JobResult {
  /** Standard output from the job */
  output?: string;
  /** Error message if job failed */
  error?: string;
  /** Execution logs */
  logs?: string;
  /** Execution duration */
  duration?: string;
  /** Worker ID that processed the job */
  worker?: number;
}

/**
 * Job object
 */
export interface Job {
  /** Unique job ID */
  id: number;
  /** Current job status */
  status: JobStatus;
  /** Job type */
  type: string;
  /** Job payload/configuration */
  payload: any;
  /** Job result (available when completed/failed) */
  result?: JobResult;
  /** Job creation timestamp */
  createdAt: string;
  /** Job completion timestamp */
  completedAt?: string;
  /** User ID who submitted the job */
  userId?: string;
  /** Worker ID assigned to the job */
  workerId?: number;
}

/**
 * User account information
 */
export interface UserInfo {
  /** User ID */
  id: string;
  /** Email address */
  email: string;
  /** Username */
  username: string;
  /** User role (contributor or developer) */
  role: 'contributor' | 'developer';
  /** API key */
  apiKey: string;
}

/**
 * DistributeX Client
 * 
 * @example
 * ```typescript
 * import { DistributeXClient } from 'distributex-cloud';
 * 
 * const client = new DistributeXClient({
 *   apiKey: 'dsx_your_api_key_here'
 * });
 * 
 * const job = await client.submit({
 *   code: 'console.log("Hello World")'
 * });
 * 
 * const result = await client.waitForJob(job.id);
 * console.log(result.result.output);
 * ```
 */
export class DistributeXClient {
  private client: AxiosInstance;
  private apiKey: string;
  private baseUrl: string;

  /**
   * Create a new DistributeX client
   * 
   * @param config - Client configuration
   * @throws {AuthenticationError} If API key is invalid
   * @throws {DistributeXError} If connection fails
   */
  constructor(config: ClientConfig) {
    if (!config.apiKey) {
      throw new AuthenticationError('API key is required');
    }

    if (!config.apiKey.startsWith('dsx_')) {
      throw new AuthenticationError('Invalid API key format. Must start with "dsx_"');
    }

    this.apiKey = config.apiKey;
    this.baseUrl = (config.baseUrl || 'https://distributex-production-7fd2.up.railway.app').replace(/\/+$/, '');
    
    this.client = axios.create({
      baseURL: this.baseUrl,
      timeout: config.timeout || 30000,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'X-API-Key': this.apiKey,
        'Content-Type': 'application/json',
        'User-Agent': `distributex-js/${VERSION}`
      }
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      response => response,
      error => this.handleError(error)
    );

    // Verify connection
    this.verifyConnection();
  }

  /**
   * Verify API connection and authentication
   * @private
   */
  private async verifyConnection(): Promise<void> {
    try {
      await this.client.get('/api/health', { timeout: 10000 });
    } catch (error) {
      throw new DistributeXError('Failed to connect to DistributeX API');
    }
  }

  /**
   * Handle API errors
   * @private
   */
  private handleError(error: AxiosError): never {
    if (error.response) {
      const status = error.response.status;
      const data: any = error.response.data;
      
      if (status === 401) {
        throw new AuthenticationError('Invalid API key or unauthorized access');
      }
      
      if (status === 404) {
        throw new JobNotFoundError('Job not found');
      }
      
      const message = data?.message || error.message || 'API request failed';
      throw new DistributeXError(`${status}: ${message}`);
    }
    
    if (error.code === 'ECONNABORTED') {
      throw new TimeoutError('Request timed out');
    }
    
    throw new DistributeXError(error.message || 'Request failed');
  }

  /**
   * Submit a job to the distributed compute network
   * 
   * @param options - Job configuration options
   * @returns Promise resolving to job details
   * @throws {DistributeXError} If submission fails
   * 
   * @example
   * ```typescript
   * const job = await client.submit({
   *   code: `
   *     const data = [1, 2, 3, 4, 5];
   *     const sum = data.reduce((a, b) => a + b, 0);
   *     console.log(JSON.stringify({ sum, count: data.length }));
   *   `,
   *   runtime: 'node',
   *   timeout: 60
   * });
   * ```
   */
  async submit(options: JobOptions): Promise<Job> {
    if (!options.code || !options.code.trim()) {
      throw new Error('Code cannot be empty');
    }

    const response = await this.client.post<Job>('/api/jobs', {
      type: options.type || 'script',
      payload: {
        script: options.code,
        requirements: options.requirements || [],
        timeout: options.timeout || 300,
        gpu: options.gpu || false,
        memory: options.memory || '2GB',
        runtime: options.runtime || 'node'
      }
    });

    return response.data;
  }

  /**
   * Get job status and results
   * 
   * @param jobId - The job ID
   * @returns Promise resolving to job details
   * @throws {JobNotFoundError} If job doesn't exist
   * 
   * @example
   * ```typescript
   * const job = await client.getJob(123);
   * console.log(job.status);
   * ```
   */
  async getJob(jobId: number): Promise<Job> {
    const response = await this.client.get<Job>(`/api/jobs/${jobId}`);
    return response.data;
  }

  /**
   * Wait for job completion with polling
   * 
   * @param jobId - The job ID to wait for
   * @param timeout - Maximum time to wait in seconds (default: 600)
   * @param pollInterval - How often to check status in seconds (default: 5)
   * @param verbose - Log status updates to console (default: false)
   * @returns Promise resolving to completed job
   * @throws {TimeoutError} If job doesn't complete within timeout
   * 
   * @example
   * ```typescript
   * const result = await client.waitForJob(123, 300, 5, true);
   * if (result.status === 'completed') {
   *   console.log(result.result.output);
   * }
   * ```
   */
  async waitForJob(
    jobId: number, 
    timeout: number = 600, 
    pollInterval: number = 5,
    verbose: boolean = false
  ): Promise<Job> {
    const startTime = Date.now();
    const pollMs = pollInterval * 1000;

    if (verbose) {
      console.log(`⏳ Waiting for job ${jobId}...`);
    }

    while (Date.now() - startTime < timeout * 1000) {
      const job = await this.getJob(jobId);

      if (verbose) {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        console.log(`⌛ Status: ${job.status} (elapsed: ${elapsed}s)`);
      }

      if (job.status === 'completed' || job.status === 'failed') {
        if (verbose) {
          console.log(`✓ Job ${job.status}`);
        }
        return job;
      }

      await new Promise(resolve => setTimeout(resolve, pollMs));
    }

    throw new TimeoutError(`Job ${jobId} did not complete within ${timeout} seconds`);
  }

  /**
   * Cancel a running job
   * 
   * @param jobId - The job ID to cancel
   * @returns Promise resolving to true if cancelled
   * 
   * @example
   * ```typescript
   * await client.cancelJob(123);
   * ```
   */
  async cancelJob(jobId: number): Promise<boolean> {
    try {
      await this.client.delete(`/api/jobs/${jobId}`);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get account information
   * 
   * @returns Promise resolving to user details
   * 
   * @example
   * ```typescript
   * const info = await client.getBalance();
   * console.log(info.email, info.role);
   * ```
   */
  async getBalance(): Promise<UserInfo> {
    const response = await this.client.get<UserInfo>('/api/auth/user');
    return response.data;
  }

  /**
   * List recent jobs
   * 
   * @param limit - Maximum number of jobs to return (default: 100)
   * @returns Promise resolving to array of jobs
   * 
   * @example
   * ```typescript
   * const jobs = await client.listJobs(10);
   * jobs.forEach(job => console.log(job.id, job.status));
   * ```
   */
  async listJobs(limit: number = 100): Promise<Job[]> {
    const response = await this.client.get<Job[]>('/api/jobs');
    const jobs = response.data;
    return Array.isArray(jobs) ? jobs.slice(0, limit) : [];
  }
}

/**
 * Quick function to submit and optionally wait for a job
 * 
 * @param apiKey - Your DistributeX API key
 * @param code - Code to execute
 * @param runtime - Runtime environment (default: "node")
 * @param wait - Whether to wait for completion (default: true)
 * @param timeout - Max execution time in seconds (default: 300)
 * @returns Promise resolving to job result
 * 
 * @example
 * ```typescript
 * import { submitJob } from 'distributex-cloud';
 * 
 * const result = await submitJob(
 *   'dsx_...',
 *   'console.log("Hello")',
 *   'node',
 *   true
 * );
 * console.log(result.result.output);
 * ```
 */
export async function submitJob(
  apiKey: string,
  code: string,
  runtime: 'node' | 'python' = 'node',
  wait: boolean = true,
  timeout: number = 300
): Promise<Job> {
  const client = new DistributeXClient({ apiKey });
  const job = await client.submit({ code, runtime, timeout });
  
  if (wait) {
    return client.waitForJob(job.id);
  }
  
  return job;
}

// Export all types
export type {
  ClientConfig,
  JobOptions,
  JobStatus,
  JobResult,
  Job,
  UserInfo
};

// Example usage
if (require.main === module) {
  console.log('DistributeX JavaScript SDK - Example Usage');
  console.log('='.repeat(50));
  
  console.log('\n1. Basic Example:');
  console.log('-'.repeat(50));
  const example1 = `
import { DistributeXClient } from 'distributex-cloud';

const client = new DistributeXClient({
  apiKey: process.env.DISTRIBUTEX_API_KEY || 'dsx_...'
});

const job = await client.submit({
  code: 'console.log("Hello from DistributeX!")',
  runtime: 'node'
});

console.log('Job ID:', job.id);
const result = await client.waitForJob(job.id, 600, 5, true);
console.log('Output:', result.result.output);
`;
  console.log(example1);

  console.log('\n2. Data Processing Example:');
  console.log('-'.repeat(50));
  const example2 = `
const job = await client.submit({
  code: \`
    const data = [1, 2, 3, 4, 5];
    const result = {
      sum: data.reduce((a, b) => a + b, 0),
      count: data.length
    };
    console.log(JSON.stringify(result));
  \`,
  runtime: 'node',
  timeout: 60
});

const result = await client.waitForJob(job.id);
const output = JSON.parse(result.result.output);
console.log(output);
`;
  console.log(example2);

  console.log('\n' + '='.repeat(50));
  console.log('Documentation: https://docs.distributex.cloud');
  console.log('NPM: https://www.npmjs.com/package/distributex-cloud');
}
