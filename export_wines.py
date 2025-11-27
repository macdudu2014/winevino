"""
Export script to scrape all wines from Carrefour, enrich with Vivino scores, and save to CSV.
Run this once to generate carrefour_wines.csv, then the app loads from the CSV.
"""
from cf_scraper import CarrefourScraper
from vivino_scraper import VivinoScraper
import pandas as pd
import time
import os

def export_wines():
    print("=" * 60)
    print("CARREFOUR WINE EXPORT SCRIPT")
    print("=" * 60)
    
    # Step 1: Scrape Carrefour
    print("\n[1/3] Scraping Carrefour for all wines...")
    carrefour = CarrefourScraper()
    wines = carrefour.get_wines()
    print(f"✓ Found {len(wines)} wines from Carrefour")
    
    if not wines:
        print("No wines found. Exiting.")
        return

    # Step 1.5: Load existing scores to avoid re-scraping
    existing_scores = {}
    try:
        if os.path.exists('carrefour_wines.csv'):
            print("Loading existing scores from carrefour_wines.csv...")
            old_df = pd.read_csv('carrefour_wines.csv')
            if 'name' in old_df.columns and 'vivino_score' in old_df.columns:
                for _, row in old_df.iterrows():
                    if pd.notna(row['vivino_score']) and str(row['vivino_score']) != 'N/A':
                        existing_scores[row['name']] = row['vivino_score']
            print(f"✓ Loaded {len(existing_scores)} existing scores")
    except Exception as e:
        print(f"Could not load existing scores: {e}")

    # Step 2: Enrich with Vivino scores
    print(f"\n[2/3] Fetching Vivino scores...")
    
    # Merge existing scores
    wines_to_scrape = []
    for wine in wines:
        if wine['name'] in existing_scores:
            wine['vivino_score'] = existing_scores[wine['name']]
        else:
            wines_to_scrape.append(wine)
            
    print(f"Need to scrape scores for {len(wines_to_scrape)} wines.")
    if wines_to_scrape:
        print("⚠️  Estimated time: {:.1f} minutes".format(len(wines_to_scrape) * 5 / 60))
    
    # Use context manager to keep browser open for all wines
    with VivinoScraper() as vivino:
        for i, wine in enumerate(wines, 1):
            if wine.get('vivino_score') == 'N/A':
                print(f"[{i}/{len(wines)}] Fetching score for: {wine['name']}")
                score = vivino.get_score(wine['name'])
                wine['vivino_score'] = score
                print(f"  → Score: {score}")
                time.sleep(2)  # Be respectful to Vivino
    
    # Step 3: Save to CSV
    print("\n[3/3] Saving to carrefour_wines.csv...")
    df = pd.DataFrame(wines)
    
    # Remove duplicates
    original_count = len(df)
    df = df.drop_duplicates()
    duplicates_removed = original_count - len(df)
    if duplicates_removed > 0:
        print(f"  Removed {duplicates_removed} duplicate wines")
    
    df.to_csv('carrefour_wines.csv', index=False, encoding='utf-8')
    print(f"✓ Saved {len(df)} wines to carrefour_wines.csv")
    
    print("\n" + "=" * 60)
    print("EXPORT COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    export_wines()
