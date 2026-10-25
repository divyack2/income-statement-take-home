from pathlib import Path

from fastapi import FastAPI

from ledger import load_ledger

# Relative to this file, not the working directory, so it loads from anywhere.
# Raises LedgerError at startup if the data is invalid.
LEDGER = load_ledger(Path(__file__).parent / "ledger.json")

app = FastAPI()


@app.get("/health")
def health():
    return {"company": LEDGER.company}
