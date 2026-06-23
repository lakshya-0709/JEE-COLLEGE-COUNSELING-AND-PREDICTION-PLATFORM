import pandas as pd

df = pd.read_excel('2024Round5.xlsx')

institutes = df['Institute'].unique()
print(f'Total unique institutes: {len(institutes)}')
print('\nSample institutes:')
for i in institutes[:30]:
    print(f'  - {i}')

print('\n\nSample Programs:')
programs = df['Academic Program Name'].unique()
print(f'Total unique programs: {len(programs)}')
for p in programs[:30]:
    print(f'  - {p}')

# Check IIT vs NIT vs IIIT
nit = [i for i in institutes if 'National Institute of Technology' in i]
iiit = [i for i in institutes if 'Indian Institute of Information' in i or 'IIIT' in i]
iit = [i for i in institutes if 'Indian Institute of Technology' in i]
gfti = [i for i in institutes if i not in nit and i not in iiit and i not in iit]

print(f'\n\nIITs: {len(iit)}')
print(f'NITs: {len(nit)}')
print(f'IIITs: {len(iiit)}')
print(f'GFTIs: {len(gfti)}')

print('\nGFTI institutes:')
for g in gfti:
    print(f'  - {g}')
