"""
Albert Heijn Belgium Wine Scraper
Scrapes wine data from ah.be and saves to ah_wines.csv
"""
import pandas as pd
import time
import os
from ah_scraper import AlbertHeijnScraper
from vivino_scraper import VivinoScraper

def export_ah_wines():
    """Export Albert Heijn wines to CSV with Vivino scores"""
    print("=" * 60)
    print("ALBERT HEIJN WINE EXPORT SCRIPT")
    print("=" * 60)
    
    # Step 1: Scrape Albert Heijn
    print("\n[1/3] Scraping Albert Heijn for wines...")
    ah_scraper = AlbertHeijnScraper()
    wines = ah_scraper.get_wines()
    print(f"✓ Found {len(wines)} wines from Albert Heijn")
    
    if len(wines) == 0:
        print("No wines found. Exiting.")
        return
    
    # Step 2: Load existing scores to avoid re-scraping
    existing_scores = {}
    try:
        if os.path.exists('ah_wines.csv'):
            print("Loading existing scores from ah_wines.csv...")
            old_df = pd.read_csv('ah_wines.csv')
            if 'name' in old_df.columns and 'vivino_score' in old_df.columns:
                for _, row in old_df.iterrows():
                    if pd.notna(row['vivino_score']) and str(row['vivino_score']) != 'N/A':
                        existing_scores[row['name']] = row['vivino_score']
            print(f"✓ Loaded {len(existing_scores)} existing scores")
    except Exception as e:
        print(f"Could not load existing scores: {e}")
    
    # Merge existing scores
    wines_to_scrape = []
    for wine in wines:
        if wine['name'] in existing_scores:
            wine['vivino_score'] = existing_scores[wine['name']]
        else:
            wines_to_scrape.append(wine)
    
    print(f"\n[2/3] Fetching Vivino scores...")
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
    print("\n[3/3] Saving to ah_wines.csv...")
    
    # Remove 'id' field before saving if present
    for w in wines:
        if 'id' in w: del w['id']
        
    df = pd.DataFrame(wines)
    
    # Remove duplicates
    original_count = len(df)
    df = df.drop_duplicates()
    duplicates_removed = original_count - len(df)
    if duplicates_removed > 0:
        print(f"  Removed {duplicates_removed} duplicate wines")
    
    df.to_csv('ah_wines.csv', index=False, encoding='utf-8')
    print(f"✓ Saved {len(df)} wines to ah_wines.csv")
    
    print("\n" + "=" * 60)
    print("EXPORT COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    export_ah_wines()
