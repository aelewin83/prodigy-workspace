import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function SettingsPage() {
  return (
    <main className="space-y-6">
      <header>
        <p className="text-xs uppercase tracking-wide text-text-muted">Workspace Controls</p>
        <h1 className="text-3xl font-semibold text-text-heading">Settings</h1>
      </header>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Membership</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-text-muted">Owner/member management and role policies.</CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Connector Policy</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-text-muted">Allowlisted public connectors and domain controls.</CardContent>
        </Card>
      </div>
    </main>
  );
}
