"""Deterministic synthetic survey fixture. No real customers or scientific evidence."""
import csv
import random
from pathlib import Path


def generate(folder, seed=74004):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    before, after = [], []
    for i in range(1, 251):
        customer = f'C{i:03d}'
        old = rng.randint(7, 10)
        new = old if i % 13 == 0 else (min(10, old + 1) if i % 29 == 0 else rng.randint(1, 5))
        if i <= 245:
            before.append([customer, old])
        if i > 5:
            after.append([customer, new])
    # Disjoint invalid examples and one duplicate: the entire ID is excluded.
    after[20][1] = ''
    after[40][1] = 'eleven'
    after[60][1] = 11
    after.append(['C100', 2])
    for name, rows in [('before.csv', before), ('after.csv', after)]:
        with (folder/name).open('w', encoding='utf-8', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(['customer_id', 'satisfaction_rating'])
            writer.writerows(rows)
    return before, after


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    parser.add_argument('--seed', type=int, default=74004)
    args = parser.parse_args()
    generate(args.folder, args.seed)
