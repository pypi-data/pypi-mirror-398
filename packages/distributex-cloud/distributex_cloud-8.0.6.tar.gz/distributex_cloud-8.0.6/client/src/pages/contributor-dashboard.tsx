import { useState } from "react";
import { useWorkers, useUser, useRemoveWorker } from "@/hooks/use-distributex";
import { GlassCard } from "@/components/ui/glass-card";
import { ShinyButton } from "@/components/ui/shiny-button";
import { Badge } from "@/components/ui/badge";
import { 
  Server, 
  Copy, 
  Terminal, 
  CheckCircle, 
  Activity,
  Eye,
  EyeOff,
  Loader2,
  Trash2,
  AlertCircle
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { useToast } from "@/hooks/use-toast";

export default function ContributorDashboard() {
  const { data: workersRaw, isLoading: workersLoading, error: workersError } = useWorkers();
  const { data: user, isLoading: userLoading, error: userError } = useUser();
  const { mutate: removeWorker } = useRemoveWorker();
  const { toast } = useToast();
  
  const [showApiKey, setShowApiKey] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // LOADING STATE
  if (workersLoading || userLoading) {
    return (
      <div className="flex h-[80vh] w-full items-center justify-center flex-col gap-4 text-white">
        <Loader2 className="h-10 w-10 animate-spin text-primary" />
        <p className="text-muted-foreground animate-pulse font-mono text-sm tracking-widest">INITIALIZING_SYSTEM...</p>
      </div>
    );
  }

  // ERROR STATE
  if (workersError || userError) {
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <GlassCard className="border-red-500/50 bg-red-500/5 p-8 flex flex-col items-center text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">Connection Error</h2>
          <p className="text-muted-foreground mb-6">We couldn't synchronize with the DistributeX network.</p>
          <ShinyButton onClick={() => window.location.reload()}>Retry Connection</ShinyButton>
        </GlassCard>
      </div>
    );
  }

  // DATA PREPARATION
  const workerList = Array.isArray(workersRaw) ? workersRaw : [];
  const activeWorkers = workerList.filter(w => w?.status === 'online').length;
  const totalJobs = workerList.reduce((acc, w) => acc + (Number(w?.jobsCompleted) || 0), 0);
  
  const fullApiKey = user?.apiKey || '';
  const hasApiKey = !!fullApiKey;
  const displayApiKey = hasApiKey ? `${fullApiKey.slice(0, 12)}...${fullApiKey.slice(-4)}` : 'N/A';

  const copyToClipboard = (text: string) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    toast({ title: "Copied to clipboard!" });
  };

  const handleRemoveWorker = async (workerId: string) => {
    if (!confirm("Are you sure you want to remove this worker?")) return;
    
    setDeletingId(workerId);
    removeWorker(workerId, {
      onSuccess: () => {
        toast({ title: "Worker removed successfully" });
        setDeletingId(null);
      },
      onError: () => {
        toast({ title: "Error removing worker", variant: "destructive" });
        setDeletingId(null);
      }
    });
  };

  // COMPLETE DOCKER COMMAND WITH DNS FIX
  const dockerCommand = `docker run -d \\
  --name distributex-worker \\
  --restart unless-stopped \\
  --dns 8.8.8.8 \\
  --dns 1.1.1.1 \\
  -e API_KEY="${fullApiKey}" \\
  -e API_URL="https://distributex-production-7fd2.up.railway.app" \\
  -v /var/run/docker.sock:/var/run/docker.sock \\
  distributexcloud/worker:latest`;

  return (
    <div className="space-y-8 p-8 animate-in fade-in duration-700">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white mb-2">
          Contributor Dashboard
        </h1>
        <p className="text-muted-foreground">
          Manage your compute nodes and track network contributions
        </p>
      </div>

      {/* Stats Section */}
      <div className="grid gap-6 sm:grid-cols-3">
        <GlassCard className="border-l-4 border-l-primary p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Active Workers</p>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-3xl font-bold font-mono text-white">{activeWorkers}</span>
                <span className="text-sm text-muted-foreground">/ {workerList.length}</span>
              </div>
            </div>
            <div className="rounded-full bg-primary/10 p-3 text-primary">
              <Server className="h-6 w-6" />
            </div>
          </div>
        </GlassCard>

        <GlassCard className="border-l-4 border-l-accent p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Total Jobs Done</p>
              <div className="mt-2">
                <span className="text-3xl font-bold font-mono text-white">{totalJobs}</span>
              </div>
            </div>
            <div className="rounded-full bg-accent/10 p-3 text-accent">
              <CheckCircle className="h-6 w-6" />
            </div>
          </div>
        </GlassCard>

        <GlassCard className="border-l-4 border-l-green-500 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">System Status</p>
              <div className="mt-2">
                <span className="text-xl font-bold text-green-500 uppercase tracking-widest">Online</span>
              </div>
            </div>
            <div className="rounded-full bg-green-500/10 p-3 text-green-500">
              <Activity className="h-6 w-6" />
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Setup Instructions */}
      <GlassCard gradient className="p-8 border-white/5">
        <div className="flex items-center gap-3 mb-8">
          <div className="p-3 rounded-lg bg-primary/10 text-primary">
            <Terminal className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">Worker Installation</h2>
            <p className="text-sm text-muted-foreground">Deploy a worker node with a single Docker command</p>
          </div>
        </div>

        <div className="space-y-6">
          {/* Step 1: API Key */}
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-[10px] font-black text-primary-foreground">1</span>
              <h3 className="font-semibold text-white">Your API Key</h3>
            </div>
            <div className="flex items-center gap-2 bg-black/60 rounded-lg p-3 border border-white/5">
              <code className="text-xs text-accent font-mono truncate flex-1 px-2">
                {showApiKey ? fullApiKey : displayApiKey}
              </code>
              <button onClick={() => setShowApiKey(!showApiKey)} className="p-2 hover:text-white text-muted-foreground transition-colors">
                {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
              <button onClick={() => copyToClipboard(fullApiKey)} className="p-2 hover:text-white text-muted-foreground border-l border-white/10 pl-3">
                <Copy className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Step 2: Docker Command */}
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-[10px] font-black text-primary-foreground">2</span>
              <h3 className="font-semibold text-white">Run Docker Command</h3>
            </div>
            <div className="relative bg-black/80 rounded-lg p-4 border border-white/5 overflow-x-auto">
              <pre className="text-xs text-primary font-mono whitespace-pre">{dockerCommand}</pre>
              <button
                onClick={() => copyToClipboard(dockerCommand)}
                className="absolute top-3 right-3 p-2 bg-primary/10 hover:bg-primary/20 rounded-md transition-colors"
              >
                <Copy className="h-4 w-4 text-primary" />
              </button>
            </div>
            <p className="text-xs text-muted-foreground">
              ⚠️ Requires Docker installed. <a href="https://docs.docker.com/get-docker/" target="_blank" className="text-primary hover:underline">Get Docker</a>
            </p>
          </div>

          {/* Step 3: Verify */}
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-[10px] font-black text-primary-foreground">3</span>
              <h3 className="font-semibold text-white">Verify Connection</h3>
            </div>
            <p className="text-sm text-muted-foreground ml-10">
              Your worker should appear below within 30 seconds. Check logs: <code className="text-accent">docker logs -f distributex-worker</code>
            </p>
          </div>
        </div>
      </GlassCard>

      {/* Active Workers Section */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white tracking-tight">Live Nodes</h2>
          <Badge variant="outline" className="bg-primary/5 text-primary border-primary/20 px-4 py-1">
            {workerList.length} Total
          </Badge>
        </div>
        
        {workerList.length === 0 ? (
          <GlassCard className="text-center py-24 border-dashed border-2 border-white/5">
            <Server className="h-12 w-12 text-muted-foreground/20 mx-auto mb-4" />
            <p className="text-muted-foreground font-medium tracking-tight">No active workers detected on your account.</p>
            <p className="text-xs text-muted-foreground/70 mt-2">Run the Docker command above to deploy your first worker.</p>
          </GlassCard>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {workerList.map((worker) => (
              <GlassCard key={worker.id} className="relative group overflow-hidden border-white/5 hover:border-primary/50 transition-all duration-300">
                <div className="p-5">
                  <div className="flex justify-between items-start mb-6">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${worker.status === 'online' ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                        <Server className={`h-5 w-5 ${worker.status === 'online' ? 'text-green-500' : 'text-red-500'}`} />
                      </div>
                      <div className="min-w-0">
                        <h3 className="font-bold text-white truncate text-sm">{worker.name || 'Worker Node'}</h3>
                        <p className="text-[9px] text-muted-foreground font-mono uppercase tracking-tighter">ID: {String(worker.id).slice(0, 12)}</p>
                      </div>
                    </div>
                    
                    <button
                      onClick={() => handleRemoveWorker(worker.id)}
                      disabled={deletingId === worker.id}
                      className="p-2 rounded-md bg-white/5 hover:bg-red-500/20 text-muted-foreground hover:text-red-400 transition-all"
                    >
                      {deletingId === worker.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <Trash2 className="h-3 w-3" />}
                    </button>
                  </div>

                  <div className="space-y-3 pt-4 border-t border-white/5">
                    <div className="flex justify-between items-center text-[10px]">
                      <span className="text-muted-foreground uppercase font-semibold">Network Status</span>
                      <span className={`font-bold uppercase tracking-widest ${worker.status === 'online' ? 'text-green-400' : 'text-red-400'}`}>
                        {worker.status}
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-[10px]">
                      <span className="text-muted-foreground uppercase font-semibold">Last Heartbeat</span>
                      <span className="text-white font-mono">
                        {worker.lastHeartbeat ? formatDistanceToNow(new Date(worker.lastHeartbeat), { addSuffix: true }) : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-[10px]">
                      <span className="text-muted-foreground uppercase font-semibold">Jobs Completed</span>
                      <span className="text-accent font-mono">{worker.jobsCompleted || 0}</span>
                    </div>
                  </div>
                </div>
              </GlassCard>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
