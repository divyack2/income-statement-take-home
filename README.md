# Income statement

A small full-stack app that shows an income statement (P&L) for Northwind Coffee Roasters
for any date range, built from the chart of accounts and journal entries in
`backend/ledger.json`.

- [SPEC.md](SPEC.md): the take-home assignment and the data
- [NOTES.md](NOTES.md): decisions, assumptions, and how the numbers were checked
- [ACCOUNTING_PRIMER.md](ACCOUNTING_PRIMER.md): accounting terms

## Versions

| Tool | Version |
| --- | --- |
| Python | 3.13.5 |
| FastAPI / Pydantic / Uvicorn / pytest | 0.162.0 / 2.14.1 / 0.54.0 / 9.1.1 (pinned in `backend/requirements.txt`) |
| Node / npm | 24.4.1 / 11.4.2 |
| React / Vite / TypeScript | 19.3.1 / 8.3.5 / 6.0.3 (locked in `frontend/package-lock.json`) |

## Setup (once)

```sh
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ../frontend
npm install
```

## Run

In two terminals:

```sh
# Backend on http://localhost:8000
cd backend && source .venv/bin/activate && uvicorn main:app --reload --port 8000

# Frontend on http://localhost:5173
cd frontend && npm run dev
```

Open http://localhost:5173, pick a start and end date, and click **Show statement**.
The frontend calls `/api/income-statement`; the Vite dev server forwards it to the backend on
port 8000 and strips the `/api` prefix, so no CORS setup is needed.

The API can also be called directly:

```sh
curl "http://localhost:8000/income-statement?start=2026-01-01&end=2026-03-31"
```

## Test

```sh
cd backend && source .venv/bin/activate && pytest
```

## Layout

```
backend/
  ledger.py      load ledger.json into validated, typed dataclasses
  statement.py   the accounting: account totals, sections, subtotals
  main.py        the FastAPI route
  tests/         ledger validation, accounting, and API tests
frontend/src/
  App.tsx            date form, fetch, page layout
  statementRows.tsx  table rows for sections and subtotals
  types.ts           the API response types
```
