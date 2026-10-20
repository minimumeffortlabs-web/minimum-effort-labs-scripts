# Episode 007 — The Robot Performance Reviews

Create personalized Word reviews from CSV records, without opening Word. Python
3.10+ and python-docx 1.2.0 (the installed version tested here) are required.
All sample employees and comments are fictional. No TTS or GPU required.

## Install and run

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python generate_robot_reviews.py sample/robots.csv --output reviews
.venv\Scripts\python -m unittest discover -s tests -v
```

Run from this episode folder. macOS/Linux use .venv/bin/python; Windows was tested.
The small sample produces 3 reviews. Open the DOCX files with a compatible reader.
To reproduce the 800-record video demonstration, choose NEW output paths:

```powershell
python generate_sample_data.py robots.csv --count 800 --seed 77007
python generate_robot_reviews.py robots.csv --output all-reviews
```

## CSV format

Required columns, exactly once: robot_id, robot_name, department, efficiency_rating,
accuracy_rating, teamwork_rating, manager_comments. Use UTF-8 (optional BOM).
csv.DictReader handles quoted commas. IDs must be R plus 3–6 digits, unique and
case sensitive. Filenames use validated IDs only, never names or comments.
Ratings are integer strings 1–5. Required text is stripped, printable, at most
240 characters. Missing/extra columns or cells, duplicates and invalid rows abort
the entire run before any output is created. Empty input is an error.

Each document contains the robot's name/ID/department, summary, rating table,
individual manager comments and a recommendation. The Decimal arithmetic mean
rounds half-up to two decimals. Recommendations use the displayed rounded score:
at least 4 recognize performance, at least 3 support development, otherwise plan
improvement. These are educational example rules, not employment guidance.

## Safe output and troubleshooting

The output directory must NOT exist, even if empty. Choose a new directory per
run; do not delete unrelated files to retry. No existing files are replaced.
The entire CSV is validated first. If document generation fails, only the newly
created run directory is removed. Parent directories may remain. Inputs are read
only. Exit 0 means success; exit 2 reports invalid input or ordinary I/O failure
on stderr. --help explains the CLI. Install requirements if docx cannot be imported.
No filesystem path is taken from CSV names; strict IDs prevent path traversal
and case-fold collisions on Windows. Layout is deterministic, but DOCX ZIP
timestamps/metadata mean independent runs need not be byte-identical.

800 generated documents were reopened and checked against the 800-record CSV in
production. Tests repeat that content/count/input-preservation verification.
Only one small verified sample DOCX is included, rather than 800 binary files.
See LESSON.md for source explanations and LICENSING.md for the pending licence.
Adapt create_review() for letters/certificates; retain input and output safeguards.
