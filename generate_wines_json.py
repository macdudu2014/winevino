import pandas as pd
import json
import os

def generate_json():
    print("Loading wine data from CSVs...")
    
    wines = []
    
    # Load Carrefour wines
    if os.path.exists('carrefour_wines.csv'):
        try:
            cf_df = pd.read_csv('carrefour_wines.csv')
            # Add store column if it doesn't exist
            if 'store' not in cf_df.columns:
                cf_df['store'] = 'Carrefour'
            cf_wines = cf_df.to_dict('records')
            print(f"Loaded {len(cf_wines)} Carrefour wines")
            wines.extend(cf_wines)
        except Exception as e:
            print(f"Error loading Carrefour wines: {e}")
            
    # Load Albert Heijn wines
    if os.path.exists('ah_wines.csv'):
        try:
            ah_df = pd.read_csv('ah_wines.csv')
            ah_wines = ah_df.to_dict('records')
            print(f"Loaded {len(ah_wines)} Albert Heijn wines")
            wines.extend(ah_wines)
        except Exception as e:
            print(f"Error loading Albert Heijn wines: {e}")

    # Load Manual wines
    if os.path.exists('manual_wines.csv'):
        try:
            manual_df = pd.read_csv('manual_wines.csv')
            manual_wines = manual_df.to_dict('records')
            print(f"Loaded {len(manual_wines)} manual wines")
            wines.extend(manual_wines)
        except Exception as e:
            print(f"Error loading manual wines: {e}")
    
    # Clean up data (handle NaN, ensure types)
    cleaned_wines = []
    for wine in wines:
        clean_wine = {}
        for k, v in wine.items():
            # Handle NaN values
            if pd.isna(v):
                if k in ['price', 'vivino_score']:
                    clean_wine[k] = 0
                else:
                    clean_wine[k] = ""
            else:
                clean_wine[k] = v
        cleaned_wines.append(clean_wine)
    
    # Save to JSON
    output_file = 'static/wines.json'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_wines, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Successfully generated {output_file}")
        print(f"Total wines: {len(cleaned_wines)}")
        print(f"File size: {os.path.getsize(output_file) / 1024:.2f} KB")
        
    except Exception as e:
        print(f"Error saving JSON: {e}")

if __name__ == "__main__":
    generate_json()
