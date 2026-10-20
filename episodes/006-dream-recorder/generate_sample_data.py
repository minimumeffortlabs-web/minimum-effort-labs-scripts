"""Create a reproducible, explicitly fictional 300-transcript English fixture."""
import argparse
from pathlib import Path
import random

SEED = 76006
OPENINGS = ['I was flying above a quiet office.',
            'A talking printer invited me to lunch.',
            'I kept falling through a stack of calendars.',
            'A giant coffee cup was chasing me.',
            'I floated past an endless meeting.',
            'My manager had become a spreadsheet.']
MIDDLES = ['The expense reports covered every desk.',
           'Even the clouds carried expense reports.',
           'I had to alphabetize expense reports before sunrise.',
           'The printer demanded expense reports instead of paper.',
           'I opened a door and found more expense reports.',
           'My future self was delivering expense reports.']
ENDINGS = ['Missing receipts drifted past the window.',
           'A timesheet folded itself into an airplane.',
           'The office printer whispered about a corporate audit.',
           'There was coffee at the endless meeting.',
           'I woke up still looking for missing receipts.',
           'The elevator asked whether my timesheets were approved.']


def generate(directory, count=300, seed=SEED):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    rng = random.Random(seed)
    for number in range(1, count + 1):
        pieces = [rng.choice(OPENINGS), rng.choice(MIDDLES)]
        pieces += rng.sample(MIDDLES, k=rng.randint(1, 2))
        pieces += rng.sample(ENDINGS, k=2)
        # Distinct fictional details keep the fixture varied; no real people.
        pieces.append(rng.choice([f'The dream ended beside cabinet {number:03}.',
                                  f'My badge displayed code {number:03}.',
                                  f'The coffee mug showed number {number:03}.',
                                  f'A receipt listed department {number:03}.',
                                  f'The elevator stopped at floor {number:03}.',
                                  f'A folder carried label {number:03}.']))
        (directory / f'dream_{number:03}.txt').write_text(' '.join(pieces)+'\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory', type=Path)
    p.add_argument('--count', type=int, default=300)
    p.add_argument('--seed', type=int, default=SEED)
    a = p.parse_args()
    if a.count < 1:
        p.error('--count must be positive')
    generate(a.directory, a.count, a.seed)
