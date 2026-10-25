import json
from pathlib import Path

from fastapi import FastAPI

# Relative to this file, not the working directory, so it loads from anywhere.
LEDGER_PATH = Path(__file__).parent / "ledger.json"
LEDGER = json.loads(LEDGER_PATH.read_text())

app = FastAPI()


@app.get("/health")
def health():
    return {"company": LEDGER["company"]}
