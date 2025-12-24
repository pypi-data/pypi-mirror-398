import { useUser } from "@/hooks/use-distributex";
import { Badge } from "@/components/ui/badge";
import { Loader2, Coins, Bell } from "lucide-react";

export function Topbar() {
  const { data: user, isLoading } = useUser();

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-white/10 bg-background/80 px-6 backdrop-blur-xl">
      <div className="flex items-center gap-4">
        {/* Breadcrumb placeholder or global status */}
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
          <span className="text-xs font-mono text-primary uppercase tracking-wider">System Online</span>
        </div>
      </div>

      <div className="flex items-center gap-6">
        <button className="relative text-muted-foreground hover:text-white transition-colors">
          <Bell className="h-5 w-5" />
          <span className="absolute top-0 right-0 h-2 w-2 rounded-full bg-accent animate-ping" />
          <span className="absolute top-0 right-0 h-2 w-2 rounded-full bg-accent" />
        </button>

        <div className="h-6 w-px bg-white/10" />

        <div className="flex items-center gap-3">
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          ) : (
            <>
              <div className="flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1">
                <Coins className="h-4 w-4 text-primary" />
                <span className="font-mono text-sm font-bold text-primary">
                  {user?.credits?.toLocaleString() ?? 0} CR
                </span>
              </div>
              <div className="flex items-center gap-3">
                <div className="text-right hidden sm:block">
                  <p className="text-sm font-medium text-white">{user?.username}</p>
                  <p className="text-xs text-muted-foreground">Operator</p>
                </div>
                <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-primary to-accent shadow-lg shadow-primary/20" />
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
