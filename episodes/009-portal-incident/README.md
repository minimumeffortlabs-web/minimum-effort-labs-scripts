# Episode 009 — The Portal Incident

**Maximum results. Minimum effort.**

A fictional portal has produced a very real administrative problem: invoice CSVs
that Accounting cannot trust. This offline command-line lesson creates an audit
report for human review. It does not pay invoices, identify proven fraud, contact
vendors, query financial services, or invent exchange rates.

## Start here

Use Python 3.10 or newer. The package uses only the standard library and has an
intentionally empty requirements.txt. Tested interpreter details are recorded in
the private production evidence; other platforms are not claimed tested.

From this episode folder in PowerShell:

```powershell
python --version
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python validate_portal_invoices.py sample/invoices.csv --currencies sample/approved_currencies.csv --output audit_report.csv
.venv\Scripts\python -B -m unittest discover -s tests -v
```

On macOS/Linux, use `.venv/bin/python` instead. You can also run the script with
your existing Python interpreter. No GPU, Remotion, voices, GUI, account, package
download or network connection is required by this lesson.

Use a NEW output path every time. The program refuses to overwrite existing files.
The short options `-c` and `-o` mean `--currencies` and `--output`.

## Input contracts

Invoice CSV headers are exactly:

```csv
invoice_id,vendor_id,invoice_date,currency,amount,description
```

All six values are required. Extra named columns are ignored; required headers
must exist and cannot be duplicated. Rows with too many/few columns are fatal
structural errors, rather than silently losing financial data. UTF-8 and UTF-8
with BOM are accepted. CSV quoted commas are supported. Empty input, missing
files and malformed CSV produce an error. A file may contain at most 100000 records.

IDs use 1–40 ASCII letters/digits/dot/underscore/hyphen and start with a letter or
digit. IDs and vendor IDs are case-sensitive after outer whitespace is removed.
Dates must be real calendar dates written YYYY-MM-DD. The validator does not
infer due dates, evaluate payment deadlines, or decide whether an invoice should
be paid. A fictional late-fee story is not an implemented accounting rule.

The separate configuration has these headers:

```csv
currency_code,description,decimal_places
USD,Accounting USD policy,2
JPY,Accounting JPY policy,0
KWD,Accounting KWD policy,3
```

Codes normalize to uppercase and require3–8 ASCII letters. Codes must be unique;
description is required; decimal_places must be an integer 0–6. These are explicit
sample Accounting policies, not an authoritative global currency database.
The supplied file also includes EUR and GBP policies. You may explicitly approve
a fictional code in your own configuration; unknown codes remain review flags.

## Amount policy — no surprise rounding

Amounts are parsed directly from their original text with Decimal, never through
float. Accepted notation is ASCII digits, optionally followed by a decimal point
and one or more digits. Leading zeros and outer whitespace are accepted. Reject
symbols, grouping commas, signs, exponents, underscores, blank values, NaN,
infinities, zero and negative amounts. Limit the stripped amount text to 64 characters.

Fractional digits may not exceed that currency's configured decimal_places.
Trailing zeros count: USD 1.200 is rejected under the sample 2-place policy.
Values are rejected, never silently rounded or converted. Unknown currencies
use a documented6-place fallback solely to check amount syntax/precision; this
does not approve that currency or supply an exchange value.

## Flags and duplicate rules

| Flag | Meaning |
| --- | --- |
| MISSING_REQUIRED_FIELD | One or more of the six required values is blank. |
| INVALID_ID | A nonblank invoice/vendor ID violates the ID format. |
| INVALID_DATE | Missing or invalid strict ISO calendar date. |
| UNKNOWN_CURRENCY | Currency is absent from the supplied configuration. |
| INVALID_AMOUNT | Parsing, finiteness, positivity, notation or precision failed. |
| DUPLICATE_INVOICE_ID | Exact normalized invoice ID repeats. |
| POSSIBLE_DUPLICATE_INVOICE | Vendor/date/currency/numeric amount/description match. |

Every member of a duplicate group is flagged, including the first. A repeated
ID and a possible duplicate claim are separate tests; a record can have both.
Claim matching ignores invoice ID but requires valid vendor/date/currency-code
syntax, a valid amount and a nonempty description. Description comparison uses
Unicode NFKC, case folding and collapsed whitespace. Numeric0.1 and 0.10 match;
different currencies or descriptions do not. Unknown but syntactically valid
currencies can still form comparable claims, without any conversion.

Flags indicate questions for a human, not confirmed duplicate payments or fraud.
This tool does not reconcile payments or contact a bank.

## Report and actual results

Every invoice is reported in original row order with the original six fields
(currency uppercase), validation_status, anomaly_flags and explanation. VALID
means no implemented rule fired, not that a vendor or expense is legitimate.
Multiple flags are separated by semicolons in a fixed order. Spreadsheet formula
prefixes are escaped and control characters flattened in report cells; original
inputs remain untouched. Review raw fields in the original CSV when needed.

The 30-row supplied sample's actual results are in sample/expected_stdout.txt and
sample/expected_audit_report.csv. The 500-row video demonstration is different:

```
Invoices: 500 | Flagged: 63
Valid: 437 | Flags: 99
Missing: 12 | Invalid IDs: 7
Invalid dates: 16
Unknown currencies: 21
Invalid amounts: 25
Duplicate IDs: 8
Possible duplicate claims: 10
Report: audit.csv
```

Counts describe records carrying each flag; a duplicate count is not a count of
pairs. The 63 unique flagged records have99 total flags because some have several.
The full500 report was checked against independent generator labels for every row.
Valid-only totals are available through the Python audit function and were also
independently verified. They are kept separately by currency, exclude every
flagged row (including all duplicate-group members), and use an80-digit Decimal
context sufficient for the documented size limits. No mixed-currency total is made.

Recreate the full fictional run in a NEW directory:

```powershell
python generate_sample_data.py demo --count 500 --seed 79009
python validate_portal_invoices.py demo/invoices.csv -c demo/approved_currencies.csv -o audit.csv
```

The generator is deterministic, including its independent injected flag labels.
It never reads private production data. expected-labels.json is verification truth,
not an input to the validator. The source, seed and actual outputs are included.

## Errors, tests and adapting the lesson

Exit0 means auditing completed, even with review flags. Exit2 means a fatal input,
configuration or output error; stderr explains it. An output I/O failure can leave
a partial NEW report; an existing output is never replaced. If you see a missing
header error, compare exact spellings. If precision fails, check Accounting's
policy before changing it. For large exports, split into bounded files and review
duplicate detection across those file boundaries yourself: this program processes
one file at a time and has no persistent ledger.

The 28 automated tests exercise valid records, Decimal exactness/context, charsets/
CSV structure, malformed/nonfinite/negative/zero amounts, precision policies,
currency rules, real dates, both duplicate checks, overlapping flags, totals,
CSV safety, CLI errors, determinism and input preservation. Separate fatal examples
are under sample/edge-cases; use the normal configuration for missing-headers.csv,
or the normal invoices with invalid-currencies.csv to see exit2.

For real data, first obtain authorization and define the business policies with
Accounting: required identifiers, currency precision, matching scope and output
handling. Work on copies. Add fixtures and tests before changing rules. Do not
interpret a clean report as financial approval. Licensing awaits the owner's choice;
see LICENSING.md. See LESSON.md for the code walkthrough and beginner exercises.
