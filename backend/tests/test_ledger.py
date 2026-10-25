import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from ledger import LedgerError, load_ledger, parse_ledger

REAL_LEDGER = Path(__file__).parent.parent / "ledger.json"


def raw_ledger():
    """A tiny valid ledger. Each test breaks one thing in it."""
    return {
        "company": "Test Co",
        "currency": "USD",
        "accounts": [
            {"number": "1000", "name": "Cash", "type": "asset", "subtype": "balance_sheet", "is_active": True},
            {"number": "4000", "name": "Sales", "type": "revenue", "subtype": "operating_revenue", "is_active": True},
        ],
        "journal_entries": [
            {"id": "JE-1", "date": "2026-01-05", "status": "posted", "memo": "sale", "lines": [
                {"account": "1000", "debit": "100.00", "credit": "0.00"},
                {"account": "4000", "debit": "0.00", "credit": "100.00"},
            ]},
        ],
    }


def first_line(raw):
    return raw["journal_entries"][0]["lines"][0]


def test_real_ledger_loads_into_typed_objects():
    ledger = load_ledger(REAL_LEDGER)
    assert len(ledger.accounts) == 15
    assert len(ledger.journal_entries) == 25
    assert ledger.accounts["6300"].is_active is False
    je016 = next(e for e in ledger.journal_entries if e.id == "JE-016")
    assert je016.date == datetime.date(2026, 3, 2)
    assert len(je016.lines) == 3
    assert je016.lines[1].debit == Decimal("150.00")


def test_valid_tiny_ledger_loads():
    ledger = parse_ledger(raw_ledger())
    assert ledger.accounts["4000"].type == "revenue"


def test_rejects_unbalanced_entry():
    raw = raw_ledger()
    first_line(raw)["debit"] = "100.01"
    with pytest.raises(LedgerError, match="JE-1: debits 100.01 do not equal credits 100.00"):
        parse_ledger(raw)


def test_rejects_unknown_account():
    raw = raw_ledger()
    first_line(raw)["account"] = "9999"
    with pytest.raises(LedgerError, match="JE-1: unknown account 9999"):
        parse_ledger(raw)


def test_rejects_line_with_both_debit_and_credit():
    raw = raw_ledger()
    first_line(raw)["credit"] = "100.00"
    with pytest.raises(LedgerError, match="exactly one of debit or credit"):
        parse_ledger(raw)


def test_rejects_line_with_neither_debit_nor_credit():
    raw = raw_ledger()
    raw["journal_entries"][0]["lines"].append({"account": "1000", "debit": "0.00", "credit": "0.00"})
    with pytest.raises(LedgerError, match="exactly one of debit or credit"):
        parse_ledger(raw)


def test_rejects_negative_amount():
    raw = raw_ledger()
    lines = raw["journal_entries"][0]["lines"]
    lines[0].update(debit="0.00", credit="-100.00")
    lines[1].update(debit="-100.00", credit="0.00")
    with pytest.raises(LedgerError, match="must not be negative"):
        parse_ledger(raw)


def test_rejects_more_than_two_decimal_places():
    raw = raw_ledger()
    first_line(raw)["debit"] = "100.001"
    with pytest.raises(LedgerError, match="more than 2 decimal places"):
        parse_ledger(raw)


def test_rejects_unknown_status():
    raw = raw_ledger()
    raw["journal_entries"][0]["status"] = "Posted"
    with pytest.raises(LedgerError, match="JE-1: status 'Posted' must be one of"):
        parse_ledger(raw)


def test_rejects_unknown_subtype():
    raw = raw_ledger()
    raw["accounts"][1]["subtype"] = "interest"
    with pytest.raises(LedgerError, match="account 4000: subtype 'interest' must be one of"):
        parse_ledger(raw)


def test_rejects_type_that_does_not_fit_subtype():
    raw = raw_ledger()
    raw["accounts"][1]["type"] = "expense"
    raw["accounts"][1]["subtype"] = "other_income"
    with pytest.raises(LedgerError, match="type 'expense' is not allowed with subtype 'other_income'"):
        parse_ledger(raw)


def test_rejects_entry_with_one_line():
    raw = raw_ledger()
    raw["journal_entries"][0]["lines"].pop()
    with pytest.raises(LedgerError, match="at least 2 lines"):
        parse_ledger(raw)
