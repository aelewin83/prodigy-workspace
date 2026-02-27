export type BTestResult = 'PASS' | 'FAIL' | 'WARN' | 'N/A';

export type BoeTestResult = {
  test_key: string;
  test_name: string;
  test_class: 'hard' | 'soft';
  threshold: number | null;
  actual: number | null;
  threshold_display: string | null;
  actual_display: string | null;
  result: BTestResult;
  note: string | null;
};

export type BoeRun = {
  id: string;
  deal_id: string;
  version: number;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
  decision: 'ADVANCE' | 'KILL';
  binding_constraint: string | null;
  hard_veto_ok: boolean;
  pass_count: number;
  advance: boolean;
  created_by: string;
  created_at: string;
  tests: BoeTestResult[];
};

export type BoeInputDraft = {
  asking_price: string;
  deposit_pct: string;
  interest_rate: string;
  ltc: string;
  capex_budget: string;
  soft_cost_pct: string;
  reserves: string;
  seller_noi_from_om: string;
  gross_income: string;
  operating_expenses: string;
  y1_noi: string;
  market_cap_rate: string;
  y1_exit_cap_rate: string;
};
