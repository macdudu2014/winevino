import csv
import os
import json

# Define source files
SOURCE_FILES = ['carrefour_wines.csv', 'ah_wines.csv', 'manual_wines.csv']
TYPE_CORRECTION_FILE = 'wines_with_other_type.csv'
NO_RATING_FILE = 'wines_with_no_rating.csv'
WINES_JSON = 'mobile_build/wines.json'

def load_corrections():
    """Load both type and score corrections"""
    type_corrections = {}
    score_corrections = {}
    
    # Read corrections from wines_with_no_rating.csv
    if os.path.exists(NO_RATING_FILE):
        with open(NO_RATING_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                wine_name = row['Name']
                
                # Check both columns for corrections
                # Priority: CORRECTED SCORE column, then Current Vivino Score if it's not 0
                corrected_score = row.get('CORRECTED SCORE (write here)', '').strip()
                current_score = row.get('Current Vivino Score', '0').strip()
                
                # Use corrected score if available, otherwise use current score if it's not 0
                if corrected_score and corrected_score != '0':
                    score_corrections[wine_name] = corrected_score
                    print(f"  Found score correction for '{wine_name}': {corrected_score}")
                elif current_score and current_score != '0':
                    score_corrections[wine_name] = current_score
                    print(f"  Found score correction for '{wine_name}': {current_score}")
    
    # Read type corrections from wines_with_other_type.csv
    if os.path.exists(TYPE_CORRECTION_FILE):
        with open(TYPE_CORRECTION_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row['Name']
                corrected_type = row.get('CORRECTED TYPE (write here)', '').strip()
                current_type = row.get('Current Type', '').strip()
                
                if corrected_type:
                    type_corrections[name] = corrected_type
                elif current_type and current_type.lower() != 'other':
                    type_corrections[name] = current_type
                    
    return type_corrections, score_corrections

def update_csv_file(filename, type_corrections, score_corrections):
    """Update a CSV file with corrections"""
    if not os.path.exists(filename):
        return 0
        
    updated_rows = []
    updates_count = 0
    header = []
    
    with open(filename, 'r', encoding='utf-8', newline='') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return 0
            
        # Find column indices
        try:
            name_idx = header.index('name')
            type_idx = header.index('type')
            score_idx = header.index('vivino_score')
        except ValueError as e:
            print(f"⚠️ Could not find required column in {filename}: {e}")
            return 0
            
        updated_rows.append(header)
        
        for row in reader:
            if len(row) <= max(name_idx, type_idx, score_idx):
                updated_rows.append(row)
                continue
                
            name = row[name_idx]
            
            # Apply type correction
            if name in type_corrections:
                new_type = type_corrections[name]
                if row[type_idx] != new_type:
                    row[type_idx] = new_type
                    updates_count += 1
                    print(f"    Updated type for '{name}': {new_type}")
            
            # Apply score correction
            if name in score_corrections:
                new_score = score_corrections[name]
                if row[score_idx] != new_score:
                    row[score_idx] = new_score
                    updates_count += 1
                    print(f"    Updated score for '{name}': {new_score}")
            
            updated_rows.append(row)
            
    if updates_count > 0:
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(updated_rows)
            
    return updates_count

def update_wines_json(score_corrections):
    """Update wines.json with score corrections"""
    if not os.path.exists(WINES_JSON):
        print(f"⚠️ {WINES_JSON} not found")
        return 0
    
    with open(WINES_JSON, 'r', encoding='utf-8') as f:
        wines_data = json.load(f)
    
    updates_count = 0
    for wine in wines_data:
        name = wine.get('name')
        if name in score_corrections:
            new_score = score_corrections[name]
            old_score = wine.get('vivino_score', 'N/A')
            if str(old_score) != str(new_score):
                wine['vivino_score'] = new_score
                updates_count += 1
                print(f"    Updated JSON for '{name}': {old_score} -> {new_score}")
    
    if updates_count > 0:
        with open(WINES_JSON, 'w', encoding='utf-8') as f:
            json.dump(wines_data, f, indent=2, ensure_ascii=False)
    
    return updates_count

def main():
    print("🔄 Loading corrections...")
    type_corrections, score_corrections = load_corrections()
    print(f"\nFound {len(type_corrections)} type corrections and {len(score_corrections)} score corrections.\n")
    
    total_updates = 0
    
    # Update source CSV files
    for filename in SOURCE_FILES:
        print(f"Processing {filename}...")
        count = update_csv_file(filename, type_corrections, score_corrections)
        print(f"  -> Updated {count} wines")
        total_updates += count
    
    # Update wines.json
    print(f"\nUpdating {WINES_JSON}...")
    json_updates = update_wines_json(score_corrections)
    print(f"  -> Updated {json_updates} wines in JSON")
    total_updates += json_updates
        
    print(f"\n✅ Total updates applied: {total_updates}")

if __name__ == "__main__":
    main()
