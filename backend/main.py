import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException

from ledger import load_ledger
from statement import IncomeStatement, build_income_statement

# Relative to this file, not the working directory, so it loads from anywhere.
# Raises LedgerError at startup if the data is invalid.
LEDGER = load_ledger(Path(__file__).parent / "ledger.json")

app = FastAPI()


# The return type annotation matters: it makes FastAPI serialize the dataclass
# through Pydantic, which sends Decimal as a string. Without it, amounts become floats.
@app.get("/income-statement")
def get_income_statement(start: datetime.date, end: datetime.date) -> IncomeStatement:
    # Typing start and end as dates makes FastAPI return 422 for missing or bad dates.
    if start > end:
        raise HTTPException(status_code=422, detail="start must be on or before end")
    return build_income_statement(LEDGER, start, end)
