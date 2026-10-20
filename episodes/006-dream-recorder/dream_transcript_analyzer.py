"""Count observable text patterns in fictional dream transcripts, not meaning."""
import argparse
from collections import Counter
from pathlib import Path
import re
import sys

# Small English tutorial list, including common apostrophe fragments.
STOP_WORDS = frozenset('''a an and are as at be been being but by can could did do
does for from had has have he her him his how i if in into is it its me my no not
of on or our she so than that the their them then there these they this those to
too up us was we were what when where which while who will with would you your
s t re ve ll d m'''.split())


def find_transcripts(directory):
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError('Transcript directory does not exist')
    files = []
    entries = sorted(directory.iterdir())
    for path in entries:
        if path.suffix.lower() != '.txt':
            continue
        if path.is_symlink():
            raise ValueError(f'Symlink transcript is not supported: {path.name}')
        if path.is_file():
            files.append(path)
    if not files:
        raise ValueError('No .txt transcript files in directory')
    return files


def extract_words(text):
    text = text.lower()
    words = re.findall(r'[a-z]+', text)
    return words


def adjacent_phrases(words):
    pairs = zip(words, words[1:])
    phrases = []
    for a, b in pairs:
        if a in STOP_WORDS:
            continue
        if b in STOP_WORDS:
            continue
        phrases.append((a, b))
    return phrases


def analyze_files(files):
    word_counts = Counter()
    phrase_counts = Counter()
    extracted = analyzed = empty = 0
    for path in files:
        try:
            text = path.read_text(encoding='utf-8-sig')
        except (OSError, UnicodeError) as error:
            raise ValueError(f'Cannot read {path.name}: {error}') from error
        words = extract_words(text)
        if not words:
            empty += 1
        extracted += len(words)
        useful = [word for word in words if word not in STOP_WORDS]
        analyzed += len(useful)
        word_counts.update(useful)
        phrase_counts.update(adjacent_phrases(words))
    return dict(files=len(files), empty=empty, extracted=extracted,
                analyzed=analyzed, words=word_counts, phrases=phrase_counts)


def rank_counts(counts, top):
    # Alphabetical insertion order makes equal-count ties explicit and portable.
    ordered = Counter(dict(sorted(counts.items())))
    return ordered.most_common(top)


def format_report(result, top):
    lines = ['Dream transcript frequency report',
             'Observable text patterns; not psychological interpretation.',
             f"Valid transcript files: {result['files']}",
             f"Empty/tokenless files: {result['empty']}",
             f"Extracted words: {result['extracted']}",
             f"Analyzed non-stop words: {result['analyzed']}",
             '', f'Top {top} words:']
    for number, (word, count) in enumerate(rank_counts(result['words'], top), 1):
        lines.append(f'{number}. {word}: {count}')
    if not result['words']:
        lines.append('(none)')
    lines += ['', f'Top {top} adjacent two-word phrases:']
    for number, (pair, count) in enumerate(rank_counts(result['phrases'], top), 1):
        lines.append(f"{number}. {' '.join(pair)}: {count}")
    if not result['phrases']:
        lines.append('(none)')
    lines += ['', 'Phrases use adjacent original tokens within each file.',
              'Pairs containing a stop word are excluded; punctuation is ignored.',
              'Counts are occurrences, not counts of employees or dreams.']
    return '\n'.join(lines) + '\n'


def positive_int(value):
    number = int(value)
    if number < 1:
        raise ValueError('Must be a positive integer')
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--top', type=positive_int, default=10)
    args = parser.parse_args(argv)
    try:
        if args.output.resolve().is_relative_to(args.directory.resolve()):
            raise ValueError('Write the report outside the transcript directory')
        files = find_transcripts(args.directory)
        result = analyze_files(files)
        report = format_report(result, args.top)
        with args.output.open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(report)
    except (OSError, UnicodeError, ValueError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 2
    print(f"Transcripts: {result['files']} / empty: {result['empty']}")
    print(f"Words: {result['extracted']} / analyzed: {result['analyzed']}")
    for word, count in rank_counts(result['words'], min(2, args.top)):
        print(f'Word: {word} / {count}')
    for pair, count in rank_counts(result['phrases'], min(2, args.top)):
        print(f"Phrase: {' '.join(pair)} / {count}")
    print(f'Report: {args.output}')
    print('Text frequency, not dream meaning.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
