import Link from 'next/link';

import { DecisionBadge } from '@/components/deal/decision-badge';
import { MetricCard } from '@/components/deal/metric-card';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { deals } from '@/lib/mock-data';

export default function DashboardPage() {
  const boePass = deals.filter((d) => d.latestRun.decision !== 'FAIL').length;
  const boeFail = deals.filter((d) => d.latestRun.decision === 'FAIL').length;

  return (
    <main className="space-y-6">
      <header>
        <p className="text-xs uppercase tracking-wide text-text-muted">Institutional GP Intelligence</p>
        <h1 className="text-3xl font-semibold text-text-heading">Dashboard</h1>
      </header>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Active Deals" value={`${deals.length}`} />
        <MetricCard label="BOE Authorized" value={`${boePass}`} />
        <MetricCard label="BOE Failed" value={`${boeFail}`} />
        <MetricCard label="Latest Max Bid" value={`$${deals[0].latestRun.maxBid.toLocaleString()}`} />
      </section>

      <section className="grid gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Latest Deal Movements</CardTitle>
            <Link href="/deals">
              <Button>Open Deals</Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-3">
            {deals.map((deal) => (
              <div key={deal.id} className="grid grid-cols-5 items-center gap-3 rounded-xl border bg-app p-3 text-sm">
                <div className="col-span-2">
                  <p className="font-medium text-text-heading">{deal.name}</p>
                  <p className="text-xs text-text-muted">{deal.address}</p>
                </div>
                <div>
                  <DecisionBadge state={deal.latestRun.decision === 'FAIL' ? 'KILL' : 'ADVANCE'} />
                </div>
                <div className="font-mono">${deal.latestRun.maxBid.toLocaleString()}</div>
                <div className="text-right">
                  <Link href={`/deals/${deal.id}?tab=boe`} className="text-sm text-accent">
                    Review
                  </Link>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Gate Discipline</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-text-muted">
            <p>All hard veto tests must pass.</p>
            <p>At least 4 of 7 tests must be PASS or WARN.</p>
            <p>Full UW remains locked until BOE ADVANCE.</p>
          </CardContent>
        </Card>
      </section>
    </main>
  );
}
