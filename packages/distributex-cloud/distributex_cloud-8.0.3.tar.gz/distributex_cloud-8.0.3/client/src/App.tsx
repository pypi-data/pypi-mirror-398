import { Switch, Route, useLocation } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { useAuth } from "@/hooks/use-auth";
import { Loader2 } from "lucide-react";

// Pages
import Dashboard from "@/pages/dashboard";
import WorkersPage from "@/pages/workers";
import JobsPage from "@/pages/jobs";
import SubmitJobPage from "@/pages/submit-job";
import AuthPage from "@/pages/auth";
import NotFound from "@/pages/not-found";

function ProtectedRoute({ component: Component }: { component: React.ComponentType }) {
  const { user, isLoading } = useAuth();
  const [, setLocation] = useLocation();

  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!user) {
    // Redirect to auth page if not logged in
    // We use window.location.href for /api/login usually, but here we have a dedicated AuthPage
    // that handles the "Connect" button.
    setTimeout(() => setLocation("/auth"), 0);
    return null;
  }

  return <Component />;
}

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col pl-64 transition-all duration-300">
        <Topbar />
        <main className="flex-1 overflow-y-auto bg-background/50 scrollbar-hide">
          {children}
        </main>
      </div>
    </div>
  );
}

function Router() {
  return (
    <Switch>
      <Route path="/auth" component={AuthPage} />
      
      {/* Protected Routes */}
      <Route path="/">
        <ProtectedRoute component={() => <Layout><Dashboard /></Layout>} />
      </Route>
      <Route path="/workers">
        <ProtectedRoute component={() => <Layout><WorkersPage /></Layout>} />
      </Route>
      <Route path="/jobs">
        <ProtectedRoute component={() => <Layout><JobsPage /></Layout>} />
      </Route>
      <Route path="/submit">
        <ProtectedRoute component={() => <Layout><SubmitJobPage /></Layout>} />
      </Route>
      
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router />
      <Toaster />
    </QueryClientProvider>
  );
}

export default App;
