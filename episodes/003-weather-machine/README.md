# Episode 003 — The Weather Machine

Compare completed daily weather highs and write a plain-text report. Turns recorded API arrays into a readable report while keeping provenance and uncertainty.

## Setup and example

Requires Python 3.10 or newer syntax/runtime APIs. Verified on Windows with
CPython 3.10.6; other versions/platforms have not been certified here.
Open a terminal in **this episode directory** (not the repository root).
On Windows, create a lightweight environment and run:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python weather_change_report.py --replay sample/recorded_weather_capture.json --output weather_report.txt
.venv\Scripts\python -m unittest discover -s tests -v
```

On macOS/Linux use `.venv/bin/python` in place of `.venv\Scripts\python`.
The shorter `python` commands below assume that environment is activated.
Dependencies are pinned to the versions verified for this distribution; no GPU
or animation software is required. Installing packages requires internet access;
the included sample and tests run offline after installation.

## Inputs, output and your own files

Input: `sample/recorded_weather_capture.json`, recorded live API data for
October 15–19, 2026 (not current weather). Output: a new UTF-8 `weather_report.txt`,
matching `sample/expected_report.txt`. The CLI explicitly prints replay mode,
the retrieval timestamp, period, five analyzed days and saved filename.
See [sample provenance](sample/README.md) for attribution and interpretation.

Live usage, after reviewing provider eligibility/usage terms:

```sh
python weather_change_report.py --latitude 39.10 --longitude -94.58 --timezone America/Chicago --days 5 --output live_report.txt --record-json live_capture.json
```

Replace the example coordinates/timezone with your chosen location. Coordinates
must be finite and within geographic bounds; `--days` is 1–31. `--end-date`
selects an earlier completed date within the recent 92-day request window.
`--record-json` optionally saves a new capture. `--replay` reads a saved capture
offline; location/dates cannot contradict it. `--output` defaults to weather_report.txt.
Run `python weather_change_report.py --help` for all arguments.
Troubleshooting: use a new output filename, install requests and Windows tzdata,
check the IANA timezone spelling, or use the recorded replay when offline.
Live requests time out after 15 seconds; HTTP/JSON/schema errors fail explicitly.
DST/offset-changing date ranges are rejected. Reports use model-derived daily
aggregates, not station measurements; changes cannot prove machine effectiveness.
Requests is needed even in replay mode because it is imported by the program.

## Learn more

Read [the full lesson](LESSON.md) and [sample notes](sample/README.md).
The script is byte-identical to its production source; SOURCE.json records its hash.
Episode upload URL has not been verified. Code licensing is pending owner approval;
see [repository licensing](LICENSING.md). No open-source licence is implied.
