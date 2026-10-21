# Python lesson — Rebuild the timeline

**Minimum Effort Labs. Questionable science. Real Python.**

JSON arrays become Python lists; JSON objects become dictionaries. This lesson
turns those unordered records into a traceable UTC report, without inventing history.

## 1. Find and load structured files

pathlib represents filesystem paths. load_events sorts immediate JSON filenames,
opens each file with UTF-8/BOM support, and uses json.load to produce native objects.
The real called source contains:

```python
            with path.open(encoding='utf-8-sig') as stream:
                records = json.load(
                    stream, object_pairs_hook=unique_object,
                    parse_constant=invalid_constant)
```

The hooks reject duplicate properties and nonstandard numbers. We require a list
of objects with five documented string fields. Exceptions are recorded per file
or record; they are never silently discarded. The original files are read only.

## 2. Convert strings to aware datetime values

parse_timestamp first enforces explicit offsets and validates their syntax.
The actual conversion and awareness guard are:

```python
    timestamp = datetime.fromisoformat(
        text.replace('Z', '+00:00'))
    if (
        timestamp.tzinfo is None
        or timestamp.utcoffset() is None
    ):
        raise ValueError('Timezone required')
    return timestamp.astimezone(timezone.utc)
```

Z means UTC; +05:30 means local time is five and a half hours ahead of UTC.
astimezone(timezone.utc) preserves the instant while changing its representation.
A naive timestamp has no established timezone, so this program rejects it before
normalizing. Never let astimezone guess the local machine timezone for such data.
Parsing also catches impossible dates and conversions outside Python's date range.

## 3. Sort by time, with stable explicit ties

This is the actual sorting key after duplicate filtering:

```python
    events.sort(key=lambda e: (
        e['parsed_timestamp'],
        e['source_file'],
        e['row']))
```

The first tuple element orders UTC datetime objects. Filename and original 1-based
row make equal-time events deterministic and auditable. Sorting raw offset strings
could put events in the wrong order. Repeated descriptions are not duplicate IDs.
All otherwise-valid members of a repeated-ID group are excluded, not arbitrarily
replaced with the first. Error details remain available for human investigation.

## 4. Write a readable audit trail

write_timeline uses the ordered events, formats UTC and records the source file,
row and ID. It escapes separators/control characters to keep one event per line:

```python
        stream.write(' | '.join(values) + '\n')
```

The wrapper opens a NEW file with exclusive mode x. Errors form a separate report
section; the concise terminal summary distinguishes record rejections from file
errors. See README for exit codes and exact supported schema, limits and policies.

## 5. Run and verify

Start with the 35-event sample and compare its expected report. Then generate 1000
events with seed 80010. The full fixture deliberately shuffles entries and changes
timezone offsets. Its independent pre-conversion UTC truth verifies every event,
not merely the program against its own parser. Tests cover clean/multiple files,
sort order, offsets, equal-time ties, naive/bad/overflow timestamps, JSON/property
errors, missing fields, duplicates, empty inputs, actual report/exit codes, input
preservation, deterministic generation and the recovered second-wipe record.

## Exercises

1. Copy two logs; write equal instants using Z and -07:00. Predict their tie order.
2. Remove a timezone and inspect the rejected row and exit code 1.
3. Repeat an ID with a different description. Explain why both records disappear
   from the primary timeline but repeated descriptions with new IDs remain.
4. Add a test for a new permitted schema before changing the implementation.

Useful in debugging, incident response and authorized operational audits. Logs may
be missing, inaccurate or incomplete. Order is not proof of causation and an absent
record does not prove an event never happened. Do not use fictional examples as
evidence about real people or systems.

Python primary references: [json](https://docs.python.org/3/library/json.html),
[datetime](https://docs.python.org/3/library/datetime.html),
[pathlib](https://docs.python.org/3/library/pathlib.html).
