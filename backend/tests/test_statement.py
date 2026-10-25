import datetime
from decimal import Decimal
from pathlib import Path

from ledger import load_ledger, parse_ledger
from statement import account_totals

REAL_LEDGER = Path(__file__).parent.parent / "ledger.json"

JAN_1 = datetime.date(2026, 1, 1)
MAR_31 = datetime.date(2026, 3, 31)

ACCOUNTS = [
    {"number": "1000", "name": "Cash", "type": "asset", "subtype": "balance_sheet", "is_active": True},
    {"number": "2100", "name": "Deferred Revenue", "type": "liability", "subtype": "balance_sheet", "is_active": True},
    {"number": "4000", "name": "Product Revenue", "type": "revenue", "subtype": "operating_revenue", "is_active": True},
    {"number": "4900", "name": "Sales Returns", "type": "revenue", "subtype": "contra_revenue", "is_active": True},
    {"number": "6200", "name": "Software", "type": "expense", "subtype": "operating_expense", "is_active": True},
    {"number": "6300", "name": "Marketing (legacy)", "type": "expense", "subtype": "operating_expense", "is_active": False},
    {"number": "7000", "name": "Interest Income", "type": "revenue", "subtype": "other_income", "is_active": True},
]


def entry(entry_id, date, status, *lines):
    """Build a raw journal entry. Each line is (account, debit, credit)."""
    return {
        "id": entry_id,
        "date": date,
        "status": status,
        "memo": "",
        "lines": [{"account": a, "debit": d, "credit": c} for a, d, c in lines],
    }


def amounts_for(*entries, start=JAN_1, end=MAR_31):
    ledger = parse_ledger({
        "company": "Test Co",
        "currency": "USD",
        "accounts": ACCOUNTS,
        "journal_entries": list(entries),
    })
    return account_totals(ledger, start, end)


def sale(entry_id, date, amount, status="posted"):
    return entry(entry_id, date, status, ("1000", amount, "0.00"), ("4000", "0.00", amount))


def test_revenue_is_positive():
    assert amounts_for(sale("JE-1", "2026-01-05", "100.00")) == {"4000": Decimal("100.00")}


def test_draft_and_void_entries_are_excluded():
    amounts = amounts_for(
        sale("JE-1", "2026-01-05", "100.00"),
        sale("JE-2", "2026-01-06", "40.00", status="draft"),
        sale("JE-3", "2026-01-07", "7.00", status="void"),
    )
    assert amounts == {"4000": Decimal("100.00")}


def test_both_date_bounds_are_inclusive():
    amounts = amounts_for(
        sale("JE-1", "2025-12-31", "1.00"),  # day before start
        sale("JE-2", "2026-01-01", "10.00"),  # on start
        sale("JE-3", "2026-03-31", "100.00"),  # on end
        sale("JE-4", "2026-04-01", "1000.00"),  # day after end
    )
    assert amounts == {"4000": Decimal("110.00")}


def test_entry_order_does_not_matter():
    amounts = amounts_for(
        sale("JE-2", "2026-03-01", "20.00"),
        sale("JE-1", "2026-01-01", "10.00"),
    )
    assert amounts == {"4000": Decimal("30.00")}


def test_contra_revenue_debit_is_negative():
    # A sale with a discount on a 3-line entry, like JE-016.
    amounts = amounts_for(
        entry("JE-1", "2026-03-02", "posted",
              ("1000", "99.00", "0.00"), ("4900", "1.00", "0.00"), ("4000", "0.00", "100.00")),
    )
    assert amounts == {"4000": Decimal("100.00"), "4900": Decimal("-1.00")}


def test_credit_to_expense_reduces_it():
    # A vendor refund, like JE-020.
    amounts = amounts_for(
        entry("JE-1", "2026-03-10", "posted", ("6200", "1199.97", "0.00"), ("1000", "0.00", "1199.97")),
        entry("JE-2", "2026-03-20", "posted", ("1000", "100.00", "0.00"), ("6200", "0.00", "100.00")),
    )
    assert amounts == {"6200": Decimal("1099.97")}


def test_interest_income_is_positive():
    # 7000 is type revenue with subtype other_income; the sign follows the type.
    amounts = amounts_for(entry("JE-1", "2026-03-31", "posted", ("1000", "42.18", "0.00"), ("7000", "0.00", "42.18")))
    assert amounts == {"7000": Decimal("42.18")}


def test_billing_to_deferred_revenue_is_not_revenue():
    # Like JE-004: only balance sheet accounts move, so nothing shows.
    amounts = amounts_for(entry("JE-1", "2026-01-10", "posted", ("1000", "12000.00", "0.00"), ("2100", "0.00", "12000.00")))
    assert amounts == {}


def test_inactive_account_history_is_included():
    # Like JE-008: is_active only governs new postings.
    amounts = amounts_for(entry("JE-1", "2026-01-20", "posted", ("6300", "2500.10", "0.00"), ("1000", "0.00", "2500.10")))
    assert amounts == {"6300": Decimal("2500.10")}


def test_q1_2026_golden_values():
    # Expected values are from a hand calculation over the ledger, not from this code.
    ledger = load_ledger(REAL_LEDGER)
    assert account_totals(ledger, JAN_1, MAR_31) == {
        "4000": Decimal("35650.75"),  # JE-002 + JE-010 + JE-016 (JE-009 void, JE-001/024 outside)
        "4100": Decimal("3000.00"),  # JE-005, JE-014, JE-021 (not JE-004 billing)
        "4900": Decimal("-800.25"),  # JE-012 + JE-016
        "5000": Decimal("14272.75"),  # JE-003 + JE-011 + JE-017
        "6000": Decimal("55500.00"),  # three payrolls (JE-019 draft bonus excluded)
        "6100": Decimal("9000.00"),  # JE-007, all three months on Jan 1
        "6200": Decimal("1099.97"),  # JE-018 less JE-020 refund
        "6300": Decimal("2500.10"),  # JE-008, inactive account
        "7000": Decimal("42.18"),  # JE-023
    }
