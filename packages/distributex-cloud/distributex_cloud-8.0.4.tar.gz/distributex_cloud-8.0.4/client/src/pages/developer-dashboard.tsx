import { useState, useEffect } from "react";
import { useJobs, useUser } from "@/hooks/use-distributex";
import { GlassCard } from "@/components/ui/glass-card";
import { ShinyButton } from "@/components/ui/shiny-button";
import { Badge } from "@/components/ui/badge";
import { 
  Code2, 
  Copy, 
  Terminal, 
  CheckCircle,
  Clock,
  XCircle,
  Eye,
  EyeOff,
  ExternalLink,
  Activity,
  Loader2
} from "lucide-react";
import { format } from "date-fns";
import { useToast } from "@/hooks/use-toast";
import { Link } from "wouter";

export default function DeveloperDashboard() {
  const { data: jobs = [] } = useJobs();
  const { data: user, isLoading: userLoading } = useUser();
  const { toast } = useToast();
  const [showApiKey, setShowApiKey] = useState(false);

  const completedJobs = jobs.filter(j => j.status === 'completed').length;
  const failedJobs = jobs.filter(j => j.status === 'failed').length;
  const pendingJobs = jobs.filter(j => j.status === 'pending').length;

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({ title: "Copied to clipboard!" });
  };

  // Debug logging
  useEffect(() => {
    console.log('Developer Dashboard - User Data:', user);
    console.log('Developer Dashboard - User Loading:', userLoading);
    console.log('Developer Dashboard - API Key:', user?.apiKey);
  }, [user, userLoading]);

  // Handle API key display
  const fullApiKey = user?.apiKey || '';
  const hasApiKey = fullApiKey.length > 0;
  const displayApiKey = hasApiKey ? `${fullApiKey.slice(0, 20)}...` : '';

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return <Badge className="bg-primary/20 text-primary border-primary/50">Completed</Badge>;
      case "processing":
        return <Badge className="bg-accent/20 text-accent border-accent/50 animate-pulse">Processing</Badge>;
      case "failed":
        return <Badge variant="destructive">Failed</Badge>;
      default:
        return <Badge variant="secondary">Pending</Badge>;
    }
  };

  return (
    <div className="space-y-8 p-8">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">
            Developer Dashboard
          </h1>
          <p className="text-muted-foreground">
            Submit jobs and utilize distributed compute power
          </p>
        </div>
        <Link href="/submit">
          <ShinyButton>
            <Terminal className="mr-2 h-4 w-4" />
            Submit New Job
          </ShinyButton>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid gap-6 sm:grid-cols-4">
        {[
          {
            label: "Total Jobs",
            value: jobs.length,
            icon: Activity,
            color: "text-blue-500"
          },
          {
            label: "Completed",
            value: completedJobs,
            icon: CheckCircle,
            color: "text-accent"
          },
          {
            label: "Pending",
            value: pendingJobs,
            icon: Clock,
            color: "text-yellow-500"
          },
          {
            label: "Failed",
            value: failedJobs,
            icon: XCircle,
            color: "text-destructive"
          }
        ].map((stat) => (
          <GlassCard key={stat.label} className="border-l-4 border-l-accent">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  {stat.label}
                </p>
                <div className="mt-2 text-3xl font-bold font-mono text-white">
                  {stat.value}
                </div>
              </div>
              <div className={`rounded-full bg-white/5 p-3 ${stat.color}`}>
                <stat.icon className="h-6 w-6" />
              </div>
            </div>
          </GlassCard>
        ))}
      </div>

      {/* API Integration */}
      <GlassCard gradient className="p-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 rounded-lg bg-accent/10">
            <Code2 className="h-6 w-6 text-accent" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">
              SDK Integration
            </h2>
            <p className="text-sm text-muted-foreground">
              Use Python or JavaScript to submit jobs programmatically
            </p>
          </div>
        </div>

        {/* API Key */}
        <div className="mb-6">
          <h3 className="font-semibold text-white mb-3">Your API Key</h3>
          
          {userLoading ? (
            <div className="flex items-center gap-2 bg-black/40 rounded-lg p-3 border border-white/5">
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
              <span className="text-muted-foreground text-sm">Loading API key...</span>
            </div>
          ) : !user ? (
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
              <span className="text-red-400 text-sm">Failed to load user data. Please refresh the page.</span>
            </div>
          ) : !hasApiKey ? (
            <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-3">
              <span className="text-yellow-400 text-sm">No API key found. Please contact support.</span>
            </div>
          ) : (
            <div className="flex gap-2">
              <div className="flex-1 bg-black/40 rounded-lg p-3 border border-white/5 font-mono text-sm flex items-center justify-between">
                <span className="text-accent break-all">
                  {showApiKey ? fullApiKey : displayApiKey}
                </span>
                <button
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="text-muted-foreground hover:text-white transition-colors ml-2 flex-shrink-0"
                >
                  {showApiKey ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
              <ShinyButton
                onClick={() => copyToClipboard(fullApiKey)}
                variant="outline"
                disabled={!hasApiKey}
              >
                <Copy className="h-4 w-4" />
              </ShinyButton>
            </div>
          )}
        </div>

        {/* Code Examples */}
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-white">Python SDK</h3>
              <a
                href="https://pypi.org/project/distributex-cloud/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent hover:underline text-sm flex items-center gap-1"
              >
                PyPI <ExternalLink className="h-3 w-3" />
              </a>
            </div>
            <div className="bg-black/40 rounded-lg p-4 border border-white/5 overflow-x-auto">
              <code className="text-sm text-accent font-mono whitespace-pre">
{`pip install distributex-cloud

from distributex import DistributeXClient

client = DistributeXClient(
    api_key="${displayApiKey || 'YOUR_API_KEY'}"
)

job = client.submit(
    type="script",
    code="print('Hello World')"
)

result = client.wait_for_job(job.id)
print(result['output'])`}
              </code>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-white">JavaScript SDK</h3>
              <a
                href="https://www.npmjs.com/package/distributex-cloud"
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent hover:underline text-sm flex items-center gap-1"
              >
                NPM <ExternalLink className="h-3 w-3" />
              </a>
            </div>
            <div className="bg-black/40 rounded-lg p-4 border border-white/5 overflow-x-auto">
              <code className="text-sm text-accent font-mono whitespace-pre">
{`npm install distributex-cloud

import { DistributeXClient } from 'distributex';

const client = new DistributeXClient({
  apiKey: '${displayApiKey || 'YOUR_API_KEY'}'
});

const job = await client.submit({
  type: 'script',
  code: 'console.log("Hello")'
});

const result = await client.waitForJob(job.id);
console.log(result.output);`}
              </code>
            </div>
          </div>
        </div>
      </GlassCard>

      {/* Recent Jobs */}
      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">Recent Jobs</h2>
          <Link href="/jobs">
            <ShinyButton variant="outline">
              View All Jobs
              <ExternalLink className="ml-2 h-4 w-4" />
            </ShinyButton>
          </Link>
        </div>

        {jobs.length === 0 ? (
          <GlassCard className="text-center py-12">
            <Terminal className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">
              No Jobs Yet
            </h3>
            <p className="text-muted-foreground mb-6">
              Submit your first job to see it here
            </p>
            <Link href="/submit">
              <ShinyButton>Submit Job</ShinyButton>
            </Link>
          </GlassCard>
        ) : (
          <GlassCard className="p-0 overflow-hidden">
            <div className="divide-y divide-white/5">
              {jobs.slice(0, 5).map((job) => (
                <div
                  key={job.id}
                  className="p-4 hover:bg-white/5 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-accent/10">
                        <Code2 className="h-4 w-4 text-accent" />
                      </div>
                      <div>
                        <div className="font-semibold text-white">
                          {job.type}
                        </div>
                        <div className="text-xs text-muted-foreground font-mono">
                          Job #{job.id}
                        </div>
                      </div>
                    </div>
                    {getStatusBadge(job.status)}
                  </div>
                  <div className="flex items-center justify-between text-sm ml-11">
                    <span className="text-muted-foreground">
                      {job.createdAt && format(new Date(job.createdAt), "MMM d, HH:mm")}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        )}
      </div>
    </div>
  );
}
