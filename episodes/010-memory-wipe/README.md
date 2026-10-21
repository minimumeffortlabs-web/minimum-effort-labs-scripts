# Episode 010 — The Memory Wipe

**Maximum results. Minimum effort.** Management forgot two days. The logs did not.
This independent Python lesson combines fictional JSON events into a UTC timeline.
It reads local files only: no account, GPU, voice engine, network or GUI required.

## Set up and run

Use Python 3.10 or newer. Runtime dependencies are standard-library only;
requirements.txt is intentionally empty. From this episode folder:

```powershell
python --version
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python reconstruct_event_timeline.py sample/logs --output timeline.txt
.venv\Scripts\python -B -m unittest discover -s tests -v
```

On macOS/Linux use `.venv/bin/python`. Windows execution is tested; other platforms
are not claimed tested. Use a NEW output path each time; existing files are preserved.
Compare timeline.txt to sample/expected_timeline.txt (35 events). Expected sample
stdout is sample/expected_stdout.txt. The video has a separate1000-event fixture.

## JSON input schema

Input is an existing directory of immediate .json files (extension case-insensitive).
No recursion or symlink files. Files are read in deterministic, case-sensitive
filename order. Each UTF-8/BOM JSON file must be an array of event dictionaries:

```json
[
  {
    "event_id": "EVT001",
    "timestamp": "2026-10-19T02:47:00Z",
    "source": "IT_OPERATIONS",
    "event_type": "BACKUP_RESTORED",
    "description": "Fictional backup restored."
  }
]
```

These five fields must be nonempty strings. Unknown keys are ignored. IDs are
case-sensitive ASCII letters/digits/dot/underscore/hyphen,1–80 characters, starting
with a letter/digit. Other fields may contain Unicode; maximum 2000 characters
per required field. File limit 10MiB, combined array-entry limit 100000. Duplicate
JSON property names and nonstandard NaN/Infinity values reject that whole file.
An unreadable/malformed file is reported; its unknowable event count is not guessed.

## Timestamp policy

Use YYYY-MM-DDTHH:MM:SS followed by Z or an explicit ±HH:MM offset. Optional 1–6
fractional-second digits are accepted. The T is required. Impossible dates,
naive times, unknown offset -00:00, leap seconds and malformed offsets are rejected.
Offset hours 0–23 and minutes 0–59 are supported. Date conversion overflow is rejected.
Do not assume a missing timezone is your computer's timezone.

The script parses actual datetime objects and normalizes them to UTC. A local
06:00 at -07:00 is13:00UTC, later than12:30Z despite how the strings sort.
Never sort differently offset timestamp strings as if they were UTC dates.
Equal instants tie by original filename then 1-based array position. Timestamp
precision is retained up to microseconds. The machine clock is never substituted.

## Duplicates and errors

All otherwise-valid occurrences of a repeated event ID are excluded from the
timeline, even if the ID also appears in a malformed record. That malformed record
keeps its original validation error. Duplicate IDs in the summary count otherwise-
valid records excluded by this duplicate check, not duplicate groups/pairs. The
rejected count includes all rejected array records. Invalid IDs do not become
valid duplicates. Identical descriptions with unique IDs remain distinct events.
No missing record, timestamp or historical explanation is invented.

Malformed JSON, bad encoding, wrong top-level schema and unreadable files are
file errors. Missing fields, bad types/IDs/timestamps are record errors. The report
retains filename,row,event ID where available and reason. A global input-limit
failure is fatal and creates no report. Empty arrays are valid; a directory with
no JSON files is a fatal error. Not having events is not proof nothing occurred.

## Output and exit codes

The NEW text report must be outside the input directory (resolved paths checked).
Its primary section lists UTC timestamp,source,type,description,file:row,event ID.
It is followed by rejection/file-error details. Control characters, backslashes,
non-ASCII text and pipe separators are escaped for an unambiguous plain-text audit
trail. Original JSON is never changed. Filenames are included for traceability.

- Exit 0: completed without rejection, including a valid empty array.
- Exit 1: report created with rejected records or file errors; review that report.
- Exit 2: fatal directory, limit or output failure; stderr gives the reason.

An output I/O failure may leave a partial NEW file; the script never overwrites
existing output. Use copies and user-authorized data when adapting this lesson.

## Reproduce the full video example

```powershell
python generate_sample_data.py demo/logs --count 1000 --seed 80010
python reconstruct_event_timeline.py demo/logs --output timeline-full.txt
```

Use a new generator directory. It writes seven fictional system logs plus an
independent UTC truth manifest adjacent to the logs directory (never inside it).
Out-of-order entries use several offsets. The 1000-event video run used the shorter
input-directory name logs and produced this exact captured output:

```
JSON files: 7 | Events: 1000
Timeline: 1000 | Rejected: 0
File errors: 0 | Duplicate IDs: 0
First: 2026-10-18T00:00:00Z
Last: 2026-10-19T23:59:59Z
Report: timeline.txt
```

Its earliest/latest events span47h59m59s. The generated data includes the
second-wipe authorization at 2026-10-19T02:47:00Z; it is a fictional sample record,
not a finding about an actual company. Independent original UTC timestamps verify
every parsed value and final order. Inputs stay byte-identical and fresh reports
are deterministic. A 30-second character estimate is not a runtime guarantee.

## Troubleshooting and adapting

For “No JSON log files”, select the folder containing the files, not its parent.
For missing timezone, correct it from a known authoritative source; never guess.
For existing output, choose another filename. For exit1, read the rejection section
before trusting the timeline. To see deliberate failures:

```powershell
python reconstruct_event_timeline.py sample/edge-cases --output rejected-demo.txt
```

This example intentionally returns 1. Do not load edge fixtures with the clean sample.
To adapt real logs, obtain permission, map their schema into these five fields,
document timezone provenance, add tests, and work on copies. Review duplicate policy
with the data owner. This bounded, in-memory lesson does not correlate identities,
authenticate records, handle every vendor schema or recover deleted/unlogged events.
A reconstructed timeline reflects available logs, not a complete or proven history.
For licensing see LICENSING.md; owner selection remains pending.
