import { useState } from "react";
import { useAuth } from "@/hooks/use-auth";
import { GlassCard } from "@/components/ui/glass-card";
import { ShinyButton } from "@/components/ui/shiny-button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Zap, Server, Code2 } from "lucide-react";
import { useLocation } from "wouter";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

type UserRole = 'contributor' | 'developer' | null;

export default function AuthPage() {
  const { user, login, register, isLoading } = useAuth();
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const [isLogin, setIsLogin] = useState(true);
  const [selectedRole, setSelectedRole] = useState<UserRole>(null);
  const [formData, setFormData] = useState({
    email: "",
    username: "",
    password: "",
    confirmPassword: "",
  });

  if (user) {
    // Redirect based on role
    const defaultPath = user.role === 'contributor' ? '/contributor' : '/developer';
    setLocation(defaultPath);
    return null;
  }

  const handleRoleSelect = (role: UserRole) => {
    setSelectedRole(role);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedRole && !isLogin) {
      toast({
        variant: "destructive",
        title: "Please select your role"
      });
      return;
    }
    
    try {
      if (isLogin) {
        await login({ email: formData.email, password: formData.password });
        toast({ title: "Welcome back!" });
      } else {
        if (formData.password !== formData.confirmPassword) {
          toast({ 
            variant: "destructive",
            title: "Passwords don't match" 
          });
          return;
        }
        
        if (formData.password.length < 8) {
          toast({ 
            variant: "destructive",
            title: "Password must be at least 8 characters" 
          });
          return;
        }
        
        await register({
          email: formData.email,
          username: formData.username,
          password: formData.password,
          role: selectedRole || 'developer',
        });
        toast({ title: "Account created successfully!" });
      }
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Authentication failed",
        description: (error as Error).message,
      });
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-4 bg-gradient-to-b from-background via-background to-background/50">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(16,185,129,0.1),transparent_50%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_80%,rgba(34,211,238,0.1),transparent_50%)]" />
      
      <GlassCard className="w-full max-w-md p-8 relative z-10" gradient>
        <div className="flex justify-center mb-6">
          <div className="rounded-full bg-primary/10 p-4 ring-1 ring-primary/50 shadow-[0_0_30px_rgba(16,185,129,0.2)]">
            <Zap className="h-12 w-12 text-primary" />
          </div>
        </div>
        
        <h1 className="text-3xl font-bold text-white mb-2 text-center">
          Distribute<span className="text-primary">X</span>
        </h1>
        <p className="text-muted-foreground mb-8 text-center">
          {isLogin ? "Welcome back" : "Create your account"}
        </p>

        {/* Role Selection (Sign Up Only) */}
        {!isLogin && (
          <div className="mb-6">
            <Label className="mb-3 block">I want to:</Label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => handleRoleSelect('contributor')}
                className={cn(
                  "p-4 rounded-lg border-2 transition-all text-left",
                  selectedRole === 'contributor'
                    ? "border-primary bg-primary/10"
                    : "border-white/10 hover:border-white/20 bg-secondary/50"
                )}
              >
                <Server className={cn(
                  "h-6 w-6 mb-2",
                  selectedRole === 'contributor' ? "text-primary" : "text-muted-foreground"
                )} />
                <div className="font-semibold text-white text-sm mb-1">
                  Contribute
                </div>
                <div className="text-xs text-muted-foreground">
                  Share compute power
                </div>
              </button>

              <button
                type="button"
                onClick={() => handleRoleSelect('developer')}
                className={cn(
                  "p-4 rounded-lg border-2 transition-all text-left",
                  selectedRole === 'developer'
                    ? "border-accent bg-accent/10"
                    : "border-white/10 hover:border-white/20 bg-secondary/50"
                )}
              >
                <Code2 className={cn(
                  "h-6 w-6 mb-2",
                  selectedRole === 'developer' ? "text-accent" : "text-muted-foreground"
                )} />
                <div className="font-semibold text-white text-sm mb-1">
                  Develop
                </div>
                <div className="text-xs text-muted-foreground">
                  Run compute jobs
                </div>
              </button>
            </div>
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
              className="bg-secondary/50 border-input"
            />
          </div>

          {!isLogin && (
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                placeholder="johndoe"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                required
                className="bg-secondary/50 border-input"
              />
            </div>
          )}
          
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
              className="bg-secondary/50 border-input"
            />
          </div>

          {!isLogin && (
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="••••••••"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                required
                className="bg-secondary/50 border-input"
              />
            </div>
          )}
          
          <ShinyButton type="submit" className="w-full" isLoading={isLoading}>
            {isLogin ? "Sign In" : "Create Account"}
          </ShinyButton>
        </form>

        <div className="mt-6 text-center">
          <button
            type="button"
            onClick={() => {
              setIsLogin(!isLogin);
              setSelectedRole(null);
            }}
            className="text-sm text-muted-foreground hover:text-white transition-colors"
          >
            {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
          </button>
        </div>
      </GlassCard>
    </div>
  );
}
