import type { BoeInputDraft, BoeRun } from '@/lib/boe-types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/v1';

function authHeaders() {
  if (typeof window === 'undefined') return {};
  const token = window.localStorage.getItem('prodigy_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function listBoeRuns(dealId: string): Promise<BoeRun[]> {
  const res = await fetch(`${API_BASE}/deals/${dealId}/boe/runs`, {
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`Failed to load BOE runs (${res.status})`);
  return res.json();
}

export async function getBoeRun(dealId: string, runId: string): Promise<BoeRun> {
  const res = await fetch(`${API_BASE}/deals/${dealId}/boe/runs/${runId}`, {
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`Failed to load BOE run (${res.status})`);
  return res.json();
}

function parseNum(v: string): number | undefined {
  if (v.trim() === '') return undefined;
  const n = Number(v);
  return Number.isFinite(n) ? n : undefined;
}

export function draftToInputPayload(draft: BoeInputDraft): Record<string, number> {
  return Object.fromEntries(
    Object.entries(draft)
      .map(([k, v]) => [k, parseNum(v)] as const)
      .filter(([, v]) => v !== undefined),
  ) as Record<string, number>;
}

export async function createBoeRun(dealId: string, draft: BoeInputDraft): Promise<BoeRun> {
  const payload = { inputs: draftToInputPayload(draft) };
  const res = await fetch(`${API_BASE}/deals/${dealId}/boe/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Failed to create BOE run (${res.status})`);
  return res.json();
}
