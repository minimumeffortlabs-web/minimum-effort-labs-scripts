"""Deterministic fictional Accounting records and independent injected flag labels."""
import argparse
import csv
import json
from pathlib import Path
import random

FIELDS = ('invoice_id', 'vendor_id', 'invoice_date', 'currency', 'amount', 'description')
CONFIG = [('USD','Accounting USD policy',2),('EUR','Accounting EUR policy',2),
          ('GBP','Accounting GBP policy',2),('JPY','Accounting JPY policy',0),
          ('KWD','Accounting KWD policy',3)]
DESCRIPTIONS = ['Interdimensional portal maintenance','Temporal customs processing',
 'Alternate-reality shipping surcharge','Replacement containment field',
 'Dimensional visitor parking','Emergency portal stabilization',
 'Quantum freight inspection','Interdimensional office supplies']


def generate(directory, count=500, seed=79009):
    if not 1 <= count <= 100000:
        raise ValueError('Count must be between 1 and 100000')
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    rng=random.Random(seed);rows=[];expected=[]
    for i in range(1,count+1):
        code,_,places=CONFIG[(i-1)%len(CONFIG)]
        amount=str(rng.randint(10,9999)) + ('.'+'123'[:places] if places else '')
        row=dict(zip(FIELDS,[f'INV{i:05}',f'VEN{i:05}',f'2026-10-{(i-1)%28+1:02}',code,amount,rng.choice(DESCRIPTIONS)]));flags=set()
        if i%25==0:row['currency']=['CRY','VOID','ZRK'][(i//25)%3];flags.add('UNKNOWN_CURRENCY')
        if i%20==0:row['amount']=['NaN','-1','0','1.0000001'][(i//20)%4];flags.add('INVALID_AMOUNT')
        if i%30==0:row['invoice_date']='2026-02-30';flags.add('INVALID_DATE')
        if i%40==0:row['vendor_id']='';flags.add('MISSING_REQUIRED_FIELD')
        if i%70==0:row['invoice_id']='bad id';flags.add('INVALID_ID')
        rows.append(row);expected.append(flags)
    for a,b in [(2,3),(62,63),(102,103),(151,152)]:
        if b<=count:
            rows[b-1]['invoice_id']=rows[a-1]['invoice_id']
            expected[a-1].add('DUPLICATE_INVOICE_ID');expected[b-1].add('DUPLICATE_INVOICE_ID')
    for a,b in [(7,8),(47,48),(87,88),(25,26),(151,152)]:
        if b<=count:
            for key in FIELDS[1:]:rows[b-1][key]=rows[a-1][key]
            expected[b-1] |= expected[a-1]-{'DUPLICATE_INVOICE_ID','INVALID_ID'}
            expected[a-1].add('POSSIBLE_DUPLICATE_INVOICE');expected[b-1].add('POSSIBLE_DUPLICATE_INVOICE')
    for name,headers,items in [('invoices.csv',FIELDS,rows),('approved_currencies.csv',('currency_code','description','decimal_places'),[dict(zip(('currency_code','description','decimal_places'),item)) for item in CONFIG])]:
        with (directory/name).open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=headers);writer.writeheader();writer.writerows(items)
    manifest=dict(seed=seed,count=count,fictional=True,expected=[dict(row=i+1,flags=sorted(flags)) for i,flags in enumerate(expected)])
    (directory/'expected-labels.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);p.add_argument('--count',type=int,default=500);p.add_argument('--seed',type=int,default=79009);a=p.parse_args();generate(a.directory,a.count,a.seed)
