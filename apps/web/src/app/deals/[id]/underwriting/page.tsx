'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/v1';

type UwPayload = {
  status: string;
  message: string;
  tabs: string[];
};

export default function UnderwritingPage({ params }: { params: { id: string } }) {
  const [data, setData] = useState<UwPayload | null>(null);
  const [locked, setLocked] = useState(false);

  useEffect(() => {
    const token = window.localStorage.getItem('prodigy_token');
    fetch(`${API_BASE}/full-underwriting/deals/${params.id}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then(async (res) => {
        if (res.status === 403 || res.status === 401) {
          setLocked(true);
          return null;
        }
        if (!res.ok) throw new Error('Failed underwriting fetch');
        return res.json();
      })
      .then((payload) => {
        if (payload) setData(payload);
      })
      .catch(() => setLocked(true));
  }, [params.id]);

  return (
    <main className="space-y-6">
      <header>
        <p className="text-xs uppercase tracking-wide text-text-muted">Deal / Full Underwriting</p>
        <h1 className="text-3xl font-semibold text-text-heading">Full Underwriting</h1>
      </header>

      {locked ? (
        <Card>
          <CardHeader>
            <CardTitle>🔒 Locked</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-text-muted">
            <p>Unlocked when BOE ADVANCE (Hard Veto PASS + 4 of 7 PASS/WARN).</p>
            <Link href={`/deals/${params.id}?tab=boe`} className="text-accent">
              Return to BOE
            </Link>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>{data?.message ?? 'Full Underwriting Enabled'}</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {(data?.tabs ?? ['Pro Forma', 'Rent Roll', 'Waterfall', 'Debt Model']).map((tab) => (
              <div key={tab} className="rounded-xl border border-border-subtle bg-app p-3 text-sm text-text-heading">
                {tab} (stub)
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </main>
  );
}
