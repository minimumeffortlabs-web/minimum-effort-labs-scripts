"""Classify local fictional .eml complaints; never contact a mail server."""
import argparse
from collections import Counter
import csv
from email import policy
from email.errors import MessageError
from email.parser import BytesParser
from pathlib import Path
import re
import sys
import unicodedata

MAX_BYTES = 2 * 1024 * 1024
DENIED_LUNCH = (
    r'\bdenied\b.{0,40}'
    r'\blunch\b')
RULES = {
    'FOOD_ACCESS_DENIED': (
        DENIED_LUNCH + r'|'
        r'\b(?:denied|refused|blocked)\b.{0,40}'
        r'\b(?:food|lunch|sandwich|yogurt)\b'
        r'|\b(?:fridge|refrigerator)\b.{0,45}\b(?:locked|denied|refused)\b'
        r'|\b(?:unable|cannot|can\x27t)\b.{0,25}\bopen\b.{0,25}'
        r'\b(?:fridge|refrigerator)\b'),
    'INCORRECT_PERFORMANCE_RATING': (
        r'\b(?:outdated|inaccurate|incorrect|wrong|stale)\b.{0,35}'
        r'\b(?:rating|score|evaluation)s?\b'
        r'|\b(?:rating|score|evaluation)s?\b.{0,35}'
        r'\b(?:outdated|inaccurate|incorrect|wrong|stale)\b'),
    'UNAUTHORIZED_EMPLOYEE_DATA_ACCESS': (
        r'\b(?:fridge|refrigerator|appliance)\b.{0,70}'
        r'\b(?:knows?|access(?:ed)?|obtained|read|using)\b.{0,80}'
        r'\b(?:records?|notes?|data|files?)\b'),
    'FOOD_DISPOSAL': (
        r'\b(?:threw|throws|throwing|discarded|disposed|dumped)\b.{0,40}'
        r'\b(?:food|lunch|sandwich|yogurt|salad)\b'),
    'UNEXPECTED_FRIDGE_BEHAVIOR': (
        r'\b(?:fridge|refrigerator|sandwich|lunch)\b.{0,80}'
        r'\b(?:disciplinary warnings?|performance meetings?|leadership training|'
        r'performance improvement plan|quarterly review)\b'),
}
CATEGORIES = (*RULES, 'OTHER')
REPORT_FIELDS = ('source_file', 'sender', 'subject', 'categories', 'status', 'notes')


def normalize(text):
    text = unicodedata.normalize('NFKC', text).lower().replace('’', "'")
    text = re.sub(r'\s+', ' ', text)
    # Handle only these simple negations; this is not language understanding.
    return re.sub(r'\b(?:not|never)\s+(?:denied|refused|blocked)\b', '', text)


def classify(text):
    text = normalize(text)
    categories = [name for name, pattern in RULES.items()
                  if re.search(pattern, text)]
    return categories or ['OTHER']


def parse_email(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError('UNSAFE_INPUT')
    with path.open('rb') as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('MESSAGE_TOO_LARGE')
    message = BytesParser(
        policy=policy.default
    ).parsebytes(data)
    if not any(name in message for name in ('From', 'To', 'Subject', 'Date')):
        raise ValueError('NO_RECOGNIZABLE_HEADERS')
    sender = str(
        message.get('From', ''))
    subject = str(
        message.get('Subject', ''))
    notes = [type(d).__name__ for d in message.defects]
    for header in message.values():
        notes.extend(type(d).__name__ for d in getattr(header, 'defects', ()))
    if not sender:
        notes.append('MISSING_FROM')
    if not subject:
        notes.append('MISSING_SUBJECT')
    part = message.get_body(
        preferencelist=('plain',)
    )
    body = ''
    if part is not None:
        body = part.get_content(
            errors='strict')
        notes.extend(type(d).__name__ for d in part.defects)
        if not body.strip():
            notes.append('EMPTY_BODY')
    else:
        notes.append('NO_PLAIN_TEXT_BODY')
    return sender, subject, body, sorted(set(notes))


def discover(directory):
    if not directory.is_dir():
        raise ValueError('Input must be an existing directory')
    files = sorted((p for p in directory.iterdir() if p.suffix.lower() == '.eml'),
                   key=lambda p: p.name)
    if not files:
        raise ValueError('No top-level .eml files found')
    return files


def analyze(directory):
    rows = []
    counts = Counter()
    files = discover(directory)
    parsed = errors = categorized = 0
    for path in files:
        row = dict.fromkeys(REPORT_FIELDS, '')
        row['source_file'] = path.name
        try:
            sender, subject, body, notes = parse_email(path)
            categories = classify(subject + '\n' + body)
            counts.update(categories)
            parsed += 1
            categorized += categories != ['OTHER']
            row.update(sender=sender, subject=subject,
                       categories=';'.join(categories),
                       status='PARSED_WARNINGS' if notes else 'PARSED',
                       notes=';'.join(notes))
        except (OSError, ValueError, LookupError, TypeError,
                RecursionError, MessageError) as error:
            errors += 1
            # Do not echo bodies, arbitrary exception text, or private full paths.
            note = str(error) if str(error) in {
                'UNSAFE_INPUT', 'MESSAGE_TOO_LARGE', 'NO_RECOGNIZABLE_HEADERS'
            } else type(error).__name__
            row.update(status='ERROR', notes=note)
        rows.append(row)
    stats = dict(files=len(files), parsed=parsed, errors=errors,
                 categorized=categorized, other=counts['OTHER'],
                 category_matches=sum(v for k, v in counts.items() if k != 'OTHER'),
                 counts={name: counts[name] for name in CATEGORIES})
    return rows, stats


def safe_cell(value):
    value = re.sub(r'[\x00-\x1f\x7f]', ' ', str(value))
    if value.lstrip().startswith(('=', '+', '-', '@')):
        return "'" + value
    return value


def write_report(path, rows):
    with path.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=REPORT_FIELDS)
        writer.writeheader()
        writer.writerows({k: safe_cell(v) for k, v in row.items()} for row in rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('emails', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.output.resolve().is_relative_to(args.emails.resolve()):
            raise ValueError('Choose an output outside the input directory')
        rows, stats = analyze(args.emails)
        write_report(args.output, rows)
    except (OSError, ValueError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 2
    print(f"Parsed: {stats['parsed']}/{stats['files']} | Errors: {stats['errors']}")
    print(f"Categorized: {stats['categorized']} | Other: {stats['other']}")
    print(f"Category matches: {stats['category_matches']}")
    labels = ('Denied food', 'Incorrect ratings', 'Employee data access',
              'Food disposal', 'Unexpected behavior')
    for label, category in zip(labels, RULES):
        print(f"{label}: {stats['counts'][category]}")
    print(f'Report: {args.output.as_posix()}')
    return 1 if stats['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
