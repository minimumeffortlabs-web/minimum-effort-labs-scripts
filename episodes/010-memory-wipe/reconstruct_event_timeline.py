"""Reconstruct available JSON events; logs are evidence, not complete history."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys

FIELDS = ('event_id', 'timestamp', 'source', 'event_type', 'description')
ISO = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})\Z')
IDENTIFIER = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z')
MAX_BYTES = 10 * 1024 * 1024
MAX_EVENTS = 100000


def parse_timestamp(text):
    """Require explicit offsets; never interpret naive time as local time."""
    if not ISO.fullmatch(text):
        raise ValueError('Expected YYYY-MM-DDTHH:MM:SS[.ffffff]Z or +/-HH:MM')
    if text.endswith('-00:00'):
        raise ValueError('Unknown offset -00:00 is not an established timezone')
    suffix = text[-6:]
    if not text.endswith('Z') and (int(suffix[1:3]) > 23 or int(suffix[4:]) > 59):
        raise ValueError('Invalid timezone offset')
    timestamp = datetime.fromisoformat(
        text.replace('Z', '+00:00'))
    if (
        timestamp.tzinfo is None
        or timestamp.utcoffset() is None
    ):
        raise ValueError('Timezone required')
    return timestamp.astimezone(timezone.utc)


def utc_text(timestamp):
    return timestamp.isoformat().replace('+00:00', 'Z')


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON property: ' + key)
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError('Nonstandard JSON number: ' + value)


def load_events(directory):
    """Read immediate .json files only; retain all rejection locations."""
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError('Input must be an existing directory')
    files = sorted((p for p in directory.iterdir()
                    if p.is_file() and p.suffix.lower() == '.json'),
                   key=lambda p: p.name)
    if not files:
        raise ValueError('No JSON log files found')
    candidates, errors = [], []
    discovered = 0
    for path in files:
        try:
            if path.is_symlink():
                raise ValueError('Symlink inputs are not supported')
            if path.stat().st_size > MAX_BYTES:
                raise ValueError('File exceeds 10 MiB limit')
            with path.open(encoding='utf-8-sig') as stream:
                records = json.load(
                    stream, object_pairs_hook=unique_object,
                    parse_constant=invalid_constant)
            if not isinstance(records, list):
                raise ValueError('Top-level JSON must be an array')
        except (OSError, UnicodeError, ValueError, RecursionError) as error:
            errors.append(dict(file=path.name, row=None, event_id='',
                               reason='FILE_ERROR: ' + str(error)))
            continue
        discovered += len(records)
        if discovered > MAX_EVENTS:
            raise ValueError('More than 100000 array entries; split the input')
        for row, event in enumerate(records, 1):
            try:
                if not isinstance(event, dict):
                    raise ValueError('Event must be an object')
                if any(not isinstance(event.get(k), str) or not event[k].strip()
                       for k in FIELDS):
                    raise ValueError('Five required fields must be nonempty strings')
                if any(len(event[k]) > 2000 for k in FIELDS):
                    raise ValueError('Field exceeds 2000 characters')
                if not IDENTIFIER.fullmatch(event['event_id']):
                    raise ValueError('Invalid event_id (ASCII identifier, 1-80 chars)')
                parsed = parse_timestamp(event['timestamp'])
                candidates.append({**{k: event[k] for k in FIELDS},
                                   'parsed_timestamp': parsed,
                                   'source_file': path.name, 'row': row})
            except (ValueError, OverflowError) as error:
                identifier = event.get('event_id', '') if isinstance(event, dict) else ''
                errors.append(dict(file=path.name, row=row,
                                   event_id=identifier if isinstance(identifier, str) else '',
                                   reason='INVALID_RECORD: ' + str(error)))
    # All occurrences of a repeated syntactically valid ID are excluded,
    # including an otherwise valid event paired with a malformed event.
    ids = Counter(e['event_id'] for e in candidates)
    ids.update(e['event_id'] for e in errors if IDENTIFIER.fullmatch(e['event_id']))
    events = []
    duplicates = 0
    for event in candidates:
        if ids[event['event_id']] > 1:
            duplicates += 1
            errors.append(dict(file=event['source_file'], row=event['row'],
                               event_id=event['event_id'], reason='DUPLICATE_ID: all occurrences excluded'))
        else:
            events.append(event)
    events.sort(key=lambda e: (
        e['parsed_timestamp'],
        e['source_file'],
        e['row']))
    errors.sort(key=lambda e: (e['file'], e['row'] or 0, e['reason']))
    stats = dict(files=len(files), discovered=discovered, valid=len(events),
                 rejected_records=sum(e['row'] is not None for e in errors),
                 file_errors=sum(e['row'] is None for e in errors),
                 duplicate_records=duplicates,
                 earliest=utc_text(events[0]['parsed_timestamp']) if events else 'NONE',
                 latest=utc_text(events[-1]['parsed_timestamp']) if events else 'NONE')
    return events, errors, stats


def cell(value):
    # Escape control chars, separators and backslashes; no forged report rows.
    return str(value).encode('unicode_escape').decode('ascii').replace('|', r'\x7c')


def write_timeline(stream, events, errors):
    stream.write('AVAILABLE-LOG TIMELINE (UTC)\n')
    stream.write('Incomplete logs do not prove complete history.\n')
    stream.write('timestamp | source | event_type | description | file:row | event_id\n')
    for event in events:
        fields = (utc_text(event['parsed_timestamp']), event['source'],
                  event['event_type'], event['description'],
                  f"{event['source_file']}:{event['row']}", event['event_id'])
        values = map(cell, fields)
        stream.write(' | '.join(values) + '\n')
    stream.write('\nREJECTED RECORDS AND FILE ERRORS\n')
    if not errors:
        stream.write('None\n')
    for error in errors:
        fields = (error['file'], error['row'] or 'FILE', error['event_id'], error['reason'])
        stream.write(' | '.join(cell(x) for x in fields) + '\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', '-o', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        # Keep outputs outside inputs, including a directory symlink target.
        source = args.directory.resolve()
        target = args.output.resolve()
        if target == source or target.is_relative_to(source):
            raise ValueError('Output must be outside the input directory')
        events, errors, stats = load_events(args.directory)
        with args.output.open('x', encoding='utf-8', newline='\n') as stream:
            write_timeline(stream, events, errors)
        print(f"JSON files: {stats['files']} | Events: {stats['discovered']}")
        print(f"Timeline: {stats['valid']} | Rejected: {stats['rejected_records']}")
        print(f"File errors: {stats['file_errors']} | Duplicate IDs: {stats['duplicate_records']}")
        print('First: ' + stats['earliest'])
        print('Last: ' + stats['latest'])
        print('Report: ' + str(args.output))
        return 1 if errors else 0
    except (OSError, ValueError, OverflowError, RecursionError) as error:
        print('Error: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
