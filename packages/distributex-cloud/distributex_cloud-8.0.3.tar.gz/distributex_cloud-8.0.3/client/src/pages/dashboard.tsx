import { GlassCard } from "@/components/ui/glass-card";
import { useWorkers, useJobs } from "@/hooks/use-distributex";
import { 
  Activity, 
  Server, 
  Cpu, 
  CheckCircle2, 
  XCircle,
  Clock
} from "lucide-react";
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from "recharts";
import { motion } from "framer-motion";

// Mock data for the chart
const chartData = [
  { time: '00:00', load: 2400 },
  { time: '04:00', load: 1398 },
  { time: '08:00', load: 9800 },
  { time: '12:00', load: 3908 },
  { time: '16:00', load: 4800 },
  { time: '20:00', load: 3800 },
  { time: '24:00', load: 4300 },
];

export default function Dashboard() {
  const { data: workers = [] } = useWorkers();
  const { data: jobs = [] } = useJobs();

  const activeWorkers = workers.filter(w => w.status === 'online').length;
  const completedJobs = jobs.filter(j => j.status === 'completed').length;
  const failedJobs = jobs.filter(j => j.status === 'failed').length;
  const pendingJobs = jobs.filter(j => j.status === 'pending').length;

  const stats = [
    {
      label: "Active Nodes",
      value: activeWorkers,
      total: workers.length,
      icon: Server,
      color: "text-primary",
      borderColor: "border-primary/20"
    },
    {
      label: "Jobs Completed",
      value: completedJobs,
      icon: CheckCircle2,
      color: "text-accent",
      borderColor: "border-accent/20"
    },
    {
      label: "Pending Queue",
      value: pendingJobs,
      icon: Clock,
      color: "text-yellow-500",
      borderColor: "border-yellow-500/20"
    },
    {
      label: "System Load",
      value: "42%",
      icon: Activity,
      color: "text-purple-500",
      borderColor: "border-purple-500/20"
    }
  ];

  return (
    <div className="space-y-8 p-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Network Overview</h1>
        <p className="text-muted-foreground">Real-time telemetry from distributed compute clusters.</p>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
          >
            <GlassCard className={`border-l-4 ${stat.borderColor}`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">{stat.label}</p>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-3xl font-bold font-mono text-white">
                      {stat.value}
                    </span>
                    {stat.total && (
                      <span className="text-sm text-muted-foreground">/ {stat.total}</span>
                    )}
                  </div>
                </div>
                <div className={`rounded-full bg-white/5 p-3 ${stat.color}`}>
                  <stat.icon className="h-6 w-6" />
                </div>
              </div>
            </GlassCard>
          </motion.div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <GlassCard className="col-span-2 min-h-[400px]" gradient>
          <div className="mb-6 flex items-center justify-between">
            <h3 className="font-semibold text-white">Compute Traffic</h3>
            <div className="flex gap-2">
               <span className="flex h-2 w-2 rounded-full bg-primary animate-pulse"></span>
               <span className="text-xs text-muted-foreground">Live</span>
            </div>
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorLoad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis 
                  dataKey="time" 
                  stroke="rgba(255,255,255,0.3)" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false}
                />
                <YAxis 
                  stroke="rgba(255,255,255,0.3)" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(0,0,0,0.8)', 
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '8px'
                  }}
                  itemStyle={{ color: '#fff' }}
                />
                <Area 
                  type="monotone" 
                  dataKey="load" 
                  stroke="hsl(var(--primary))" 
                  strokeWidth={2}
                  fillOpacity={1} 
                  fill="url(#colorLoad)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        <GlassCard className="col-span-1">
          <h3 className="mb-4 font-semibold text-white">Recent Activity</h3>
          <div className="space-y-4">
            {jobs.slice(0, 5).map((job) => (
              <div key={job.id} className="flex items-center justify-between border-b border-white/5 pb-3 last:border-0 last:pb-0">
                <div className="flex items-center gap-3">
                  <div className={`flex h-8 w-8 items-center justify-center rounded-lg border border-white/10 bg-white/5`}>
                    <Cpu className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white">{job.type}</p>
                    <p className="text-xs text-muted-foreground font-mono">ID: #{job.id}</p>
                  </div>
                </div>
                <div className={`px-2 py-1 rounded text-xs font-medium ${
                  job.status === 'completed' ? 'bg-primary/10 text-primary' :
                  job.status === 'failed' ? 'bg-destructive/10 text-destructive' :
                  'bg-yellow-500/10 text-yellow-500'
                }`}>
                  {job.status}
                </div>
              </div>
            ))}
            {jobs.length === 0 && (
              <div className="text-center py-8 text-muted-foreground text-sm">
                No recent activity recorded.
              </div>
            )}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
