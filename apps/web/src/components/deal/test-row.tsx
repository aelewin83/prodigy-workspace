import { DecisionBadge } from '@/components/deal/decision-badge';

const MEANING: Record<string, string> = {
  yield_on_cost: 'Checks spread between YOC and exit cap hurdle.',
  capex_value_multiple: 'Measures value creation per CapEx dollar.',
  positive_leverage: 'Requires unlevered yield to exceed debt cost.',
  cash_on_cash: 'Checks annual cash return on invested equity.',
  dscr: 'Debt service coverage safety buffer.',
  expense_ratio: 'Expense load sanity check vs revenue.',
  market_cap_rate: 'Compares market cap to asking cap.',
};

export function TestRow({
  keyName,
  name,
  klass,
  threshold,
  actual,
  result,
}: {
  keyName: string;
  name: string;
  klass: string;
  threshold: string;
  actual: string;
  result: 'PASS' | 'FAIL' | 'WARN' | 'N/A';
}) {
  return (
    <div className="grid grid-cols-12 items-center gap-2 border-b border-border-subtle py-2 last:border-b-0">
      <div className="col-span-4 text-sm text-text-body">{name}</div>
      <div className="col-span-2 text-xs uppercase tracking-wide text-text-muted">{klass}</div>
      <div className="col-span-3 text-xs text-text-muted">{threshold}</div>
      <div className="col-span-1 font-mono text-sm text-text-heading">{actual}</div>
      <div className="col-span-2 flex items-center justify-end gap-2">
        <span className="cursor-help text-xs text-text-muted" title={MEANING[keyName] ?? 'BOE test rule.'}>
          ?
        </span>
        <span data-testid={`boe-test-result-${keyName}`}>
          <DecisionBadge state={result} className="min-w-16 justify-center" />
        </span>
      </div>
    </div>
  );
}
