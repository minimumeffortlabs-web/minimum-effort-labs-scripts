"""Generate deterministic fictional email fixtures and independent expected labels."""
import argparse
from email.message import EmailMessage
from email import policy
import json
from pathlib import Path
import random

TEXT = {
 'FOOD_ACCESS_DENIED': ['The refrigerator denied my lunch request.', 'I cannot open the fridge to collect my lunch.', 'The appliance refused food because my rating was low.'],
 'INCORRECT_PERFORMANCE_RATING': ['My performance rating is outdated.', 'It used an incorrect employee score.', 'The evaluation is inaccurate and needs correction.'],
 'UNAUTHORIZED_EMPLOYEE_DATA_ACCESS': ["The refrigerator accessed my confidential employee records.", "Why does an appliance know my manager's confidential performance notes?", 'The fridge obtained private HR data without permission.'],
 'FOOD_DISPOSAL': ['The refrigerator threw out my sandwich.', 'It discarded my lunch before I arrived.', 'The appliance disposed of my yogurt.'],
 'UNEXPECTED_FRIDGE_BEHAVIOR': ['The refrigerator sends disciplinary warnings.', 'My sandwich has been placed on a performance improvement plan.', 'The fridge suggested leadership training.'],
 'OTHER': ['Please label the shelves more clearly.', 'I would like an additional vegetarian option.', 'The office needs more reusable lunch containers.'],
}


def generate(directory, count=400, seed=78008):
    if not 1 <= count <= 10000:
        raise ValueError('Count must be between 1 and 10000')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    rng = random.Random(seed)
    records = []
    names = list(TEXT)
    for i in range(1, count + 1):
        category = names[(i - 1) % len(names)]
        labels = [category]
        if category != 'OTHER' and rng.random() < .35:
            labels.append(rng.choice([x for x in names[:-1] if x != category]))
        body = ' '.join(rng.choice(TEXT[x]) for x in labels)
        body += f' This is fictional complaint {i:03}; café reference only.'
        m = EmailMessage(policy=policy.SMTP)
        m['From'] = f'Fictional Employee {i:03} <employee{i:03}@example.invalid>'
        m['To'] = 'fictional-hr@example.invalid'
        m['Date'] = 'Tue, 20 Oct 2026 09:00:00 +0000'
        m['Message-ID'] = f'<synthetic-{i:03}@example.invalid>'
        m['Subject'] = f'Fictional appliance complaint {i:03}'
        m.set_content(body, charset='iso-8859-1' if i % 11 == 0 else 'utf-8',
                      cte='quoted-printable' if i % 3 == 0 else 'base64')
        if i % 4 == 0:
            m.add_alternative('<p>Fictional HTML alternative. Links are not followed.</p>', subtype='html')
        if i % 7 == 0:
            m.add_attachment(b'Fictional attachment: denied lunch. Must not be classified.',
                             maintype='application', subtype='octet-stream', filename='ignore-this.bin')
        for index, part in enumerate(m.walk()):
            if part.is_multipart():
                part.set_boundary(f'mel-{seed}-{i}-{index}')
        filename=f'complaint_{i:03}.eml';(directory/filename).write_bytes(m.as_bytes())
        records.append(dict(filename=filename,expected_categories=[n for n in names if n in labels]))
    return records


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory',type=Path);p.add_argument('--count',type=int,default=400)
    p.add_argument('--seed',type=int,default=78008);p.add_argument('--manifest',type=Path)
    a=p.parse_args()
    if a.manifest and a.manifest.exists():p.error('Manifest already exists')
    records=generate(a.directory,a.count,a.seed)
    if a.manifest:
        with a.manifest.open('x',encoding='utf-8') as f:json.dump(dict(seed=a.seed,records=records),f,indent=2)
