"""
Vivino Score Enrichment Script
Reads existing wine CSVs and adds/updates Vivino scores without re-scraping the stores
"""
import pandas as pd
import time
from vivino_scraper import VivinoScraper

def enrich_csv_with_vivino(csv_file):
    """Enrich a CSV file with Vivino scores"""
    print(f"\n{'='*60}")
    print(f"Processing: {csv_file}")
    print(f"{'='*60}")
    
    # Load existing CSV
    print(f"\n[1/3] Loading {csv_file}...")
    df = pd.read_csv(csv_file)
    print(f"✓ Loaded {len(df)} wines")
    
    # Count wines needing scores
    wines_needing_scores = df # Scrape ALL wines
    print(f"\n[2/3] Wines to scrape (Force Update): {len(wines_needing_scores)}")
    
    if len(wines_needing_scores) == 0:
        print("✓ No wines found!")
        return
    
    # Estimate time
    estimated_minutes = len(wines_needing_scores) * 5 / 60
    print(f"⚠️  Estimated time: {estimated_minutes:.1f} minutes")
    print(f"    ({len(wines_needing_scores)} wines × ~5 seconds each)")
    
    # Scrape Vivino scores
    print(f"\n[3/3] Fetching Vivino scores...")
    with VivinoScraper() as vivino:
        for idx, row in wines_needing_scores.iterrows():
            wine_name = row['name']
            print(f"[{idx+1}/{len(df)}] Fetching score for: {wine_name}")
            
            score = vivino.get_score(wine_name)
            df.at[idx, 'vivino_score'] = score
            print(f"  → Score: {score}")
            
            time.sleep(2)  # Be respectful to Vivino
    
    # Save updated CSV
    print(f"\nSaving updated {csv_file}...")
    df.to_csv(csv_file, index=False, encoding='utf-8')
    print(f"✓ Saved {len(df)} wines with updated scores")

def main():
    """Main function to enrich both CSVs"""
    print("="*60)
    print("VIVINO SCORE ENRICHMENT SCRIPT")
    print("="*60)
    print("\nThis script will add Vivino scores to existing wine CSVs")
    print("without re-scraping the supermarket websites.")
    
    # Process Carrefour wines
    try:
        enrich_csv_with_vivino('carrefour_wines.csv')
    except FileNotFoundError:
        print("\n⚠️  carrefour_wines.csv not found, skipping...")
    except Exception as e:
        print(f"\n❌ Error processing carrefour_wines.csv: {e}")
    
    # Process Albert Heijn wines
    try:
        enrich_csv_with_vivino('ah_wines.csv')
    except FileNotFoundError:
        print("\n⚠️  ah_wines.csv not found, skipping...")
    except Exception as e:
        print(f"\n❌ Error processing ah_wines.csv: {e}")
    
    print("\n" + "="*60)
    print("ENRICHMENT COMPLETE!")
    print("="*60)
    print("\nRestart the Flask app to see wines with Vivino scores.")

if __name__ == "__main__":
    main()
