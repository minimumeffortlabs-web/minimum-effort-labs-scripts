"""Fictional 48-hour logs, deterministic seed 80010; never private records."""
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import random

SOURCES = ['LAB_SYSTEM', 'SECURITY', 'HR_SYSTEM', 'BUILDING_AUTOMATION',
           'IT_OPERATIONS', 'RESEARCH_NETWORK', 'EXECUTIVE_SCHEDULER']
RECOVERED = dict(event_id='EVT-SECOND-WIPE', timestamp='2026-10-19T02:47:00Z',
                 source='EXECUTIVE_SCHEDULER', event_type='SECOND_WIPE_AUTHORIZED',
                 description='Management authorized a second memory wipe to forget the results of the first.')


def generate(destination, count=1000, seed=80010):
    if not 10 <= count <= 100000:
        raise ValueError('Count must be 10-100000')
    destination = Path(destination)
    if destination.exists():
        raise ValueError('Use a new destination; existing files are preserved')
    rng = random.Random(seed)
    start = datetime(2026, 10, 18, tzinfo=timezone.utc)
    end = start + timedelta(days=2) - timedelta(seconds=1)
    groups = {source: [] for source in SOURCES}
    truth = []
    for index in range(count - 1):
        when = start if index == 0 else end if index == 1 else start + timedelta(seconds=rng.randrange(172800))
        if index in (2, 3, 4, 5):
            when = start + timedelta(hours={2: 8, 3: 8.1, 4: 25, 5: 36}[index])
        offset = rng.choice([-420, 0, 330, 540])
        text = when.astimezone(timezone(timedelta(minutes=offset))).isoformat()
        source = SOURCES[index % len(SOURCES)]
        special = {
            0: ('CALIBRATION_STARTED', 'Memory device calibration initiated.'),
            1: ('MEETING_RESTARTED', 'Management meeting restarted.'),
            2: ('EXPERIMENT_ACTIVATED', 'Experimental memory wipe activated.'),
            3: ('CONTAINMENT_STARTED', 'Emergency containment protocol initiated.'),
            4: ('BACKUP_RESTORED', 'IT backup restored.'),
            5: ('CAFETERIA_REOPENED', 'Employee cafeteria reopened.')}
        kind, description = special.get(index, ('ROUTINE_CHECK', 'Routine authorized system check completed.'))
        event = dict(event_id=f'EVT{index+1:06}', timestamp=text, source=source,
                     event_type=kind, description=description)
        groups[source].append(event);truth.append((when.isoformat(), event['event_id']))
    groups[RECOVERED['source']].append(dict(RECOVERED))
    truth.append(('2026-10-19T02:47:00+00:00', RECOVERED['event_id']))
    destination.mkdir(parents=True)
    for source, events in groups.items():
        rng.shuffle(events)
        (destination/(source.lower()+'.json')).write_text(json.dumps(events, indent=2)+'\n', encoding='utf-8')
    # Independent UTC timestamps created before offset conversion, outside logs.
    return dict(count=count, seed=seed, utc_by_id=dict((id, stamp) for stamp, id in truth),
                recovered=RECOVERED, earliest=start.isoformat(), latest=end.isoformat())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--count', type=int, default=1000)
    parser.add_argument('--seed', type=int, default=80010)
    args = parser.parse_args()
    manifest = generate(args.destination, args.count, args.seed)
    args.destination.with_name(args.destination.name+'-truth.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(f"Created {manifest['count']} fictional events in {args.destination}")
