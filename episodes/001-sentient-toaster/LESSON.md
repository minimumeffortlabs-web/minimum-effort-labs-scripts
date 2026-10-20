# Episode 001 — The Sentient Toaster: full Python lesson

## Learning objectives
Use pathlib to select files, understand deterministic sorting, assemble documents
with pypdf, and distinguish a teaching function from a guarded command-line wrapper.

## The problem
MEL's sentient toaster has acquired a paperwork habit. In ordinary work, separate
PDFs often need one ordered bundle. A repeatable merge is less error-prone than
manually opening every file. This download uses three fictional pages; the episode
demonstration processes 400 using this exact same source.

## Python concepts
`Path` represents filesystem paths. `glob("*.pdf")` selects matching direct children;
it is not recursive. `sorted` orders names, not dates or human numeric values:
`02.pdf` sorts before `10.pdf`, whereas `10.pdf` sorts before `2.pdf`.
`PdfWriter` comes from pypdf, an external dependency. A `with` context closes it.
`append` adds each input's pages, `write` serializes the result, and `len` returns
the number of documents (which need not equal the number of pages).

## Code walkthrough
The complete teaching function below is copied directly from the runnable source:

```python
def merge_pdfs(folder, output):
    files = sorted(
        Path(folder).glob("*.pdf")
    )
    with PdfWriter() as writer:
        for pdf in files:
            writer.append(pdf)
        writer.write(output)
    return len(files)
```

1. Select lowercase-extension PDFs, then freeze their sorted order in a list.
2. Open a writer and append each document, preserving its internal page order.
3. Write the bundle and return the input-document count.
4. `main()` adds argparse, checks for empty/encrypted/corrupt inputs and rejects
   existing destinations. It hashes each input, writes to a temporary file,
   verifies page counts/readability, then creates the final file exclusively.
5. A JSON report is optional. Errors print `ERROR:` and return status 2.

## How the solution works
Arguments become Paths -> validate/read/hash PDFs -> call `merge_pdfs` on a
temporary destination -> reread and verify -> copy to a newly created output ->
optionally write report -> print verified counts. Use the CLI for safety; directly
calling the small teaching function bypasses its wrapper's safeguards.

## Running the example
Follow README setup, then run from this directory:

```sh
python merge_pdfs.py sample/input merged.pdf --report merge_report.json
python -m unittest discover -s tests -v
```

## Understanding the results
Expect `Merged 3 PDFs into merged.pdf` and `Verified 3 pages. Original files unchanged.`
Compare report `processed` filenames with sample/expected.json. Each supplied PDF
has one page, so the two counts happen to match. Tests reopen the output, compare
page text/order and hash the original files. The PDF byte hash can vary with metadata;
semantic page/order validation is the meaningful comparison.

## Exercises
1. Add a fourth PDF in a copy of the sample. Hint: use a zero-padded filename and
   predict both counts before running with a new output name.
2. Print the selected filenames before merging. Hint: iterate over `files` without
   changing their order. Keep this experiment separate from the featured source.
3. Try `2.pdf` and `10.pdf`. Hint: compare alphabetical order with numeric order.

## Limitations
Direct children only; lowercase `.pdf` selection; no password handling, OCR,
redaction or content sanitization. Preserve backups and use a stable input folder.
Hash checks detect changes but are not a transaction against concurrent writers.
If optional report writing fails after PDF creation, the PDF may already exist;
inspect it before retrying. Huge files can consume substantial memory. PDFs from
untrusted sources still require your normal document-security practices.

## Further learning
Explore pathlib, context managers, argparse, cryptographic hashes, temporary files
and unittest. Next, compare naturally sorted filenames with lexical ordering.


[Back to setup and commands](README.md).
