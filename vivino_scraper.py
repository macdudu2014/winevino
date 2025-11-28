"""
Vivino Scraper - Extracts wine ratings from Vivino.com
"""
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import json
import time
import urllib.parse
import re
import difflib

class VivinoScraper:
    def __init__(self):
        self.base_url = "https://www.vivino.com"
        self.driver = None

    def start_browser(self):
        """Start the browser session"""
        if not self.driver:
            options = uc.ChromeOptions()
            # options.add_argument('--headless') 
            options.add_argument('--no-sandbox')
            
            self.driver = uc.Chrome(options=options)
            print("Vivino browser started (standard)")

    def close_browser(self):
        """Close the browser session"""
        if self.driver:
            try:
                self.driver.quit()
                print("Vivino browser closed")
            except:
                pass
            self.driver = None

    def clean_wine_name(self, name):
        """Clean wine name for better search results"""
        # Remove common container sizes and types
        name = re.sub(r'\b(75cl|750ml|1L|1\.5L|3L|Bag in Box|Bib)\b', '', name, flags=re.IGNORECASE)
        # Remove "alc." and percentage
        name = re.sub(r'\b\d+(\.\d+)?%\s*alc\b', '', name, flags=re.IGNORECASE)
        # Remove extra whitespace
        return re.sub(r'\s+', ' ', name).strip()

    def extract_year(self, name):
        """Extract vintage year from wine name"""
        match = re.search(r'\b(19|20)\d{2}\b', name)
        return match.group(0) if match else None

    def log(self, message):
        """Log message to file and console"""
        print(message)
        try:
            with open('scraper_debug.txt', 'a', encoding='utf-8') as f:
                f.write(f"{message}\n")
        except:
            pass

    def find_by_partial_class(self, element, partial_class, tag=None):
        """Find element where class contains partial_class"""
        if tag:
            return element.find(tag, class_=lambda x: x and partial_class in x)
        return element.find(class_=lambda x: x and partial_class in x)

    def get_score(self, wine_name):
        """Get Vivino score with fuzzy matching and multi-result analysis"""
        if not self.driver:
            raise Exception("Browser not started. Call start_browser() first.")
        
        # Clear log file on first call
        with open('scraper_debug.txt', 'w', encoding='utf-8') as f:
            f.write(f"--- Scraping '{wine_name}' ---\n")
            
        original_name = wine_name
        clean_name = self.clean_wine_name(wine_name)
        target_year = self.extract_year(wine_name)
        
        self.log(f"Searching for: '{clean_name}' (Year: {target_year})")
        
        try:
            search_url = f"{self.base_url}/search/wines?q={urllib.parse.quote_plus(clean_name)}"
            self.driver.get(search_url)
            time.sleep(3) # Wait for results to load
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Save HTML for debugging
            with open('page_source.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            # Find wine cards using partial class match (list comprehension method)
            all_divs = soup.find_all('div')
            cards = [div for div in all_divs if div.get('class') and any('wineCard__wineCard' in cls for cls in div.get('class', []))]
            
            self.log(f"Found {len(cards)} results")
            
            best_match = None
            highest_ratio = 0.0
            
            # Analyze top 5 results
            for i, card in enumerate(cards[:5]):
                try:
                    # Extract name
                    # Look for the link which usually contains the name
                    name_elem = self.find_by_partial_class(card, 'anchor_anchor', 'a')
                    if not name_elem:
                        # Fallback: look for any element with 'wineCard__name' or similar
                        name_elem = self.find_by_partial_class(card, 'wineCard__name')
                    
                    if not name_elem:
                        self.log(f"  Result {i+1}: Could not find name element")
                        continue
                        
                    result_name = name_elem.get_text(strip=True)
                    
                    # Extract rating
                    # Look for the rating number. It's usually a large number.
                    # We can look for a div with 'vivinoRating__averageValue' or similar
                    rating_elem = self.find_by_partial_class(card, 'averageValue')
                    if not rating_elem:
                        # Try finding text that looks like a rating (e.g. "3.7")
                        for elem in card.find_all(string=True):
                            if re.match(r'^\d\.\d$', elem.strip()):
                                score = elem.strip()
                                break
                        else:
                            score = "N/A"
                    else:
                        score = rating_elem.get_text(strip=True)
                        
                    # If score is not a number (e.g. "N/A" or empty), skip
                    try:
                        float(score.replace(',', '.'))
                    except ValueError:
                        self.log(f"  Result {i+1}: {result_name} | Score: {score} (Skipped - invalid score)")
                        continue

                    # Calculate similarity
                    # We compare the result name with the CLEANED name
                    ratio = difflib.SequenceMatcher(None, clean_name.lower(), result_name.lower()).ratio()
                    
                    # Check for year match if target year exists
                    result_year = self.extract_year(result_name)
                    year_match = True
                    if target_year and result_year:
                        if target_year != result_year:
                            year_match = False
                            ratio -= 0.1 # Penalize wrong year
                    
                    self.log(f"  Result {i+1}: {result_name} | Score: {score} | Match: {ratio:.2f}")
                    
                    if ratio > highest_ratio and year_match:
                        highest_ratio = ratio
                        best_match = score
                        
                except Exception as e:
                    self.log(f"  Error parsing result {i}: {e}")
                    continue
            
            # Threshold for accepting a match
            if highest_ratio > 0.4: 
                self.log(f"✅ Selected match with ratio {highest_ratio:.2f}: {best_match}")
                return str(best_match).replace(',', '.')
            else:
                self.log(f"❌ No good match found (best ratio: {highest_ratio:.2f})")
                return "N/A"

        except Exception as e:
            self.log(f"Vivino scraping error for '{wine_name}': {e}")
            return "N/A"
    
    def __enter__(self):
        """Context manager entry"""
        self.start_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close_browser()
