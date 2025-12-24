import React from 'react';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

interface ShinyButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  isLoading?: boolean;
  variant?: 'primary' | 'outline' | 'ghost' | 'danger';
}

export const ShinyButton = React.forwardRef<HTMLButtonElement, ShinyButtonProps>(
  ({ children, className, isLoading, variant = 'primary', disabled, ...props }, ref) => {
    const variants = {
      primary: "bg-primary text-primary-foreground hover:bg-primary/90 shadow-[0_0_20px_rgba(16,185,129,0.3)] hover:shadow-[0_0_25px_rgba(16,185,129,0.5)] border-primary/50",
      outline: "bg-transparent border-primary/20 text-primary hover:bg-primary/10 hover:border-primary/50",
      ghost: "bg-transparent border-transparent text-foreground hover:bg-white/5",
      danger: "bg-destructive/20 text-destructive border-destructive/50 hover:bg-destructive/30"
    };

    return (
      <button
        ref={ref}
        disabled={isLoading || disabled}
        className={cn(
          "relative px-6 py-2.5 rounded-lg font-medium transition-all duration-300 ease-out border backdrop-blur-sm",
          "disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none",
          "active:scale-[0.98]",
          variants[variant],
          className
        )}
        {...props}
      >
        <span className="flex items-center justify-center gap-2">
          {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
          {children}
        </span>
      </button>
    );
  }
);
ShinyButton.displayName = "ShinyButton";
