// worker/index.js - REAL DOCKER CONTAINER EXECUTION
const axios = require('axios');
const { exec, execSync } = require('child_process');
const { promisify } = require('util');
const os = require('os');
const fs = require('fs').promises;

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

console.log('🚀 Starting DistributeX Worker (Real Docker Execution)...');
console.log(`📡 API URL: ${API_URL}`);
console.log(`⚙️  Resources: ${SHARED_CPUS} CPUs, ${SHARED_MEM_GB}GB RAM, GPU: ${HAS_GPU ? 'Yes' : 'No'}`);

if (!API_KEY) {
  console.error('❌ ERROR: API_KEY environment variable is required');
  process.exit(1);
}

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
    
    const response = await axios.post(`${API_URL}/api/workers`, {
      name: `Worker-${specs.hostname}`,
      hostname: specs.hostname,
      specs: specs,
      status: 'online'
    }, {
      headers: {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
      },
      timeout: 15000
    });

    if (!response.data || !response.data.id) {
      throw new Error('Invalid registration response');
    }

    workerId = response.data.id;
    console.log(`✅ Registered as Worker #${workerId}`);
    return workerId;
  } catch (error) {
    console.error('❌ Failed to register worker');
    if (error.response) {
      console.error(`Status: ${error.response.status}`);
      console.error(`Data:`, JSON.stringify(error.response.data, null, 2));
    } else {
      console.error(error.message);
    }
    process.exit(1);
  }
}

async function sendHeartbeat() {
  if (!workerId) return;

  try {
    const response = await axios.post(
      `${API_URL}/api/workers/${workerId}/heartbeat`,
      { specs: getSystemSpecs() },
      {
        headers: {
          'X-API-Key': API_KEY,
          'Content-Type': 'application/json'
        },
        timeout: 10000
      }
    );

    // Check for available jobs
    if (response.data?.jobs && response.data.jobs.length > 0 && !isProcessing) {
      const job = response.data.jobs[0];
      console.log(`📬 Received job #${job.id} in heartbeat`);
      await claimAndProcessJob(job);
    }

    console.log(`💓 Heartbeat sent [Worker #${workerId}]`);
  } catch (error) {
    console.error('⚠️  Heartbeat failed:', error.message);
  }
}

async function pollForJobs() {
  if (isProcessing || currentJob || !workerId) return;

  try {
    const response = await axios.get(`${API_URL}/api/jobs/available`, {
      params: { workerId },
      headers: {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
      },
      timeout: 10000
    });

    const jobs = response.data;
    if (jobs && Array.isArray(jobs) && jobs.length > 0) {
      const job = jobs[0];
      if (job.id && job.type) {
        await claimAndProcessJob(job);
      }
    }
  } catch (error) {
    if (error.response && error.response.status !== 404) {
      console.error('⚠️  Poll error:', error.message);
    }
  }
}

async function claimAndProcessJob(job) {
  if (isProcessing || currentJob) return;
  
  isProcessing = true;
  currentJob = job;

  try {
    // Claim the job
    await axios.patch(`${API_URL}/api/jobs/${job.id}`, {
      status: 'processing',
      workerId: workerId
    }, {
      headers: {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
      },
      timeout: 10000
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
    
    let command = '';
    const timeout = job.payload?.timeout || 300;

    if (job.type === 'script' || job.type === 'compute') {
      const runtime = job.payload?.runtime || 'node';
      const script = job.payload?.script || job.payload?.code || '';
      
      if (!script) throw new Error('No script provided');

      // Write script to temp file
      const tempFile = `/tmp/job-${job.id}.${runtime === 'python' ? 'py' : 'js'}`;
      await fs.writeFile(tempFile, script);

      const escapedScript = script.replace(/'/g, `'\\''`);
      const image = runtime === 'python' ? 'python:3.11-slim' : 'node:20-alpine';
      const gpuFlag = HAS_GPU ? '--gpus all' : '';

      command = [
        `docker run --name ${containerId} --rm`,
        `--cpus="${SHARED_CPUS}"`,
        `--memory="${SHARED_MEM_GB}g"`,
        gpuFlag,
        `--network none`,
        `-v ${tempFile}:/app/script.${runtime === 'python' ? 'py' : 'js'}`,
        `${image} ${runtime === 'python' ? 'python' : 'node'} /app/script.${runtime === 'python' ? 'py' : 'js'}`
      ].filter(Boolean).join(' ');
    } else {
      throw new Error(`Unsupported job type: ${job.type}`);
    }

    const { stdout, stderr } = await execAsync(command, {
      timeout: timeout * 1000,
      maxBuffer: 50 * 1024 * 1024
    });

    const duration = ((Date.now() - startTime) / 1000).toFixed(2);

    await axios.patch(`${API_URL}/api/jobs/${job.id}`, {
      status: 'completed',
      result: {
        output: stdout.trim(),
        logs: stderr.trim(),
        duration: `${duration}s`,
        worker: workerId
      }
    }, {
      headers: {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
      },
      timeout: 10000
    });

    console.log(`✅ Job #${job.id} completed in ${duration}s`);

  } catch (error) {
    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    console.error(`❌ Job #${job.id} failed:`, error.message);
    
    try {
      await axios.patch(`${API_URL}/api/jobs/${job.id}`, {
        status: 'failed',
        result: {
          error: error.message,
          logs: error.stderr || '',
          duration: `${duration}s`,
          worker: workerId
        }
      }, {
        headers: {
          'X-API-Key': API_KEY,
          'Content-Type': 'application/json'
        },
        timeout: 10000
      });
    } catch (reportError) {
      console.error('⚠️  Failed to report error:', reportError.message);
    }
  } finally {
    try {
      await execAsync(`docker rm -f ${containerId}`, { timeout: 5000 });
    } catch (e) {}
    
    // Cleanup temp file
    const tempFile = `/tmp/job-${job.id}.*`;
    try {
      await execAsync(`rm -f ${tempFile}`);
    } catch (e) {}
    
    currentJob = null;
    isProcessing = false;
  }
}

process.on('SIGTERM', async () => {
  console.log('\n🛑 Shutting down gracefully...');
  try {
    if (workerId) {
      await axios.post(`${API_URL}/api/workers/${workerId}/heartbeat`, {
        status: 'offline'
      }, {
        headers: { 'X-API-Key': API_KEY },
        timeout: 5000
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
  
  // Send heartbeat every 30s
  setInterval(sendHeartbeat, HEARTBEAT_INTERVAL);
  
  // Poll for jobs every 10s
  setInterval(pollForJobs, 10000);
  
  // Initial heartbeat and poll
  sendHeartbeat();
  pollForJobs();

  console.log('✅ Worker is running with REAL Docker execution...\n');
}

main().catch(err => {
  console.error('💥 Fatal error:', err.message);
  process.exit(1);
});
