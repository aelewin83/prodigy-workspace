import { useEffect, useState } from 'react';
import Link from 'next/link';

import { cn } from '@/lib/utils';
import { listWorkspaces, type Workspace } from '@/lib/workspace-api';

const items = [
  { href: '/', label: 'Dashboard' },
  { href: '/deals', label: 'Deals' },
  { href: '/comps', label: 'Comps' },
  { href: '/settings', label: 'Settings' },
];

export function SidebarNav({ pathname }: { pathname: string }) {
  const [workspace, setWorkspace] = useState<Workspace | null>(null);

  useEffect(() => {
    let mounted = true;
    listWorkspaces()
      .then((rows) => {
        if (!mounted) return;
        setWorkspace(rows[0] ?? null);
      })
      .catch(() => {
        setWorkspace(null);
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-border-subtle bg-sidebar p-5 dark:border-slate-700 dark:bg-slate-950 lg:block">
      <p className="text-xs uppercase tracking-wide text-text-muted dark:text-slate-400">Workspace</p>
      <div className="mt-2 rounded-xl border border-border-subtle bg-card px-3 py-2 text-sm text-text-heading dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100">
        <p>{workspace?.name ?? 'Prodigy NYC Fund I'}</p>
        <p className="text-xs text-text-muted">Edition: {workspace?.edition ?? 'SYNDICATOR'}</p>
      </div>

      <nav className="mt-6 space-y-1">
        {items.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'block rounded-xl px-3 py-2 text-sm transition-colors',
                active
                  ? 'bg-accent/10 text-text-heading dark:text-slate-100'
                  : 'text-text-muted hover:bg-card dark:text-slate-400 dark:hover:bg-slate-900',
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
