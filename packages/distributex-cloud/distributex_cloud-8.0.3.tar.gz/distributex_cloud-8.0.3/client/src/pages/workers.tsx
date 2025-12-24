import { useState } from "react";
import { useWorkers, useCreateWorker } from "@/hooks/use-distributex";
import { GlassCard } from "@/components/ui/glass-card";
import { ShinyButton } from "@/components/ui/shiny-button";
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogDescription,
  DialogFooter
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Server, Power, Laptop, Terminal, Copy } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { useToast } from "@/hooks/use-toast";

export default function WorkersPage() {
  const { data: workers = [], isLoading } = useWorkers();
  const createWorker = useCreateWorker();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newWorkerName, setNewWorkerName] = useState("");
  const { toast } = useToast();

  const handleCreateWorker = async () => {
    try {
      await createWorker.mutateAsync({ name: newWorkerName, specs: {}, status: 'offline' });
      setIsModalOpen(false);
      setNewWorkerName("");
      toast({
        title: "Worker Created",
        description: "Configure your worker with the provided token.",
      });
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to create worker",
      });
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({ title: "Copied to clipboard" });
  };

  return (
    <div className="space-y-8 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Compute Nodes</h1>
          <p className="text-muted-foreground">Manage your distributed worker fleet.</p>
        </div>
        <ShinyButton onClick={() => setIsModalOpen(true)}>
          <Server className="mr-2 h-4 w-4" />
          Register Node
        </ShinyButton>
      </div>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        {isLoading ? (
          // Skeleton loading state
          Array(3).fill(0).map((_, i) => (
            <GlassCard key={i} className="h-48 animate-pulse bg-white/5" children={null} />
          ))
        ) : workers.map((worker) => (
          <GlassCard key={worker.id} className="relative group overflow-visible transition-all hover:border-primary/30">
            <div className="absolute top-4 right-4">
               <span className={`flex h-3 w-3 rounded-full ${worker.status === 'online' ? 'bg-primary shadow-[0_0_10px_#10b981]' : 'bg-muted-foreground'}`} />
            </div>
            
            <div className="mb-6 flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-white/10 to-transparent border border-white/5">
                <Laptop className="h-6 w-6 text-accent" />
              </div>
              <div>
                <h3 className="font-bold text-white text-lg">{worker.name}</h3>
                <p className="text-xs text-muted-foreground font-mono">ID: {worker.id}</p>
              </div>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-muted-foreground">Status</span>
                <span className={worker.status === 'online' ? 'text-primary' : 'text-muted-foreground'}>
                  {worker.status.toUpperCase()}
                </span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-muted-foreground">Last Heartbeat</span>
                <span className="text-white">
                  {worker.lastHeartbeat ? formatDistanceToNow(new Date(worker.lastHeartbeat), { addSuffix: true }) : 'Never'}
                </span>
              </div>
              <div className="flex justify-between">
                 <span className="text-muted-foreground">Specs</span>
                 <span className="text-white">{(worker.specs as any)?.cpu || 'Unknown CPU'}</span>
              </div>
            </div>

            <div className="mt-6">
              <button 
                className="w-full flex items-center justify-center gap-2 rounded bg-white/5 py-2 text-xs font-medium text-muted-foreground hover:bg-white/10 hover:text-white transition-colors group-hover:bg-primary/10 group-hover:text-primary"
                onClick={() => copyToClipboard(`docker run distributex/worker --id=${worker.id}`)}
              >
                <Terminal className="h-3 w-3" />
                Copy Launch Command
              </button>
            </div>
          </GlassCard>
        ))}
      </div>

      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="bg-background border-border sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Register New Compute Node</DialogTitle>
            <DialogDescription>
              Create a new worker identity. You'll receive a command to run on your machine.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Worker Name</Label>
              <Input
                id="name"
                value={newWorkerName}
                onChange={(e) => setNewWorkerName(e.target.value)}
                placeholder="e.g. AWS-US-East-1"
                className="bg-secondary/50 border-input"
              />
            </div>
          </div>
          <DialogFooter>
            <ShinyButton 
              onClick={handleCreateWorker} 
              disabled={createWorker.isPending || !newWorkerName}
              isLoading={createWorker.isPending}
            >
              Create Node
            </ShinyButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
