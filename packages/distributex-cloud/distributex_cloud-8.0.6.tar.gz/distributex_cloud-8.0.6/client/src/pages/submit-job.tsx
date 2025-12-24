import { useState } from "react";
import { useCreateJob } from "@/hooks/use-distributex";
import { useToast } from "@/hooks/use-toast";
import { useLocation } from "wouter";
import { GlassCard } from "@/components/ui/glass-card";
import { ShinyButton } from "@/components/ui/shiny-button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AlertCircle, Terminal, Code2, Play, Sparkles, Copy, BookOpen } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useUser } from "@/hooks/use-distributex";

const EXAMPLE_SCRIPTS = {
  javascript: `// Data Processing Example
const data = [1, 2, 3, 4, 5];
const result = data.map(x => x * 2);
console.log("Processed:", JSON.stringify(result));`,
  
  python: `# Machine Learning Example
import json

data = [10, 20, 30, 40, 50]
predictions = [x * 1.5 for x in data]
result = {"predictions": predictions, "count": len(predictions)}
print(json.dumps(result))`,
  
  compute: `// Fibonacci Computation
function fibonacci(n) {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}

const result = fibonacci(15);
console.log(JSON.stringify({ result, input: 15 }));`
};

export default function SubmitJobPage() {
  const { mutateAsync: createJob, isPending } = useCreateJob();
  const { data: user } = useUser();
  const { toast } = useToast();
  const [, setLocation] = useLocation();

  const [runtime, setRuntime] = useState<"javascript" | "python">("javascript");
  const [script, setScript] = useState(EXAMPLE_SCRIPTS.javascript);
  const [timeout, setTimeout] = useState("300");
  const [showSDK, setShowSDK] = useState(false);

  const apiKey = user?.apiKey || 'YOUR_API_KEY';

  const handleRuntimeChange = (value: "javascript" | "python") => {
    setRuntime(value);
    setScript(EXAMPLE_SCRIPTS[value]);
  };

  const loadExample = (type: keyof typeof EXAMPLE_SCRIPTS) => {
    setScript(EXAMPLE_SCRIPTS[type]);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({ title: "Copied to clipboard!" });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!script.trim()) {
      toast({
        variant: "destructive",
        title: "Script Required",
        description: "Please enter a script to execute",
      });
      return;
    }

    try {
      await createJob({
        type: "script",
        payload: {
          script: script,
          runtime: runtime === "python" ? "python" : "node",
          timeout: parseInt(timeout),
          requirements: []
        }
      });

      toast({
        title: "Job Submitted ✓",
        description: "Your task is now queued for processing by available workers.",
      });
      
      setLocation("/jobs");
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Submission Failed",
        description: error instanceof Error ? error.message : "Failed to submit job",
      });
    }
  };

  // SDK Examples
  const pythonSDK = `# Install SDK
pip install distributex-cloud

# Submit a job
from distributex import DistributeXClient

client = DistributeXClient(
    api_key="${apiKey}",
    base_url="https://distributex-production-7fd2.up.railway.app"
)

# Submit job
job = client.submit(
    type="script",
    script="""
import time
print("Processing data...")
time.sleep(2)
print("Complete!")
    """,
    requirements=[],
    timeout=300
)

print(f"Job ID: {job['id']}")

# Wait for completion
result = client.wait_for_job(job["id"])
print(f"Status: {result['status']}")
print(f"Output: {result['result']['output']}")`;

  const jsSDK = `// Install SDK
// npm install distributex-cloud

// Submit a job
import { DistributeXClient } from 'distributex-cloud';

const client = new DistributeXClient({
  apiKey: '${apiKey}',
  baseUrl: 'https://distributex-production-7fd2.up.railway.app'
});

// Submit job
const job = await client.submit({
  type: 'script',
  code: \`
    console.log('Processing data...');
    setTimeout(() => {
      console.log('Complete!');
    }, 2000);
  \`
});

console.log('Job ID:', job.id);

// Wait for completion
const result = await client.waitForJob(job.id);
console.log('Status:', result.status);
console.log('Output:', result.result.output);`;

  const curlExample = `# Submit job via REST API
curl -X POST https://distributex-production-7fd2.up.railway.app/api/jobs \\
  -H "X-API-Key: ${apiKey}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "type": "script",
    "payload": {
      "script": "console.log(\"Hello World\");",
      "runtime": "node",
      "timeout": 300
    }
  }'

# Check job status
curl -X GET https://distributex-production-7fd2.up.railway.app/api/jobs/:jobId \\
  -H "X-API-Key: ${apiKey}"`;

  return (
    <div className="max-w-6xl mx-auto space-y-8 p-8">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Submit Computational Task</h1>
          <p className="text-muted-foreground">Deploy code across distributed worker nodes</p>
        </div>
        <ShinyButton 
          variant="outline" 
          onClick={() => setShowSDK(!showSDK)}
        >
          <BookOpen className="mr-2 h-4 w-4" />
          {showSDK ? 'Hide' : 'Show'} SDK Guide
        </ShinyButton>
      </div>

      {/* SDK Integration Guide */}
      {showSDK && (
        <GlassCard gradient className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <Code2 className="h-6 w-6 text-accent" />
            <div>
              <h2 className="text-xl font-bold text-white">SDK Integration</h2>
              <p className="text-sm text-muted-foreground">Use these SDKs to submit jobs programmatically</p>
            </div>
          </div>

          <Tabs defaultValue="python" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="python">Python</TabsTrigger>
              <TabsTrigger value="javascript">JavaScript</TabsTrigger>
              <TabsTrigger value="curl">cURL</TabsTrigger>
            </TabsList>

            <TabsContent value="python" className="space-y-4">
              <div className="relative">
                <pre className="bg-black/80 rounded-lg p-4 text-sm text-primary font-mono overflow-x-auto">
                  <code>{pythonSDK}</code>
                </pre>
                <button
                  onClick={() => copyToClipboard(pythonSDK)}
                  className="absolute top-3 right-3 p-2 bg-primary/10 hover:bg-primary/20 rounded-md transition-colors"
                >
                  <Copy className="h-4 w-4 text-primary" />
                </button>
              </div>
              <div className="flex gap-2">
                <a 
                  href="https://pypi.org/project/distributex-cloud/" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-sm text-primary hover:underline"
                >
                  View on PyPI →
                </a>
                <span className="text-muted-foreground">|</span>
                <a 
                  href="https://github.com/DistributeX-Cloud/distributex" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-sm text-primary hover:underline"
                >
                  Documentation →
                </a>
              </div>
            </TabsContent>

            <TabsContent value="javascript" className="space-y-4">
              <div className="relative">
                <pre className="bg-black/80 rounded-lg p-4 text-sm text-primary font-mono overflow-x-auto">
                  <code>{jsSDK}</code>
                </pre>
                <button
                  onClick={() => copyToClipboard(jsSDK)}
                  className="absolute top-3 right-3 p-2 bg-primary/10 hover:bg-primary/20 rounded-md transition-colors"
                >
                  <Copy className="h-4 w-4 text-primary" />
                </button>
              </div>
              <div className="flex gap-2">
                <a 
                  href="https://www.npmjs.com/package/distributex-cloud" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-sm text-primary hover:underline"
                >
                  View on NPM →
                </a>
                <span className="text-muted-foreground">|</span>
                <a 
                  href="https://github.com/DistributeX-Cloud/distributex" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-sm text-primary hover:underline"
                >
                  Documentation →
                </a>
              </div>
            </TabsContent>

            <TabsContent value="curl" className="space-y-4">
              <div className="relative">
                <pre className="bg-black/80 rounded-lg p-4 text-sm text-primary font-mono overflow-x-auto whitespace-pre-wrap">
                  <code>{curlExample}</code>
                </pre>
                <button
                  onClick={() => copyToClipboard(curlExample)}
                  className="absolute top-3 right-3 p-2 bg-primary/10 hover:bg-primary/20 rounded-md transition-colors"
                >
                  <Copy className="h-4 w-4 text-primary" />
                </button>
              </div>
            </TabsContent>
          </Tabs>
        </GlassCard>
      )}

      <div className="grid gap-8 lg:grid-cols-3">
        {/* Main Form */}
        <form onSubmit={handleSubmit} className="lg:col-span-2 space-y-6">
          <GlassCard className="space-y-6">
            {/* Runtime Selection */}
            <div className="space-y-3">
              <Label>Runtime Environment</Label>
              <Tabs value={runtime} onValueChange={(v) => handleRuntimeChange(v as any)} className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="javascript">
                    <Code2 className="h-4 w-4 mr-2" />
                    JavaScript (Node.js)
                  </TabsTrigger>
                  <TabsTrigger value="python">
                    <Terminal className="h-4 w-4 mr-2" />
                    Python 3
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </div>

            {/* Script Editor */}
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <Label>Script Code</Label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => loadExample(runtime)}
                    className="text-xs text-primary hover:underline"
                  >
                    Load Example
                  </button>
                  <button
                    type="button"
                    onClick={() => loadExample("compute")}
                    className="text-xs text-accent hover:underline"
                  >
                    Load Compute Example
                  </button>
                </div>
              </div>
              <div className="relative">
                <Textarea 
                  value={script}
                  onChange={(e) => setScript(e.target.value)}
                  className="font-mono min-h-[400px] bg-black/80 border-input pl-12 resize-none text-sm"
                  spellCheck={false}
                  placeholder={`Enter your ${runtime} code here...`}
                />
                <div className="absolute top-3 left-3 text-muted-foreground pointer-events-none">
                  {runtime === "python" ? (
                    <Terminal className="h-5 w-5" />
                  ) : (
                    <Code2 className="h-5 w-5" />
                  )}
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                {runtime === "python" 
                  ? "Python 3.11 with common data science libraries included"
                  : "Node.js 20 with standard library access"}
              </p>
            </div>

            {/* Timeout */}
            <div className="space-y-3">
              <Label>Execution Timeout (seconds)</Label>
              <Select value={timeout} onValueChange={setTimeout}>
                <SelectTrigger className="bg-secondary/50 border-input">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="60">1 minute</SelectItem>
                  <SelectItem value="180">3 minutes</SelectItem>
                  <SelectItem value="300">5 minutes (recommended)</SelectItem>
                  <SelectItem value="600">10 minutes</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            {/* Submit */}
            <div className="pt-4 flex gap-4">
              <ShinyButton 
                type="submit" 
                className="flex-1"
                isLoading={isPending}
              >
                <Play className="mr-2 h-4 w-4" />
                Deploy to Network
              </ShinyButton>
              <ShinyButton
                type="button"
                variant="outline"
                onClick={() => setLocation("/jobs")}
              >
                View Jobs
              </ShinyButton>
            </div>
          </GlassCard>
        </form>

        {/* Sidebar Info */}
        <div className="space-y-6">
          {/* How It Works */}
          <GlassCard className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="h-5 w-5 text-primary" />
              <h3 className="font-semibold text-white">How Jobs Work</h3>
            </div>
            <div className="space-y-3 text-sm text-muted-foreground">
              <div className="flex gap-3">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-bold">1</span>
                <p>Job is queued and distributed to available workers</p>
              </div>
              <div className="flex gap-3">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-bold">2</span>
                <p>Worker claims job and executes in isolated Docker container</p>
              </div>
              <div className="flex gap-3">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-bold">3</span>
                <p>Results returned and available in job details</p>
              </div>
            </div>
          </GlassCard>

          {/* Documentation */}
          <Alert className="bg-blue-500/10 border-blue-500/20 text-blue-200">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Script Guidelines</AlertTitle>
            <AlertDescription className="text-xs mt-2 space-y-2">
              <p>✓ Use <code className="text-accent">console.log()</code> or <code className="text-accent">print()</code> for output</p>
              <p>✓ Jobs run in isolated Docker containers</p>
              <p>✓ No network access for security</p>
              <p>✓ Max timeout: 10 minutes</p>
            </AlertDescription>
          </Alert>

          {/* Examples */}
          <GlassCard className="p-6">
            <h3 className="font-semibold text-white mb-3">Example Use Cases</h3>
            <div className="space-y-2 text-xs text-muted-foreground">
              <div className="p-3 rounded-lg bg-white/5 border border-white/5">
                <p className="font-semibold text-white mb-1">Data Processing</p>
                <p>Transform, filter, and analyze datasets</p>
              </div>
              <div className="p-3 rounded-lg bg-white/5 border border-white/5">
                <p className="font-semibold text-white mb-1">Mathematical Computation</p>
                <p>Heavy calculations, simulations, algorithms</p>
              </div>
              <div className="p-3 rounded-lg bg-white/5 border border-white/5">
                <p className="font-semibold text-white mb-1">Machine Learning</p>
                <p>Model inference and predictions</p>
              </div>
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
