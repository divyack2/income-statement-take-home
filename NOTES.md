## To run:
Backend: `cd backend && source .venv/bin/activate && uvicorn main:app --reload --port 8000`

Frontend: `cd frontend && npm run dev`

## Decisions
- The JSON is treated as untrusted. It is parsed and validated once at startup into frozen, typed dataclasses, so the accounting code assumes valid data and has no defensive checks.
- Response types are dataclasses; FastAPI serializes them through Pydantic because the route declares its return type, so Decimal goes over the wire as a string.
- Accounts with no posted activity in the date range are left off the statement, rather than shown as 0.00 lines. All four sections always appear, with a 0.00 total when empty. An account whose activity nets to exactly 0.00 (e.g. a sale fully returned) is still shown, since it did have activity.

## Assumptions
- Journal entry ids are unique. The loader does not check this, so a repeated entry would be counted twice.
- ledger.json has the shape described in SPEC.md, and amounts and dates are in the right format to parse directly: amounts as decimal strings (not JSON numbers, which would arrive as floats) and dates as `YYYY-MM-DD`. Validation currently covers the accounting rules, not the raw format. A roadmap item is more in-depth validation of the JSON shape and formats, with clear error messages instead of a plain `KeyError` or `ValueError`.
- Account numbers are unique. The loader does not check this, so a repeated number would silently replace the earlier account.
- All amounts are in whole cents (at most 2 decimal places, which the loader checks). Sums of Decimals keep exactly 2 places, so no rounding is done anywhere. A `-0.00` can't arise either: every line is non-zero, totals start at a positive zero, and Decimal's default rounding gives `x - x` as `0.00`.
