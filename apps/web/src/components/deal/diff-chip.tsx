import { cn } from '@/lib/utils';

export function DiffChip({ value }: { value: number }) {
  const state = value > 0 ? 'improve' : value < 0 ? 'regress' : 'neutral';
  return (
    <span
      className={cn(
        'inline-flex rounded-full px-2 py-0.5 font-mono text-xs',
        state === 'improve' && 'bg-pass-bg text-pass-fg',
        state === 'regress' && 'bg-fail-bg text-fail-fg',
        state === 'neutral' && 'bg-sidebar text-text-muted',
      )}
    >
      {value > 0 ? '+' : ''}
      {value.toFixed(2)}
    </span>
  );
}
