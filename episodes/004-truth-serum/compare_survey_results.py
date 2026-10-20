"""Compare paired fictional survey ratings. Differences do not establish causation."""
import argparse
import csv
import re
import statistics
import sys
from collections import Counter
from pathlib import Path


def read_survey(path):
    """Exclude every occurrence of a duplicate ID, never pick a convenient row."""
    ratings, seen, issues = {}, Counter(), []
    with Path(path).open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream, strict=True)
        headers = reader.fieldnames
        required = {'customer_id', 'satisfaction_rating'}
        if not headers or len(headers) != len(set(headers)) or not required <= set(headers):
            raise ValueError(f'{Path(path).name}: missing or duplicate required headers')
        rows = 0
        for row in reader:
            rows += 1
            customer = (row.get('customer_id') or '').strip()
            if customer:
                seen[customer] += 1
            value = (row.get('satisfaction_rating') or '').strip()
            if not customer or None in row or any(v is None for v in row.values()):
                issues.append(f'Row {reader.line_num}: missing ID/field or extra CSV fields')
            elif not re.fullmatch(r'[0-9]+', value) or not 1 <= int(value) <= 10:
                issues.append(f'Row {reader.line_num}: {customer}: invalid rating {value!r}')
            else:
                ratings[customer] = int(value)
        if rows == 0:
            raise ValueError(f'{Path(path).name}: no survey rows')
    duplicates = sorted(customer for customer, count in seen.items() if count > 1)
    for customer in duplicates:
        ratings.pop(customer, None)
        issues.append(f'Duplicate ID excluded: {customer} ({seen[customer]} rows)')
    return {'ratings': ratings, 'seen': set(seen), 'issues': issues,
            'duplicates': duplicates, 'rows': rows}


def paired_changes(before, after):
    pairs = []
    matched = sorted(before.keys() & after.keys())
    for customer in matched:
        old, new = before[customer], after[customer]
        change = new - old
        pairs.append((customer, old, new, change))
    return pairs


def summarize(pairs):
    if not pairs:
        raise ValueError('No valid paired responses; averages are undefined')
    changes = [row[3] for row in pairs]
    mean_change = statistics.mean(changes)
    return {
        'count': len(pairs),
        'before': statistics.mean(old for _, old, _, _ in pairs),
        'after': statistics.mean(new for _, _, new, _ in pairs),
        'change': mean_change,
        'declines': sum(change < 0 for _, _, _, change in pairs),
        'improvements': sum(change > 0 for _, _, _, change in pairs),
        'unchanged': sum(change == 0 for _, _, _, change in pairs),
    }


def format_report(before, after, pairs, summary):
    lines = ['PAIRED SURVEY REPORT — FICTIONAL DEMONSTRATION',
             'Scale: integers 1–10. All means use the SAME valid paired participants.',
             f"Paired valid responses: {summary['count']}",
             f"Mean before: {summary['before']:.2f}",
             f"Mean after: {summary['after']:.2f}",
             f"Mean paired change (after - before): {summary['change']:+.2f}",
             f"Declines: {summary['declines']}; improvements: {summary['improvements']}; unchanged: {summary['unchanged']}",
             'Before-only IDs: ' + (', '.join(sorted(before['seen'] - after['seen'])) or 'none'),
             'After-only IDs: ' + (', '.join(sorted(after['seen'] - before['seen'])) or 'none'),
             'Invalid or duplicate records are excluded, never replaced with zero.', '',
             'customer_id,before,after,change']
    lines += [f'{customer},{old},{new},{change:+d}' for customer, old, new, change in pairs]
    for name, survey in [('before', before), ('after', after)]:
        lines += ['', name.upper() + ' VALIDATION'] + (survey['issues'] or ['No issues'])
    lines += ['', 'Observed response differences do not independently establish causation.',
              'This fictional before/after design cannot prove that a serum caused the change.']
    return '\n'.join(lines) + '\n'


def write_report(path, text):
    # Exclusive creation protects previous reports and every existing input.
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(text)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', type=Path)
    parser.add_argument('after', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.before.resolve() == args.after.resolve():
            raise ValueError('Use two distinct survey inputs')
        if args.output.exists() or args.output.resolve() in [args.before.resolve(), args.after.resolve()]:
            raise ValueError('Choose a new output path; existing files are never overwritten')
        before = read_survey(args.before)
        after = read_survey(args.after)
        pairs = paired_changes(before['ratings'], after['ratings'])
        summary = summarize(pairs)
        text = format_report(before, after, pairs, summary)
        write_report(args.output, text)
        print(f"Paired valid responses: {summary['count']}")
        print(f"Average before: {summary['before']:.2f} / after: {summary['after']:.2f}")
        print(f"Average change: {summary['change']:+.2f} points")
        print(f"Declined: {summary['declines']} / improved: {summary['improvements']} / unchanged: {summary['unchanged']}")
        print(f'Saved: {args.output.name}')
        print('Observed differences; causation not established. Inputs unchanged.')
        return 0
    except (OSError, ValueError, csv.Error, UnicodeError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
