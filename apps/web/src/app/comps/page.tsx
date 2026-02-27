import { MetricCard } from '@/components/deal/metric-card';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function GlobalCompsPage() {
  return (
    <main className="space-y-6">
      <header className="flex items-start justify-between">
        <div>
          <p className="text-xs uppercase tracking-wide text-text-muted">Phase 2</p>
          <h1 className="text-3xl font-semibold text-text-heading">Comps</h1>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary">Import File</Button>
          <Button>Run Public Pull</Button>
        </div>
      </header>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Avg Rent (1BR)" value="$3,250" />
        <MetricCard label="Avg Gross (1BR)" value="$3,410" />
        <MetricCard label="Avg Disc/Premium" value="4.7%" />
        <MetricCard label="Sample Size" value="28" />
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Unit Type Panels</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-text-muted">
          Per-unit-type comps cards, rollups, subject variance, and preview-to-BOE workflows render in deal context.
        </CardContent>
      </Card>
    </main>
  );
}
