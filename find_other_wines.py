import json

# Load wines data
with open('static/wines.json', encoding='utf-8') as f:
    data = json.load(f)

# Find wines with "Other" type
other_wines = [w for w in data if w.get('type', '').lower() == 'other']

# Find wines with no Vivino rating (0, None, or missing)
no_rating_wines = [w for w in data if not w.get('vivino_score') or w.get('vivino_score') == 0]

print("=" * 80)
print(f"WINES WITH 'OTHER' TYPE ({len(other_wines)} total)")
print("=" * 80)
for i, wine in enumerate(other_wines, 1):
    print(f"{i}. {wine['name']}")
    print(f"   Store: {wine['store']}")
    print(f"   Price: €{wine['price']}")
    print(f"   Vivino Score: {wine.get('vivino_score', 'N/A')}")
    print(f"   URL: {wine.get('url', 'N/A')}")
    print()

print("\n" + "=" * 80)
print(f"WINES WITH NO VIVINO RATING ({len(no_rating_wines)} total)")
print("=" * 80)
for i, wine in enumerate(no_rating_wines, 1):
    print(f"{i}. {wine['name']}")
    print(f"   Type: {wine.get('type', 'N/A')}")
    print(f"   Store: {wine['store']}")
    print(f"   Price: €{wine['price']}")
    print(f"   URL: {wine.get('url', 'N/A')}")
    print()
