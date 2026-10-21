# From MIME messages to a category report

The task is to turn many local email files into a reviewable table. Unlike a text
transcript, an email carries headers, transfer encodings and possibly several MIME
parts. Searching the raw file would count encoded strings and attachment content.
Use the standard library to recover the intended structure first.

The exact source excerpts below come from the runnable file. They are focused
pieces of a guarded CLI, not a separate complete program. The README explains
the full parsing/error policy and the smaller versus 400-message fixtures.

```python
    message = BytesParser(
        policy=policy.default
    ).parsebytes(data)
```

```python
    sender = str(
        message.get('From', ''))
    subject = str(
        message.get('Subject', ''))
```

```python
    part = message.get_body(
        preferencelist=('plain',)
    )
```

```python
        body = part.get_content(
            errors='strict')
```

```python
DENIED_LUNCH = (
    r'\bdenied\b.{0,40}'
    r'\blunch\b')
```

```python
    categories = [name for name, pattern in RULES.items()
                  if re.search(pattern, text)]
```

```python
            counts.update(categories)
```

BytesParser with policy.default produces an EmailMessage. Header lookup returns
the sender and subject. get_body(preferencelist=('plain',)) chooses a plain-text
body while excluding attachment candidates. Decode only that selected part with
get_content(errors='strict'); this reports unsupported charsets rather than
quietly substituting corrupted text. HTML-only messages use subject-only matching
and warn. See the official [body-selection reference](https://docs.python.org/3/library/email.message.html#email.message.EmailMessage.get_body)
and [content decoder reference](https://docs.python.org/3/library/email.contentmanager.html).

Normalize the recovered subject/body before applying rules. DENIED_LUNCH is one
real alternative used by RULES: a word-boundary denied, at most forty characters,
then a word-boundary lunch. Other alternatives cover refusal, blocked food and
locked refrigerators. This is transparent rule matching, not machine learning.
The list comprehension retains all matching categories; repeated mentions of one
category do not add another match. If nothing matches, use OTHER.

Counter.update receives category labels rather than individual words. Compare
unique categorized messages with the sum of category matches: those are different
quantities. Error rows have no categories. Real 400-message results are 334 unique
categorized +66 OTHER, with 455 non-OTHER matches and zero processing errors.
The independent fixture manifest validates every label, not just those totals.

csv.DictWriter writes deterministic fields and rows in filename order. Report
metadata is useful for manual follow-up without exporting bodies. Sender/subject
are still potentially personal information. Treat inputs as data: never execute
content, follow links or open attachments. Output cells receive control-character
cleanup and spreadsheet formula-prefix protection. Existing files are refused.

Exercises: change a fictional subject to match two categories; add a plain-text
attachment containing a matching phrase and verify it is ignored; compare HTML
and plain alternatives; try a missing body or unknown charset; repeat a phrase
inside one email and confirm its category contributes only once. Predict each
result, run the tests and inspect a NEW output report. Adapt RULES for other
local complaint workflows, document ambiguous language, and review classifications
before acting on them.
