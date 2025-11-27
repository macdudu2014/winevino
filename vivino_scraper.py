"""
Vivino Scraper - Extracts wine ratings from Vivino.com
"""
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import json
import time
import urllib.parse
import re

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
            print("Vivino browser started")

    def close_browser(self):
        """Close the browser session"""
        if self.driver:
            try:
                self.driver.quit()
                print("Vivino browser closed")
            except:
                pass
            self.driver = None

    def get_score(self, wine_name):
        """Get Vivino score for a wine. Browser must be started first."""
        if not self.driver:
            raise Exception("Browser not started. Call start_browser() first.")
        
        score = "N/A"
        try:
            search_url = f"{self.base_url}/search/wines?q={urllib.parse.quote_plus(wine_name)}"
            self.driver.get(search_url)
            time.sleep(2)
            
            # Try to read rating directly from search results
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            try:
                rating_container = soup.find('div', attrs={'class': re.compile(r"wineCard__ratingAndAddtoCart")})
                if rating_container:
                    text = rating_container.get_text(strip=True)
                    match = re.search(r"(\d{1,2}(?:[\\.,]\d)?)", text)
                    if match:
                        score = match.group(1).replace(',', '.')
                        return score
            except:
                pass
                
            # Fallback: Click first result
            try:
                first_card = soup.find('div', {'class': 'card'})
                if first_card:
                    link = first_card.find('a')['href']
                    self.driver.get(f"{self.base_url}{link}")
                    time.sleep(2)
                    
                    # Parse JSON-LD
                    page_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    script = page_soup.find('script', {'type': 'application/ld+json'})
                    if script:
                        data = json.loads(script.string)
                        score = data.get('aggregateRating', {}).get('ratingValue', 'N/A')
            except:
                pass

        except Exception as e:
            print(f"Vivino scraping error for '{wine_name}': {e}")
                    
        return str(score)
    
    def __enter__(self):
        """Context manager entry"""
        self.start_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close_browser()
