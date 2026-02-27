export type WorkspaceEdition = 'SYNDICATOR' | 'FUND';

export type WorkspaceFeatures = {
  deals: boolean;
  boe: boolean;
  ic_packet_basic: boolean;
  portfolio_view: boolean;
  fund_mode: boolean;
  fund_admin: boolean;
  fund_reporting: boolean;
};

export type Workspace = {
  id: string;
  name: string;
  edition: WorkspaceEdition;
  capabilities: { features: WorkspaceFeatures };
  is_admin: boolean;
  edition_updated_at: string | null;
  edition_updated_by_user_id: string | null;
  created_by: string;
  created_at: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/v1';

function authHeaders() {
  if (typeof window === 'undefined') return {};
  const token = window.localStorage.getItem('prodigy_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function listWorkspaces(): Promise<Workspace[]> {
  const res = await fetch(`${API_BASE}/workspaces`, {
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`Failed to load workspaces (${res.status})`);
  return res.json();
}

export async function updateWorkspaceEdition(workspaceId: string, edition: WorkspaceEdition): Promise<Workspace> {
  const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/edition`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ edition }),
  });
  if (!res.ok) throw new Error(`Failed to update workspace edition (${res.status})`);
  return res.json();
}
