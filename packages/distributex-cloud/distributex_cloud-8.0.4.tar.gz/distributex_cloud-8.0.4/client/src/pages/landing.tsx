// client/src/pages/landing.tsx - FIXED: Real-time data and accurate text
import { Link } from "wouter";
import { Zap, Server, Code2, CheckCircle, Terminal, Github, ArrowRight } from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { ShinyButton } from "@/components/ui/shiny-button";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

interface Stats {
  activeWorkers: number;
  totalWorkers: number;
  completedJobs: number;
  totalJobs: number;
  onlineUsers: number;
}

async function fetchPublicStats(): Promise<Stats> {
  try {
    const [workersRes, jobsRes] = await Promise.all([
      fetch("/api/workers/stats").catch(() => ({ ok: false })),
      fetch("/api/jobs/stats").catch(() => ({ ok: false }))
    ]);

    let workers = { active: 0, total: 0, unique_users: 0 };
    let jobs = { completed: 0, total: 0 };

    if (workersRes.ok) {
      workers = await workersRes.json();
    }
    
    if (jobsRes.ok) {
      jobs = await jobsRes.json();
    }

    return {
      activeWorkers: workers.active || 0,
      totalWorkers: workers.total || 0,
      completedJobs: jobs.completed || 0,
      totalJobs: jobs.total || 0,
      onlineUsers: workers.unique_users || 0,
    };
  } catch (error) {
    console.error('Failed to fetch stats:', error);
    return {
      activeWorkers: 0,
      totalWorkers: 0,
      completedJobs: 0,
      totalJobs: 0,
      onlineUsers: 0,
    };
  }
}

