"""Flag questionable fictional expense records; never modify or reject claims."""
import argparse
import csv
import re
import sys
from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path

FIELDS = ['expense_id', 'employee_id', 'expense_date',
          'merchant', 'amount', 'description']
REPORT_FIELDS = ['source_row', *FIELDS, 'anomaly_flags', 'explanation']
FLAG_TEXT = {
    'FUTURE_DATE': 'Expense date is later than the audit cutoff.',
    'INVALID_DATE': 'Missing or invalid YYYY-MM-DD calendar date.',
    'DUPLICATE_EXPENSE_ID': 'Expense ID occurs more than once in this file.',
    'POSSIBLE_DUPLICATE_CLAIM': 'Matching claim details; human review required.',
    'INVALID_AMOUNT': 'Amount must be positive plain decimal with at most two decimal places.',
    'MISSING_EXPENSE_ID': 'Expense ID is blank.',
    'MISSING_EMPLOYEE_ID': 'Employee ID is blank.',
    'MISSING_MERCHANT': 'Merchant is blank.',
}


def parse_date(value):
    if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value):
        raise ValueError('Use YYYY-MM-DD')
    return date.fromisoformat(value)


def parse_amount(value):
    if not re.fullmatch(r'[0-9]+(?:\.[0-9]{1,2})?', value):
        raise ValueError('Use plain decimal money')
    amount = Decimal(value)
    if not amount.is_finite() or amount <= 0:
        raise ValueError('Amount must be positive')
    return amount


def read_expenses(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle, strict=True)
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)) or not set(FIELDS) <= set(headers):
            raise ValueError('Required unique CSV headers: ' + ','.join(FIELDS))
        rows = []
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f'Malformed CSV record near line {reader.line_num}')
            rows.append({key: row[key] for key in FIELDS})
    if not rows:
        raise ValueError('CSV contains no expense records')
    return rows


def prepare_claim(row):
    date_text = row['expense_date'].strip()
    try:
        expense_date = parse_date(date_text)
    except ValueError:
        expense_date = None
    try:
        amount = parse_amount(row['amount'].strip())
    except ValueError:
        amount = None
    employee = row['employee_id'].strip()
    merchant = row['merchant'].strip().casefold()
    key = (employee, expense_date, merchant, amount)
    valid_key = employee and merchant and expense_date is not None and amount is not None
    return expense_date, amount, key if valid_key else None


def audit_expenses(rows, audit_date):
    prepared = [prepare_claim(row) for row in rows]
    ids = Counter(row['expense_id'].strip() for row in rows)
    claims = Counter(key for _, _, key in prepared if key is not None)
    flagged = []
    counts = Counter({flag: 0 for flag in FLAG_TEXT})
    for number, (row, parsed) in enumerate(zip(rows, prepared), start=2):
        expense_date, amount, key = parsed
        flags = []
        if expense_date is None:
            flags.append('INVALID_DATE')
        elif expense_date > audit_date:
            flags.append('FUTURE_DATE')
        if amount is None:
            flags.append('INVALID_AMOUNT')
        expense_id = row['expense_id'].strip()
        if expense_id and ids[expense_id] > 1:
            flags.append('DUPLICATE_EXPENSE_ID')
        if key is not None and claims[key] > 1:
            flags.append('POSSIBLE_DUPLICATE_CLAIM')
        for field, flag in [('expense_id', 'MISSING_EXPENSE_ID'),
                            ('employee_id', 'MISSING_EMPLOYEE_ID'),
                            ('merchant', 'MISSING_MERCHANT')]:
            if not row[field].strip():
                flags.append(flag)
        if flags:
            counts.update(flags)
            flagged.append({'source_row': number, **row,
                            'anomaly_flags': '|'.join(flags),
                            'explanation': ' '.join(FLAG_TEXT[f] for f in flags)})
    return flagged, counts


def write_report(path, flagged):
    with Path(path).open('x', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_FIELDS)
        writer.writeheader()
        writer.writerows(flagged)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--as-of', type=parse_date, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError('Input and output must be different files')
        rows = read_expenses(args.input)
        flagged, counts = audit_expenses(rows, args.as_of)
        write_report(args.output, flagged)
    except (OSError, UnicodeError, ValueError, csv.Error) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 2
    print(f'Expenses: {len(rows)} / as-of {args.as_of}')
    print(f"Future dates: {counts['FUTURE_DATE']}")
    print(f"Invalid dates: {counts['INVALID_DATE']}")
    print(f"Repeated ID rows: {counts['DUPLICATE_EXPENSE_ID']}")
    print(f"Suspected duplicate rows: {counts['POSSIBLE_DUPLICATE_CLAIM']}")
    print(f"Invalid amounts: {counts['INVALID_AMOUNT']}")
    missing = sum(counts[f] for f in ['MISSING_EXPENSE_ID', 'MISSING_EMPLOYEE_ID', 'MISSING_MERCHANT'])
    print(f'Missing identity flags: {missing}')
    print(f'Flagged rows: {len(flagged)} / total flags: {sum(counts.values())}')
    print(f'Report: {args.output}')
    print('Human review. Input unchanged.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
