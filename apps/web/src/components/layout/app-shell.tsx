'use client';

import type { ReactNode } from 'react';
import { usePathname } from 'next/navigation';

import { SidebarNav } from '@/components/layout/sidebar-nav';

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return (
    <div>
      <SidebarNav pathname={pathname} />
      <div className="lg:pl-64">
        <div className="mx-auto max-w-[1600px] px-4 py-6 sm:px-6 lg:px-8">{children}</div>
      </div>
    </div>
  );
}
