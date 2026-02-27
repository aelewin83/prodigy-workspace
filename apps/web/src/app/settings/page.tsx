'use client';

import { useEffect, useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Toast } from '@/components/ui/toast';
import { listWorkspaces, updateWorkspaceEdition, type Workspace, type WorkspaceEdition } from '@/lib/workspace-api';

const FALLBACK_WORKSPACE: Workspace = {
  id: 'local-workspace',
  name: 'Prodigy NYC Fund I',
  edition: 'SYNDICATOR',
  capabilities: {
    features: {
      deals: true,
      boe: true,
      ic_packet_basic: true,
      portfolio_view: true,
      fund_mode: false,
      fund_admin: false,
      fund_reporting: false,
    },
  },
  is_admin: true,
  edition_updated_at: null,
  edition_updated_by_user_id: null,
  created_by: 'local-user',
  created_at: new Date().toISOString(),
};

export default function SettingsPage() {
  const [workspace, setWorkspace] = useState<Workspace>(FALLBACK_WORKSPACE);
  const [editionDraft, setEditionDraft] = useState<WorkspaceEdition>('SYNDICATOR');
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ message: string; tone: 'info' | 'success' | 'error' } | null>(null);

  useEffect(() => {
    let mounted = true;
    listWorkspaces()
      .then((rows) => {
        if (!mounted || rows.length === 0) return;
        setWorkspace(rows[0]);
        setEditionDraft(rows[0].edition);
      })
      .catch(() => {
        setToast({ message: 'Using local workspace defaults (API unavailable).', tone: 'info' });
      });
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 2500);
    return () => clearTimeout(t);
  }, [toast]);

  const hasChanges = useMemo(() => editionDraft !== workspace.edition, [editionDraft, workspace.edition]);

  async function onSaveEdition() {
    if (!hasChanges) return;
    if (!window.confirm('Switching modes changes workflows and available features. Continue?')) return;
    setSaving(true);
    try {
      const updated = await updateWorkspaceEdition(workspace.id, editionDraft);
      setWorkspace(updated);
      setEditionDraft(updated.edition);
      setToast({ message: `Workspace edition switched to ${updated.edition}.`, tone: 'success' });
    } catch {
      setToast({ message: 'Failed to update workspace edition.', tone: 'error' });
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="space-y-6">
      <header>
        <p className="text-xs uppercase tracking-wide text-text-muted">Workspace Controls</p>
        <h1 className="text-3xl font-semibold text-text-heading">Settings</h1>
      </header>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Edition Mode</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p className="text-text-muted">
              Current workspace: <span className="font-medium text-text-heading">{workspace.name}</span>
            </p>
            <p className="text-text-muted" data-testid="workspace-edition-indicator">
              Edition: <span className="font-medium text-text-heading">{workspace.edition}</span>
            </p>
            <label className="block text-text-muted">
              Select edition
              <select
                data-testid="workspace-edition-select"
                className="mt-1 w-full rounded-xl border border-border-subtle bg-card px-3 py-2 text-sm"
                value={editionDraft}
                onChange={(e) => setEditionDraft(e.target.value as WorkspaceEdition)}
                disabled={!workspace.is_admin || saving}
              >
                <option value="SYNDICATOR">Syndicator</option>
                <option value="FUND">Fund</option>
              </select>
            </label>
            <Button data-testid="workspace-edition-save" onClick={onSaveEdition} disabled={!workspace.is_admin || !hasChanges || saving}>
              {saving ? 'Saving…' : 'Save Edition'}
            </Button>
            {!workspace.is_admin ? (
              <p className="text-xs text-text-muted">Only workspace admins can switch editions.</p>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Capabilities</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-text-muted">
            <p>Deal workflow: {workspace.capabilities.features.deals ? 'Enabled' : 'Disabled'}</p>
            <p>BOE gate: {workspace.capabilities.features.boe ? 'Enabled' : 'Disabled'}</p>
            <p>Portfolio view: {workspace.capabilities.features.portfolio_view ? 'Enabled' : 'Disabled'}</p>
            <p>Fund admin: {workspace.capabilities.features.fund_admin ? 'Enabled' : 'Disabled'}</p>
          </CardContent>
        </Card>

        {workspace.capabilities.features.fund_mode ? (
          <Card data-testid="fund-admin-placeholder" className="xl:col-span-2">
            <CardHeader>
              <CardTitle>Fund Admin (coming soon)</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-text-muted">
              Fund-only configuration and reporting modules will appear here when enabled.
            </CardContent>
          </Card>
        ) : null}
      </div>

      {toast ? <Toast message={toast.message} tone={toast.tone} /> : null}
    </main>
  );
}
