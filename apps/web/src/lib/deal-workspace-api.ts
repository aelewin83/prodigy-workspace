import { createBoeRun, getBoeRun, listBoeRuns, type BoeInputDraft } from '@/lib/boe-api';
import type { BoeRun } from '@/lib/boe-types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/v1';

function authHeaders() {
  if (typeof window === 'undefined') return {};
  const token = window.localStorage.getItem('prodigy_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export type DealWorkspaceSummary = {
  deal_id: string;
  workspace_id: string;
  deal_name: string;
  address: string | null;
  gate_status: string;
  gate_status_effective: string;
  ic_score: number | null;
  recommended_max_bid: number | null;
  binding_constraint: string | null;
  latest_run_id: string | null;
  latest_run_created_at: string | null;
  decision_summary: {
    status: string;
    hard_veto_ok: boolean;
    pass_count: number;
    total_tests: number;
    advance: boolean;
    failed_hard_tests: string[];
    failed_soft_tests: string[];
    warn_tests: string[];
    pass_tests: string[];
    na_tests: string[];
    ic_score: number;
  } | null;
  override: {
    status: string | null;
    reason: string | null;
    by: string | null;
    at: string | null;
  } | null;
  capabilities: { features: Record<string, boolean> };
};

export type ActivityEvent = {
  id: string;
  type: string;
  created_at: string;
  actor: { id: string | null; email: string | null; name: string | null };
  summary: string;
  metadata: Record<string, unknown>;
};

export async function getDealWorkspaceSummary(workspaceId: string, dealId: string): Promise<DealWorkspaceSummary> {
  const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/deals/${dealId}/summary`, {
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`Failed to load deal summary (${res.status})`);
  return res.json();
}

export async function getDealActivity(dealId: string): Promise<ActivityEvent[]> {
  const res = await fetch(`${API_BASE}/deals/${dealId}/activity?limit=50`, {
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`Failed to load deal activity (${res.status})`);
  return res.json();
}

export async function postDealComment(dealId: string, body: string): Promise<void> {
  const res = await fetch(`${API_BASE}/deals/${dealId}/comments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ body }),
  });
  if (!res.ok) throw new Error(`Failed to add comment (${res.status})`);
}

export async function overrideDealGate(
  dealId: string,
  status: 'ADVANCE' | 'REVIEW' | 'KILL' | 'CLEAR',
  comment: string,
): Promise<void> {
  const res = await fetch(`${API_BASE}/deals/${dealId}/gate/override`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ status, comment }),
  });
  if (!res.ok) throw new Error(`Failed to apply gate override (${res.status})`);
}

export async function runBoeForWorkspaceDeal(dealId: string): Promise<BoeRun> {
  const draft: BoeInputDraft = {
    asking_price: '10000000',
    deposit_pct: '0.05',
    interest_rate: '0.06',
    ltc: '0.7',
    capex_budget: '1000000',
    soft_cost_pct: '0',
    reserves: '0',
    seller_noi_from_om: '500000',
    gross_income: '1000000',
    operating_expenses: '300000',
    y1_noi: '700000',
    market_cap_rate: '0.05',
    y1_exit_cap_rate: '0.05',
  };
  const created = await createBoeRun(dealId, draft);
  return getBoeRun(dealId, created.id);
}

export { listBoeRuns };
