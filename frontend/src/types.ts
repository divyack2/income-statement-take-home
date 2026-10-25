// Mirrors the backend response. Amounts are strings so they stay exact;
// the page only formats them and never does arithmetic on them.
export type StatementLine = { account: string; name: string; amount: string }
export type StatementSection = { label: string; total: string; lines: StatementLine[] }
export type IncomeStatement = {
  company: string
  currency: string
  start: string
  end: string
  sections: {
    revenue: StatementSection
    cost_of_goods_sold: StatementSection
    operating_expenses: StatementSection
    other_income: StatementSection
  }
  subtotals: { gross_profit: string; operating_income: string; net_income: string }
}
