import { expect, test } from '@playwright/test';

const RUN_LIST = [
  {
    id: 'run-1',
    deal_id: 'queens-24',
    version: 1,
    inputs: { asking_price: 10400000, deposit_pct: 0.05, interest_rate: 0.061, ltc: 0.7 },
    outputs: {
      boe_max_bid: 9725000,
      delta_vs_asking: -675000,
      deposit_amount: 486250,
      binding_constraint: 'CapEx Multiple',
      market_cap_rate: 0.053,
      asking_cap_rate: 0.05,
      y1_exit_cap_rate: 0.052,
      y1_dscr: 1.2,
      y1_expense_ratio: 0.31,
      y1_yield_on_cost_unlevered: 0.068,
    },
    decision: 'ADVANCE',
    binding_constraint: 'CapEx Multiple',
    hard_veto_ok: true,
    pass_count: 6,
    advance: true,
    created_by: 'u1',
    created_at: new Date().toISOString(),
    tests: [
      { test_key: 'yield_on_cost', test_name: 'Yield on Cost Test', test_class: 'hard', threshold: null, actual: null, threshold_display: '>= Exit Cap + 1.00%', actual_display: '6.80%', result: 'PASS', note: null },
      { test_key: 'capex_value_multiple', test_name: 'CapEx Value Multiple Test', test_class: 'hard', threshold: null, actual: null, threshold_display: '>= 2.00x', actual_display: '2.10x', result: 'PASS', note: null },
      { test_key: 'positive_leverage', test_name: 'Positive Leverage Test', test_class: 'hard', threshold: null, actual: null, threshold_display: '>= Interest Rate', actual_display: '6.80%', result: 'PASS', note: null },
      { test_key: 'cash_on_cash', test_name: 'Cash on Cash Test', test_class: 'soft', threshold: null, actual: null, threshold_display: '>= 4.50%', actual_display: '4.90%', result: 'PASS', note: null },
      { test_key: 'dscr', test_name: 'DSCR Test', test_class: 'soft', threshold: null, actual: null, threshold_display: 'PASS>=1.25 | WARN>=1.15 | FAIL<1.15', actual_display: '1.20', result: 'WARN', note: null },
      { test_key: 'expense_ratio', test_name: 'Expense Ratio Test', test_class: 'soft', threshold: null, actual: null, threshold_display: '>= 28.00%', actual_display: '31.00%', result: 'PASS', note: null },
      { test_key: 'market_cap_rate', test_name: 'Market Cap Rate Test', test_class: 'soft', threshold: null, actual: null, threshold_display: '>= Asking Cap Rate', actual_display: '5.30%', result: 'PASS', note: null },
    ],
  },
];

test.beforeEach(async ({ page }) => {
  await page.route('**/v1/deals/queens-24/boe/runs', async (route) => {
    if (route.request().method() === 'POST') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(RUN_LIST[0]) });
      return;
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(RUN_LIST) });
  });

  await page.route('**/v1/deals/queens-24/boe/runs/*', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(RUN_LIST[0]) });
  });
});

test('create deal and open detail', async ({ page }) => {
  await page.goto('/deals');
  await page.getByLabel('Deal name').fill('New Test Deal');
  await page.getByLabel('Deal address').fill('1 Main St');
  await page.getByRole('button', { name: 'Create Deal' }).click();
  await expect(page.getByText('New Test Deal')).toBeVisible();
  const queensRow = page.locator('tr', { hasText: 'Queens 24-Unit' });
  await queensRow.getByRole('link', { name: 'Open' }).click();
  await page.waitForURL(/\/deals\/queens-24\?tab=boe$/);
  await expect(page.getByTestId('deal-detail-title')).toBeVisible();
  await expect(page.getByTestId('deal-detail-title')).toHaveText('Queens 24-Unit');
});

test('run boe and render pass fail warn states', async ({ page }) => {
  await page.goto('/deals/queens-24?tab=boe');
  await page.getByTestId('boe-run-button').click();
  await expect(page.getByTestId('boe-run-toast')).toHaveText('BOE run created.');
  const testsPanel = page.getByTestId('boe-tests-panel');
  await expect(testsPanel.getByTestId('boe-test-result-dscr')).toHaveText('WARN');
  await expect(testsPanel.getByTestId('boe-test-result-yield_on_cost')).toHaveText('PASS');
});

test('compare runs ui renders', async ({ page }) => {
  await page.goto('/deals/queens-24?tab=boe');
  await page.getByRole('button', { name: 'Compare Runs' }).click();
  await expect(page.getByText('Compare Runs')).toBeVisible();
  await expect(page.getByText('Inputs Diff')).toBeVisible();
  await expect(page.getByText('Outputs Diff')).toBeVisible();
  await expect(page.getByText('Test State Changes')).toBeVisible();
});
