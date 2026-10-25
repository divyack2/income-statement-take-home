"""Pure accounting functions. No FastAPI imports here."""

import datetime
from decimal import Decimal

from ledger import Ledger


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
