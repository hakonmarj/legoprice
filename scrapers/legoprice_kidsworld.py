import re
import time
import random
import csv
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from utils.price_utils import (
    parse_price_isk,
    format_price_isk,
    extract_set_number,
    enrich_with_lego_data,
    dedupe_products,
)

def extract_lego_set_number(title):
    """Extract the LEGO set number from the product title."""
    return extract_set_number(title)


def log_unresolved_products(products):
    missing = [p for p in products if not p.get('lego_set_number')]
    print(f"Unresolved set numbers: {len(missing)}/{len(products)}")
    for product in missing:
        print(f"  - {product.get('name', '')} | {product.get('kidsworld_url') or 'no-url'}")

def extract_products_from_soup(soup, lego_data):
    """Extract product details from the BeautifulSoup object."""
    product_cards = soup.select("div.product")
    products = []

    for card in product_cards:
        title = card.select_one("a.title")
        price = card.select_one("span.normalPrice")
        
        if not title or not price:
            continue
        # Skip out-of-stock cards (Kids World marks them with 'out-of-stock' class or similar text)
        card_classes = ' '.join(card.get('class', []))
        card_text = card.get_text(' ', strip=True)
        if 'out-of-stock' in card_classes.lower() or 'uppselt' in card_text.lower() or 'out of stock' in card_text.lower():
            continue
            
        title_text = title.get_text(strip=True)
        price_text = price.get_text(strip=True)
        href = title.get('href', '').strip()
        if href and href.startswith('/'):
            href = f"https://www.kids-world.com{href}"

        # Skip if price is missing or invalid
        formatted_price = format_price_isk(price_text)
        if not formatted_price or parse_price_isk(formatted_price) is None:
            continue
        
        # Extract LEGO set number from the title
        lego_set_number = extract_lego_set_number(title_text)
        if lego_set_number and lego_set_number not in lego_data:
            lego_set_number = None
        
        # Clean up the title by removing the set number and extra spaces
        if lego_set_number:
            title_text = re.sub(rf'\s*{lego_set_number}\s*', ' ', title_text)
        title_text = re.sub(r'\s+', ' ', title_text).strip()
        
        product = {
            "kidsworld_price": formatted_price,
            "lowest_price": formatted_price,
            "lego_set_number": lego_set_number,
            "name": title_text,
            "kidsworld_url": href or None,
        }

        enrich_with_lego_data(product, lego_data, title_fallback=title_text)
        
        products.append(product)

    return products

def load_lego_data(csv_filename):
    """Load LEGO set data from a CSV file into a dictionary."""
    lego_data = {}
    with open(csv_filename, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        for row in reader:
            set_num = row[0].strip().split('-')[0]
            lego_data[set_num] = {
                'name': row[1].strip(),
                'year': row[2].strip(),
                'theme_id': row[3].strip(),
                'num_parts': row[4].strip(),
                'img_url': row[5].strip()
            }
    return lego_data

def create_driver():
    """Create a new Selenium WebDriver instance with anti-scraping techniques."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0"
    ]
    options.add_argument(f"user-agent={random.choice(user_agents)}")
    
    driver = webdriver.Chrome(options=options)
    
    # Execute CDP commands to prevent detection
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": random.choice(user_agents)})
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })
    
    return driver

def fetch_all_pages(csv_filename):
    """Fetch all pages of LEGO products from Kids World."""
    base_url = "https://www.kids-world.com/is-is/lego-c-13090.html"
    lego_data = load_lego_data(csv_filename)
    driver = create_driver()
    all_products = []
    
    try:
        # Get first page
        driver.get(base_url)
        WebDriverWait(driver, 12).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # Wait for products to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.product"))
        )
        
        # Get total number of pages
        try:
            pagination = driver.find_element(By.CSS_SELECTOR, "div.pagination")
            page_links = pagination.find_elements(By.CSS_SELECTOR, "a.pagLink")
            page_numbers = set()
            for link in page_links:
                text = (link.text or '').strip()
                href = link.get_attribute('href') or ''
                if text.isdigit():
                    page_numbers.add(int(text))
                match = re.search(r"[?&]page=(\d+)", href)
                if match:
                    page_numbers.add(int(match.group(1)))
            total_pages = max(page_numbers) if page_numbers else 1
            print(f"Found {total_pages} pages to scrape")
        except Exception as e:
            print(f"⚠️ Pagination not found or failed: {e}. Will scrape only the first page.")
            total_pages = 1
        
        # Process each page
        for page in range(1, total_pages + 1):
            print(f"Scraping page {page}...")
            
            if page > 1:
                page_url = f"{base_url}?page={page}"
                driver.get(page_url)
                WebDriverWait(driver, 12).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                # Wait for products to load
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.product"))
                )
            
            # Extract products from current page
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            products = extract_products_from_soup(soup, lego_data)
            all_products.extend(products)
            
            print(f"Found {len(products)} products on page {page}")
            
            time.sleep(random.uniform(0.2, 0.6))
            
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
    finally:
        driver.quit()
    
    all_products = dedupe_products(all_products, ['lego_set_number', 'kidsworld_price', 'name'])
    log_unresolved_products(all_products)
    return all_products

def sort_by_pieces_per_kr(products):
    """Sort products by best value (pieces per króna)."""
    def calculate_pieces_per_kr(product):
        try:
            lowest_price = parse_price_isk(product.get('lowest_price'))
            num_parts = int(product.get('num_parts', -1))
            if num_parts <= 0 or not lowest_price:
                return float('inf')
            pieces_per_kr = num_parts / lowest_price
            product['pieces_per_kr'] = pieces_per_kr
            product['pieces_per_dollar'] = pieces_per_kr * 130.66
            return pieces_per_kr
        except (ValueError, TypeError):
            return float('inf')

    return sorted(products, key=calculate_pieces_per_kr, reverse=True)

if __name__ == "__main__":
    csv_filename = "data/sets.csv"
    products = fetch_all_pages(csv_filename)

    print(f"\nTotal {len(products)} LEGO products found.")

    sorted_products = sort_by_pieces_per_kr(products)

    if sorted_products:
        print(f"\nFirst 10 sorted products by price per piece:")
        for product in sorted_products[:10]:
            print(product)
            
        # Save all products to JSON file
        with open('data/store_products/kidsworld_products.json', 'w', encoding='utf-8') as f:
            json.dump(sorted_products, f, ensure_ascii=False, indent=2)
        print("\nSaved all products to data/store_products/kidsworld_products.json")