// client/src/App.tsx - FIXED: Role-based routing
import { Switch, Route, useLocation } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { useAuth } from "@/hooks/use-auth";
import { Loader2 } from "lucide-react";
import { useEffect } from "react";

// Pages
import LandingPage from "@/pages/landing";
import ContributorDashboard from "@/pages/contributor-dashboard";
import DeveloperDashboard from "@/pages/developer-dashboard";
import WorkersPage from "@/pages/workers";
import JobsPage from "@/pages/jobs";
import SubmitJobPage from "@/pages/submit-job";
import AuthPage from "@/pages/auth";
import NotFound from "@/pages/not-found";

function ProtectedRoute({ component: Component, allowedRoles }: { 
  component: React.ComponentType;
  allowedRoles?: string[];
}) {
  const { user, isLoading } = useAuth();
  const [, setLocation] = useLocation();

  useEffect(() => {
    if (!isLoading && !user) {
      setTimeout(() => setLocation("/auth"), 0);
    } else if (!isLoading && user && allowedRoles && !allowedRoles.includes(user.role)) {
      // Redirect to appropriate dashboard if accessing wrong role pages
      const defaultPath = user.role === 'contributor' ? '/contributor' : '/developer';
      setTimeout(() => setLocation(defaultPath), 0);
    }
  }, [user, isLoading, allowedRoles, setLocation]);

  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
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
      {/* Public Routes */}
      <Route path="/" component={LandingPage} />
      <Route path="/auth" component={AuthPage} />
      
      {/* Contributor Routes */}
      <Route path="/contributor">
        <ProtectedRoute 
          component={() => <Layout><ContributorDashboard /></Layout>}
          allowedRoles={['contributor']}
        />
      </Route>
      
      <Route path="/workers">
        <ProtectedRoute 
          component={() => <Layout><WorkersPage /></Layout>}
          allowedRoles={['contributor']}
        />
      </Route>
      
      {/* Developer Routes */}
      <Route path="/developer">
        <ProtectedRoute 
          component={() => <Layout><DeveloperDashboard /></Layout>}
          allowedRoles={['developer']}
        />
      </Route>
      
      <Route path="/jobs">
        <ProtectedRoute 
          component={() => <Layout><JobsPage /></Layout>}
          allowedRoles={['developer']}
        />
      </Route>
      
      <Route path="/submit">
        <ProtectedRoute 
          component={() => <Layout><SubmitJobPage /></Layout>}
          allowedRoles={['developer']}
        />
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
