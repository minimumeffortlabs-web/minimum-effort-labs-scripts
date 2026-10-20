# One employee record becomes one Word document

csv.DictReader maps column names to values. The full input is validated before
generation: ratings 1–5, unique safe IDs and required text. python-docx writes
the Office Open XML package directly; no Word GUI or Microsoft Office install is
needed. pathlib handles paths and argparse supplies the command-line interface.

The real create_review() function creates a document, formats styles and margins,
adds an Annual Robot Performance Review title, personalized identity paragraphs,
a summary and a table. Each table row pairs a performance category with its score.
Manager comments are inserted as plain text. Decimal computes a rounded average.

Exact source excerpts follow. These are focused excerpts of the guarded runnable
script, not a second implementation or a complete standalone program.

```python
    document = Document()
```

```python
    table = document.add_table(
        rows=1, cols=2)
```

```python
            document.save(output / filename)
```

generate_reviews() loops over validated records. Each iteration calls
create_review(robot), builds a filename from the unique safe robot_id and saves
the document. One record becomes one personalized file, repeated 800 times in
the full demo. Existing output directories are refused. Test with the three-row
sample before using authorized real records. The separate invalid fixture proves
duplicate IDs cannot overwrite documents. Exercises: change a rating, inspect
the new average in a NEW output directory, add a quoted comma in comments,
and try a duplicate ID. Extend the layout for letters or certificates while
keeping validation separate from document formatting.
