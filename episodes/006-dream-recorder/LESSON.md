# From fictional dreams to observable text counts

HR asks for common subjects in dream transcripts. A real program can count
repeated strings; it cannot establish what an employee thinks, feels or fears.
The fixture is deliberately biased synthetic comedy, not employee research.
Similar techniques can help explore feedback, search terms and application logs.

pathlib enumerates top-level files in sorted order. UTF-8/BOM decoding either
succeeds or names a fatal error. re.findall extracts lowercase ASCII letter runs.
The same word in different capitalization therefore shares one Counter key.
Numbers/punctuation are separators; English contractions split. This is simple
English tokenization, not language-independent natural-language processing.

The small STOP_WORDS set removes common function words from word rankings. Counter
is a dictionary subclass that aggregates occurrences via update. Adjacent phrases
use the ORIGINAL normalized token list, not a list after deleting stop words:
otherwise expense and the report could become a false expense report pair.
zip(words, words[1:]) stays inside one file; eligible pairs contain no stop word.
Sentence punctuation is ignored by this documented token policy.

Exact excerpts from the executable file follow. Use the full script for CLI,
validation and output handling; these are source-context excerpts, not a separate
standalone program.

```python
    entries = sorted(directory.iterdir())
    for path in entries:
```

```python
    text = text.lower()
    words = re.findall(r'[a-z]+', text)
    return words
```

```python
        word_counts.update(useful)
        phrase_counts.update(adjacent_phrases(words))
```

```python
    pairs = zip(words, words[1:])
    phrases = []
    for a, b in pairs:
        if a in STOP_WORDS:
            continue
        if b in STOP_WORDS:
            continue
        phrases.append((a, b))
    return phrases
```

```python
    ordered = Counter(dict(sorted(counts.items())))
    return ordered.most_common(top)
```

Alphabetically inserted Counter keys make most_common ties stable. The report
contains both extracted and analyzed totals; ranking counts are occurrences, not
numbers of staff. The small sample and full 300-file fixture have DIFFERENT counts;
use the exact README commands and compare the matching expected report.

Exercises: change Coffee to COFFEE; insert a stop word between two words; split a
phrase into separate files; compare report vs reports; try a punctuation boundary;
add an empty file. Predict the result, run tests, inspect the output, and verify
source hashes did not change. Extensions such as multilingual tokenization,
stemming or sentence segmentation require explicit revised rules and tests.
