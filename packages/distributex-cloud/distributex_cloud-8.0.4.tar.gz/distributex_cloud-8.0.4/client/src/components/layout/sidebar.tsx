// client/src/components/layout/sidebar.tsx - FIXED: Role-based navigation
import { Link, useLocation } from "wouter";
import { cn } from "@/lib/utils";
import { 
  Server, 
  Code2, 
  Cpu, 
  Terminal, 
  LogOut,
  Zap
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";

export function Sidebar() {
  const [location] = useLocation();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    window.location.href = "/auth";
  };

  // Navigation items based on role
  const contributorItems = [
    { 
      href: "/contributor", 
      icon: Server, 
      label: "Dashboard",
      description: "Overview & stats"
    },
    { 
      href: "/workers", 
      icon: Server, 
      label: "Workers",
      description: "Manage nodes"
    },
  ];

  const developerItems = [
    { 
      href: "/developer", 
      icon: Code2, 
      label: "Dashboard",
      description: "Overview & SDK"
    },
    { 
      href: "/jobs", 
      icon: Cpu, 
      label: "Jobs",
      description: "View all jobs"
    },
    { 
      href: "/submit", 
      icon: Terminal, 
      label: "Submit Job",
      description: "New compute task"
    },
  ];

  const navItems = user?.role === 'contributor' ? contributorItems : developerItems;

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-white/10 bg-background/80 backdrop-blur-xl">
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className="flex h-16 items-center border-b border-white/10 px-6">
          <Zap className="mr-2 h-6 w-6 text-primary animate-pulse" />
          <span className="text-xl font-bold tracking-tight">
            Distribute<span className="text-primary">X</span>
          </span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 px-3 py-6 overflow-y-auto">
          <div className="mb-4">
            <div className="px-3 mb-2">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                {user?.role === 'contributor' ? 'Contributor' : 'Developer'}
              </span>
            </div>
            {navItems.map((item) => {
              const isActive = location === item.href;
              return (
                <Link key={item.href} href={item.href}>
                  <div
                    className={cn(
                      "group flex flex-col px-3 py-3 text-sm font-medium rounded-lg transition-all duration-200 cursor-pointer mb-1",
                      isActive
                        ? "bg-primary/10 text-primary shadow-[0_0_15px_rgba(16,185,129,0.1)]"
                        : "text-muted-foreground hover:bg-white/5 hover:text-white"
                    )}
                  >
                    <div className="flex items-center">
                      <item.icon
                        className={cn(
                          "mr-3 h-5 w-5 flex-shrink-0 transition-colors",
                          isActive ? "text-primary" : "text-muted-foreground group-hover:text-white"
                        )}
                      />
                      <span>{item.label}</span>
                    </div>
                    <span className={cn(
                      "text-xs ml-8 mt-0.5",
                      isActive ? "text-primary/70" : "text-muted-foreground/70"
                    )}>
                      {item.description}
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        </nav>

        {/* Sign Out */}
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
