'use client';

import { useState } from 'react';
import type { FormEvent } from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function BoeInputForm() {
  const [form, setForm] = useState({
    askingPrice: '',
    depositPct: '',
    interestRate: '',
    ltc: '',
    capexBudget: '',
    notes: '',
  });

  function onChange(key: keyof typeof form, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    window.alert('BOE stub saved. Live calculation ships in PR2.');
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>BOE Inputs (PR1 Stub)</CardTitle>
      </CardHeader>
      <CardContent>
        <form className="space-y-3" onSubmit={onSubmit}>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="text-sm text-text-muted">
              Asking Price
              <input
                className="mt-1 w-full rounded-xl border border-border-subtle bg-card px-3 py-2 text-sm"
                value={form.askingPrice}
                onChange={(e) => onChange('askingPrice', e.target.value)}
                placeholder="10400000"
              />
            </label>
            <label className="text-sm text-text-muted">
              Deposit %
              <input
                className="mt-1 w-full rounded-xl border border-border-subtle bg-card px-3 py-2 text-sm"
                value={form.depositPct}
                onChange={(e) => onChange('depositPct', e.target.value)}
                placeholder="0.05"
              />
            </label>
            <label className="text-sm text-text-muted">
              Interest Rate
              <input
                className="mt-1 w-full rounded-xl border border-border-subtle bg-card px-3 py-2 text-sm"
                value={form.interestRate}
                onChange={(e) => onChange('interestRate', e.target.value)}
                placeholder="0.061"
              />
            </label>
            <label className="text-sm text-text-muted">
              LTC
              <input
                className="mt-1 w-full rounded-xl border border-border-subtle bg-card px-3 py-2 text-sm"
                value={form.ltc}
                onChange={(e) => onChange('ltc', e.target.value)}
                placeholder="0.70"
              />
            </label>
            <label className="text-sm text-text-muted sm:col-span-2">
              CapEx Budget
              <input
                className="mt-1 w-full rounded-xl border border-border-subtle bg-card px-3 py-2 text-sm"
                value={form.capexBudget}
                onChange={(e) => onChange('capexBudget', e.target.value)}
                placeholder="1300000"
              />
            </label>
            <label className="text-sm text-text-muted sm:col-span-2">
              Notes
              <textarea
                className="mt-1 w-full rounded-xl border border-border-subtle bg-card px-3 py-2 text-sm"
                value={form.notes}
                onChange={(e) => onChange('notes', e.target.value)}
                rows={3}
                placeholder="Optional deal notes"
              />
            </label>
          </div>
          <div className="flex items-center gap-2">
            <Button type="submit">Save Draft</Button>
            <Button type="button" variant="secondary">Run BOE (Stub)</Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
