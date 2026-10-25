"""Load ledger.json into typed, validated objects.

The JSON is untrusted. It is checked once, here, at load time, so the accounting
code can assume every Account and JournalEntry it receives is valid.

Each dataclass checks its own rules in __post_init__, so objects built by hand
(e.g. in tests) are validated too. The parse_* functions turn raw JSON into those
dataclasses and add context (which account, which entry) to error messages.
"""

import datetime
import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Literal, get_args

AccountType = Literal["asset", "liability", "equity", "revenue", "expense"]
Subtype = Literal[
    "operating_revenue",
    "contra_revenue",
    "cogs",
    "operating_expense",
    "other_income",
    "balance_sheet",
]
Status = Literal["posted", "draft", "void"]

# Which account types each subtype may have. other_income is revenue-only for now:
# an expense-type account there (e.g. interest expense) would show as positive and
# be added to net income, so we reject it until the sign rule handles that case.
VALID_TYPES_FOR_SUBTYPE: dict[str, set[str]] = {
    "operating_revenue": {"revenue"},
    "contra_revenue": {"revenue"},
    "cogs": {"expense"},
    "operating_expense": {"expense"},
    "other_income": {"revenue"},
    "balance_sheet": {"asset", "liability", "equity"},
}


class LedgerError(ValueError):
    """The ledger data is invalid. The message says where and why."""


@dataclass(frozen=True)
class Account:
    number: str
    name: str
    type: AccountType
    subtype: Subtype
    is_active: bool

    def __post_init__(self):
        _require_one_of_literal("type", self.type, AccountType)
        _require_one_of_literal("subtype", self.subtype, Subtype)
        if self.type not in VALID_TYPES_FOR_SUBTYPE[self.subtype]:
            raise LedgerError(
                f"type {self.type!r} is not allowed with subtype {self.subtype!r}"
            )


@dataclass(frozen=True)
class JournalLine:
    account: str
    debit: Decimal
    credit: Decimal

    def __post_init__(self):
        for name, amount in (("debit", self.debit), ("credit", self.credit)):
            if not amount.is_finite():
                raise LedgerError(f"account {self.account}: {name} must be a finite number")
            if amount < 0:
                raise LedgerError(f"account {self.account}: {name} must not be negative")
            if amount.as_tuple().exponent < -2:
                raise LedgerError(f"account {self.account}: {name} has more than 2 decimal places")
        if (self.debit > 0) == (self.credit > 0):
            raise LedgerError(
                f"account {self.account}: exactly one of debit or credit must be non-zero"
            )


@dataclass(frozen=True)
class JournalEntry:
    id: str
    date: datetime.date
    status: Status
    memo: str
    lines: tuple[JournalLine, ...]

    def __post_init__(self):
        _require_one_of_literal("status", self.status, Status)
        if len(self.lines) < 2:
            raise LedgerError("an entry needs at least 2 lines")
        debits = sum((line.debit for line in self.lines), Decimal("0"))
        credits = sum((line.credit for line in self.lines), Decimal("0"))
        if debits != credits:
            raise LedgerError(f"debits {debits} do not equal credits {credits}")


@dataclass(frozen=True)
class Ledger:
    company: str
    currency: str
    accounts: dict[str, Account]  # keyed by account number
    journal_entries: tuple[JournalEntry, ...]

    def __post_init__(self):
        for entry in self.journal_entries:
            for line in entry.lines:
                if line.account not in self.accounts:
                    raise LedgerError(f"{entry.id}: unknown account {line.account}")


def load_ledger(path: Path) -> Ledger:
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise LedgerError(f"{path.name} is not valid JSON: {e}") from None
    return parse_ledger(raw)


def parse_ledger(raw) -> Ledger:
    accounts: dict[str, Account] = {}
    for raw_account in raw["accounts"]:
        account = parse_account(raw_account)
        accounts[account.number] = account

    journal_entries = tuple(parse_entry(raw_entry) for raw_entry in raw["journal_entries"])
    return Ledger(
        company=raw["company"],
        currency=raw["currency"],
        accounts=accounts,
        journal_entries=journal_entries,
    )


def parse_account(raw) -> Account:
    try:
        return Account(
            number=raw["number"],
            name=raw["name"],
            type=raw["type"],
            subtype=raw["subtype"],
            is_active=raw["is_active"],
        )
    except LedgerError as e:
        raise LedgerError(f"account {raw['number']}: {e}") from None


def parse_entry(raw) -> JournalEntry:
    try:
        return JournalEntry(
            id=raw["id"],
            date=datetime.date.fromisoformat(raw["date"]),
            status=raw["status"],
            memo=raw["memo"],
            lines=tuple(parse_line(raw_line) for raw_line in raw["lines"]),
        )
    except LedgerError as e:
        raise LedgerError(f"{raw['id']}: {e}") from None


def parse_line(raw) -> JournalLine:
    return JournalLine(
        account=raw["account"],
        debit=Decimal(raw["debit"]),
        credit=Decimal(raw["credit"]),
    )


def _require_one_of_literal(field: str, value, literal) -> None:
    """Raise unless value is one of the strings listed in the Literal type."""
    allowed = get_args(literal)
    if value not in allowed:
        raise LedgerError(f"{field} {value!r} must be one of {', '.join(allowed)}")
