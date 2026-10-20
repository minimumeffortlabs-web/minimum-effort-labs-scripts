# Episode 006 — The Dream Recorder

Count recurring words and adjacent two-word phrases in text transcripts. This is
observable text analysis, NOT dream interpretation or an emotion/diagnostic model.
Useful for feedback exploration and simple log/topic counts. All samples are fiction.
Python 3.10+; standard library only. requirements.txt is intentionally empty.

## Setup and small example

Open a terminal in this folder. On Windows:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python dream_transcript_analyzer.py sample/transcripts --output dream_report.txt --top 10
.venv\Scripts\python -m unittest discover -s tests -v
```

On macOS/Linux use `.venv/bin/python`; only Windows was tested here. Output must
be NEW and outside the input directory. Compare it with sample/expected_report.txt.
The small sample has 3 files, 45 extracted words and 32 non-stop words. Top words:
expense 6, reports 5. Top phrases: expense reports 5, missing receipts 2.

## Reproduce the complete video fixture

```powershell
python generate_sample_data.py video_transcripts --seed 76006 --count 300
python dream_transcript_analyzer.py video_transcripts --output video_report.txt --top 10
```

Use a new directory: generator refuses an existing one. These 300 varied fictional
transcripts contain 13,286 extracted and 8,967 analyzed words. expense and reports
each occur 745 times. expense reports is the top phrase with 745 occurrences;
missing receipts follows with 192. Compare video_report.txt with
sample/full_expected_report.txt. Real execution and independent ranking checks
produced these numbers. Hundreds of repetitive text files are not needed in Git.

## Your own input and exact rules

Replace the positional path with your own directory. Only top-level regular
.txt files are used, including .TXT, sorted by filename. No recursion. Symlink
transcripts are rejected. Files must be UTF-8 (optional BOM). A named read/decode
error aborts; it is never silently replaced or omitted. Empty directories fail
with exit 2. Empty/tokenless files count as valid readable files with zero words.
All-empty or all-stop-word collections still produce an explicit empty ranking.

The regex [a-z]+ runs after .lower(): English ASCII letters only. Digits,
underscores and punctuation delimit tokens. Apostrophes split contractions;
common fragments are in the small built-in STOP_WORDS set. Accented/non-Latin
language analysis is outside this beginner example. See the complete set in source.

Word counts omit stop words. Phrases are adjacent pairs in each original token
stream, THEN pairs containing either stop word are excluded. Thus 'expense and
the report' never creates 'expense report'. Punctuation is ignored, so pairs may
span a sentence boundary in ONE file. Phrases never cross files. There is no
stemming: report and reports are distinct. Ties are alphabetical, not arbitrary.

--top must be a positive integer and limits both report rankings. CLI prints up
to two entries in each ranking, while the file contains up to --top. Counts are
occurrences; one file can contribute many. Total extracted words precede stop-word
filtering; analyzed words follow it. The plain-text report includes file/empty
counts, both word totals, rankings and limitations. Identical bytes/settings give
identical output. Source transcripts are read only.

## Errors and troubleshooting

Exit 0: report written. Exit 2: invalid path, unreadable/invalid UTF-8 input,
missing .txt files, invalid --top, output inside the input directory, existing
output or other fatal I/O error. Read stderr; choose a new output file. The
output is outside inputs so later runs cannot analyze an earlier report as data.
Use --help for all options. Empty requirements means pip has nothing to install.

See LESSON.md for code explanations, exercises and limitations; LICENSING.md
records the pending owner license choice. No public Episode006 URL is assumed.
