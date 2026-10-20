# Episode 005 — The Time Machine

Find future-dated expenses, invalid dates/amounts, repeated expense IDs and
suspected matching claims. Python 3.10+; standard library only. requirements.txt
is intentionally empty. No GPU, voice engine, GUI or network is needed.

## Setup and run

Open a terminal in this folder. On Windows:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python expense_anomaly_detector.py sample/expenses.csv --as-of 2026-10-20 --output audit_report.csv
.venv\Scripts\python -m unittest discover -s tests -v
```

On macOS/Linux use `.venv/bin/python`. Tests were run on Windows; other
platforms are not claimed verified. Compare audit_report.csv with
sample/expected_audit_report.csv. To regenerate inputs, run
`python generate_expenses.py new_expenses.csv` (fixed seed 75005).

## CSV rules and safeguards

Required unique headers: expense_id, employee_id, expense_date, merchant,
amount, description. Extra named columns are ignored. UTF-8/BOM supported.
Dates must be calendar-valid YYYY-MM-DD; surrounding field whitespace is trimmed
for validation. --as-of is required, making the audit deterministic.
Amounts use Decimal, must be finite and greater than zero, with at most two
decimal places. Plain decimal only: no currency symbols, exponent, separators
or sign. Integer amounts are accepted. No currency conversion is attempted.

IDs are trimmed and case-sensitive. A potential claim match uses employee ID,
valid date, trimmed casefolded merchant and exact Decimal amount. Description
and expense ID are excluded from that key. Invalid or incomplete keys are never
grouped. ALL rows in a repeated group are flagged, including the first.

## Flags

- FUTURE_DATE: valid date later than --as-of (equal date is allowed).
- INVALID_DATE: missing, non-ISO or invalid calendar date.
- DUPLICATE_EXPENSE_ID: nonblank ID occurs more than once.
- POSSIBLE_DUPLICATE_CLAIM: matching valid claim key; suspected, never proof of fraud.
- INVALID_AMOUNT: missing or violates the positive plain-decimal rules above.
- MISSING_EXPENSE_ID, MISSING_EMPLOYEE_ID, MISSING_MERCHANT: blank required identity fields.

The CSV report contains flagged rows only, preserving original field values,
plus source_row (CSV data-record ordinal, starting at 2), pipe-separated
anomaly_flags and human-readable explanation. A row can have several flags.
No source file or claim is modified, deleted, rejected or automatically accused.
If nothing is flagged, output still contains headers.

## Verified sample

500 records; 46 future dates; 13 invalid dates; 13 repeated-ID rows;
12 suspected matching-claim rows; 9 invalid amounts; zero missing-identity flags.
73 unique rows carry 93 flags. Group-member row counts are not excess-only
duplicate counts. The report was independently checked against source records.

## Troubleshooting

Exit 0 means a report was written (flags do not cause failure). Exit 2 means
fatal input/CLI/output error: missing files, empty data, duplicate/missing headers,
malformed CSV field counts/quoting, bad --as-of or existing output. Choose a NEW
output filename; input collisions are rejected and existing reports preserved.
Check the error on stderr. Fix records in a separate copy only after human review.

Read LESSON.md for the tutorial and LICENSING.md for the pending license decision.
No live episode/download URL is assumed.
