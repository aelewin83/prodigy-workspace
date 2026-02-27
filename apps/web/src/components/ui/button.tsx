import type { ButtonHTMLAttributes } from 'react';

import { cn } from '@/lib/utils';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost';
};

export function Button({ className, variant = 'primary', ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-medium transition-colors',
        variant === 'primary' && 'bg-accent text-white hover:bg-accent/90',
        variant === 'secondary' && 'border bg-card text-text-heading hover:border-border-hover dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100',
        variant === 'ghost' && 'text-text-muted hover:bg-sidebar dark:text-slate-300 dark:hover:bg-slate-800',
        className,
      )}
      {...props}
    />
  );
}
