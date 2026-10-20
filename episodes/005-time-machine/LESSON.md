# Dates, duplicate claims and a very awkward timeline

The fictional lab has a time machine; Accounting has future expense claims.
The same checks help real CSV quality reviews, without deciding whether a claim
is fraudulent. An anomaly is a request for human review.

csv.DictReader maps named columns to strings. datetime.date.fromisoformat turns
validated YYYY-MM-DD text into comparable calendar objects; a regex first
rejects compact/week-date forms. Invalid calendar dates raise ValueError and
receive INVALID_DATE. The CLI audit date is explicit, never today's clock.
The strict comparison flags future dates while allowing the cutoff itself.

Counter dictionaries count every nonblank ID and valid claim key before
classifying rows. This flags every group member, not just later duplicates.
Repeated ID and matching employee/date/merchant/amount are separate tests.
Decimal preserves exact monetary values such as 0.10; binary floats do not.
Missing, nonpositive or malformed money is flagged and excluded from claim keys.

These excerpts come verbatim from the runnable file; use the complete script,
which also includes input validation, exception handling and safe output creation.

```python
from datetime import date
```

```python
        expense_date = parse_date(date_text)
```

```python
        elif expense_date > audit_date:
            flags.append('FUTURE_DATE')
```

```python
    claims = Counter(key for _, _, key in prepared if key is not None)
```

```python
        writer = csv.DictWriter(handle, fieldnames=REPORT_FIELDS)
        writer.writeheader()
        writer.writerows(flagged)
```

The report writer emits the original fields, source record ordinal and all
flags. It uses exclusive creation, preserving existing output. Flags overlap:
73 rows in the sample carry 93 flags, not 93 distinct suspicious expenses.
Run the exact README command, then inspect both the CSV and terminal summary.

Exercises: move a date onto the cutoff; change an amount from 10.20 to 10.2;
compare identical IDs with different employees; add a blank date; verify the
original remains byte-identical. Future extensions need explicit policies for
currencies and fuzzy matching; neither is inferred here.
