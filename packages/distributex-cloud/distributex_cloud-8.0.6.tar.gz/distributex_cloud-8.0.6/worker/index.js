// worker/index.js - COMPLETE FIX: Proper script execution
const axios = require('axios');
const { exec, execSync } = require('child_process');
const { promisify } = require('util');
const os = require('os');
const fs = require('fs').promises;
const path = require('path');

const execAsync = promisify(exec);

const API_KEY = process.env.API_KEY || process.env.WORKER_TOKEN;
const API_URL = (process.env.API_URL || 'https://distributex-production-7fd2.up.railway.app').replace(/\/+$/, '');
const HEARTBEAT_INTERVAL = parseInt(process.env.HEARTBEAT_INTERVAL || '30000', 10);

const TOTAL_CPUS = os.cpus().length;
const TOTAL_MEM_GB = os.totalmem() / 1024 / 1024 / 1024;
const SHARED_CPUS = (TOTAL_CPUS * 0.5).toFixed(2);
const SHARED_MEM_GB = (TOTAL_MEM_GB * 0.5).toFixed(2);

let HAS_GPU = false;
try {
  execSync('nvidia-smi', { stdio: 'ignore' });
  HAS_GPU = true;
} catch (e) {
  HAS_GPU = false;
}

let workerId = null;
let currentJob = null;
let isProcessing = false;
let consecutiveFailures = 0;
const MAX_CONSECUTIVE_FAILURES = 10;

console.log('🚀 Starting DistributeX Worker (Production Ready)...');
console.log(`📡 API URL: ${API_URL}`);
console.log(`⚙️  Resources: ${SHARED_CPUS} CPUs, ${SHARED_MEM_GB}GB RAM, GPU: ${HAS_GPU ? 'Yes' : 'No'}`);

if (!API_KEY) {
  console.error('❌ ERROR: API_KEY environment variable is required');
  process.exit(1);
}

// Create axios instance with retry logic
const axiosInstance = axios.create({
  timeout: 15000,
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
  }
});

// Add retry interceptor
axiosInstance.interceptors.response.use(
  response => {
    consecutiveFailures = 0;
    return response;
  },
  async error => {
    const config = error.config;
    
    if (!config || config.__retryCount >= 2) {
      return Promise.reject(error);
    }
    
    config.__retryCount = config.__retryCount || 0;
    config.__retryCount += 1;
    
    const delay = Math.min(1000 * Math.pow(2, config.__retryCount), 5000);
    await new Promise(resolve => setTimeout(resolve, delay));
    
    return axiosInstance(config);
  }
);

function getSystemSpecs() {
  const cpus = os.cpus();
  const totalMem = os.totalmem();
  
  return {
    cpu: `${cpus.length}x ${cpus[0]?.model || 'Unknown'}`,
    memory: `${(totalMem / 1024 / 1024 / 1024).toFixed(1)}GB`,
    platform: os.platform(),
    arch: os.arch(),
    hostname: os.hostname(),
    limits: {
      sharedCpu: SHARED_CPUS,
      sharedMemory: `${SHARED_MEM_GB}GB`,
      gpuAvailable: HAS_GPU
    }
  };
}

async function registerWorker() {
  try {
    const specs = getSystemSpecs();
    console.log('📋 Registering worker...');
    
    const response = await axiosInstance.post(`${API_URL}/api/workers`, {
      name: `Worker-${specs.hostname}`,
      hostname: specs.hostname,
      specs: specs,
      status: 'online'
    });

    if (!response.data || !response.data.id) {
      throw new Error('Invalid registration response');
    }

    workerId = response.data.id;
    consecutiveFailures = 0;
    console.log(`✅ Registered as Worker #${workerId}`);
    return workerId;
  } catch (error) {
    console.error('❌ Failed to register worker');
    if (error.response) {
      console.error(`Status: ${error.response.status}`);
      console.error(`Data:`, JSON.stringify(error.response.data, null, 2));
    } else if (error.code === 'EAI_AGAIN' || error.code === 'ENOTFOUND') {
      console.error('DNS resolution failed. Retrying in 10 seconds...');
      await new Promise(resolve => setTimeout(resolve, 10000));
      return registerWorker();
    } else {
      console.error(error.message);
    }
    process.exit(1);
  }
}

async function sendHeartbeat() {
  if (!workerId) return;

  try {
    const response = await axiosInstance.post(
      `${API_URL}/api/workers/${workerId}/heartbeat`,
      { specs: getSystemSpecs() }
    );

    if (response.data?.jobs && response.data.jobs.length > 0 && !isProcessing) {
      const job = response.data.jobs[0];
      console.log(`📬 Received job #${job.id} in heartbeat`);
      await claimAndProcessJob(job);
    }

    console.log(`💓 Heartbeat OK [Worker #${workerId}]`);
    consecutiveFailures = 0;
  } catch (error) {
    consecutiveFailures++;
    
    if (error.code === 'EAI_AGAIN' || error.code === 'ENOTFOUND') {
      console.error(`⚠️  DNS failure (${consecutiveFailures}/${MAX_CONSECUTIVE_FAILURES})`);
    } else {
      console.error(`⚠️  Heartbeat failed (${consecutiveFailures}/${MAX_CONSECUTIVE_FAILURES}):`, error.message);
    }
    
    if (consecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
      console.error('💥 Too many consecutive failures. Exiting...');
      process.exit(1);
    }
  }
}

