import { DiffChip } from '@/components/deal/diff-chip';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function ComparisonDiffHighlight({
  title,
  rows,
}: {
  title: string;
  rows: Array<{ label: string; delta?: number; detail?: string; tone?: 'improve' | 'regress' | 'warn' }>;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        {rows.length === 0 ? (
          <p className="text-text-muted">No changes.</p>
        ) : (
          rows.map((row) => (
            <div key={`${row.label}${row.detail ?? ''}`} className="rounded-xl border border-border-subtle bg-app p-2">
              <div className="flex items-center justify-between gap-2">
                <span className="text-text-heading">{row.label}</span>
                {typeof row.delta === 'number' ? <DiffChip value={row.delta} /> : null}
              </div>
              {row.detail ? <p className="mt-1 text-xs text-text-muted">{row.detail}</p> : null}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
