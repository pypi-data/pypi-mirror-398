import { useJobs } from "@/hooks/use-distributex";
import { GlassCard } from "@/components/ui/glass-card";
import { 
  Table, 
  TableHeader, 
  TableRow, 
  TableHead, 
  TableBody, 
  TableCell 
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Loader2, Cpu, FileJson } from "lucide-react";
import { format } from "date-fns";

export default function JobsPage() {
  const { data: jobs = [], isLoading } = useJobs();

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return <Badge className="bg-primary/20 text-primary border-primary/50 hover:bg-primary/30">Completed</Badge>;
      case "processing":
        return <Badge className="bg-accent/20 text-accent border-accent/50 hover:bg-accent/30 animate-pulse">Processing</Badge>;
      case "failed":
        return <Badge variant="destructive">Failed</Badge>;
      default:
        return <Badge variant="secondary">Pending</Badge>;
    }
  };

  return (
    <div className="space-y-8 p-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Job Queue</h1>
        <p className="text-muted-foreground">Monitor tasks running across the decentralized grid.</p>
      </div>

      <GlassCard className="p-0 overflow-hidden">
        <Table>
          <TableHeader className="bg-white/5">
            <TableRow className="border-white/5 hover:bg-transparent">
              <TableHead className="text-white">Job ID</TableHead>
              <TableHead className="text-white">Type</TableHead>
              <TableHead className="text-white">Status</TableHead>
              <TableHead className="text-white">Assigned Worker</TableHead>
              <TableHead className="text-white">Price</TableHead>
              <TableHead className="text-white">Created</TableHead>
              <TableHead className="text-right text-white">Payload</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-10">
                  <Loader2 className="mx-auto h-8 w-8 animate-spin text-primary" />
                </TableCell>
              </TableRow>
            ) : jobs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-10 text-muted-foreground">
                  No jobs found in the queue.
                </TableCell>
              </TableRow>
            ) : (
              jobs.map((job) => (
                <TableRow key={job.id} className="border-white/5 hover:bg-white/5 transition-colors">
                  <TableCell className="font-mono text-xs">#{job.id}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Cpu className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">{job.type}</span>
                    </div>
                  </TableCell>
                  <TableCell>{getStatusBadge(job.status)}</TableCell>
                  <TableCell>
                    {job.workerId ? (
                      <span className="text-accent font-mono text-xs">Worker #{job.workerId}</span>
                    ) : (
                      <span className="text-muted-foreground text-xs italic">Unassigned</span>
                    )}
                  </TableCell>
                  <TableCell className="font-mono text-primary">{job.price} CR</TableCell>
                  <TableCell className="text-muted-foreground text-xs">
                    {job.createdAt && format(new Date(job.createdAt), "MMM d, HH:mm")}
                  </TableCell>
                  <TableCell className="text-right">
                    <button className="text-muted-foreground hover:text-white transition-colors">
                      <FileJson className="h-4 w-4 ml-auto" />
                    </button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </GlassCard>
    </div>
  );
}
