# Python lesson — invoices meet Decimal

**Minimum Effort Labs: maximum results, minimum effort.**

The fictional scenario is interdimensional invoices. The practical problem is
ordinary structured-data validation: inspect records, explain anomalies, and leave
the final decision to a human. CSV loading is the supporting step; careful monetary
representation and explicit rules are the new lesson.

## Read records without guessing types

The actual read_csv helper checks required headers and row structure before returning
string-valued records. This excerpt comes directly from the runnable source:

```python
        reader = csv.DictReader(
            stream, strict=True)
```

CSV quoted descriptions may contain commas. Open CSV files with newline='' and
let the CSV library handle quoting. A missing value can become a row-level review
flag; a broken row structure is fatal because we cannot reliably assign columns.

## Construct Decimal from the original text

The parse_amount helper contains the real conversion and explicit error path:

```python
    try:
        amount = Decimal(text)
    except InvalidOperation:
        raise ValueError('Amount is not a decimal number') from None
```

Binary floating point cannot exactly represent every decimal fraction. Decimal
constructed from text preserves that decimal value. Converting a float afterward
would retain the float's approximation. Arithmetic still needs an appropriate
precision context; Decimal is not a guarantee that arbitrary later arithmetic
can never round. The actual validator sets80 digits when summing its bounded input.

## A parsed number is not yet a valid invoice amount

Decimal can represent NaN, infinity and negative numbers. The actual guard is:

```python
    if (
        not amount.is_finite()
        or amount <= 0
    ):
        raise ValueError(
            'Not finite and positive')
```

The function also enforces the README's strict notation and configured number of
fractional digits. It rejects unsupported precision; it does not round away an
error. Explicit0-,2- and 3-place sample policies demonstrate why a universal
two-decimal assumption would be wrong. All these are local Accounting policies,
not claims about every real-world currency or transaction type.

## Currency lookup is configuration, not exchange-rate calculation

load_currencies reads the separate configuration and validates it. audit uppercases
each invoice code and flags values absent from that dictionary. A well-formed
unknown code is still a review question. There is no conversion, rate table or
summed total across currencies. See the actual dictionary lookup in audit.

## Two different duplicate questions

A dictionary groups row indices by invoice ID. After reading all rows, a group
with more than one member flags every member. Another dictionary groups potential
claims by vendor/date/currency/Decimal amount/normalized description. The same ID
with different details and different IDs with matching claims are distinct cases.
Both flags can occur together. Repeated words in a description alone are irrelevant.

The full500 sample independently injects duplicate patterns and checks every report
row. This avoids merely comparing the script to its own classification function.

## Write a useful audit trail

The script retains all input rows/order, original fields and explanations. It writes
to a new file with csv.DictWriter. Safe cell escaping prevents obvious spreadsheet
formula prefixes from being executed if the report is opened in a spreadsheet.
The report is evidence for review, not a database update or payment command.

Run the complete command from README. First use the 30-row sample, compare the
expected report, then generate500 records with seed79009. Count unique flagged
rows separately from per-flag counts. The actual full result is63 flagged records
and 99 flags; never add those categories and call them distinct invoices.

## Beginner exercises

1. Run the sample twice with different output filenames. Compare their bytes.
2. Change one copied invoice to an unknown code; inspect its review explanation.
3. Compare a0-place currency amount of1 with 1.0. Explain the documented policy.
4. Create two invoice IDs with identical claim fields. Explain why both are flagged.
5. Add a test before allowing a new currency or changing the matching rules.

For errors, limits, human review and exact rules, use README. The implementation
does not assess deadlines, verify vendors, reconcile bank payments or find every
possible duplicate. Run all 28 tests before adapting it.

Primary references: [Python Decimal documentation](https://docs.python.org/3/library/decimal.html)
and [Python CSV documentation](https://docs.python.org/3/library/csv.html).
