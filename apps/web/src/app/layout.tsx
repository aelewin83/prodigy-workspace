import './globals.css';
import type { Metadata } from 'next';
import type { ReactNode } from 'react';

import { AppShell } from '@/components/layout/app-shell';

export const metadata: Metadata = {
  title: 'Prodigy Workspace',
  description: 'Institutional Intelligence for Emerging GPs',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
