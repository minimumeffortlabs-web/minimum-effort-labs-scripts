"""Compare electronic records; discrepancies require human review, never establish guilt."""
import csv
from datetime import datetime
from datetime import timedelta, timezone


def read_rows(path):
    with path.open(
        newline="",
        encoding="utf-8-sig"
    ) as file:
        return list(
            csv.DictReader(file)
        )


def parse_time(value):
    if "T" not in value:
        raise ValueError("Use an ISO date and time separated by T.")
    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )


def unmatched(shifts, doors,
              before, after):
    by_id = {}
    for row in doors:
        by_id.setdefault(
            row["id"], []
        )
        by_id[row["id"]].append(
            row["time"]
        )
    for shift in shifts:
        start = shift["time"]
        entries = by_id.get(
            shift["id"], []
        )
        if not any(
            start-before <= t
            <= start+after
            for t in entries
        ):
            yield shift


def write_report(path, rows):
    fields = ["employee_id", "clock_in", "clock_out", "reason", "source_row"]
    with path.open(
        "x", newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=fields
        )
        writer.writeheader()
        writer.writerows(rows)


def reconcile(timecards, access, output, before_minutes=30, after_minutes=10):
    import hashlib
    from pathlib import Path
    cards, door_path, output = map(Path, (timecards, access, output))
    if before_minutes < 0 or after_minutes < 0:
        raise ValueError("Tolerance minutes must be nonnegative.")
    if output.resolve() in [cards.resolve(), door_path.resolve()] or output.exists():
        raise ValueError("Choose a new output file separate from the inputs.")
    if output.suffix.lower() != ".csv":
        raise ValueError("Output filename must end in .csv.")
    hashes = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in [cards, door_path]}
    schemas = [(cards, {"employee_id", "clock_in", "clock_out"}),
               (door_path, {"employee_id", "timestamp", "event", "result"})]
    tables = []
    for path, required in schemas:
        with path.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.reader(file)
            header = next(reader, [])
        if not required.issubset(header) or len(header) != len(set(header)):
            raise ValueError(f"Missing required or duplicate columns in {path.name}: {', '.join(sorted(required))}")
        tables.append(read_rows(path))
    mode = None
    def stamp(value):
        nonlocal mode
        date = parse_time(value)
        aware = date.utcoffset() is not None
        if mode is not None and mode != aware:
            raise RuntimeError("Do not mix timezone-aware and local-naive timestamps across files.")
        mode = aware
        return date.astimezone(timezone.utc) if aware else date
    def valid_row(row):
        if None in row or any(value is None for value in row.values()) or not row.get("employee_id", "").strip():
            raise ValueError("Malformed CSV row or missing employee ID.")
    doors = []; bad_doors = 0
    for row in tables[1]:
        try:
            valid_row(row)
            when = stamp(row["timestamp"])
            event, result = row["event"].strip().upper(), row["result"].strip().upper()
            if event not in {"ENTRY", "EXIT"} or result not in {"GRANTED", "DENIED"}:
                raise ValueError("Unknown access event or result.")
            if event == "ENTRY" and result == "GRANTED":
                doors.append({"id": row["employee_id"].strip(), "time": when})
        except (ValueError, TypeError):
            bad_doors += 1
    shifts = []; flagged = []
    for number, row in enumerate(tables[0], 2):
        record = {key: row.get(key) or "" for key in ["employee_id", "clock_in", "clock_out"]}
        record["source_row"] = number
        try:
            valid_row(row)
            clock_in, clock_out = stamp(row["clock_in"]), stamp(row["clock_out"])
            if clock_out < clock_in:
                raise ValueError("Clock-out precedes clock-in.")
            shifts.append({"id": row["employee_id"].strip(), "time": clock_in, "record": record})
        except (ValueError, TypeError):
            flagged.append({**record, "reason": "invalid_timecard_review"})
    missing = list(unmatched(shifts, doors, timedelta(minutes=before_minutes), timedelta(minutes=after_minutes)))
    flagged += [{**shift["record"], "reason": "no_entry_in_window_review"} for shift in missing]
    flagged.sort(key=lambda row: row["source_row"])
    if any(hashlib.sha256(p.read_bytes()).hexdigest() != digest for p, digest in hashes.items()):
        raise ValueError("Input changed during reconciliation; retry with stable files.")
    write_report(output, flagged)
    return {"checked": len(tables[0]), "matched": len(shifts)-len(missing), "flagged": len(flagged),
            "invalid_timecards": len(tables[0])-len(shifts), "invalid_access": bad_doors,
            "output": output.name, "input_hashes_unchanged": True}


def main():
    import argparse
    import sys
    parser = argparse.ArgumentParser(description="Flag unmatched timecards for human review, not proof of absence.")
    parser.add_argument("timecards"); parser.add_argument("access")
    parser.add_argument("--output", required=True)
    parser.add_argument("--before-minutes", type=int, default=30)
    parser.add_argument("--after-minutes", type=int, default=10)
    args = parser.parse_args()
    try:
        result = reconcile(args.timecards, args.access, args.output, args.before_minutes, args.after_minutes)
    except (OSError, ValueError, RuntimeError, csv.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr); return 2
    print(f"Checked {result['checked']} shifts. Matched {result['matched']}.")
    print(f"Flagged {result['flagged']} for review -> {result['output']}")
    print(f"Invalid rows: {result['invalid_timecards']} timecards, {result['invalid_access']} access events.")
    print("Missing logs are not proof of absence. Inputs unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
