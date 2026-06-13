import csv
from pathlib import Path
p = Path(__file__).parents[1] / 'data' / 'question_bank.csv'
bad=[]
with p.open(encoding='utf-8') as f:
    reader = csv.reader(f)
    for i,row in enumerate(reader, start=1):
        if len(row) != 6:
            bad.append((i,len(row), row))

print(f"Checked: {p}\nTotal lines: {i}")
print('Bad rows count:', len(bad))
for idx,count,row in bad:
    print('LINE', idx, 'FIELDS', count, '->', row)
