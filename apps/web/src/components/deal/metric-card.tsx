import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function MetricCard({
  label,
  value,
  subtext,
  prominent = false,
}: {
  label: string;
  value: string;
  subtext?: string;
  prominent?: boolean;
}) {
  return (
    <Card>
      <CardHeader>
        <p className="text-xs uppercase tracking-wide text-text-muted">{label}</p>
        <CardTitle className={prominent ? 'text-2xl' : 'text-xl'}>{value}</CardTitle>
      </CardHeader>
      {subtext ? (
        <CardContent>
          <p className="text-sm text-text-muted">{subtext}</p>
        </CardContent>
      ) : null}
    </Card>
  );
}
