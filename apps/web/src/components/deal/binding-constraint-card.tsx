import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function BindingConstraintCard({ constraint, detail }: { constraint: string; detail: string }) {
  return (
    <Card>
      <CardHeader>
        <p className="text-xs uppercase tracking-wide text-text-muted">Binding Constraint</p>
        <CardTitle>{constraint}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-text-muted">{detail}</p>
      </CardContent>
    </Card>
  );
}
