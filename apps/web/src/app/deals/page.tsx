'use client';

import { useState } from 'react';
import Link from 'next/link';

import { DecisionBadge } from '@/components/deal/decision-badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Toast } from '@/components/ui/toast';
import { deals as initialDeals } from '@/lib/mock-data';

export default function DealsPage() {
  const [deals, setDeals] = useState(initialDeals);
  const [name, setName] = useState('');
  const [address, setAddress] = useState('');
  const [toast, setToast] = useState<string | null>(null);

  function createDeal() {
    if (!name.trim()) {
      setToast('Deal name is required.');
      return;
    }
    const id = name.toLowerCase().replace(/[^a-z0-9]+/g, '-');
    setDeals((prev) => [
      {
        ...prev[0],
        id,
        name,
        address,
        stage: 'Intake',
      },
      ...prev,
    ]);
    setName('');
    setAddress('');
    setToast('Deal created locally. API create wiring can be added to your auth context.');
  }

  return (
    <main className="space-y-6">
      <header className="flex flex-col gap-3 rounded-2xl border bg-card p-5 shadow-soft lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-wide text-text-muted">Pipeline</p>
          <h1 className="text-3xl font-semibold text-text-heading">Deals</h1>
          <p className="text-sm text-text-muted">Intake, BOE gate, and Full UW authorization in one surface.</p>
        </div>
        <div className="grid gap-2 sm:grid-cols-3">
          <input
            aria-label="Deal name"
            className="rounded-xl border border-border-subtle bg-card px-3 py-2 text-sm"
            placeholder="Deal name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            aria-label="Deal address"
            className="rounded-xl border border-border-subtle bg-card px-3 py-2 text-sm"
            placeholder="Address"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
          />
          <Button onClick={createDeal}>Create Deal</Button>
        </div>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Deal List</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px] border-collapse text-sm">
              <thead>
                <tr className="border-b text-left text-xs uppercase tracking-wide text-text-muted">
                  <th className="pb-3">Deal Name</th>
                  <th className="pb-3">Address</th>
                  <th className="pb-3">Stage</th>
                  <th className="pb-3">Latest BOE</th>
                  <th className="pb-3">Updated</th>
                  <th className="pb-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {deals.map((deal) => {
                  const status = deal.latestRun.decision === 'FAIL' ? 'FAIL' : 'PASS';
                  const deltaPct = (deal.latestRun.deltaToAsk / deal.ask) * 100;
                  return (
                    <tr key={deal.id} className="border-b border-border-subtle">
                      <td className="py-4 font-medium text-text-heading">{deal.name}</td>
                      <td className="py-4 text-text-muted">{deal.address ?? '-'}</td>
                      <td className="py-4">
                        <span className="rounded-full bg-sidebar px-3 py-1 text-xs">{deal.stage}</span>
                      </td>
                      <td className="py-4">
                        <div className="flex items-center gap-2">
                          <DecisionBadge state={status} />
                          <span className="font-mono text-xs text-text-muted">
                            ${deal.latestRun.maxBid.toLocaleString()} / {deltaPct.toFixed(1)}%
                          </span>
                        </div>
                      </td>
                      <td className="py-4 text-text-muted">{deal.updatedDate}</td>
                      <td className="py-4 text-right">
                        <Link href={`/deals/${deal.id}?tab=boe`} className="mr-3 text-accent">
                          Open
                        </Link>
                        <Link href={`/workspaces/local-workspace/deals/${deal.id}`} className="text-text-muted hover:text-text-heading">
                          Workspace
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {toast ? <Toast message={toast} tone="info" /> : null}
    </main>
  );
}
