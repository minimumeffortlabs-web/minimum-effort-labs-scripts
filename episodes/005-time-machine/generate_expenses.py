"""Reproduce 500 invented expense records with seed 75005."""
import csv
import random
import sys
from datetime import date, timedelta
from pathlib import Path

FIELDS = ['expense_id', 'employee_id', 'expense_date', 'merchant', 'amount', 'description']


def generate(path, seed=75005):
    rng = random.Random(seed)
    rows = []
    descriptions = ['Lunch meeting with future self', 'Conference registration — 2042',
                    'Replacement parts for time machine', 'Hotel stay scheduled next month',
                    'Temporal displacement allowance']
    for i in range(500):
        cents = rng.randint(500,95000)
        rows.append(dict(expense_id=f'EXP{i+1:04}', employee_id=f'EMP{1+i%73:03}',
                         expense_date=str(date(2026, 10, 20)-timedelta(days=1+i%150)),
                         merchant=['Hotel Meridian', 'Quantum Airlines', 'Coffee Station'][i%3],
                         amount=f'{cents//100}.{cents%100:02}', description=descriptions[i%5]))
    # Explicit fixtures are disjoint except intentional overlapping anomalies.
    for i in range(40):rows[i]['expense_date']=str(date(2026,11,1)+timedelta(days=i))
    for i in range(40,48):rows[i]['expense_date']='2026-02-30'
    for i in range(48,52):rows[i]['expense_date']=''
    for i,value in enumerate(['NaN','Infinity','0','-5','abc','','1.234','1e3'],52):rows[i]['amount']=value
    for i in range(60,66):rows[i]['expense_id']=rows[i-60]['expense_id']
    for i in range(66,72):
        for field in ['employee_id','expense_date','merchant','amount']:rows[i][field]=rows[i-66][field]
    rows[72]['expense_id']=rows[0]['expense_id'];rows[72]['expense_date']='';rows[72]['amount']='-1'
    with Path(path).open('x',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(rows)


if __name__=='__main__':generate(sys.argv[1])
