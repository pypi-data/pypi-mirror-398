import { useState } from "react";
import { useCreateJob, useUser } from "@/hooks/use-distributex";
import { useToast } from "@/hooks/use-toast";
import { useLocation } from "wouter";
import { GlassCard } from "@/components/ui/glass-card";
import { ShinyButton } from "@/components/ui/shiny-button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AlertCircle, Terminal, Coins, Code2 } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export default function SubmitJobPage() {
  const { mutateAsync: createJob, isPending } = useCreateJob();
  const { data: user } = useUser();
  const { toast } = useToast();
  const [, setLocation] = useLocation();

  const [jobType, setJobType] = useState("script");
  const [price, setPrice] = useState("10");
  const [payload, setPayload] = useState('{\n  "script": "console.log(\'Hello World\')"\n}');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const parsedPayload = JSON.parse(payload);
      
      await createJob({
        type: jobType,
        price: parseInt(price),
        payload: parsedPayload
      });

      toast({
        title: "Job Submitted",
        description: "Your task has been queued for processing.",
      });
      
      setLocation("/jobs");
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Submission Failed",
        description: error instanceof Error ? error.message : "Invalid JSON payload or server error",
      });
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 p-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Submit Task</h1>
        <p className="text-muted-foreground">Deploy a computational payload to the grid.</p>
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        <form onSubmit={handleSubmit} className="lg:col-span-2 space-y-6">
          <GlassCard className="space-y-6">
            <div className="grid gap-2">
              <Label>Task Type</Label>
              <Select value={jobType} onValueChange={setJobType}>
                <SelectTrigger className="bg-secondary/50 border-input">
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="script">NodeJS Script</SelectItem>
                  <SelectItem value="render">3D Render (Blender)</SelectItem>
                  <SelectItem value="compute">Scientific Compute (Python)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-2">
              <Label className="flex justify-between">
                <span>Payload Configuration</span>
                <span className="text-xs text-muted-foreground font-mono">JSON</span>
              </Label>
              <div className="relative">
                <Textarea 
                  value={payload}
                  onChange={(e) => setPayload(e.target.value)}
                  className="font-mono min-h-[300px] bg-secondary/50 border-input pl-10 resize-none"
                  spellCheck={false}
                />
                <div className="absolute top-3 left-3 text-muted-foreground">
                  <Code2 className="h-5 w-5" />
                </div>
              </div>
            </div>

            <div className="grid gap-2">
              <Label>Bid Price (Credits)</Label>
              <div className="relative">
                <Input
                  type="number"
                  min="1"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  className="pl-10 bg-secondary/50 border-input"
                />
                <Coins className="absolute left-3 top-3 h-4 w-4 text-primary" />
              </div>
              <p className="text-xs text-muted-foreground">Higher bids are prioritized by workers.</p>
            </div>
            
            <div className="pt-4">
              <ShinyButton 
                type="submit" 
                className="w-full"
                isLoading={isPending}
              >
                <Terminal className="mr-2 h-4 w-4" />
                Deploy to Grid
              </ShinyButton>
            </div>
          </GlassCard>
        </form>

        <div className="space-y-6">
          <GlassCard gradient className="border-l-4 border-l-accent">
            <h3 className="font-semibold text-white mb-2">Current Balance</h3>
            <div className="text-3xl font-mono font-bold text-primary mb-1">
              {user?.credits ?? 0} CR
            </div>
            <p className="text-xs text-muted-foreground">
              Estimated cost: <span className="text-white">{price} CR</span>
            </p>
          </GlassCard>

          <Alert className="bg-blue-500/10 border-blue-500/20 text-blue-200">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Documentation</AlertTitle>
            <AlertDescription className="text-xs mt-2">
              Ensure your payload matches the schema for the selected job type. 
              Scripts have a max timeout of 60s.
            </AlertDescription>
          </Alert>
        </div>
      </div>
    </div>
  );
}
