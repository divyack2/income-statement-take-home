# Notes

**Q1 2026 net income (2026-01-01 to 2026-03-31): −44,480.14**, shown in the app as ($44,480.14).

## Decisions
- **Sign (+/-):** each line is `debit − credit`, negated for `revenue`-type accounts, so revenue and expenses both show positive. Contra-revenue (4900) and credits to an expense (the JE-020 vendor refund) come out negative with no special cases.
- **Sections by subtype, never by type.** Interest Income (7000) is type `revenue` but subtype `other_income`, so it goes in Other income. The type only decides the sign (+/-) of the amount change.
- **Only `posted` entries count**; drafts and voids are excluded. Both date bounds are inclusive.
- **Entries are reported as recorded:** JE-007's three months of rent all land on Jan 1, JE-004's billing to Deferred Revenue is not revenue, and JE-008 on inactive account 6300 is included (`is_active` only blocks new postings, not historical postings).
- **Validate early.** The ledger JSON is treated as untrusted input (for the most part). It is parsed and validated once at startup into frozen, typed dataclasses, so the accounting code assumes valid data and has no defensive checks. Startup fails loudly on an unbalanced entry, an unknown account, a line with both or neither of debit and credit, more than 2 decimal places, or an unknown status, subtype, or type/subtype pairing.
- **Money stays exact.** Amounts are `Decimal`, built from strings. The API method `/income-statement` response type is a dataclass `IncomeStatement`. FastAPI serializes it through Pydantic because the route declares its return type, so Decimal goes over the wire as a string. The frontend only formats amounts (with `Intl.NumberFormat`'s accounting style, passed the string) and never does arithmetic on them.
- **Zero activity:** accounts with no posted activity in the range are left off. All four sections of the statement always appear with a 0.00 total when empty. An account whose activity nets to exactly 0.00 is still shown, since it did have activity.
- **`start > end` returns 422,** the same status FastAPI uses for a missing or invalid date.

## Assumptions
- ledger.json has the shape described in SPEC.md: every field is present with the right JSON type, amounts are decimal strings (not JSON numbers, which would arrive as floats), and dates are `YYYY-MM-DD`. Validation covers the accounting rules, not the raw format.
- Journal entry ids and account numbers are unique. Neither is checked: a repeated entry would be counted twice, and a repeated account number would silently replace the earlier account.
- All amounts are in whole cents (checked at load). Sums of Decimals keep exactly 2 places, so no rounding is done anywhere, and a `-0.00` can't arise.

## How I checked the numbers
- Calculated Q1 by hand from the ledger. The golden test's expected values (every line, section total, and subtotal) come from that hand calculation, never from the code's output. I also had Claude parse through the ledger on its own and calculate the income statement values to cross-check with my own calculations.
- Each data edge case has its own test on a tiny hand-built ledger: drafts and voids, both date edges, contra-revenue, the vendor refund, deferred revenue, the inactive account, and interest income in Other income.
- Mutation checks: I broke the code on purpose (exclusive date bounds, drafts let in, sign flipped by subtype, sections grouped by type) and confirmed tests fail each time.
- Cross-check: −41,280.14 would mean both the draft (JE-019) and the void (JE-009) leaked in.

## AI
**Where it helped:** scaffolding, test ledgers, and checking things empirically rather than from memory (that FastAPI sends Decimal as a string inside a dataclass only when the route declares its return type; that `Intl.NumberFormat` formats a numeric string exactly, etc).

**Where it got things wrong, or I pushed back:**
- **Over-engineered section mapping.** It went from a tuple table to a `SectionDefinition` dataclass with frozensets. I reduced it to one flat subtype → section map.
- **Convoluted grouping of accounts into sections.** It tried a pre-filled dict, then filtering once per section, then a `defaultdict`. I asked for a single pass through all the accounts that groups the accounts into their respective sections as it goes.
- **Unneeded rounding.** It added a `_money` helper to quantize and fix `-0.00`. Every amount is already in cents, so I removed the rounding, then the `-0.00` guard, which the data can't reach in its current state (this could be a later addition).
- **Refetch on every date change.** It used a `useEffect` that refetched whenever a date changed, with a flag to ignore stale responses. I replaced it with a form and a submit button, which needs neither and is cleaner from a  UX perspective.
- **Hand-rolled formatting.** It wrote a regex for thousands separators and parentheses, plus a custom date formatter and spacer rows for layout. I switched to the built-in accounting format, plain `YYYY-MM-DD` dates, and simple padding.
- **Deprecated API.** It typed the submit handler with React's `FormEvent`, which is deprecated; I caught it and we switched to `SubmitEvent`.
- **Too many tests.** It wrote 32, many overlapping. I audited each one and cut to 19 that each catch a distinct mistake.
- **Naming.** I pushed for clearer function + dataclass names throughout (e.g. at first it had both `Section` and `Sections`, so I renamed `Section` to `StatementSection`).

## Next steps
- Validate the JSON shape and formats with clear error messages, instead of a plain `KeyError` or `ValueError`.
- Frontend tests, and account numbers sorted numerically if the chart ever has mixed-length numbers.
- More detailed handling + validation of the input ledger data (i.e. validating that the decimal format and datetime formats can be correctly parsed, enforce unique account IDs and journal entry IDs, etc).
- Clean up the UI to be mobile-friendly/responsive.
