import { Link, useLocation } from "wouter";
import { cn } from "@/lib/utils";
import { 
  LayoutDashboard, 
  Server, 
  Cpu, 
  Terminal, 
  CreditCard, 
  Settings,
  LogOut,
  Zap
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";

const navItems = [
  { href: "/", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/workers", icon: Server, label: "Compute Nodes" },
  { href: "/jobs", icon: Cpu, label: "Job Queue" },
  { href: "/submit", icon: Terminal, label: "Submit Job" },
];

export function Sidebar() {
  const [location] = useLocation();
  const { logout } = useAuth();

  const handleLogout = () => {
    logout();
    window.location.href = "/auth";
  };

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-white/10 bg-background/80 backdrop-blur-xl">
      <div className="flex h-full flex-col">
        <div className="flex h-16 items-center border-b border-white/10 px-6">
          <Zap className="mr-2 h-6 w-6 text-primary animate-pulse" />
          <span className="text-xl font-bold tracking-tight">
            Distribute<span className="text-primary">X</span>
          </span>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-6">
          {navItems.map((item) => {
            const isActive = location === item.href;
            return (
              <Link key={item.href} href={item.href}>
                <div
                  className={cn(
                    "group flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 cursor-pointer",
                    isActive
                      ? "bg-primary/10 text-primary shadow-[0_0_15px_rgba(16,185,129,0.1)]"
                      : "text-muted-foreground hover:bg-white/5 hover:text-white"
                  )}
                >
                  <item.icon
                    className={cn(
                      "mr-3 h-5 w-5 flex-shrink-0 transition-colors",
                      isActive ? "text-primary" : "text-muted-foreground group-hover:text-white"
                    )}
                  />
                  {item.label}
                </div>
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-white/10 p-3">
          <button 
            className="flex w-full items-center px-3 py-2.5 text-sm font-medium text-muted-foreground rounded-lg hover:bg-white/5 hover:text-white transition-colors"
            onClick={handleLogout}
          >
            <LogOut className="mr-3 h-5 w-5" />
            Sign Out
          </button>
        </div>
      </div>
    </aside>
  );
}
