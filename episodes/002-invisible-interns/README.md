# Episode 002 — The Invisible Interns

Compare timecards with successful door entries and flag records for review. Replaces repetitive record comparison with a reproducible, explicitly limited check.

## Setup and example

Requires Python 3.10 or newer syntax/runtime APIs. Verified on Windows with
CPython 3.10.6; other versions/platforms have not been certified here.
Open a terminal in **this episode directory** (not the repository root).
On Windows, create a lightweight environment and run:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python reconcile_timecards.py sample/timecards.csv sample/door_access.csv --output discrepancies.csv
.venv\Scripts\python -m unittest discover -s tests -v
```

On macOS/Linux use `.venv/bin/python` in place of `.venv\Scripts\python`.
The shorter `python` commands below assume that environment is activated.
Dependencies are pinned to the versions verified for this distribution; no GPU
or animation software is required. Installing packages requires internet access;
the included sample and tests run offline after installation.

## Inputs, output and your own files

Inputs: fictional CSV files `sample/timecards.csv` and `sample/door_access.csv`.
Output: a new `discrepancies.csv`; compare with `sample/expected_discrepancies.csv`.
Sample stdout:

```text
Checked 5 shifts. Matched 3.
Flagged 2 for review -> discrepancies.csv
Invalid rows: 1 timecards, 1 access events.
Missing logs are not proof of absence. Inputs unchanged.
```

Use your own files by replacing both sample paths; keep the headers shown in the
sample. Timecards need employee_id, clock_in, clock_out; access rows need
employee_id, timestamp, event, result. Dates use ISO `YYYY-MM-DDTHH:MM:SS`.
Successful ENTRY events match the same employee from 30 minutes before through
10 minutes after clock-in (inclusive). `--before-minutes` and `--after-minutes`
change those nonnegative tolerances. Both input paths are positional and
`--output` is required. Run `python reconcile_timecards.py --help` for all options.
Troubleshooting: missing/duplicate columns, inconsistent timezone styles or an
existing output cause an error. Use one consistent local time convention or
explicit UTC offsets throughout both files. Review invalid rows before drawing
conclusions. No third-party dependencies are required; requirements.txt is empty.

## Learn more

Read [the full lesson](LESSON.md) and [sample notes](sample/README.md).
The script is byte-identical to its production source; SOURCE.json records its hash.
Episode upload URL has not been verified. Code licensing is pending owner approval;
see [repository licensing](LICENSING.md). No open-source licence is implied.
