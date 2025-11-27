import pandas as pd

# Read the CSV
df = pd.read_csv('carrefour_wines.csv')

# Find duplicates (all columns)
duplicates = df[df.duplicated(keep=False)].sort_values('name')

print(f'Total duplicate rows: {len(duplicates)}')
print(f'Total wines in file: {len(df)}')
print(f'Unique wines: {len(df) - len(duplicates) + len(duplicates.drop_duplicates())}')

if len(duplicates) > 0:
    print('\n' + '='*80)
    print('DUPLICATE WINES:')
    print('='*80)
    
    for name, group in duplicates.groupby('name'):
        print(f'\n"{name}" - appears {len(group)} times')
        print(f'  Price: €{group.iloc[0]["price"]}')
        print(f'  Type: {group.iloc[0]["type"]}')
        print(f'  Size: {group.iloc[0]["size"]}')
        print(f'  Line numbers: {", ".join(str(i+2) for i in group.index)}')  # +2 because of header and 0-indexing
else:
    print('\n✅ No duplicates found!')
