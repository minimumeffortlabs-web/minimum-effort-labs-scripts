"""Audit fictional invoice CSVs offline; flags are requests for human review."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
import re
import sys
import unicodedata

FIELDS = ('invoice_id', 'vendor_id', 'invoice_date', 'currency', 'amount', 'description')
CONFIG_FIELDS = ('currency_code', 'description', 'decimal_places')
FLAGS = ('MISSING_REQUIRED_FIELD', 'INVALID_ID', 'INVALID_DATE', 'UNKNOWN_CURRENCY',
         'INVALID_AMOUNT', 'DUPLICATE_INVOICE_ID', 'POSSIBLE_DUPLICATE_INVOICE')
REPORT_FIELDS = (*FIELDS, 'validation_status', 'anomaly_flags', 'explanation')
ID_PATTERN = r'[A-Za-z0-9][A-Za-z0-9._-]{0,39}'
MAX_ROWS = 100000


def read_csv(path, required):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(
            stream, strict=True)
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)) or not set(required) <= set(headers):
            raise ValueError('Missing or duplicate required CSV headers')
        rows = []
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError('CSV row has the wrong number of columns')
            rows.append({key: row[key] for key in required})
            if len(rows) > MAX_ROWS:
                raise ValueError('CSV exceeds the 100000-record limit')
    if not rows:
        raise ValueError('CSV contains no records')
    return rows


def load_currencies(path):
    currencies = {}
    for row in read_csv(path, CONFIG_FIELDS):
        code = row['currency_code'].strip().upper()
        places = row['decimal_places'].strip()
        if (not re.fullmatch(r'[A-Z]{3,8}', code) or code in currencies
                or not row['description'].strip() or not re.fullmatch(r'[0-6]', places)):
            raise ValueError('Invalid or duplicate currency configuration')
        currencies[code] = int(places)
    return currencies


def parse_amount(text, decimal_places):
    text = text.strip()
    if len(text) > 64:
        raise ValueError('Amount exceeds the 64-character limit')
    try:
        amount = Decimal(text)
    except InvalidOperation:
        raise ValueError('Amount is not a decimal number') from None
    if (
        not amount.is_finite()
        or amount <= 0
    ):
        raise ValueError(
            'Not finite and positive')
    if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?', text):
        raise ValueError('Use unsigned decimal text; no exponent, separators or symbols')
    fraction = text.partition('.')[2]
    if len(fraction) > decimal_places:
        raise ValueError('Amount exceeds the configured decimal places')
    return amount


def valid_date(text):
    if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', text):
        return False
    try:
        date.fromisoformat(text)
        return True
    except ValueError:
        return False


def normalized_description(text):
    return ' '.join(unicodedata.normalize('NFKC', text).casefold().split())


def audit(rows, currencies):
    records = []
    ids = defaultdict(list)
    claims = defaultdict(list)
    for original in rows:
        row = {key: original[key].strip() for key in FIELDS}
        row['currency'] = row['currency'].upper()
        reasons = {}
        missing = [key for key in FIELDS if not row[key]]
        if missing:
            reasons['MISSING_REQUIRED_FIELD'] = 'Missing: ' + ', '.join(missing)
        for key in ('invoice_id', 'vendor_id'):
            if row[key] and not re.fullmatch(ID_PATTERN, row[key]):
                reasons['INVALID_ID'] = 'IDs require 1-40 ASCII letters/digits/dot/underscore/hyphen'
        if not valid_date(row['invoice_date']):
            reasons['INVALID_DATE'] = 'Expected a real YYYY-MM-DD calendar date'
        code = row['currency']
        if code not in currencies:
            reasons['UNKNOWN_CURRENCY'] = 'Currency is not in the supplied Accounting configuration'
        amount = None
        try:
            places = currencies.get(code, 6)
            amount = parse_amount(row['amount'], places)
        except ValueError as error:
            reasons['INVALID_AMOUNT'] = str(error)
        index = len(records)
        invoice_id = row['invoice_id']
        if re.fullmatch(ID_PATTERN, invoice_id):
            ids[invoice_id].append(index)
        # Unknown currencies can still have comparable claims; no exchange conversion.
        if (amount is not None and valid_date(row['invoice_date'])
                and re.fullmatch(ID_PATTERN, row['vendor_id'])
                and re.fullmatch(r'[A-Z]{3,8}', code) and row['description']):
            claim = (
                row['vendor_id'],
                row['invoice_date'],
                code, amount,
                normalized_description(
                    row['description']),
            )
            claims[claim].append(index)
        records.append(dict(original=original, row=row, amount=amount, reasons=reasons))
    for group in ids.values():
        if len(group) > 1:
            for index in group:
                records[index]['reasons']['DUPLICATE_INVOICE_ID'] = 'Invoice ID repeats in this input; all members flagged'
    for group in claims.values():
        if len(group) > 1:
            for index in group:
                records[index]['reasons']['POSSIBLE_DUPLICATE_INVOICE'] = 'Matching vendor/date/currency/amount/description; review all members'
    counts = Counter()
    report = []
    totals = {}
    # Precision 80 exceeds 64 amount characters + six sum digits for 100000 rows.
    with localcontext() as context:
        context.prec = 80
        for item in records:
            flags = [flag for flag in FLAGS if flag in item['reasons']]
            counts.update(flags)
            code = item['row']['currency']
            if not flags:
                totals[code] = totals.get(code, Decimal('0')) + item['amount']
            report.append({**item['original'], 'currency': code,
                           'validation_status': 'FLAGGED' if flags else 'VALID',
                           'anomaly_flags': ';'.join(flags),
                           'explanation': '; '.join(item['reasons'][flag] for flag in flags)})
    flagged = sum(row['validation_status'] == 'FLAGGED' for row in report)
    return report, dict(records=len(rows), flagged=flagged, valid=len(rows)-flagged,
                       total_flags=sum(counts.values()), counts={f: counts[f] for f in FLAGS},
                       valid_totals={code: format(totals[code], 'f') for code in sorted(totals)})


def safe_cell(text):
    text = re.sub(r'[\x00-\x1f\x7f]', ' ', str(text))
    return "'" + text if text.lstrip().startswith(('=', '+', '-', '@')) else text


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('invoices', type=Path)
    parser.add_argument('-c', '--currencies', required=True, type=Path)
    parser.add_argument('-o', '--output', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.output.resolve() in (args.invoices.resolve(), args.currencies.resolve()):
            raise ValueError('Output must differ from both input paths')
        currencies = load_currencies(args.currencies)
        report, stats = audit(read_csv(args.invoices, FIELDS), currencies)
        with args.output.open('x', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(
                stream, fieldnames=REPORT_FIELDS)
            writer.writeheader()
            for row in report:
                safe_row = {k: safe_cell(v) for k, v in row.items()}
                writer.writerow(safe_row)
    except (OSError, ValueError, csv.Error, UnicodeError) as error:
        print('Error: ' + str(error), file=sys.stderr)
        return 2
    print(f"Invoices: {stats['records']} | Flagged: {stats['flagged']}")
    print(f"Valid: {stats['valid']} | Flags: {stats['total_flags']}")
    labels = ('Missing fields', 'Invalid IDs', 'Invalid dates', 'Unknown currencies',
              'Invalid amounts', 'Duplicate IDs', 'Possible duplicate claims')
    print(f"Missing: {stats['counts']['MISSING_REQUIRED_FIELD']} | Invalid IDs: {stats['counts']['INVALID_ID']}")
    for flag, label in zip(FLAGS[2:], labels[2:]):
        print(f'{label}: {stats["counts"][flag]}')
    print('Report: ' + args.output.name)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
