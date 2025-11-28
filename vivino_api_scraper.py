"""
Vivino API Scraper - Uses Vivino's official API (inspired by viviner library)
Much more reliable than HTML scraping!
"""
import requests
import time
import re
import difflib

class VivinoAPIScraper:
    def __init__(self):
        self.base_url = "https://www.vivino.com/api/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    def clean_wine_name(self, name):
        """Remove size indicators and clean the name"""
        # Remove common size indicators
        name = re.sub(r'\b\d+\s*(cl|ml|L|l)\b', '', name, flags=re.IGNORECASE)
        # Remove extra whitespace
        name = ' '.join(name.split())
        return name.strip()
    
    def extract_year(self, name):
        """Extract vintage year from wine name"""
        match = re.search(r'\b(19|20)\d{2}\b', name)
        return match.group(0) if match else None
    
    def search_wine(self, wine_name):
        """
        Search for a wine using Vivino's API
        Returns the best match with rating
        """
        clean_name = self.clean_wine_name(wine_name)
        target_year = self.extract_year(wine_name)
        
        print(f"Searching for: '{clean_name}' (Year: {target_year})")
        
        try:
            # Use Vivino's explore API with required parameters
            # Note: API requires at least one filter parameter
            params = {
                "q": clean_name,
                "page": 1,
                "language": "en",
                "min_rating": "1",  # Minimum filter required by API
            }
            
            url = f"{self.base_url}explore/explore"
            
            # Debug: print the request
            print(f"  Request URL: {url}")
            print(f"  Params: {params}")
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            # Debug: print response
            print(f"  Response status: {response.status_code}")
            if response.status_code != 200:
                print(f"  Response text: {response.text[:200]}")
            
            if response.status_code != 200:
                print(f"  API returned status {response.status_code}")
                return None
            
            data = response.json()
            
            # Extract matches
            if 'explore_vintage' not in data or 'matches' not in data['explore_vintage']:
                print(f"  No matches found in API response")
                return None
            
            matches = data['explore_vintage']['matches']
            
            if not matches:
                print(f"  No results found")
                return None
            
            print(f"  Found {len(matches)} results")
            
            # Analyze top 5 results
            best_match = None
            highest_ratio = 0.0
            
            for i, match in enumerate(matches[:5]):
                try:
                    vintage = match.get('vintage', {})
                    wine = vintage.get('wine', {})
                    statistics = vintage.get('statistics', {})
                    
                    result_name = wine.get('name', '')
                    rating = statistics.get('ratings_average')
                    ratings_count = statistics.get('ratings_count', 0)
                    
                    if not rating or ratings_count < 5:
                        print(f"    Result {i+1}: {result_name} - No rating or too few ratings")
                        continue
                    
                    # Calculate similarity
                    ratio = difflib.SequenceMatcher(None, clean_name.lower(), result_name.lower()).ratio()
                    
                    # Check year match
                    result_year = self.extract_year(result_name)
                    year_match = True
                    if target_year and result_year:
                        if target_year != result_year:
                            year_match = False
                            ratio -= 0.1
                    
                    print(f"    Result {i+1}: {result_name} | Rating: {rating} ({ratings_count} ratings) | Match: {ratio:.2f}")
                    
                    if ratio > highest_ratio and year_match:
                        highest_ratio = ratio
                        best_match = {
                            'name': result_name,
                            'rating': rating,
                            'ratings_count': ratings_count,
                            'match_ratio': ratio
                        }
                
                except Exception as e:
                    print(f"    Error parsing result {i}: {e}")
                    continue
            
            # Threshold for accepting a match
            if highest_ratio > 0.4 and best_match:
                print(f"  ✅ Selected: {best_match['name']} - Rating: {best_match['rating']} (Match: {highest_ratio:.2f})")
                return best_match['rating']
            else:
                print(f"  ❌ No good match found (best ratio: {highest_ratio:.2f})")
                return None
        
        except Exception as e:
            print(f"  Error: {e}")
            return None
    
    def get_score(self, wine_name):
        """Get Vivino score (compatible with old interface)"""
        rating = self.search_wine(wine_name)
        return str(rating) if rating else "N/A"


# Test
if __name__ == "__main__":
    scraper = VivinoAPIScraper()
    
    test_wines = [
        "Estandon Vignerons Terres de Saint-Louis Rosé 75cl",
        "Vin Blanc sec 3 L",
        "Château Margaux 2015",
    ]
    
    for wine in test_wines:
        print(f"\n{'='*60}")
        score = scraper.get_score(wine)
        print(f"Final Score: {score}")
        time.sleep(1)
