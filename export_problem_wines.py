import json
import csv

# Load wines data
with open('static/wines.json', encoding='utf-8') as f:
    data = json.load(f)

# Find wines with "Other" type
other_wines = [w for w in data if w.get('type', '').lower() == 'other']

# Find wines with no Vivino rating (0, None, or missing)
no_rating_wines = [w for w in data if not w.get('vivino_score') or w.get('vivino_score') == 0]

# Save wines with "Other" type - with correction column
with open('wines_with_other_type.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Name', 'Store', 'Price', 'Current Type', 'CORRECTED TYPE (write here)', 'Vivino Score', 'URL'])
    for wine in other_wines:
        writer.writerow([
            wine['name'],
            wine['store'],
            wine['price'],
            wine.get('type', 'Other'),
            '',  # Empty column for correction
            wine.get('vivino_score', 'N/A'),
            wine.get('url', 'N/A')
        ])

# Save wines with no rating - with correction column
with open('wines_with_no_rating.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Name', 'Type', 'Store', 'Price', 'Current Vivino Score', 'CORRECTED SCORE (write here)', 'URL'])
    for wine in no_rating_wines:
        writer.writerow([
            wine['name'],
            wine.get('type', 'N/A'),
            wine['store'],
            wine['price'],
            wine.get('vivino_score', 'N/A'),
            '',  # Empty column for correction
            wine.get('url', 'N/A')
        ])

print(f"✅ Created 'wines_with_other_type.csv' with {len(other_wines)} wines (column 5: CORRECTED TYPE)")
print(f"✅ Created 'wines_with_no_rating.csv' with {len(no_rating_wines)} wines (column 6: CORRECTED SCORE)")
print("\n📝 Instructions:")
print("   - Open the CSV files in Excel")
print("   - Fill in the empty 'CORRECTED' columns")
print("   - Save the files when done")
