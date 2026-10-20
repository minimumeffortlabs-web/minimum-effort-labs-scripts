# Episode 001 — The Sentient Toaster

Merge PDFs in filename order into a single verified document. Combines a folder of evidence into one file without overwriting originals.

## Setup and example

Requires Python 3.10 or newer syntax/runtime APIs. Verified on Windows with
CPython 3.10.6; other versions/platforms have not been certified here.
Open a terminal in **this episode directory** (not the repository root).
On Windows, create a lightweight environment and run:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python merge_pdfs.py sample/input merged.pdf --report merge_report.json
.venv\Scripts\python -m unittest discover -s tests -v
```

On macOS/Linux use `.venv/bin/python` in place of `.venv\Scripts\python`.
The shorter `python` commands below assume that environment is activated.
Dependencies are pinned to the versions verified for this distribution; no GPU
or animation software is required. Installing packages requires internet access;
the included sample and tests run offline after installation.

## Inputs, output and your own files

Inputs: three valid one-page fictional PDFs in `sample/input/`. `sample/expected.json`
lists their filename order. Output: new `merged.pdf` (three pages) and optional
`merge_report.json` (counts, input hashes and output hash). Sample stdout:

```text
Merged 3 PDFs into merged.pdf
Verified 3 pages. Original files unchanged.
```

For your own files: `python merge_pdfs.py my_pdfs combined.pdf --report combined.json`.
Use lowercase `.pdf` filenames, prefix numbers with zeros, and choose new outputs
outside the input directory. `folder` and `output` are positional arguments;
`--report` is optional. Run `python merge_pdfs.py --help` for usage.
Troubleshooting: install pypdf in the same interpreter; check the input directory,
file case, readable PDFs and write permissions. Empty, encrypted or malformed
PDFs are rejected by the CLI. Choose a new filename on repeat runs.

## Learn more

Read [the full lesson](LESSON.md) and [sample notes](sample/README.md).
The script is byte-identical to its production source; SOURCE.json records its hash.
Episode upload URL has not been verified. Code licensing is pending owner approval;
see [repository licensing](LICENSING.md). No open-source licence is implied.
