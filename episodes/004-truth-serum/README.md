# Episode 004 — The Truth Serum

Compare before/after satisfaction surveys by customer ID. Calculate paired
individual changes, means, decline/improvement counts and a plain-text report.
Python 3.10+; Windows verification uses CPython 3.10.6. Standard library only.

## Setup and sample

Open a terminal in this episode folder. On Windows:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python compare_survey_results.py sample/before.csv sample/after.csv --output report.txt
.venv\Scripts\python -m unittest discover -s tests -v
```

On macOS/Linux use `.venv/bin/python`. requirements.txt is intentionally empty.
The sample prints four valid pairs, means 8.50 and 2.50, mean change -6.00 points,
and four declines. Compare report.txt with sample/expected_report.txt.

## Your own data and safeguards

Replace the two input paths. CSVs need unique `customer_id` and
`satisfaction_rating` headers. Ratings are integers 1–10. Extra named columns are
allowed and ignored. Blank IDs, malformed fields, missing/noninteger/out-of-range
ratings are reported and excluded. Every occurrence of a duplicate ID in either
survey is excluded; no first/last-row guess. Before-only/after-only IDs appear
in the report. Both means and mean difference use the SAME valid paired cohort.
Unmatched or invalid rows are never zero. No valid pairs, empty input, malformed
headers, unreadable files or an existing output cause a helpful error and exit 2.
Success exits 0. Choose a new output path for every run; originals are unchanged.
UTF-8/UTF-8 BOM input is supported. IDs are trimmed, case-sensitive strings.

## Reproduce the larger fictional fixture

```powershell
python generate_fictional_surveys.py fictional --seed 74004
python compare_survey_results.py fictional/before.csv fictional/after.csv --output large_report.txt
```

250 invented IDs include unmatched, invalid, duplicate, improved and unchanged
responses. The fixed seed makes the input reproducible. This is a programming
demonstration, not evidence that a treatment causes changes. No significance or
causal claim is made. Terminal/report values come from actual execution.

Read [LESSON.md](LESSON.md), [sample notes](sample/README.md), and
[licensing status](LICENSING.md). No verified download/video URL is assumed.
