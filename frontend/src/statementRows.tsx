// Table rows for the income statement: each section's lines and total, and the subtotals.
import type { StatementSection } from './types.ts'

// "-800.25" -> "($800.25)". The "accounting" sign puts negatives in parentheses.
// Passing the string (not Number(amount)) keeps the value exact.
function formatAmount(amount: string, currency: string): string {
  const formatter = new Intl.NumberFormat('en-US', { style: 'currency', currency, currencySign: 'accounting' })
  return formatter.format(amount as Intl.StringNumericLiteral)
}

const amountStyle = { textAlign: 'right', paddingLeft: '3em', fontVariantNumeric: 'tabular-nums' } as const
const bold = { fontWeight: 'bold' } as const
// Space after each total and subtotal, so the sections read as separate blocks.
const spaceBelow = { paddingBottom: '1em' } as const

export function sectionRows(section: StatementSection, currency: string) {
  return (
    <>
      <tr>
        <td colSpan={3} style={bold}>{section.label}</td>
      </tr>
      {section.lines.map((line) => (
        <tr key={line.account}>
          <td style={{ paddingLeft: '2em', paddingRight: '1em' }}>{line.account}</td>
          <td>{line.name}</td>
          <td style={amountStyle}>{formatAmount(line.amount, currency)}</td>
        </tr>
      ))}
      <tr style={bold}>
        <td colSpan={2} style={spaceBelow}>Total {section.label.toLowerCase()}</td>
        <td style={{ ...amountStyle, ...spaceBelow, borderTop: '1px solid' }}>{formatAmount(section.total, currency)}</td>
      </tr>
    </>
  )
}

export function subtotalRow(label: string, amount: string, currency: string, border = '') {
  return (
    <tr style={bold}>
      <td colSpan={2} style={spaceBelow}>{label}</td>
      <td style={{ ...amountStyle, ...spaceBelow, borderTop: border }}>{formatAmount(amount, currency)}</td>
    </tr>
  )
}
