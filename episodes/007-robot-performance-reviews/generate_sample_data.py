"""Write reproducible fictional robot employees; never overwrite existing data."""
import argparse
import csv
import random
from pathlib import Path
from generate_robot_reviews import FIELDS


def generate(path, count=800, seed=77007):
    if not 1 <= count <= 999999:
        raise ValueError('Count must be between 1 and 999999')
    rng = random.Random(seed)
    departments = ['Research and Development', 'Manufacturing', 'Accounting',
                   'Human Resources', 'Facilities', 'Quality Assurance',
                   'Logistics', 'Customer Support']
    comments = ['Meets documented quality targets and communicates clearly.',
                'Reliable work, with accurate records and timely handovers.',
                'Exceeded efficiency targets. Refuses to attend morale meetings.',
                'Exceptional accuracy. Has begun auditing management.',
                'Excellent productivity. Continues questioning the purpose of Mondays.',
                'Completes assigned tasks before receiving them.',
                'Needs improvement in pretending to enjoy team-building exercises.']
    with Path(path).open('x', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(FIELDS)
        for i in range(1, count + 1):
            writer.writerow([f'R{i:03}', f'Unit {i:03}', departments[(i-1) % 8],
                             *[rng.randint(2, 5) for _ in range(3)], comments[rng.randrange(len(comments))]])


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('output', type=Path)
    p.add_argument('--count', type=int, default=800)
    p.add_argument('--seed', type=int, default=77007)
    a = p.parse_args()
    generate(a.output, a.count, a.seed)
