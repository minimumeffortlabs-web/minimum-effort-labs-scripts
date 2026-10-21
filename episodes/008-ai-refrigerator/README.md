# Episode 008 — The AI Refrigerator

Turn fictional local email complaints into a structured CSV and category summary.
This is deterministic rule matching, not AI or a personnel-decision system.
All supplied senders and records are synthetic, using reserved example.invalid
addresses. Python 3.10+; standard library only. requirements.txt is empty.

## Setup and small sample

Open a terminal in this episode directory:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python analyze_fridge_complaints.py sample/emails --output complaint_report.csv
.venv\Scripts\python -m unittest discover -s tests -v
```

On macOS/Linux use python3 for venv creation and .venv/bin/python thereafter;
Windows is the tested platform. Installation is offline-capable because no
external packages are required. See the repository setup guide for beginners.

Small sample: 6 parsed, 0 errors, 5 categorized, 1 OTHER, 8 non-OTHER category
matches. Category counts: denied food1, incorrect ratings2, employee data access2,
food disposal2, unexpected behavior1. Compare the CSV with
sample/expected_complaint_report.csv. expected_stdout.txt uses the expected-file
name from its original verification command; your last Report line will use
complaint_report.csv. The CSV bytes are identical regardless of output filename.

## Reproduce the 400-email demonstration

Use NEW paths. These shorter commands assume an activated environment:

```powershell
python generate_sample_data.py emails --count 400 --seed 78008 --manifest expected-labels.json
python analyze_fridge_complaints.py emails --output full_complaint_report.csv
```

Actual verified results: 400/400 parsed, 0 errors, 334 categorized messages,
66 OTHER messages, 455 non-OTHER category matches. Denied food91, incorrect
ratings93, employee data access93, food disposal87, unexpected behavior91.
The full stdout snapshot is sample/full_expected_stdout.txt (its Report line
records the demonstration's original output filename).

The generator uses fixed dates, message IDs, a local random seed and explicit
MIME boundaries, making message bytes reproducible. It creates plain messages,
multipart alternatives, harmless attachments, base64/quoted-printable bodies,
and UTF-8/ISO-8859-1 text. Its optional label manifest is independent fixture
truth, not data read by the analyzer. All 400 classifications were compared
against that manifest, and every input hash remained unchanged.

## How email processing differs from a text-file counter

An .eml file contains headers, a blank separator and message content. MIME can
split content into a body, HTML alternatives and attachments. BytesParser with
policy.default creates EmailMessage objects rather than searching raw encoded
message bytes. From and Subject are decoded header values. get_body selects
an eligible text/plain part; get_content decodes its transfer encoding/charset.
Attachments are not opened, decoded for classification, saved or executed.

Implementation references: [email parser](https://docs.python.org/3/library/email.parser.html)
and [MIME body selection](https://docs.python.org/3/library/email.message.html#email.message.EmailMessage.get_body).

## Input and parsing policy

- Input is a directory of top-level .eml candidates, including .EML, sorted by
  filename. No recursion. Non-message files are ignored. Symlinks and directories
  named .eml become ERROR rows without following/reading them.
- Each message is limited to 2 MiB, including encoded attachments. At least one
  recognizable From/To/Subject/Date header is required; absent From/Subject warn.
- Only the first eligible plain-text body is used. HTML-only/no-body messages
  receive a warning and can still be categorized from their subject. Additional
  bodies, forwarded attached messages and attachments are not concatenated.
- Declared charset decoding is strict. Unknown charsets or invalid encoded text
  produce ERROR rows. Recoverable parser/header/MIME defects are reported as
  warning names; they do not necessarily make the entire message unprocessable.
- Subject plus selected body are normalized with Unicode NFKC, lowercasing,
  straight apostrophes and collapsed whitespace. Headers other than Subject do
  not drive classification.

## Categories and counts

Rules are readable regexes in RULES; edit them and rerun tests for a new domain.

| Category | Examples of matching context |
| --- | --- |
| FOOD_ACCESS_DENIED | Denied/refused food or lunch; a locked fridge; cannot open the refrigerator |
| INCORRECT_PERFORMANCE_RATING | Outdated/incorrect/wrong rating or score, including inverse word order |
| UNAUTHORIZED_EMPLOYEE_DATA_ACCESS | Appliance/fridge knows, obtained or accessed records, notes or data |
| FOOD_DISPOSAL | Threw out, discarded or disposed of food/lunch/sandwich/yogurt |
| UNEXPECTED_FRIDGE_BEHAVIOR | Fridge or lunch linked to disciplinary warnings, performance meetings or training |
| OTHER | A successfully parsed message matching none of the five rules |

Every matching rule contributes ONCE per email, even if its phrase repeats.
Several different categories may match one message. Categorized is a UNIQUE
message count; category_matches sums the five named categories and excludes OTHER.
Categorized + OTHER = parsed; parsed + errors = discovered candidates. Error rows
have no category and are not counted as OTHER. Thus 455 matches does not mean
455 emails. Body words are not the units being counted.

Rules catch documented wording variations, not meaning, intent, truth or every
paraphrase. There is limited handling of 'not denied/refused/blocked', not general
negation or sarcasm understanding. Longer phrasing and other languages may be
missed; coincidental phrases can be false positives. Human review is needed for
real decisions. The absurd appliance scenario is not an acceptable HR policy.

## Report and exit codes

CSV fields: source_file, sender, subject, categories (semicolon separated), status,
notes. Status is PARSED, PARSED_WARNINGS or ERROR. Notes contain diagnostic names,
not raw bodies or exception paths. The report excludes message bodies; sender,
subject and filenames can still identify people, so this is NOT anonymization.
Control characters are flattened in CSV cells. Cells beginning with =,+,-,@
(after whitespace) receive a leading apostrophe for spreadsheet protection.

Output must be a NEW file outside the input directory, with an existing parent.
Existing outputs are never overwritten. No replies, links, attachment downloads,
mail-server connections or account credentials are involved.

- Exit0: report written; every message processed (warnings may remain).
- Exit1: report written with one or more ERROR rows; inspect those rows.
- Exit2: fatal input/output/argument error. An output I/O failure may leave an
  incomplete new report; inspect it and choose a fresh path when retrying.

Empty/missing input directories are fatal. Use --help for arguments. Keep source
emails read only; test with fictional or otherwise authorized local data.

## Edge cases and troubleshooting

```powershell
python analyze_fridge_complaints.py sample/edge-cases --output edge_report.csv
```

Expected exit1: malformed and unknown-charset messages generate errors; an
empty-body message generates a warning. Compare sample/expected_edge_report.csv
and expected_edge_stdout.txt. Do not mix this deliberate error fixture into the
main 400-message demo. Missing categories? Inspect subject/plain-body wording and
RULES. HTML-only emails intentionally do not get an HTML-to-text fallback.
Existing output? Choose a new file. Unknown charset? Inspect a copy of that
message manually rather than silently replacing bytes in the original.

See LESSON.md for source excerpts and exercises. LICENSING.md records the pending
code-redistribution licence decision. No public episode URL is assumed.
