// worker/index.js
const axios = require('axios');
const { exec } = require('child_process');
const { promisify } = require('util');
const os = require('os');

const execAsync = promisify(exec);

const API_URL = process.env.API_URL || 'https://api.distributex.cloud';
const WORKER_TOKEN = process.env.WORKER_TOKEN;
const MAX_CPU_PERCENT = parseInt(process.env.MAX_CPU_PERCENT || '50', 10);
const MAX_MEMORY_GB = parseInt(process.env.MAX_MEMORY_GB || '2', 10);
const HEARTBEAT_INTERVAL = parseInt(process.env.HEARTBEAT_INTERVAL || '30000', 10);

let workerId = null;
let currentJob = null;

// Get system specs
function getSystemSpecs() {
  const cpus = os.cpus();
  const totalMem = os.totalmem();
  const freeMem = os.freemem();

  return {
    cpu: `${cpus.length}x ${cpus[0].model}`,
    memory: `${(totalMem / 1024 / 1024 / 1024).toFixed(1)}GB`,
    platform: os.platform(),
    arch: os.arch()
  };
}

// Check system resources before accepting jobs
function canAcceptJob() {
  const loadAvg = os.loadavg()[0] || 0;
  const cpuCount = os.cpus().length || 1;
  const cpuUsage = (loadAvg / cpuCount) * 100;

  const totalMem = os.totalmem();
  const freeMem = os.freemem();
  const memUsage = ((totalMem - freeMem) / totalMem) * 100;

  return cpuUsage < MAX_CPU_PERCENT && memUsage < 80;
}

// Register worker on startup
async function registerWorker() {
  try {
    const response = await axios.post(`${API_URL}/api/workers`, {
      name: `Worker-${os.hostname()}`,
      specs: getSystemSpecs(),
      status: 'online'
    }, {
      headers: {
        'Authorization': `Bearer ${WORKER_TOKEN}`
      },
      timeout: 10000
    });

    workerId = response.data.id;
    console.log(`✓ Registered as worker #${workerId}`);
    return workerId;
  } catch (error) {
    console.error('✗ Failed to register worker:', (error && error.message) || error);
    process.exit(1);
  }
}

// Send heartbeat
async function sendHeartbeat() {
  if (!workerId) return;

  try {
    await axios.post(`${API_URL}/api/workers/${workerId}/heartbeat`, {
      specs: getSystemSpecs(),
      canAcceptJob: canAcceptJob()
    }, {
      headers: {
        'Authorization': `Bearer ${WORKER_TOKEN}`
      },
      timeout: 10000
    });
    console.log(`❤ Heartbeat sent`);
  } catch (error) {
    console.error('✗ Heartbeat failed:', (error && error.message) || error);
  }
}

// Poll for jobs
async function pollForJobs() {
  if (currentJob || !canAcceptJob()) return;

  try {
    const response = await axios.get(`${API_URL}/api/jobs/available`, {
      params: { workerId },
      headers: {
        'Authorization': `Bearer ${WORKER_TOKEN}`
      },
      timeout: 10000
    });

    if (response.data && response.data.id) {
      currentJob = response.data;
      console.log(`→ Accepted job #${currentJob.id}`);
      await processJob(currentJob);
    }
  } catch (error) {
    // No jobs available or error (silently ignore to allow retry)
    // console.error('Job poll error:', error && error.message);
  }
}

// Process job in Docker container
async function processJob(job) {
  const containerId = `distributex-job-${job.id}`;

  try {
    // Update job status
    await axios.patch(`${API_URL}/api/jobs/${job.id}`, {
      status: 'processing',
      workerId
    }, {
      headers: {
        'Authorization': `Bearer ${WORKER_TOKEN}`
      },
      timeout: 10000
    });

    // Prepare job based on type
    let command = '';

    if (job.type === 'script' || job.type === 'compute') {
      // Run Node.js or Python script
      const runtime = job.payload.runtime || 'node';
      const script = job.payload.script || job.payload.code || '';

      // Safely escape single quotes inside script for inner '-c' argument
      const escapedScript = script.replace(/'/g, `'\\''`);

      // Build docker run command; --cpus expects a decimal (e.g. 0.5)
      const cpus = Math.max(0.1, (MAX_CPU_PERCENT / 100).toFixed(2));
      command = `docker run --name ${containerId} --rm --cpus="${cpus}" --memory="${MAX_MEMORY_GB}g" --network none ${runtime}:latest ${runtime === 'node' ? 'node' : 'python'} -c '${escapedScript}'`;
    } else {
      throw new Error(`Unsupported job type: ${job.type}`);
    }

    // Execute with timeout
    const timeout = (job.payload && job.payload.timeout) || 300; // seconds
    const { stdout, stderr } = await execAsync(command, {
      timeout: timeout * 1000,
      maxBuffer: 50 * 1024 * 1024 // 50MB
    });

    // Report success
    await axios.patch(`${API_URL}/api/jobs/${job.id}`, {
      status: 'completed',
      result: {
        output: stdout,
        logs: stderr
      }
    }, {
      headers: {
        'Authorization': `Bearer ${WORKER_TOKEN}`
      },
      timeout: 10000
    });

    console.log(`✓ Job #${job.id} completed`);

  } catch (error) {
    // Report failure
    try {
      await axios.patch(`${API_URL}/api/jobs/${job.id}`, {
        status: 'failed',
        result: {
          error: (error && error.message) || String(error),
          logs: (error && error.stderr) || ''
        }
      }, {
        headers: {
          'Authorization': `Bearer ${WORKER_TOKEN}`
        },
        timeout: 10000
      });
    } catch (e) {
      // swallow
    }

    console.error(`✗ Job #${job.id} failed:`, (error && error.message) || error);
  } finally {
    // Cleanup container if present
    try {
      await execAsync(`docker rm -f ${containerId}`, { timeout: 10000 });
    } catch (e) { /* ignore */ }
    currentJob = null;
  }
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('Shutting down...');
  try {
    if (workerId) {
      await axios.patch(`${API_URL}/api/workers/${workerId}`, { status: 'offline' }, {
        headers: { 'Authorization': `Bearer ${WORKER_TOKEN}` },
        timeout: 5000
      });
    }
  } catch (e) { /* ignore */ }
  process.exit(0);
});

// Main
async function main() {
  console.log('🚀 DistributeX Worker Starting...');

  if (!WORKER_TOKEN) {
    console.error('✗ WORKER_TOKEN environment variable required');
    process.exit(1);
  }

  // Register
  await registerWorker();

  // Start heartbeat
  setInterval(sendHeartbeat, HEARTBEAT_INTERVAL);

  // Start polling for jobs
  setInterval(pollForJobs, 5000);

  // Initial immediate poll/heartbeat
  sendHeartbeat();
  pollForJobs();

  console.log('✓ Worker ready and polling for jobs');
}

main().catch(err => {
  console.error('Fatal error:', err && err.message ? err.message : err);
  process.exit(1);
});
