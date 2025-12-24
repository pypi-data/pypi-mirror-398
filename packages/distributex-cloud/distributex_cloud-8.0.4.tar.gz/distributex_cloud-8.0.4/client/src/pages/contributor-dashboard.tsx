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

  // 1. LOADING STATE GUARD
  if (workersLoading || userLoading) {
    return (
      <div className="flex h-[80vh] w-full items-center justify-center flex-col gap-4 text-white">
        <Loader2 className="h-10 w-10 animate-spin text-primary" />
        <p className="text-muted-foreground animate-pulse font-mono text-sm tracking-widest">INITIALIZING_SYSTEM...</p>
      </div>
    );
  }

  // 2. ERROR STATE GUARD
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

  // 3. DEFENSIVE DATA PREPARATION
  // Ensures 'workers' is always an array even if the hook returns null/undefined
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
            <p className="text-sm text-muted-foreground">Follow these steps to start earning credits</p>
          </div>
        </div>

        <div className="grid gap-8 md:grid-cols-3">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-[10px] font-black text-primary-foreground">1</span>
              <h3 className="font-semibold text-white">API Credentials</h3>
            </div>
            <div className="flex items-center gap-2 bg-black/60 rounded-lg p-2 border border-white/5">
              <code className="text-[10px] text-accent font-mono truncate flex-1 px-2">
                {showApiKey ? fullApiKey : displayApiKey}
              </code>
              <button onClick={() => setShowApiKey(!showApiKey)} className="p-1 hover:text-white text-muted-foreground">
                {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
              <button onClick={() => copyToClipboard(fullApiKey)} className="p-1 hover:text-white text-muted-foreground border-l border-white/10 pl-2">
                <Copy className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-[10px] font-black text-primary-foreground">2</span>
              <h3 className="font-semibold text-white">Docker Engine</h3>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">Ensure Docker Desktop or Engine is active on your host machine.</p>
            <a href="https://docs.docker.com/get-docker/" target="_blank" className="text-[10px] font-bold text-primary uppercase hover:underline flex items-center gap-1">
              Download Docker <Terminal className="h-3 w-3" />
            </a>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-[10px] font-black text-primary-foreground">3</span>
              <h3 className="font-semibold text-white">Deploy Node</h3>
            </div>
            <ShinyButton 
              className="w-full text-[10px] py-2 uppercase tracking-tighter"
              onClick={() => copyToClipboard(`docker run -d --name distributex-worker --restart always -e API_KEY=${fullApiKey} -e API_URL=https://distributex-production-7fd2.up.railway.app -v /var/run/docker.sock:/var/run/docker.sock distributexcloud/worker:latest`)}
            >
              Copy Run Command
            </ShinyButton>
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
                      <span className="text-muted-foreground uppercase font-semibold">Active Since</span>
                      <span className="text-white font-mono">
                        {worker.lastHeartbeat ? formatDistanceToNow(new Date(worker.lastHeartbeat), { addSuffix: true }) : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-[10px]">
                      <span className="text-muted-foreground uppercase font-semibold">Hardware</span>
                      <span className="text-accent font-mono">{(worker.specs as any)?.cpu || 'Standard'}</span>
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
