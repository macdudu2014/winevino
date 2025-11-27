import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import time
import random
import urllib.parse
import re
import os

import html

def determine_wine_type(name):
    """Infer wine type from name."""
    name_lower = name.lower()
    if any(word in name_lower for word in ['rouge', 'red', 'merlot', 'cabernet', 'syrah', 'pinot noir']):
        return 'Red'
    elif any(word in name_lower for word in ['blanc', 'white', 'chardonnay', 'sauvignon']):
        return 'White'
    elif any(word in name_lower for word in ['rosé', 'rose']):
        return 'Rosé'
    elif any(word in name_lower for word in ['champagne', 'cava', 'prosecco', 'sparkling', 'crémant']):
        return 'Sparkling'
    return 'Other'

def determine_bottle_size(name):
    """Infer bottle size from name."""
    name_lower = name.lower()
    if '25cl' in name_lower or '25 cl' in name_lower:
        return '25cl'
    elif any(x in name_lower for x in ['3 l', '3l', 'bib', 'box', 'bag in box']):
        return 'Box'
    elif '75cl' in name_lower or '75 cl' in name_lower:
        return '75cl'
    return 'Other'


class CarrefourScraper:
    def __init__(self):
        self.base_url = "https://www.carrefour.be/fr/boissons/vins"
        self.mock_data_path = os.path.join(os.path.dirname(__file__), 'mock_data.json')

    def get_wines(self, search_term="wijn"):
        print(f"Scraping {self.base_url} with Selenium...")
        wines = []
        driver = None
        try:
            options = uc.ChromeOptions()
            # options.add_argument('--headless') # Run visible to bypass Cloudflare
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            driver = uc.Chrome(options=options)
            driver.get(self.base_url)
            time.sleep(5) # Wait for initial load
            
            # Handle cookies
            try:
                accept_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "onetrust-accept-btn-handler"))
                )
                accept_button.click()
                print("Cookies accepted.")
            except:
                print("Cookie banner not found or already accepted.")

            # Wait for products
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "js-product"))
                )
            except:
                print("Timeout waiting for products.")

            # Load all wines by clicking "Montrer plus de produits" button
            print("Loading all wines by clicking 'Montrer plus de produits'...")
            wines_loaded = 0
            max_clicks = 20  # Prevent infinite loop (514 wines / ~30 per page = ~17 clicks)
            
            for i in range(max_clicks):
                try:
                    # Wait a bit for content to load
                    time.sleep(2)
                    
                    # Count current wines
                    current_wines = len(driver.find_elements(By.CLASS_NAME, "js-product"))
                    if current_wines > wines_loaded:
                        print(f"Loaded {current_wines} wines so far...")
                        wines_loaded = current_wines
                    
                    # Find the "show-more" button (French: "Montrer plus de produits")
                    show_more_buttons = driver.find_elements(By.CLASS_NAME, "show-more")
                    
                    if show_more_buttons and show_more_buttons[0].is_displayed():
                        # Scroll to button first
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", show_more_buttons[0])
                        time.sleep(1)
                        
                        # Click the button
                        show_more_buttons[0].click()
                        print(f"Clicked 'Montrer plus de produits' button (click {i+1})")
                        time.sleep(3)  # Wait for new products to load
                    else:
                        print(f"No more 'show-more' button found after {i} clicks")
                        break
                        
                except Exception as e:
                    print(f"Error clicking show more: {e}")
                    print(f"Finished loading after {i} clicks")
                    break
            
            print(f"Finished loading. Total wines on page: {wines_loaded}")

            # Parse content
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            products = soup.find_all('div', {'class': 'product js-product'})
            
            if not products:
                # Fallback to generic selector if specific class not found
                products = soup.select(".product-card, article")

            print(f"Found {len(products)} products.")

            for product in products:
                try:
                    # Try legacy parsing logic first (data attribute)
                    product_tile = product.select_one('.product-tile')
                    if product_tile and product_tile.get('data-select-item-event-object'):
                        raw_json = product_tile.get('data-select-item-event-object')
                        # Unescape HTML entities in JSON string
                        decoded_json = html.unescape(raw_json)
                        event_data = json.loads(decoded_json)
                        item = event_data.get('ecommerce', {}).get('items', [{}])[0]
                        name = item.get('item_name', 'N/A')
                        price = str(item.get('price', 'N/A'))
                        
                        # Find the product link (avoid wishlist button)
                        link_elem = product.select_one('.pdp-link a') or product.select_one('.image-container a')
                        link = link_elem['href'] if link_elem else "#"
                        
                        # Find image URL
                        img_elem = product.select_one('.product-card__image img, .image-container img')
                        image_url = "https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg"
                        if img_elem:
                            image_url = img_elem.get('src') or img_elem.get('data-src') or image_url
                            
                    else:
                        # Fallback to DOM parsing
                        name = product.select_one(".product-card__title, h3").get_text(strip=True)
                        price = product.select_one(".product-card__price, .price").get_text(strip=True)
                        link_elem = product.find('a')
                        link = link_elem['href'] if link_elem else "#"
                        
                        # Find image URL
                        img_elem = product.select_one('img')
                        image_url = "https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg"
                        if img_elem:
                            image_url = img_elem.get('src') or img_elem.get('data-src') or image_url

                    wines.append({
                        "name": name,
                        "price": price,
                        "url": "https://www.carrefour.be" + link if link.startswith("/") else link,
                        "image_url": image_url,
                        "type": determine_wine_type(name),
                        "size": determine_bottle_size(name),
                        "vivino_score": "N/A"
                    })
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"Selenium scraping error: {e}")
            wines = self.load_mock_data()
        finally:
            if driver:
                try:
                    with open("selenium_dump.html", "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    print("Saved HTML to selenium_dump.html")
                    driver.quit()
                except:
                    pass
        
        if not wines:
            print("No wines found. Loading mock data.")
            wines = self.load_mock_data()
            
        return wines

    def load_mock_data(self):
        if os.path.exists(self.mock_data_path):
            with open(self.mock_data_path, 'r') as f:
                return json.load(f)
        return []


if __name__ == "__main__":
    scraper = CarrefourScraper()
    print(json.dumps(scraper.get_wines(), indent=2))

