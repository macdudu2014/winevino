import pandas as pd

# Remove duplicates from carrefour_wines.csv
print("Cleaning carrefour_wines.csv...")
df_carrefour = pd.read_csv('carrefour_wines.csv')
original_count = len(df_carrefour)
df_carrefour = df_carrefour.drop_duplicates()
df_carrefour.to_csv('carrefour_wines.csv', index=False)
print(f"  Removed {original_count - len(df_carrefour)} duplicates")
print(f"  {len(df_carrefour)} wines remaining")

# Remove duplicates from ah_wines.csv
print("\nCleaning ah_wines.csv...")
df_ah = pd.read_csv('ah_wines.csv')
original_count = len(df_ah)
df_ah = df_ah.drop_duplicates()
df_ah.to_csv('ah_wines.csv', index=False)
print(f"  Removed {original_count - len(df_ah)} duplicates")
print(f"  {len(df_ah)} wines remaining")

print("\n✅ All duplicates removed!")