export default function LandingPage() {
  const { data: stats, refetch } = useQuery({
    queryKey: ["public-stats"],
    queryFn: fetchPublicStats,
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  // Animated counter
  const [displayStats, setDisplayStats] = useState({
    activeWorkers: 0,
    completedJobs: 0,
    onlineUsers: 0,
  });

  useEffect(() => {
    if (stats) {
      const duration = 1000;
      const steps = 20;
      const interval = duration / steps;

      let step = 0;
      const timer = setInterval(() => {
        step++;
        const progress = step / steps;

        setDisplayStats({
          activeWorkers: Math.floor(stats.activeWorkers * progress),
          completedJobs: Math.floor(stats.completedJobs * progress),
          onlineUsers: Math.floor(stats.onlineUsers * progress),
        });

        if (step >= steps) clearInterval(timer);
      }, interval);

      return () => clearInterval(timer);
    }
  }, [stats]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-background to-background/50">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(16,185,129,0.1),transparent_50%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_80%,rgba(34,211,238,0.1),transparent_50%)]" />
        
        <nav className="relative z-10 flex items-center justify-between p-6 max-w-7xl mx-auto">
          <div className="flex items-center gap-2">
            <Zap className="h-8 w-8 text-primary animate-pulse" />
            <span className="text-2xl font-bold">
              Distribute<span className="text-primary">X</span>
            </span>
          </div>
          <Link href="/auth">
            <ShinyButton>Get Started Free</ShinyButton>
          </Link>
        </nav>

        <div className="relative z-10 max-w-7xl mx-auto px-6 py-24 text-center">
          <div className="inline-flex items-center gap-2 bg-primary/10 border border-primary/20 rounded-full px-4 py-2 mb-8">
            <span className="h-2 w-2 rounded-full bg-primary animate-pulse" />
            <span className="text-sm text-primary font-medium">Open Source • Decentralized • Free</span>
          </div>
          
          <h1 className="text-6xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-white via-white to-white/60 bg-clip-text text-transparent">
            Distributed Computing<br />Made Simple
          </h1>
          
          <p className="text-xl text-muted-foreground mb-12 max-w-3xl mx-auto">
            Share idle compute resources or run computational workloads across a decentralized network. 
            No servers to manage, pay-per-use pricing, instant scaling.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-20">
            <Link href="/auth">
              <ShinyButton className="text-lg px-8 py-6">
                Start Computing Free
                <ArrowRight className="ml-2 h-5 w-5" />
              </ShinyButton>
            </Link>
            <a href="https://github.com/DistributeX-Cloud" target="_blank" rel="noopener">
              <ShinyButton variant="outline" className="text-lg px-8 py-6">
                <Github className="mr-2 h-5 w-5" />
                View on GitHub
              </ShinyButton>
            </a>
          </div>

          {/* Live Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <GlassCard className="text-center">
              <div className="flex items-center justify-center mb-3">
                <Server className="h-8 w-8 text-primary" />
                {stats?.activeWorkers > 0 && (
                  <span className="ml-2 h-2 w-2 rounded-full bg-primary animate-pulse" />
                )}
              </div>
              <div className="text-3xl font-bold text-white mb-1 font-mono">
                {displayStats.activeWorkers}
              </div>
              <div className="text-sm text-muted-foreground">Active Workers</div>
            </GlassCard>

            <GlassCard className="text-center">
              <Zap className="h-8 w-8 text-primary mx-auto mb-3" />
              <div className="text-3xl font-bold text-white mb-1 font-mono">
                {displayStats.completedJobs}
              </div>
              <div className="text-sm text-muted-foreground">Jobs Completed</div>
            </GlassCard>

            <GlassCard className="text-center">
              <CheckCircle className="h-8 w-8 text-accent mx-auto mb-3" />
              <div className="text-3xl font-bold text-white mb-1 font-mono">
                {displayStats.onlineUsers}
              </div>
              <div className="text-sm text-muted-foreground">Contributors</div>
            </GlassCard>
          </div>
        </div>
      </div>

      {/* Two Paths Section */}
      <div className="max-w-7xl mx-auto px-6 py-24">
        <h2 className="text-4xl font-bold text-center mb-4">Two Ways to Use DistributeX</h2>
        <p className="text-center text-muted-foreground mb-16">
          Earn by sharing resources or access compute power on-demand
        </p>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Contributors */}
          <GlassCard className="p-8 border-l-4 border-l-primary" gradient>
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-lg bg-primary/10">
                <Server className="h-8 w-8 text-primary" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-white">Contributors</h3>
                <p className="text-sm text-muted-foreground">Monetize idle hardware</p>
              </div>
            </div>

            <ul className="space-y-4 mb-8">
              {[
                "Run workers with a single Docker command",
                "Earn from idle CPU & GPU time",
                "Automatic job distribution",
                "Set your own resource limits",
                "100% free to join"
              ].map((feature) => (
                <li key={feature} className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                  <span className="text-muted-foreground">{feature}</span>
                </li>
              ))}
            </ul>

            <div className="bg-black/40 rounded-lg p-4 border border-white/5 mb-6">
              <div className="flex items-center gap-2 mb-2">
                <Terminal className="h-4 w-4 text-accent" />
                <span className="text-xs text-muted-foreground font-mono">One Command Setup</span>
              </div>
              <code className="text-sm text-accent font-mono">
                docker run -e API_KEY=your_key distributex/worker
              </code>
            </div>

            <Link href="/auth">
              <ShinyButton className="w-full">
                Start Contributing
                <ArrowRight className="ml-2 h-4 w-4" />
              </ShinyButton>
            </Link>
          </GlassCard>

          {/* Developers */}
          <GlassCard className="p-8 border-l-4 border-l-accent" gradient>
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-lg bg-accent/10">
                <Code2 className="h-8 w-8 text-accent" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-white">Developers</h3>
                <p className="text-sm text-muted-foreground">Run distributed workloads</p>
              </div>
            </div>

            <ul className="space-y-4 mb-8">
              {[
                "Run Python, Node.js, or custom code",
                "Scale from 1 to 1000+ machines",
                "Simple Python & JavaScript SDKs",
                "Pay only for compute time used",
                "No infrastructure to manage"
              ].map((feature) => (
                <li key={feature} className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-accent flex-shrink-0 mt-0.5" />
                  <span className="text-muted-foreground">{feature}</span>
                </li>
              ))}
            </ul>

            <div className="bg-black/40 rounded-lg p-4 border border-white/5 mb-6">
              <div className="flex items-center gap-2 mb-2">
                <Code2 className="h-4 w-4 text-accent" />
                <span className="text-xs text-muted-foreground font-mono">Python Example</span>
              </div>
              <code className="text-sm text-accent font-mono block">
                from distributex import Client<br/>
                job = client.submit(code="...")<br/>
                result = client.wait(job.id)
              </code>
            </div>

            <Link href="/auth">
              <ShinyButton variant="outline" className="w-full">
                Start Building
                <ArrowRight className="ml-2 h-4 w-4" />
              </ShinyButton>
            </Link>
          </GlassCard>
        </div>
      </div>

      {/* How It Works */}
      <div className="max-w-7xl mx-auto px-6 py-24">
        <h2 className="text-4xl font-bold text-center mb-16">How It Works</h2>
        
        <div className="grid md:grid-cols-3 gap-8">
          {[
            {
              step: "1",
              title: "Sign Up",
              description: "Create a free account. Choose contributor to share compute or developer to submit jobs.",
              icon: Zap
            },
            {
              step: "2",
              title: "Connect",
              description: "Contributors run Docker workers. Developers use Python/JS SDKs to submit jobs via API.",
              icon: Server
            },
            {
              step: "3",
              title: "Compute",
              description: "Jobs are distributed to available workers automatically. Get results in seconds or minutes.",
              icon: CheckCircle
            }
          ].map((item) => (
            <div key={item.step} className="text-center">
              <div className="relative inline-flex mb-6">
                <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full" />
                <div className="relative p-6 rounded-2xl bg-gradient-to-br from-primary/10 to-transparent border border-primary/20">
                  <item.icon className="h-12 w-12 text-primary" />
                </div>
              </div>
              <div className="text-sm font-mono text-primary mb-2">STEP {item.step}</div>
              <h3 className="text-xl font-bold text-white mb-3">{item.title}</h3>
              <p className="text-muted-foreground">{item.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* CTA */}
      <div className="max-w-4xl mx-auto px-6 py-24 text-center">
        <GlassCard className="p-12" gradient>
          <h2 className="text-4xl font-bold mb-4">Ready to Get Started?</h2>
          <p className="text-xl text-muted-foreground mb-8">
            Join the decentralized compute network. Free to join, no credit card required.
          </p>
          <Link href="/auth">
            <ShinyButton className="text-lg px-8 py-6">
              Create Free Account
              <ArrowRight className="ml-2 h-5 w-5" />
            </ShinyButton>
          </Link>
        </GlassCard>
      </div>

      {/* Footer */}
      <footer className="border-t border-white/5 py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <Zap className="h-6 w-6 text-primary" />
              <span className="font-bold">DistributeX</span>
            </div>
            <div className="text-sm text-muted-foreground">
              © 2024 DistributeX. Open source distributed computing platform.
            </div>
            <div className="flex gap-6">
              <a href="https://github.com/DistributeX-Cloud" target="_blank" rel="noopener" className="text-muted-foreground hover:text-primary transition-colors">
                <Github className="h-5 w-5" />
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
