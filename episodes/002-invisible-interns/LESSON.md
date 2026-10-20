# Episode 002 — The Invisible Interns: full Python lesson

## Learning objectives
Read CSV dictionaries, parse timestamps, group records by ID, use a generator and
inclusive time windows, and interpret discrepancy flags without overclaiming.

## The problem
MEL suspects invisible interns. Real organizations instead need reliable ways to
compare two imperfect logs. This script reports inconsistencies for a person to
review. A missing access event cannot establish absence or misconduct.

## Python concepts
`csv.DictReader` uses the header row as dictionary keys; `newline=""` lets csv
handle line endings correctly. `utf-8-sig` accepts a Windows UTF-8 byte-order mark.
`datetime.fromisoformat` parses ISO dates/times; `timedelta` expresses tolerance.
A dictionary of lists groups successful door entries by employee ID. `any` stops
at the first match; `yield` produces unmatched shifts lazily.

## Code walkthrough
These are actual functions from the distributed program:

```python
def read_rows(path):
    with path.open(
        newline="",
        encoding="utf-8-sig"
    ) as file:
        return list(
            csv.DictReader(file)
        )
```

Headers become keys, so misspelled headers matter. The CLI validates required
headers and rejects duplicates before interpreting the rows.

```python
def unmatched(shifts, doors,
              before, after):
    by_id = {}
    for row in doors:
        by_id.setdefault(
            row["id"], []
        )
        by_id[row["id"]].append(
            row["time"]
        )
    for shift in shifts:
        start = shift["time"]
        entries = by_id.get(
            shift["id"], []
        )
        if not any(
            start-before <= t
            <= start+after
            for t in entries
        ):
            yield shift
```

`setdefault` creates one list per employee. Only successful ENTRY events reach
this function. For each shift, the condition accepts both window endpoints;
the default is 30 minutes early through 10 minutes late. No match yields a shift
to the report. This checks clock-in context, not every minute of attendance.

```python
def write_report(path, rows):
    fields = ["employee_id", "clock_in", "clock_out", "reason", "source_row"]
    with path.open(
        "x", newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=fields
        )
        writer.writeheader()
        writer.writerows(rows)
```

The fixed field list controls report columns. Mode `x` requires a new output
and avoids overwriting existing reports. `source_row` refers to the input CSV
line number, counting the header as line 1.

## How the solution works
Validate paths/headers -> read CSVs -> normalize timestamps -> keep granted ENTRY
events -> validate shifts -> group/match -> combine invalid timecards with missing
matches -> sort by source row -> confirm input hashes -> write new CSV and counts.
Invalid door rows are counted separately; denied entries and exits are not matches.
Timezone-aware timestamps normalize to UTC. Mixing aware and naive styles fails.

## Running the example
Install as documented in README (there are no third-party dependencies), then:

```sh
python reconcile_timecards.py sample/timecards.csv sample/door_access.csv --output discrepancies.csv
python -m unittest discover -s tests -v
```

## Understanding the results
Five checked, three matched, two flagged. DEMO003 has no granted entry in its
window; DEMO004 has an invalid timecard. DEMO001/002 exercise exact tolerance
boundaries; DEMO005 crosses midnight. One invalid door row is reported separately.
Compare every report row with sample/expected_discrepancies.csv. The video uses
500 shifts with different totals; the downloadable algorithm is identical.

## Exercises
1. Change a copied DEMO003 door row to GRANTED. Hint: predict the new matched count.
2. Try `--before-minutes 20`. Hint: the 07:30 boundary no longer matches 08:00.
3. Add an overnight fictional shift. Hint: clock-out needs the next calendar date.

## Limitations
All data is loaded into memory. Matching scans entries for an employee, so very
large logs need indexing. Duplicate entries do not double-count shifts, but one
entry can match multiple nearby shifts; this is not one-to-one allocation.
No holiday schedules, access-system outages, remote-work policy or payroll/legal
judgment is inferred. Naive timestamps assume one consistent local convention;
explicit offsets are preferable near DST. Empty but valid tables are permitted.
Choose new outputs, retain backups and do not use fictional samples as real HR data.

## Further learning
Study CSV schemas, dictionaries, generators, timezone-aware datetimes, boundary
testing and data-quality reports. For scale, explore indexed database joins.


[Back to setup and commands](README.md).
