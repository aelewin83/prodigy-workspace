'use client';

import { useEffect, useMemo, useState } from 'react';

import { BindingConstraintCard } from '@/components/deal/binding-constraint-card';
import { ComparisonDiffHighlight } from '@/components/deal/comparison-diff-highlight';
import { DecisionBadge } from '@/components/deal/decision-badge';
import { MetricCard } from '@/components/deal/metric-card';
import { RunSelector } from '@/components/deal/run-selector';
import { TestRow } from '@/components/deal/test-row';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Toast } from '@/components/ui/toast';
import { createBoeRun, getBoeRun, listBoeRuns } from '@/lib/boe-api';
import type { BoeInputDraft, BoeRun } from '@/lib/boe-types';
import type { Deal } from '@/lib/mock-data';

const tabs = [
  { key: 'overview', label: 'Overview' },
  { key: 'boe', label: 'BOE' },
  { key: 'comps', label: 'Comps' },
  { key: 'documents', label: 'Documents' },
  { key: 'full-uw', label: 'Full Underwriting' },
] as const;

const EMPTY_DRAFT: BoeInputDraft = {
  asking_price: '',
  deposit_pct: '',
  interest_rate: '',
  ltc: '',
  capex_budget: '',
  soft_cost_pct: '',
  reserves: '',
  seller_noi_from_om: '',
  gross_income: '',
  operating_expenses: '',
  y1_noi: '',
  market_cap_rate: '',
  y1_exit_cap_rate: '',
};

function toDraft(run: BoeRun | null): BoeInputDraft {
  if (!run) return EMPTY_DRAFT;
  const get = (k: string) => {
    const v = run.inputs[k];
    return v == null ? '' : String(v);
  };
  return {
    asking_price: get('asking_price'),
    deposit_pct: get('deposit_pct'),
    interest_rate: get('interest_rate'),
    ltc: get('ltc'),
    capex_budget: get('capex_budget'),
    soft_cost_pct: get('soft_cost_pct'),
    reserves: get('reserves'),
    seller_noi_from_om: get('seller_noi_from_om'),
    gross_income: get('gross_income'),
    operating_expenses: get('operating_expenses'),
    y1_noi: get('y1_noi'),
    market_cap_rate: get('market_cap_rate'),
    y1_exit_cap_rate: get('y1_exit_cap_rate'),
  };
}

function fromMockDeal(deal: Deal): BoeRun[] {
  return deal.runs.map((r, idx) => ({
    id: r.id,
    deal_id: deal.id,
    version: deal.runs.length - idx,
    inputs: {
      asking_price: Number(String(deal.ask).replace(/[^0-9.-]/g, '')),
      deposit_pct: Number(String(r.inputs['Deposit %'] ?? '0').replace('%', '')) / 100,
      interest_rate: Number(String(r.inputs['Interest Rate'] ?? '0').replace('%', '')) / 100,
      ltc: Number(String(r.inputs.LTC ?? '0').replace('%', '')) / 100,
      capex_budget: Number(String(r.inputs['CapEx Budget'] ?? '0').replace(/[^0-9.-]/g, '')),
    },
    outputs: {
      boe_max_bid: r.maxBid,
      delta_vs_asking: r.deltaToAsk,
      deposit_amount: Number(String(r.outputs['Deposit Amount'] ?? '0').replace(/[^0-9.-]/g, '')),
      binding_constraint: r.bindingConstraint,
      y1_dscr: r.y1Dscr,
      y1_yield_on_cost_unlevered: r.yoc,
      y1_exit_cap_rate: r.exitCap,
      y1_expense_ratio: r.expenseRatio,
    },
    decision: r.decision === 'FAIL' ? 'KILL' : 'ADVANCE',
    binding_constraint: r.bindingConstraint,
    hard_veto_ok: r.tests.filter((t) => t.klass === 'Hard Veto').every((t) => t.result === 'PASS'),
    pass_count: r.tests.filter((t) => t.result === 'PASS' || t.result === 'WARN').length,
    advance: r.decision !== 'FAIL',
    created_by: 'mock-user',
    created_at: new Date().toISOString(),
    tests: r.tests.map((t) => ({
      test_key: t.name.toLowerCase().replace(/[^a-z0-9]+/g, '_'),
      test_name: t.name,
      test_class: t.klass === 'Hard Veto' ? 'hard' : 'soft',
      threshold: null,
      actual: null,
      threshold_display: t.threshold,
      actual_display: t.actual,
      result: t.result,
      note: null,
    })),
  }));
}

