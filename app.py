from flask import Flask, render_template, jsonify, request
import json
from cf_scraper import CarrefourScraper
from vivino_scraper import VivinoScraper
import threading
import pandas as pd
import os

app = Flask(__name__)
carrefour_scraper = CarrefourScraper()
vivino_scraper = VivinoScraper()

# Cache for wines to avoid re-scraping on every request
wine_cache = []

def load_wines_from_csv():
    """Load wine data from CSVs."""
    all_wines = []
    seen_urls = set()  # Track URLs to avoid duplicates
    
    # Load Carrefour wines
    if os.path.exists('carrefour_wines.csv'):
        print("Loading wines from carrefour_wines.csv...")
        df = pd.read_csv('carrefour_wines.csv')
        if 'name' in df.columns:
            for _, row in df.iterrows():
                url = row.get('url', '#')
                # Skip if we've already seen this URL (duplicate)
                if url in seen_urls or url == '#':
                    continue
                seen_urls.add(url)
                all_wines.append(process_wine_row(row, 'Carrefour'))
    
    # Load Albert Heijn wines
    if os.path.exists('ah_wines.csv'):
        print("Loading wines from ah_wines.csv...")
        df = pd.read_csv('ah_wines.csv')
        if 'name' in df.columns:
            for _, row in df.iterrows():
                url = row.get('url', '#')
                # Skip if we've already seen this URL (duplicate)
                if url in seen_urls or url == '#':
                    continue
                seen_urls.add(url)
                all_wines.append(process_wine_row(row, 'Albert Heijn'))
                
    print(f"Total loaded wines: {len(all_wines)}")
    return all_wines

def process_wine_row(row, store_name):
    """Helper to process a CSV row into a wine object"""
    # Handle NaN values
    score = row.get('vivino_score', 'N/A')
    if pd.isna(score): score = "N/A"
    
    price = row.get('price', 'N/A')
    if pd.isna(price): price = "N/A"
    
    image_url = row.get('image_url', 'https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg')
    if pd.isna(image_url): image_url = "https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg"
    
    wine_type = row.get('type', 'Other')
    if pd.isna(wine_type): wine_type = 'Other'
    
    size = row.get('size', 'Other')
    if pd.isna(size): size = 'Other'

    return {
        "name": row['name'],
        "price": price,
        "url": row.get('url', '#'),
        "image_url": image_url,
        "vivino_score": score,
        "type": wine_type,
        "size": size,
        "store": store_name
    }

def update_cache():
    global wine_cache
    print("Updating wine cache...")
    
    # Load from CSV (names only)
    wines = load_wines_from_csv()
    
    wine_cache = wines
    print(f"Wine cache updated with {len(wines)} wines.")

PAIRINGS_FILE = 'pairings.json'

def load_pairings():
    if os.path.exists(PAIRINGS_FILE):
        try:
            with open(PAIRINGS_FILE, 'r') as f:
                data = json.load(f)
                # Migration: If values are lists, convert to dicts
                migrated = {}
                for k, v in data.items():
                    if isinstance(v, list):
                        migrated[k] = {"pairings": v, "description": ""}
                    else:
                        migrated[k] = v
                return migrated
        except json.JSONDecodeError:
            return {}
    return {}

def save_pairings(pairings):
    with open(PAIRINGS_FILE, 'w') as f:
        json.dump(pairings, f, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/wine/<path:wine_name>')
def wine_detail(wine_name):
    global wine_cache
    if not wine_cache:
        update_cache()
        
    # Find wine
    wine = next((w for w in wine_cache if w['name'] == wine_name), None)
    if not wine:
        return "Wine not found", 404
        
    # Merge pairings and description
    pairings_data = load_pairings()
    wine_data = pairings_data.get(wine['name'], {"pairings": [], "description": ""})
    wine['pairings'] = wine_data.get('pairings', [])
    wine['description'] = wine_data.get('description', "")
    
    return render_template('wine_detail.html', wine=wine)

@app.route('/api/wines')
def get_wines():
    global wine_cache
    if not wine_cache:
        update_cache()
    
    pairings_data = load_pairings()
    wines = []
    for w in wine_cache:
        wine_copy = w.copy()
        # Handle both old (list) and new (dict) formats just in case, though load_pairings handles migration
        p_data = pairings_data.get(w['name'], {"pairings": [], "description": ""})
        wine_copy['pairings'] = p_data.get('pairings', [])
        wine_copy['description'] = p_data.get('description', "")
        wines.append(wine_copy)
    
    # Filter by store if specified
    store_filter = request.args.get('store', 'all')
    if store_filter != 'all':
        wines = [w for w in wines if w.get('store', '').lower() == store_filter.lower()]
    
    sort_by = request.args.get('sort', 'price-low')
    
    if sort_by == 'price-low':
        def get_price(w):
            try:
                return float(str(w['price']).replace('€', '').replace(',', '.').strip())
            except (ValueError, TypeError):
                return 99999.0
        wines.sort(key=get_price)
    elif sort_by == 'price-high':
        def get_price(w):
            try:
                return float(str(w['price']).replace('€', '').replace(',', '.').strip())
            except (ValueError, TypeError):
                return 0.0
        wines.sort(key=get_price, reverse=True)
    elif sort_by == 'score':
        def get_score(w):
            try:
                return float(w['vivino_score'])
            except (ValueError, TypeError):
                return 0.0
        wines.sort(key=get_score, reverse=True)
        
    return jsonify(wines)

@app.route('/api/pairings', methods=['POST'])
def update_pairing():
    data = request.json
    wine_name = data.get('name')
    
    if not wine_name:
        return jsonify({"error": "Invalid data"}), 400
        
    all_pairings = load_pairings()
    
    # Get existing data or initialize
    current_data = all_pairings.get(wine_name, {"pairings": [], "description": ""})
    
    # Update fields if present
    if 'pairings' in data:
        current_data['pairings'] = data['pairings']
    if 'description' in data:
        current_data['description'] = data['description']
        
    all_pairings[wine_name] = current_data
    save_pairings(all_pairings)
    
    return jsonify({"status": "success", "data": current_data})

@app.route('/api/refresh')
def refresh():
    thread = threading.Thread(target=update_cache)
    thread.start()
    return jsonify({"status": "refreshing"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
