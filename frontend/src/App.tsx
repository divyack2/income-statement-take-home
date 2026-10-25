import { useState, type SubmitEvent } from 'react'
import { sectionRows, subtotalRow } from './statementRows.tsx'
import type { IncomeStatement } from './types.ts'

export default function App() {
  const [start, setStart] = useState('2026-01-01')
  const [end, setEnd] = useState('2026-03-31')
  const [statement, setStatement] = useState<IncomeStatement | null>(null)
  const [error, setError] = useState('')

  async function loadStatement(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault() // stop the browser from reloading the page on submit
    try {
      const response = await fetch(`/api/income-statement?start=${start}&end=${end}`)
      const body = await response.json()
      if (response.ok) {
        setStatement(body)
        setError('')
      } else {
        setStatement(null)
        setError(typeof body.detail === 'string' ? body.detail : `Request failed (${response.status})`)
      }
    } catch {
      setStatement(null)
      setError('Could not reach the server')
    }
  }

  return (
    <main style={{ fontFamily: 'sans-serif', padding: '1em' }}>
      <form onSubmit={loadStatement}>
        <label>
          Start <input type="date" required value={start} onChange={(e) => setStart(e.target.value)} />
        </label>{' '}
        <label>
          End <input type="date" required value={end} onChange={(e) => setEnd(e.target.value)} />
        </label>{' '}
        <button type="submit">Show statement</button>
      </form>

      {error && <p>{error}</p>}

      {statement && (
        <>
          <h2 style={{ marginBottom: 0 }}>{statement.company}</h2>
          <p style={{ marginTop: '0.25em' }}>
            Income statement · {statement.start} to {statement.end} · {statement.currency}
          </p>
          <table style={{ borderCollapse: 'collapse' }}>
            <tbody>
              {sectionRows(statement.sections.revenue, statement.currency)}
              {sectionRows(statement.sections.cost_of_goods_sold, statement.currency)}
              {subtotalRow('Gross profit', statement.subtotals.gross_profit, statement.currency)}
              {sectionRows(statement.sections.operating_expenses, statement.currency)}
              {subtotalRow('Operating income', statement.subtotals.operating_income, statement.currency)}
              {sectionRows(statement.sections.other_income, statement.currency)}
              {subtotalRow('Net income', statement.subtotals.net_income, statement.currency, '3px double')}
            </tbody>
          </table>
        </>
      )}
    </main>
  )
}
