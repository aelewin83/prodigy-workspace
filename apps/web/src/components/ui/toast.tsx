import { cn } from '@/lib/utils';

export function Toast({
  message,
  tone = 'info',
  testId,
}: {
  message: string;
  tone?: 'info' | 'success' | 'error';
  testId?: string;
}) {
  return (
    <div
      data-testid={testId}
      className={cn(
        'fixed bottom-4 right-4 z-50 rounded-xl border bg-card px-4 py-2 text-sm shadow-soft',
        tone === 'success' && 'border-pass-fg/30 text-pass-fg',
        tone === 'error' && 'border-fail-fg/30 text-fail-fg',
        tone === 'info' && 'border-border-subtle text-text-body',
      )}
      role="status"
      aria-live="polite"
    >
      {message}
    </div>
  );
}
