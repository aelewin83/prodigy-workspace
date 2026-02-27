export type Stage = 'Intake' | 'Screening' | 'BOE Pass' | 'BOE Fail' | 'Full UW Authorized';

export type TestResult = 'PASS' | 'FAIL' | 'WARN' | 'N/A';

export type TestRow = {
  name: string;
  klass: 'Hard Veto' | 'Soft';
  threshold: string;
  actual: string;
  result: TestResult;
};

export type BOERun = {
  id: string;
  timestamp: string;
  author: string;
  decision: 'PASS' | 'FAIL' | 'PASS_WITH_NOTES';
  maxBid: number;
  bindingConstraint: string;
  deltaToAsk: number;
  y1Dscr: number;
  yoc: number;
  exitCap: number;
  expenseRatio: number;
  inputs: Record<string, string>;
  outputs: Record<string, string>;
  tests: TestRow[];
};

export type Deal = {
  id: string;
  name: string;
  address?: string;
  neighborhood: string;
  stage: Stage;
  ask: number;
  updatedDate: string;
  notes: string[];
  latestRun: BOERun;
  runs: BOERun[];
};

const runA: BOERun = {
  id: 'run-2026-02-20-1',
  timestamp: '2026-02-20 09:42 ET',
  author: 'Alex Kim',
  decision: 'PASS_WITH_NOTES',
  maxBid: 9725000,
  bindingConstraint: 'CapEx Multiple',
  deltaToAsk: -675000,
  y1Dscr: 1.21,
  yoc: 0.067,
  exitCap: 0.052,
  expenseRatio: 0.301,
  inputs: {
    'Asking Price': '$10,400,000',
    'Deposit %': '5.00%',
    'Interest Rate': '6.10%',
    LTC: '70.00%',
    'CapEx Budget': '$1,300,000',
  },
  outputs: {
    'Market Cap Rate': '5.35%',
    'Asking Cap Rate': '5.02%',
    'Y1 Exit Cap Rate': '5.20%',
    'Residual @ Exit Cap': '$11,020,000',
    'Profit Potential': '$1,295,000',
    'Max Price @ YOC': '$9,890,000',
    'Max Price @ CapEx Multiple': '$9,725,000',
    'Max Price @ CoC': '$9,910,000',
    'BOE Max Bid': '$9,725,000',
    'Delta to Asking': '-$675,000 (-6.49%)',
    'Deposit Amount': '$486,250',
  },
  tests: [
    { name: 'Yield on Cost', klass: 'Hard Veto', threshold: '>= Exit Cap + 1.00%', actual: '6.70%', result: 'PASS' },
    { name: 'CapEx Value Multiple', klass: 'Hard Veto', threshold: '>= 2.00x', actual: '2.12x', result: 'PASS' },
    { name: 'Positive Leverage', klass: 'Hard Veto', threshold: 'YOC >= Rate', actual: '6.70% vs 6.10%', result: 'PASS' },
    { name: 'Cash on Cash', klass: 'Soft', threshold: '>= 4.50%', actual: '4.92%', result: 'PASS' },
    { name: 'DSCR', klass: 'Soft', threshold: '>=1.30 PASS / >=1.15 WARN', actual: '1.21', result: 'WARN' },
    { name: 'Expense Ratio', klass: 'Soft', threshold: '>= 28.00%', actual: '30.10%', result: 'PASS' },
    { name: 'Market Cap Rate', klass: 'Soft', threshold: 'Market >= Asking', actual: '5.35% vs 5.02%', result: 'PASS' },
  ],
};

const runB: BOERun = {
  ...runA,
  id: 'run-2026-02-16-1',
  timestamp: '2026-02-16 16:03 ET',
  decision: 'FAIL',
  maxBid: 9190000,
  bindingConstraint: 'YOC',
  deltaToAsk: -1210000,
  y1Dscr: 1.1,
  yoc: 0.059,
  exitCap: 0.052,
  expenseRatio: 0.274,
  outputs: {
    ...runA.outputs,
    'BOE Max Bid': '$9,190,000',
    'Delta to Asking': '-$1,210,000 (-11.63%)',
  },
  tests: [
    { name: 'Yield on Cost', klass: 'Hard Veto', threshold: '>= Exit Cap + 1.00%', actual: '5.90%', result: 'FAIL' },
    { name: 'CapEx Value Multiple', klass: 'Hard Veto', threshold: '>= 2.00x', actual: '1.88x', result: 'FAIL' },
    { name: 'Positive Leverage', klass: 'Hard Veto', threshold: 'YOC >= Rate', actual: '5.90% vs 6.10%', result: 'FAIL' },
    { name: 'Cash on Cash', klass: 'Soft', threshold: '>= 4.50%', actual: '4.23%', result: 'FAIL' },
    { name: 'DSCR', klass: 'Soft', threshold: '>=1.30 PASS / >=1.15 WARN', actual: '1.10', result: 'FAIL' },
    { name: 'Expense Ratio', klass: 'Soft', threshold: '>= 28.00%', actual: '27.40%', result: 'FAIL' },
    { name: 'Market Cap Rate', klass: 'Soft', threshold: 'Market >= Asking', actual: '5.12% vs 5.02%', result: 'PASS' },
  ],
};

export const deals: Deal[] = [
  {
    id: 'queens-24',
    name: 'Queens 24-Unit',
    address: '31-18 37th St, Astoria, NY',
    neighborhood: 'Astoria',
    stage: 'BOE Pass',
    ask: 10400000,
    updatedDate: '2026-02-20',
    notes: [
      'Seller open to quick close if non-refundable goes hard in 21 days.',
      'Tax certiorari downside partially underwritten.',
    ],
    latestRun: runA,
    runs: [runA, runB],
  },
  {
    id: 'bronx-31',
    name: 'Bronx 31-Unit',
    address: '1129 Grant Ave, Bronx, NY',
    neighborhood: 'Morrisania',
    stage: 'BOE Fail',
    ask: 8900000,
    updatedDate: '2026-02-22',
    notes: ['Rent roll has two recent non-payment move-outs.', 'High deferred maintenance noted in OM.'],
    latestRun: { ...runB, id: 'run-2026-02-22-1' },
    runs: [{ ...runB, id: 'run-2026-02-22-1' }],
  },
];

export function getDeal(id: string): Deal | undefined {
  return deals.find((deal) => deal.id === id);
}
