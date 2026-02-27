'use client';

import { Button } from '@/components/ui/button';

type RunOption = {
  id: string;
  version: number;
  created_at: string;
  decision: string;
};

export function RunSelector({
  runs,
  selectedRunId,
  onSelect,
  onLatest,
}: {
  runs: RunOption[];
  selectedRunId: string | null;
  onSelect: (id: string) => void;
  onLatest?: () => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <label className="text-xs uppercase tracking-wide text-text-muted" htmlFor="run-selector">
        Run
      </label>
      <select
        id="run-selector"
        className="rounded-xl border border-border-subtle bg-card px-3 py-2 text-sm"
        value={selectedRunId ?? ''}
        onChange={(e) => onSelect(e.target.value)}
      >
        {runs.map((run) => (
          <option value={run.id} key={run.id}>
            v{run.version} · {new Date(run.created_at).toLocaleString()} · {run.decision}
          </option>
        ))}
      </select>
      <Button variant="secondary" type="button" onClick={onLatest}>
        Latest
      </Button>
    </div>
  );
}
