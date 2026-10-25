## To run:
Backend: `cd backend && source .venv/bin/activate && uvicorn main:app --reload --port 8000`

Frontend: `cd frontend && npm run dev`

## Decisions
- The JSON is treated as untrusted. It is parsed and validated once at startup into frozen, typed dataclasses, so the accounting code assumes valid data and has no defensive checks.

## Assumptions
- Journal entry ids are unique. The loader does not check this, so a repeated entry would be counted twice.
- ledger.json has the shape described in the README, and amounts and dates are in the right format to parse directly: amounts as decimal strings (not JSON numbers, which would arrive as floats) and dates as `YYYY-MM-DD`. Validation currently covers the accounting rules, not the raw format. A roadmap item is more in-depth validation of the JSON shape and formats, with clear error messages instead of a plain `KeyError` or `ValueError`.
- Account numbers are unique. The loader does not check this, so a repeated number would silently replace the earlier account.
