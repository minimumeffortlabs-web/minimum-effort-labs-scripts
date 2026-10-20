# Fictional PDF sample
Three valid one-page synthetic MEL documents, not private records. Filenames are
zero-padded to make alphabetical order match intended document order. The video
uses 400 documents; this small download uses the same program with three.
From the episode directory: `python merge_pdfs.py sample/input merged.pdf --report merge_report.json`.
Expect three readable pages in the order listed in expected.json. Original bytes
must remain unchanged. The output PDF hash is not fixed (PDF metadata can vary).
