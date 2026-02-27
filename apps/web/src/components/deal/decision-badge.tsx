import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

export type DecisionState = 'PASS' | 'FAIL' | 'WARN' | 'N/A' | 'NO_RUN' | 'ADVANCE' | 'KILL' | 'PASS_WITH_NOTES';

export function DecisionBadge({ state, className }: { state: DecisionState; className?: string }) {
  const normalized = state === 'ADVANCE' || state === 'PASS_WITH_NOTES' ? 'PASS' : state === 'KILL' ? 'FAIL' : state;

  return (
    <Badge
      className={cn(
        normalized === 'PASS' && 'bg-pass-bg text-pass-fg',
        normalized === 'WARN' && 'bg-warn-bg text-warn-fg',
        normalized === 'FAIL' && 'bg-fail-bg text-fail-fg',
        (state === 'N/A' || state === 'NO_RUN') && 'bg-slate-100 text-text-muted',
        className,
      )}
    >
      {state}
    </Badge>
  );
}
