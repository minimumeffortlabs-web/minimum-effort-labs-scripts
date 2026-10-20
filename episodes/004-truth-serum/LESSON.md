# Paired before-and-after analysis

## Objectives and fictional problem

Marketing wants a report after its truth-serum experiment. Learn to read two
CSVs, pair the SAME respondents, calculate after-minus-before differences,
average them with statistics.mean and write a readable summary. In real work,
this applies to repeated survey scores, training assessments and product trials.

## CSV handling and validation

csv.DictReader maps named columns to strings. The wrapper validates headers,
integer ratings, unique IDs and file safety before analysis. Missing data stays
missing. IDs with duplicates are excluded entirely. Extra named columns are
ignored. See read_survey in the complete runnable source for those safeguards.

## Actual core code

These exact functions are called by the downloadable CLI. They are excerpts;
the complete file includes imports, validation, report formatting and main().

```python
def paired_changes(before, after):
    pairs = []
    matched = sorted(before.keys() & after.keys())
    for customer in matched:
        old, new = before[customer], after[customer]
        change = new - old
        pairs.append((customer, old, new, change))
    return pairs


def summarize(pairs):
    if not pairs:
        raise ValueError('No valid paired responses; averages are undefined')
    changes = [row[3] for row in pairs]
    mean_change = statistics.mean(changes)
    return {
        'count': len(pairs),
        'before': statistics.mean(old for _, old, _, _ in pairs),
        'after': statistics.mean(new for _, _, new, _ in pairs),
        'change': mean_change,
        'declines': sum(change < 0 for _, _, _, change in pairs),
        'improvements': sum(change > 0 for _, _, _, change in pairs),
        'unchanged': sum(change == 0 for _, _, _, change in pairs),
    }
```

The shared-ID intersection pairs each person with themselves. The important new
operation is `new - old`: negative is a decline, zero unchanged, positive an
improvement. All averages use the same valid paired population. statistics.mean
computes arithmetic means. The mean of paired differences equals mean-after
minus mean-before for this same cohort; averaging different cohorts would answer
a different question. A missing pair cannot be silently assigned zero.

## Execute and interpret

Run the exact README command from the episode folder. The four-pair sample has
means 8.50 and 2.50; each person's change is -6, so the mean paired change is
-6.00 points. These are points on a 1–10 scale, not a claimed percentage or
proof of effectiveness. The report includes every included person's values,
unmatched IDs and validation issues. write_report uses exclusive creation;
existing output files and inputs are protected.

## Limits and exercises

This fictional pre/post comparison observes changes only. Selection effects,
time, question framing and missing participants could affect responses. It does
not independently establish treatment causation; no significance test is added.

1. Change one valid after rating and predict the mean paired difference.
2. Add an unmatched ID and confirm that both cohort means stay unchanged.
3. Add a duplicate ID and inspect which participant is excluded and why.

Further learning: Python's official documentation for csv, statistics.mean,
collections.Counter and pathlib. Run the unittest suite before changing logic.