async function pollForJobs() {
  if (isProcessing || currentJob || !workerId) return;

  try {
    const response = await axiosInstance.get(`${API_URL}/api/jobs/available`, {
      params: { workerId }
    });

    const jobs = response.data;
    if (jobs && Array.isArray(jobs) && jobs.length > 0) {
      const job = jobs[0];
      if (job.id && job.type) {
        await claimAndProcessJob(job);
      }
    }
    consecutiveFailures = 0;
  } catch (error) {
    if (error.response && error.response.status !== 404) {
      consecutiveFailures++;
      console.error(`⚠️  Poll error (${consecutiveFailures}/${MAX_CONSECUTIVE_FAILURES}):`, error.message);
    }
  }
}

async function claimAndProcessJob(job) {
  if (isProcessing || currentJob) return;
  
  isProcessing = true;
  currentJob = job;

  try {
    await axiosInstance.patch(`${API_URL}/api/jobs/${job.id}`, {
      status: 'processing',
      workerId: workerId
    });
    
    console.log(`📥 Claimed job #${job.id} [${job.type}]`);
    await processJobRealDocker(job);
  } catch (claimError) {
    console.log(`⏭️  Job #${job.id} already claimed: ${claimError.message}`);
    currentJob = null;
    isProcessing = false;
  }
}

async function processJobRealDocker(job) {
  const containerId = `distributex-job-${job.id}`;
  const startTime = Date.now();

  try {
    console.log(`⚙️  Processing job #${job.id} in Docker container...`);
    
    const timeout = job.payload?.timeout || 300;
    const runtime = job.payload?.runtime || 'node';
    const script = job.payload?.script || job.payload?.code || '';
    
    if (!script) throw new Error('No script provided');

    // CRITICAL FIX: Create proper temp directory and file
    const tempDir = path.join(os.tmpdir(), `job-${job.id}`);
    await fs.mkdir(tempDir, { recursive: true });
    
    const ext = runtime === 'python' ? 'py' : 'js';
    const scriptFileName = `script.${ext}`;
    const hostScriptPath = path.join(tempDir, scriptFileName);
    const containerScriptPath = `/app/${scriptFileName}`;
    
    // Write script to file
    await fs.writeFile(hostScriptPath, script, 'utf8');
    console.log(`📝 Script written to: ${hostScriptPath}`);

    // Determine Docker image and interpreter
    const image = runtime === 'python' ? 'python:3.11-slim' : 'node:20-alpine';
    const interpreter = runtime === 'python' ? 'python' : 'node';
    const gpuFlag = HAS_GPU ? '--gpus all' : '';

    // FIXED: Proper Docker command with working directory
    const dockerCmd = [
      'docker run',
      `--name ${containerId}`,
      '--rm',
      `--cpus="${SHARED_CPUS}"`,
      `--memory="${SHARED_MEM_GB}g"`,
      gpuFlag,
      '--network none',
      `-v "${hostScriptPath}:${containerScriptPath}:ro"`,
      `-w /app`,
      image,
      interpreter,
      scriptFileName
    ].filter(Boolean).join(' ');

    console.log(`🐳 Executing: ${dockerCmd}`);

    const { stdout, stderr } = await execAsync(dockerCmd, {
      timeout: timeout * 1000,
      maxBuffer: 50 * 1024 * 1024
    });

    const duration = ((Date.now() - startTime) / 1000).toFixed(2);

    await axiosInstance.patch(`${API_URL}/api/jobs/${job.id}`, {
      status: 'completed',
      result: {
        output: stdout.trim(),
        logs: stderr.trim(),
        duration: `${duration}s`,
        worker: workerId
      }
    });

    console.log(`✅ Job #${job.id} completed in ${duration}s`);

    // Cleanup
    await fs.rm(tempDir, { recursive: true, force: true });

  } catch (error) {
    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    console.error(`❌ Job #${job.id} failed:`, error.message);
    
    try {
      await axiosInstance.patch(`${API_URL}/api/jobs/${job.id}`, {
        status: 'failed',
        result: {
          error: error.message,
          logs: error.stderr || '',
          duration: `${duration}s`,
          worker: workerId
        }
      });
    } catch (reportError) {
      console.error('⚠️  Failed to report error:', reportError.message);
    }
  } finally {
    try {
      await execAsync(`docker rm -f ${containerId}`, { timeout: 5000 });
    } catch (e) {}
    
    try {
      const tempDir = path.join(os.tmpdir(), `job-${job.id}`);
      await fs.rm(tempDir, { recursive: true, force: true });
    } catch (e) {}
    
    currentJob = null;
    isProcessing = false;
  }
}

process.on('SIGTERM', async () => {
  console.log('\n🛑 Shutting down gracefully...');
  try {
    if (workerId) {
      await axiosInstance.post(`${API_URL}/api/workers/${workerId}/heartbeat`, {
        status: 'offline'
      });
    }
  } catch (e) {}
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('\n🛑 Interrupted, shutting down...');
  process.exit(0);
});

async function main() {
  console.log('🔧 Configuration:');
  console.log(`  API URL: ${API_URL}`);
  console.log(`  Shared CPU: ${SHARED_CPUS} cores`);
  console.log(`  Shared RAM: ${SHARED_MEM_GB}GB`);
  console.log(`  GPU: ${HAS_GPU ? 'Enabled' : 'Disabled'}\n`);

  await registerWorker();
  
  setInterval(sendHeartbeat, HEARTBEAT_INTERVAL);
  setInterval(pollForJobs, 10000);
  
  sendHeartbeat();
  pollForJobs();

  console.log('✅ Worker is running and ready for jobs...\n');
}

main().catch(err => {
  console.error('💥 Fatal error:', err.message);
  process.exit(1);
});
