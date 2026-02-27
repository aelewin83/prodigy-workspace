'use client';

import { Fragment, useCallback, useEffect, useMemo, useState } from 'react';

import { DecisionBadge } from '@/components/deal/decision-badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Toast } from '@/components/ui/toast';
import type { BoeRun } from '@/lib/boe-types';
import {
  getDealActivity,
  getDealWorkspaceSummary,
  overrideDealGate,
  postDealComment,
  runBoeForWorkspaceDeal,
  type ActivityEvent,
  type DealWorkspaceSummary,
} from '@/lib/deal-workspace-api';
import { getDeal } from '@/lib/mock-data';

function resultTone(result: string): string {
  if (result === 'PASS') return 'bg-pass-bg text-pass-text';
  if (result === 'WARN') return 'bg-warn-bg text-warn-text';
  if (result === 'FAIL') return 'bg-fail-bg text-fail-text';
  return 'bg-sidebar text-text-muted';
}

function toDecisionState(status: string): 'ADVANCE' | 'KILL' | 'NO_RUN' {
  if (status === 'ADVANCE' || status === 'APPROVED') return 'ADVANCE';
  if (status === 'NO_RUN') return 'NO_RUN';
  return 'KILL';
}

export function DealWorkspaceClient({ workspaceId, dealId }: { workspaceId: string; dealId: string }) {
  const [summary, setSummary] = useState<DealWorkspaceSummary | null>(null);
  const [runs, setRuns] = useState<BoeRun[]>([]);
  const [activity, setActivity] = useState<ActivityEvent[]>([]);
  const [expandedTest, setExpandedTest] = useState<string | null>(null);
  const [overrideStatus, setOverrideStatus] = useState<'ADVANCE' | 'REVIEW' | 'KILL' | 'CLEAR'>('CLEAR');
  const [overrideComment, setOverrideComment] = useState('');
  const [commentBody, setCommentBody] = useState('');
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<{ message: string; tone: 'info' | 'success' | 'error' } | null>(null);

  const fallbackDeal = getDeal(dealId);

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [s, a] = await Promise.all([getDealWorkspaceSummary(workspaceId, dealId), getDealActivity(dealId)]);
      setSummary(s);
      setActivity(a);
      if (s.latest_run_id) {
        const { listBoeRuns } = await import('@/lib/deal-workspace-api');
        const rows = await listBoeRuns(dealId);
        setRuns(rows);
      } else {
        setRuns([]);
      }
    } catch {
      if (fallbackDeal) {
        setToast({ message: 'Using local demo data (API unavailable).', tone: 'info' });
      } else {
        setToast({ message: 'Failed to load deal workspace.', tone: 'error' });
      }
    } finally {
      setLoading(false);
    }
  }, [workspaceId, dealId, fallbackDeal]);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 2500);
    return () => clearTimeout(t);
  }, [toast]);

  const latestRun = useMemo(() => runs[0] ?? null, [runs]);
  const tests = latestRun?.tests ?? [];
  const canAdminOverride = Boolean(summary?.capabilities?.features?.fund_admin) || Boolean(summary?.override?.by);
  const showFundOnly = Boolean(summary?.capabilities?.features?.fund_mode);

  async function onRunBoe() {
    try {
      await runBoeForWorkspaceDeal(dealId);
      await loadAll();
      setToast({ message: 'BOE run created.', tone: 'success' });
    } catch {
      setToast({ message: 'Failed to run BOE.', tone: 'error' });
    }
  }

  async function onApplyOverride() {
    if (overrideStatus !== 'CLEAR' && !overrideComment.trim()) {
      setToast({ message: 'Comment is required for overrides.', tone: 'error' });
      return;
    }
    try {
      await overrideDealGate(dealId, overrideStatus, overrideComment.trim());
      setOverrideComment('');
      await loadAll();
      setToast({ message: 'Override applied.', tone: 'success' });
    } catch {
      setToast({ message: 'Override failed.', tone: 'error' });
    }
  }

  async function onAddComment() {
    if (!commentBody.trim()) return;
    try {
      await postDealComment(dealId, commentBody.trim());
      setCommentBody('');
      await loadAll();
      setToast({ message: 'Comment added.', tone: 'success' });
    } catch {
      setToast({ message: 'Failed to add comment.', tone: 'error' });
    }
  }

  if (loading) {
    return <main className="space-y-4"><Card><CardContent className="p-6 text-sm text-text-muted">Loading deal workspace...</CardContent></Card></main>;
  }

  if (!summary && !fallbackDeal) {
    return <main><Card><CardContent className="p-6 text-sm text-fail-text">Deal not found.</CardContent></Card></main>;
  }

  return (
    <main className="space-y-6">
      <header className="rounded-2xl border bg-card p-5 shadow-soft">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-text-muted">Institutional Deal Workspace</p>
            <h1 className="text-3xl font-semibold text-text-heading">{summary?.deal_name ?? fallbackDeal?.name}</h1>
            <p className="text-sm text-text-muted">{summary?.address ?? fallbackDeal?.address ?? 'Address pending'}</p>
          </div>
          <div className="flex items-center gap-2">
            <DecisionBadge state={toDecisionState(summary?.gate_status_effective ?? 'NO_RUN')} />
            {summary?.override?.status ? <span className="rounded-full bg-warn-bg px-3 py-1 text-xs text-warn-text">OVERRIDDEN</span> : null}
            <Button onClick={onRunBoe}>Run BOE</Button>
          </div>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-4">
          <Card><CardContent className="p-4"><p className="text-xs text-text-muted">IC Score</p><p className="font-mono text-xl">{summary?.ic_score ?? 'N/A'}</p></CardContent></Card>
          <Card><CardContent className="p-4"><p className="text-xs text-text-muted">Recommended Max Bid</p><p className="font-mono text-xl">{summary?.recommended_max_bid ? `$${summary.recommended_max_bid.toLocaleString()}` : 'N/A'}</p></CardContent></Card>
          <Card><CardContent className="p-4"><p className="text-xs text-text-muted">Binding Constraint</p><p className="text-xl">{summary?.binding_constraint ?? 'N/A'}</p></CardContent></Card>
          <Card><CardContent className="p-4"><p className="text-xs text-text-muted">Edition</p><p className="text-xl">{showFundOnly ? 'FUND' : 'SYNDICATOR'}</p></CardContent></Card>
        </div>
      </header>

      <section className="grid gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader><CardTitle>Gate Summary</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm">
            <ul className="list-disc space-y-1 pl-5 text-text-muted">
              <li>All hard veto tests must pass</li>
              <li>&gt;= 4 of 7 tests PASS or WARN</li>
              <li>Full UW locked until BOE ADVANCE</li>
            </ul>
            <div className="grid gap-2 md:grid-cols-2">
              <div>Hard Veto OK: <strong>{String(summary?.decision_summary?.hard_veto_ok ?? false)}</strong></div>
              <div>Pass Count: <strong>{summary?.decision_summary?.pass_count ?? 0}/{summary?.decision_summary?.total_tests ?? 7}</strong></div>
              <div>Failed Hard: <strong>{(summary?.decision_summary?.failed_hard_tests ?? []).join(', ') || 'None'}</strong></div>
              <div>Failed Soft: <strong>{(summary?.decision_summary?.failed_soft_tests ?? []).join(', ') || 'None'}</strong></div>
              <div className="md:col-span-2">Warn Tests: <strong>{(summary?.decision_summary?.warn_tests ?? []).join(', ') || 'None'}</strong></div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Decision Controls</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm">
            {canAdminOverride ? (
              <>
                <label className="block">
                  Status
                  <select className="mt-1 w-full rounded-xl border border-border-subtle bg-card px-3 py-2" value={overrideStatus} onChange={(e) => setOverrideStatus(e.target.value as 'ADVANCE' | 'REVIEW' | 'KILL' | 'CLEAR')}>
                    <option value="ADVANCE">ADVANCE</option>
                    <option value="REVIEW">REVIEW</option>
                    <option value="KILL">KILL</option>
                    <option value="CLEAR">CLEAR OVERRIDE</option>
                  </select>
                </label>
                <textarea
                  className="min-h-24 w-full rounded-xl border border-border-subtle bg-card px-3 py-2"
                  placeholder="Comment required for override changes"
                  value={overrideComment}
                  onChange={(e) => setOverrideComment(e.target.value)}
                />
                <Button onClick={onApplyOverride}>Apply Override</Button>
              </>
            ) : (
              <p className="text-text-muted">Read-only: override controls are admin-only.</p>
            )}
            <div className="border-t pt-3">
              <textarea
                className="min-h-20 w-full rounded-xl border border-border-subtle bg-card px-3 py-2"
                placeholder="Add activity comment"
                value={commentBody}
                onChange={(e) => setCommentBody(e.target.value)}
              />
              <div className="mt-2"><Button variant="secondary" onClick={onAddComment}>Add Comment</Button></div>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader><CardTitle>BOE Test Breakdown</CardTitle></CardHeader>
          <CardContent>
            {tests.length === 0 ? (
              <div className="rounded-xl border border-dashed p-4 text-sm text-text-muted">No BOE runs yet. Run BOE to populate test outcomes.</div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-text-muted">
                    <th className="pb-2">Test</th><th className="pb-2">Class</th><th className="pb-2">Threshold</th><th className="pb-2">Actual</th><th className="pb-2">Result</th><th className="pb-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {tests.map((t) => {
                    const open = expandedTest === t.test_key;
                    return (
                      <Fragment key={t.test_key}>
                        <tr className="border-t align-top">
                          <td className="py-2">{t.test_name}</td>
                          <td className="py-2">{t.test_class === 'hard' ? 'Hard' : 'Soft'}</td>
                          <td className="py-2">{t.threshold_display ?? 'N/A'}</td>
                          <td className="py-2">{t.actual_display ?? 'N/A'}</td>
                          <td className="py-2"><span className={`rounded-full px-2 py-1 text-xs ${resultTone(t.result)}`}>{t.result}</span></td>
                          <td className="py-2 text-right">
                            <button type="button" className="text-xs text-accent" onClick={() => setExpandedTest(open ? null : t.test_key)}>{open ? 'Hide' : 'Details'}</button>
                          </td>
                        </tr>
                        {open ? (
                          <tr className="bg-app/60">
                            <td colSpan={6} className="px-2 pb-3 text-xs text-text-muted">
                              <p>Key: {t.test_key}</p>
                              <p>Threshold (raw): {t.threshold ?? 'N/A'} · Actual (raw): {t.actual ?? 'N/A'}</p>
                              <p>Explanation: Deterministic rule-based BOE test outcome.</p>
                            </td>
                          </tr>
                        ) : null}
                      </Fragment>
                    );
                  })}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Audit Timeline</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm">
            {activity.length === 0 ? <p className="text-text-muted">No activity yet.</p> : activity.map((e) => (
              <div key={e.id} className="rounded-xl border bg-app p-3">
                <p className="font-medium text-text-heading">{e.type}</p>
                <p className="text-xs text-text-muted">{e.summary}</p>
                <p className="mt-1 text-xs text-text-muted">{e.actor.name ?? e.actor.email ?? 'System'} · {new Date(e.created_at).toLocaleString()}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      <Card>
        <CardHeader><CardTitle>Attachments</CardTitle></CardHeader>
        <CardContent className="space-y-3 text-sm text-text-muted">
          <div className="rounded-xl border border-dashed p-6 text-center">Upload coming soon</div>
          <p>No attachments yet.</p>
        </CardContent>
      </Card>

      {showFundOnly ? (
        <Card>
          <CardHeader><CardTitle>Fund-Only Controls</CardTitle></CardHeader>
          <CardContent className="text-sm text-text-muted">Fund-level portfolio governance and policy controls will surface here.</CardContent>
        </Card>
      ) : null}

      {toast ? <Toast message={toast.message} tone={toast.tone} /> : null}
    </main>
  );
}
import { Fragment, useEffect, useMemo, useState } from 'react';
