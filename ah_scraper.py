"""
Albert Heijn Scraper - Simplified DOM-based approach
Uses the same pattern as CarrefourScraper for consistency
"""
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import time
from cf_scraper import determine_wine_type, determine_bottle_size

class AlbertHeijnScraper:
    def __init__(self):
        self.category_urls = [
            "https://www.ah.be/producten/21613/witte-wijn",      # White wine
            "https://www.ah.be/producten/21539/rose",             # Rosé
            "https://www.ah.be/producten/21532/rode-wijn",        # Red wine
            "https://www.ah.be/producten/23522/bubbels-en-mousserende-wijn"  # Sparkling
        ]
        
    def get_wines(self):
        """Scrape wines from all categories using Selenium + BeautifulSoup"""
        print("Starting Albert Heijn scraper...")
        all_wines = []
        seen_urls = set()  # Simple deduplication by URL
        driver = None
        
        try:
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            # options.add_argument('--headless')  # Keep visible to avoid detection
            
            driver = uc.Chrome(options=options)
            
            # Handle cookies once at the start
            driver.get(self.category_urls[0])
            time.sleep(5)
            try:
                cookie_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accepteren') or contains(text(), 'Accept') or contains(text(), 'accepteren')]"))
                )
                cookie_btn.click()
                print("Cookies accepted.")
                time.sleep(2)
            except:
                print("No cookie banner found.")

            # Scrape each category
            for url in self.category_urls:
                print(f"\nScraping URL: {url}")
                driver.get(url)
                time.sleep(5)
                
                # Click "meer resultaten" button to load all wines
                print("  Loading all products by clicking 'meer resultaten'...")
                products_loaded = 0
                max_clicks = 30
                
                for i in range(max_clicks):
                    try:
                        time.sleep(2)
                        
                        # Count current products
                        current_products = len(driver.find_elements(By.TAG_NAME, "article"))
                        if current_products > products_loaded:
                            print(f"  Loaded {current_products} products so far...")
                            products_loaded = current_products
                        
                        # Find the "meer resultaten" button
                        meer_buttons = driver.find_elements(By.CSS_SELECTOR, "[data-testid='load-more']")
                        if not meer_buttons:
                            meer_buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Meer resultaten') or contains(., 'meer resultaten')]")
                        
                        if meer_buttons:
                            # Check if button is displayed - if not, try JavaScript click
                            btn = meer_buttons[0]
                            # Scroll to button
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                            time.sleep(1)
                            
                            # Click the button using JavaScript to avoid visibility issues
                            driver.execute_script("arguments[0].click();", btn)
                            print(f"  Clicked 'meer resultaten' button (click {i+1})")
                            time.sleep(3)
                        else:
                            print(f"  No more 'meer resultaten' button found after {i} clicks")
                            break
                            
                    except Exception as e:
                        print(f"  Error clicking load more: {e}")
                        print(f"  Finished loading after {i} clicks")
                        break
                
                print(f"  Finished loading. Total products on page: {products_loaded}")
                
                # Parse content with BeautifulSoup
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                products = soup.find_all('article')
                
                print(f"  Found {len(products)} article elements")
                
                for product in products:
                    try:
                        # Extract name - try multiple selectors
                        name_elem = product.select_one("[data-testid='product-title']")
                        if not name_elem:
                            name_elem = product.select_one("h3")
                        if not name_elem:
                            name_elem = product.select_one(".title")
                        
                        if not name_elem:
                            continue
                            
                        name = name_elem.get_text(strip=True)
                        
                        # Extract price
                        price = "N/A"
                        price_elem = product.select_one("[data-testid='price-amount']")
                        if not price_elem:
                            price_elem = product.select_one(".price-amount")
                        if price_elem:
                            price = price_elem.get_text(strip=True).replace('€', '').strip()
                        
                        # Extract URL
                        link = "#"
                        link_elem = product.find('a')
                        if link_elem:
                            link = link_elem.get('href', '#')
                        
                        if link.startswith('/'):
                            link = f"https://www.ah.be{link}"
                        
                        # Skip if we've seen this URL before (deduplication)
                        if link in seen_urls or link == "#":
                            continue
                        
                        seen_urls.add(link)
                        
                        # Extract image
                        image_url = "https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg"
                        img_elem = product.select_one("img")
                        if img_elem:
                            image_url = img_elem.get('src', image_url)
                        
                        all_wines.append({
                            "name": name,
                            "price": price,
                            "url": link,
                            "image_url": image_url,
                            "type": determine_wine_type(name),
                            "size": determine_bottle_size(name),
                            "vivino_score": "N/A",
                            "store": "Albert Heijn"
                        })
                        
                    except Exception as e:
                        # Skip products that fail to parse
                        continue
                
                category_count = len(all_wines) - len([w for w in all_wines if w not in all_wines[-products_loaded:]])
                print(f"  Extracted {len(all_wines)} total wines so far")
                        
        except Exception as e:
            print(f"Selenium scraping error: {e}")
        finally:
            if driver:
                try:
                    with open("ah_selenium_dump.html", "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    print("Saved HTML to ah_selenium_dump.html")
                    driver.quit()
                except:
                    pass
        
        print(f"\nTotal unique wines scraped: {len(all_wines)}")
        return all_wines

if __name__ == "__main__":
    scraper = AlbertHeijnScraper()
    wines = scraper.get_wines()
    print(json.dumps(wines[:5], indent=2))