function num(v: unknown): number | null {
  if (v == null) return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function fmtCurrency(v: unknown): string {
  const n = num(v);
  if (n == null) return 'N/A';
  return `$${n.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

function fmtPct(v: unknown): string {
  const n = num(v);
  if (n == null) return 'N/A';
  return `${(n * 100).toFixed(2)}%`;
}

export function DealDetailClient({
  deal,
  initialTab,
}: {
  deal: Deal;
  initialTab: string;
}) {
  const initialMockRuns = useMemo(() => fromMockDeal(deal), [deal]);
  const [tab, setTab] = useState(initialTab);
  const [runs, setRuns] = useState<BoeRun[]>(initialMockRuns);
  const [selectedRunId, setSelectedRunId] = useState<string>(initialMockRuns[0]?.id ?? '');
  const [draft, setDraft] = useState<BoeInputDraft>(toDraft(initialMockRuns[0] ?? null));
  const [isRunning, setIsRunning] = useState(false);
  const [isLoadingRuns, setIsLoadingRuns] = useState(false);
  const [compareMode, setCompareMode] = useState(false);
  const [runAId, setRunAId] = useState<string>('');
  const [runBId, setRunBId] = useState<string>('');
  const [toast, setToast] = useState<{ msg: string; tone: 'info' | 'success' | 'error' } | null>(null);

  const selectedRun = useMemo(() => runs.find((r) => r.id === selectedRunId) ?? runs[0] ?? null, [runs, selectedRunId]);
  const latestRun = useMemo(
    () =>
      [...runs].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0] ?? null,
    [runs],
  );

  useEffect(() => {
    let mounted = true;
    setIsLoadingRuns(true);
    listBoeRuns(deal.id)
      .then((serverRuns) => {
        if (!mounted) return;
        setRuns(serverRuns);
        setSelectedRunId(serverRuns[0]?.id ?? '');
        setDraft(toDraft(serverRuns[0] ?? null));
      })
      .catch(() => {
        setToast({ msg: 'Using local mock runs (API unavailable or unauthorized).', tone: 'info' });
      })
      .finally(() => setIsLoadingRuns(false));
    return () => {
      mounted = false;
    };
  }, [deal.id]);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 2500);
    return () => clearTimeout(t);
  }, [toast]);

  useEffect(() => {
    if (!runAId && runs[0]) setRunAId(runs[0].id);
    if (!runBId && runs[1]) setRunBId(runs[1].id);
    if (!runBId && runs[0] && !runs[1]) setRunBId(runs[0].id);
  }, [runs, runAId, runBId]);

  useEffect(() => {
    if (!selectedRunId) return;
    getBoeRun(deal.id, selectedRunId)
      .then((fresh) => {
        setRuns((prev) => prev.map((r) => (r.id === fresh.id ? fresh : r)));
      })
      .catch(() => {
        // keep local cached run
      });
  }, [deal.id, selectedRunId]);

  const gateState = latestRun ? (latestRun.advance ? 'ADVANCE' : 'KILL') : 'NO_RUN';
  const gatePass = gateState === 'ADVANCE';

  async function onRunBoe() {
    setIsRunning(true);
    try {
      const created = await createBoeRun(deal.id, draft);
      const fullRun = await getBoeRun(deal.id, created.id);
      setRuns((prev) => [fullRun, ...prev]);
      setSelectedRunId(fullRun.id);
      setToast({ msg: 'BOE run created.', tone: 'success' });
    } catch {
      setToast({ msg: 'Run failed. Check API/auth and try again.', tone: 'error' });
    } finally {
      setIsRunning(false);
    }
  }

  function resetToLastRun() {
    setDraft(toDraft(selectedRun));
  }

  const hardTests = (selectedRun?.tests ?? []).filter((t) => t.test_class === 'hard');
  const softTests = (selectedRun?.tests ?? []).filter((t) => t.test_class === 'soft');
  const hardPassCount = hardTests.filter((t) => t.result === 'PASS').length;

  const failingDrivers = (selectedRun?.tests ?? []).filter((t) => t.result === 'FAIL').slice(0, 2);

  const runA = runs.find((r) => r.id === runAId) ?? null;
  const runB = runs.find((r) => r.id === runBId) ?? null;

  const inputDiffRows = useMemo(() => {
    if (!runA || !runB) return [];
    const keys = new Set([...Object.keys(runA.inputs), ...Object.keys(runB.inputs)]);
    const rows: Array<{ label: string; detail: string }> = [];
    keys.forEach((k) => {
      const a = runA.inputs[k];
      const b = runB.inputs[k];
      if (String(a ?? '') !== String(b ?? '')) rows.push({ label: k, detail: `${a ?? 'N/A'} -> ${b ?? 'N/A'}` });
    });
    return rows;
  }, [runA, runB]);

  const outputDiffRows = useMemo(() => {
    if (!runA || !runB) return [];
    const keys = new Set([...Object.keys(runA.outputs), ...Object.keys(runB.outputs)]);
    const rows: Array<{ label: string; delta?: number; detail?: string }> = [];
    keys.forEach((k) => {
      const a = num(runA.outputs[k]);
      const b = num(runB.outputs[k]);
      if (a == null && b == null) return;
      if (a != null && b != null && a !== b) {
        rows.push({ label: k, delta: b - a, detail: `${a.toFixed(2)} -> ${b.toFixed(2)}` });
      } else if (String(runA.outputs[k] ?? '') !== String(runB.outputs[k] ?? '')) {
        rows.push({ label: k, detail: `${String(runA.outputs[k] ?? 'N/A')} -> ${String(runB.outputs[k] ?? 'N/A')}` });
      }
    });
    return rows;
  }, [runA, runB]);

  const testDiffRows = useMemo(() => {
    if (!runA || !runB) return [];
    const aMap = new Map(runA.tests.map((t) => [t.test_key, t.result]));
    return runB.tests
      .filter((t) => aMap.get(t.test_key) && aMap.get(t.test_key) !== t.result)
      .map((t) => ({ label: t.test_name, detail: `${aMap.get(t.test_key)} -> ${t.result}` }));
  }, [runA, runB]);

  return (
    <main className="space-y-6">
      <header className="sticky top-3 z-10 rounded-2xl border bg-card/95 p-5 shadow-soft backdrop-blur">
        <p className="text-xs uppercase tracking-wide text-text-muted">Prodigy NYC Fund I / Deals / {deal.name}</p>
        <div className="mt-2 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 data-testid="deal-detail-title" className="text-3xl font-semibold text-text-heading">{deal.name}</h1>
            <p className="text-sm text-text-muted">{deal.address} · {deal.neighborhood}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <DecisionBadge state={gateState} />
            <RunSelector
              runs={runs.map((r) => ({ id: r.id, version: r.version, created_at: r.created_at, decision: r.decision }))}
              selectedRunId={selectedRun?.id ?? null}
              onSelect={setSelectedRunId}
              onLatest={() => runs[0] && setSelectedRunId(runs[0].id)}
            />
            <Button data-testid="boe-run-button" onClick={onRunBoe} disabled={isRunning}>
              {isRunning ? 'Running…' : 'Run BOE'}
            </Button>
          </div>
        </div>
      </header>

      <nav className="flex flex-wrap gap-2">
        {tabs.map((item) => {
          const locked = item.key === 'full-uw' && !gatePass;
          return (
            <button
              key={item.key}
              type="button"
              className={`rounded-xl border px-3 py-2 text-sm transition-colors ${
                tab === item.key ? 'border-accent bg-accent/10 text-text-heading' : 'bg-card text-text-muted hover:border-border-hover'
              } ${locked ? 'cursor-not-allowed opacity-60' : ''}`}
              onClick={() => !locked && setTab(item.key)}
              title={locked ? 'Unlocked when BOE ADVANCE (Hard Veto PASS + 4 of 7 PASS/WARN).' : ''}
            >
              {item.label} {locked ? '🔒' : ''}
            </button>
          );
        })}
      </nav>

      {gateState === 'NO_RUN' ? (
        <Card>
          <CardContent className="p-4 text-sm text-text-muted">Run BOE to evaluate deal.</CardContent>
        </Card>
      ) : null}

      {gateState === 'KILL' ? (
        <Card>
          <CardContent className="p-4 text-sm text-text-muted">
            Deal does not meet BOE criteria. Hard Veto failure or insufficient PASS/WARN tests.
          </CardContent>
        </Card>
      ) : null}

      {tab === 'overview' && selectedRun && (
        <section className="grid grid-cols-12 gap-4">
          <div className="col-span-12 xl:col-span-8 space-y-4">
            <MetricCard label="Gate State" value={gateState} />
            <div className="grid gap-4 md:grid-cols-2">
              <MetricCard label="BOE Max Bid" value={fmtCurrency(selectedRun.outputs.boe_max_bid)} prominent />
              <MetricCard
                label="Delta to Ask"
                value={fmtCurrency(selectedRun.outputs.delta_vs_asking)}
                subtext={fmtPct((num(selectedRun.outputs.delta_vs_asking) ?? 0) / (num(selectedRun.inputs.asking_price) ?? 1))}
              />
            </div>
            <BindingConstraintCard
              constraint={selectedRun.binding_constraint ?? 'N/A'}
              detail="Constraint currently setting the BOE max bid."
            />
          </div>
          <div className="col-span-12 xl:col-span-4">
            <Card>
              <CardHeader>
                <CardTitle>Run Notes</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-text-muted">
                <p>Run version: v{selectedRun.version}</p>
                <p>Created: {new Date(selectedRun.created_at).toLocaleString()}</p>
                <p>Source: {isLoadingRuns ? 'Loading API…' : 'API + local fallback'}</p>
              </CardContent>
            </Card>
          </div>
        </section>
      )}

      {tab === 'boe' && selectedRun && (
        <>
          <section className="grid grid-cols-12 gap-4">
            <div className="col-span-12 xl:col-span-4 space-y-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle>Input Draft</CardTitle>
                  <Button variant="secondary" onClick={resetToLastRun}>
                    Reset to last run
                  </Button>
                </CardHeader>
                <CardContent className="space-y-4">
                  {[
                    ['Property Assumptions', ['asking_price', 'deposit_pct']],
                    ['Revenue', ['gross_income', 'seller_noi_from_om', 'y1_noi']],
                    ['Expenses', ['operating_expenses', 'reserves']],
                    ['CapEx', ['capex_budget', 'soft_cost_pct']],
                    ['Financing', ['interest_rate', 'ltc', 'market_cap_rate', 'y1_exit_cap_rate']],
                  ].map(([title, keys]) => (
                    <details key={title as string} open className="rounded-xl border border-border-subtle bg-app">
                      <summary className="cursor-pointer list-none px-3 py-2 text-sm font-medium text-text-heading">{title as string}</summary>
                      <div className="space-y-2 border-t border-border-subtle p-3">
                        {(keys as string[]).map((k) => (
                          <label className="block text-xs text-text-muted" key={k}>
                            {k}
                            <input
                              value={draft[k as keyof BoeInputDraft]}
                              onChange={(e) => setDraft((prev) => ({ ...prev, [k]: e.target.value }))}
                              className="mt-1 w-full rounded-lg border border-border-subtle bg-card px-2 py-1.5 text-sm"
                            />
                          </label>
                        ))}
                      </div>
                    </details>
                  ))}
                </CardContent>
              </Card>
            </div>

            <div className="col-span-12 xl:col-span-5 space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Year 1 Return Metrics</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-3 sm:grid-cols-2">
                  <MetricCard label="Market Cap Rate" value={fmtPct(selectedRun.outputs.market_cap_rate)} />
                  <MetricCard label="Asking Cap Rate" value={fmtPct(selectedRun.outputs.asking_cap_rate)} />
                  <MetricCard label="Y1 Exit Cap Rate" value={fmtPct(selectedRun.outputs.y1_exit_cap_rate)} />
                  <MetricCard label="Y1 DSCR" value={(num(selectedRun.outputs.y1_dscr) ?? 0).toFixed(2)} />
                  <MetricCard label="Y1 Expense Ratio" value={fmtPct(selectedRun.outputs.y1_expense_ratio)} />
                  <MetricCard label="Y1 Yield on Cost" value={fmtPct(selectedRun.outputs.y1_yield_on_cost_unlevered)} />
                </CardContent>
              </Card>

              <MetricCard
                label="BOE Max Bid"
                value={fmtCurrency(selectedRun.outputs.boe_max_bid)}
                prominent
                subtext={`Delta ${fmtCurrency(selectedRun.outputs.delta_vs_asking)} · Deposit ${fmtCurrency(selectedRun.outputs.deposit_amount)}`}
              />

              <BindingConstraintCard
                constraint={selectedRun.binding_constraint ?? 'N/A'}
                detail="Binding constraint used to determine BOE Max Bid."
              />

              <Card>
                <CardHeader>
                  <CardTitle>Key Drivers</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm text-text-muted">
                  {failingDrivers.length === 0 ? <p>No failing tests on this run.</p> : failingDrivers.map((t) => <p key={t.test_key}>• {t.test_name} = {t.result}</p>)}
                </CardContent>
              </Card>
            </div>

            <div data-testid="boe-tests-panel" className="col-span-12 xl:col-span-3 space-y-4">
              <Card>
                <CardContent className="p-5">
                  <p className="text-xs uppercase tracking-wide text-text-muted">Decision Discipline</p>
                  <div className="mt-2">
                    <span data-testid="boe-decision-badge">
                      <DecisionBadge state={selectedRun.advance ? 'ADVANCE' : 'KILL'} className="px-4 py-2 text-sm" />
                    </span>
                  </div>
                  <p className="mt-3 text-sm text-text-muted">Hard Veto: {hardPassCount}/3 PASS</p>
                  <p className="text-sm text-text-muted">
                    Total: {(latestRun?.pass_count ?? selectedRun.pass_count)}/7 PASS+WARN (&gt;=4 required)
                  </p>
                  <p className="mt-2 text-xs text-text-muted">N/A does not count. DSCR WARN counts toward the 4-of-7 requirement.</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Hard Veto Tests</CardTitle>
                </CardHeader>
                <CardContent>
                  {hardTests.map((t) => (
                    <TestRow
                      key={t.test_key}
                      keyName={t.test_key}
                      name={t.test_name}
                      klass="Hard"
                      threshold={t.threshold_display ?? 'N/A'}
                      actual={t.actual_display ?? 'N/A'}
                      result={t.result}
                    />
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Soft Tests</CardTitle>
                </CardHeader>
                <CardContent>
                  {softTests.map((t) => (
                    <TestRow
                      key={t.test_key}
                      keyName={t.test_key}
                      name={t.test_name}
                      klass="Soft"
                      threshold={t.threshold_display ?? 'N/A'}
                      actual={t.actual_display ?? 'N/A'}
                      result={t.result}
                    />
                  ))}
                </CardContent>
              </Card>
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-text-heading">Run History</h2>
              <Button variant="secondary" onClick={() => setCompareMode((v) => !v)}>
                {compareMode ? 'Close Compare' : 'Compare Runs'}
              </Button>
            </div>
            <Card>
              <CardContent className="space-y-2 pt-6">
                {runs.map((r) => (
                  <button
                    key={r.id}
                    className={`grid w-full grid-cols-4 items-center rounded-xl border p-3 text-left text-sm ${selectedRunId === r.id ? 'border-accent bg-accent/5' : 'border-border-subtle bg-app'}`}
                    onClick={() => setSelectedRunId(r.id)}
                  >
                    <span>{new Date(r.created_at).toLocaleString()}</span>
                    <span>{r.decision}</span>
                    <span className="font-mono">{fmtCurrency(r.outputs.boe_max_bid)}</span>
                    <span>{r.binding_constraint ?? 'N/A'}</span>
                  </button>
                ))}
              </CardContent>
            </Card>
          </section>

          {compareMode && (
            <section className="space-y-4">
              <Card>
                <CardHeader className="flex flex-row items-center gap-3">
                  <CardTitle>Compare Runs</CardTitle>
                  <select className="rounded-lg border px-2 py-1 text-sm" value={runAId} onChange={(e) => setRunAId(e.target.value)}>
                    {runs.map((r) => (
                      <option value={r.id} key={r.id}>Run v{r.version}</option>
                    ))}
                  </select>
                  <span className="text-sm text-text-muted">vs</span>
                  <select className="rounded-lg border px-2 py-1 text-sm" value={runBId} onChange={(e) => setRunBId(e.target.value)}>
                    {runs.map((r) => (
                      <option value={r.id} key={r.id}>Run v{r.version}</option>
                    ))}
                  </select>
                </CardHeader>
              </Card>

              <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
                <ComparisonDiffHighlight title="Inputs Diff" rows={inputDiffRows.map((r) => ({ label: r.label, detail: r.detail }))} />
                <ComparisonDiffHighlight title="Outputs Diff" rows={outputDiffRows} />
                <ComparisonDiffHighlight title="Test State Changes" rows={testDiffRows.map((r) => ({ label: r.label, detail: r.detail }))} />
              </div>
            </section>
          )}
        </>
      )}

      {tab === 'comps' && (
        <Card>
          <CardHeader>
            <CardTitle>Comps (Phase 2 Placeholder)</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-text-muted">Comps module is out of PR3 scope.</CardContent>
        </Card>
      )}

      {tab === 'documents' && (
        <Card>
          <CardHeader>
            <CardTitle>Documents (Phase 2 Placeholder)</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-text-muted">Documents module is out of PR3 scope.</CardContent>
        </Card>
      )}

      {tab === 'full-uw' && (
        <Card>
          <CardHeader>
            <CardTitle>Full Underwriting</CardTitle>
          </CardHeader>
          <CardContent>
            {gatePass ? (
              <div className="space-y-3">
                <p className="text-sm text-text-muted">Unlocked. Placeholder surface for PR4+.</p>
                <a href={`/deals/${deal.id}/underwriting`} className="text-sm text-accent">
                  Open Full Underwriting Module
                </a>
              </div>
            ) : (
              <div className="rounded-xl border border-warn-fg/20 bg-warn-bg p-4 text-sm text-warn-fg">
                Locked. Unlocked when BOE ADVANCE (Hard Veto PASS + 4 of 7 PASS/WARN).
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {toast ? <Toast testId="boe-run-toast" message={toast.msg} tone={toast.tone} /> : null}
    </main>
  );
}
