"""Build an income statement from a validated ledger. Pure functions, no web code."""

import datetime
from dataclasses import dataclass
from decimal import Decimal

from ledger import Ledger, Subtype

# Which section each account goes in, decided by its subtype (never its type:
# Interest Income is type revenue but belongs in Other income). Values are the
# field names of Sections. Balance sheet accounts are in no section.
SECTION_FOR_SUBTYPE: dict[Subtype, str] = {
    "operating_revenue": "revenue",
    "contra_revenue": "revenue",
    "cogs": "cost_of_goods_sold",
    "operating_expense": "operating_expenses",
    "other_income": "other_income",
}


@dataclass(frozen=True)
class StatementLine:
    account: str  # account number
    name: str
    amount: Decimal


@dataclass(frozen=True)
class StatementSection:
    label: str
    total: Decimal
    lines: tuple[StatementLine, ...]


@dataclass(frozen=True)
class Sections:
    revenue: StatementSection
    cost_of_goods_sold: StatementSection
    operating_expenses: StatementSection
    other_income: StatementSection


@dataclass(frozen=True)
class Subtotals:
    gross_profit: Decimal
    operating_income: Decimal
    net_income: Decimal


@dataclass(frozen=True)
class IncomeStatement:
    company: str
    currency: str
    start: datetime.date
    end: datetime.date
    sections: Sections
    subtotals: Subtotals


def per_account_totals(
    ledger: Ledger, start: datetime.date, end: datetime.date
) -> dict[str, Decimal]:
    """Sum each income statement account's posted activity from start to end, inclusive.

    Amounts are signed so that normal activity is positive: revenue is credit minus
    debit, expenses are debit minus credit. So contra-revenue (returns, discounts)
    and credits to an expense (vendor refunds) come out negative on their own.

    Balance sheet accounts are skipped. Accounts with no lines in the range are
    left out of the result.
    """
    amounts: dict[str, Decimal] = {}
    for journal_entry in ledger.journal_entries:
        if journal_entry.status != "posted" or not (start <= journal_entry.date <= end):
            continue
        for line in journal_entry.lines:
            account = ledger.accounts[line.account]
            if account.subtype == "balance_sheet":
                continue
            # Revenue grows with credits, so flip it to show as positive like expenses.
            amount = line.debit - line.credit
            if account.type == "revenue":
                amount = -amount
            amounts[line.account] = amounts.get(line.account, Decimal("0")) + amount
    return amounts
