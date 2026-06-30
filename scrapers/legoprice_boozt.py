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
        print(f"  - {product.get('name', '')} | {product.get('boozt_url') or 'no-url'}")

def extract_products_from_soup(soup, lego_data):
    """Extract product details from the BeautifulSoup object."""
    product_cards = soup.select("div.palette-product-card")
    products = []

    for card in product_cards:
        title = card.get("aria-label", "").strip()
        product_id = card.get("data-product-id", "")
        product_link = card.get("data-url", "")
        if product_link and product_link.startswith('/'):
            product_link = f"https://www.boozt.com{product_link}"

        # Current price: prefer data-actual-price attribute, fallback to visible price text
        price_text = card.get("data-actual-price") or ''
        if not price_text:
            price_span = card.select_one('.product-prices__price .typography--weight-bold')
            price_text = price_span.get_text(strip=True) if price_span else ''

        # Original price is often inside an <s> tag
        original_tag = card.select_one('s')
        original_text = original_tag.get_text(strip=True) if original_tag else ''

        # Normalize prices: '3.614 kr' -> '3614 kr'
        def normalize_price(pr_text):
            if not pr_text:
                return None
            m = re.search(r"[\d\.,]+", pr_text)
            if not m:
                return None
            digits = m.group(0)
            digits = digits.replace('.', '').replace(',', '')
            return f"{digits} kr"

        lowest_price = normalize_price(price_text)
        original_price = normalize_price(original_text)

        # Skip items with no price (sold out / unavailable)
        if not lowest_price:
            continue

        # Try to extract LEGO set number from title only
        lego_set_number = extract_lego_set_number(title)
        if lego_set_number and lego_set_number not in lego_data:
            lego_set_number = None

        product = {
            "boozt_price": format_price_isk(price_text),
            "lowest_price": lowest_price or (price_text and price_text + ' kr') or None,
            "original_boozt_price": original_price or None,
            "lego_set_number": lego_set_number,
            "name": title,
            "product_id": product_id,
            "boozt_url": product_link or None,
        }

        products.append(product)

    return products

def load_lego_data(csv_filename):
    """Load LEGO set data from a CSV file into a dictionary."""
    lego_data = {}
    with open(csv_filename, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        for row in reader:
            set_num = row[0].strip().split('-')[0]  # Ensure no leading/trailing whitespace
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
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Randomize the User-Agent to make requests appear legitimate
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.54 Safari/537.36"
    ]
    options.add_argument(f"user-agent={random.choice(user_agents)}")
    
    # Set options for handling potential anti-bot challenges
    driver = webdriver.Chrome(options=options)
    return driver

def fetch_all_pages(csv_filename):
    """Fetch all pages of LEGO products and lookup set data from CSV."""
    base_url = "https://www.boozt.com/is/is/born/leikfong/lego-leikfong?order=sale_asc&page="
    
    # Load LEGO set data from the CSV file
    lego_data = load_lego_data(csv_filename)
    
    driver = create_driver()
    driver.get(base_url + "1")  # Start with page 1

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.palette-pagination__dropdown button'))
        )
        # Wait for the pagination button to have non-empty text
        def button_has_text(driver):
            btn = driver.find_element(By.CSS_SELECTOR, 'div.palette-pagination__dropdown button')
            return bool(btn.text and '/' in btn.text)
        try:
            WebDriverWait(driver, 10).until(button_has_text)
            print("✅ First page loaded and pagination text found.")
        except Exception as e:
            print(f"⚠️ Pagination text not found: {e}. Will scrape only the first page.")
    except Exception as e:
        print(f"❌ Timed out waiting for the first page or pagination button: {e}")
        driver.quit()
        return []

    pagination_button = driver.find_element(By.CSS_SELECTOR, 'div.palette-pagination__dropdown button')
    # Use JS to get the actual text content
    page_text = driver.execute_script('return arguments[0].innerText;', pagination_button)
    import re
    total_pages = 1
    match = re.search(r'Síða \d+/(\d+)', page_text)
    if match:
        total_pages = int(match.group(1))
        print(f"✅ Extracted total pages from page_text: {total_pages}")
    else:
        print(f"⚠️ Could not extract total pages from: '{page_text}', defaulting to 1.")
    print(f"Total pages found: {total_pages}")

    all_products = []

    for page_num in range(1, total_pages + 1):
        print(f"Scraping page {page_num}/{total_pages}...")
        driver.get(base_url + str(page_num))
        # Wait for product cards to appear
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.palette-product-card'))
            )
        except Exception:
            print(f"❌ Timed out waiting for products on page {page_num}.")
            continue

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        products_on_page = extract_products_from_soup(soup, lego_data)
        print(f"Found {len(products_on_page)} products on page {page_num}")

        # Enrich with LEGO set data when possible
        all_products.extend(products_on_page)

    all_products = [enrich_with_lego_data(product, lego_data) for product in all_products]
    all_products = dedupe_products(all_products, ['product_id', 'lego_set_number', 'boozt_price', 'name'])
    log_unresolved_products(all_products)

    driver.quit()

    return all_products

def sort_by_pieces_per_kr(products):
    """Sort products by the best price per piece (lowest first)."""
    # Helper function to calculate price per piece
    def calculate_pieces_per_kr(product):
        try:
            lowest_price = parse_price_isk(product.get('lowest_price'))
            num_parts = int(product.get('num_parts', -1))  # Get number of parts, default to -1 if not found
            if num_parts <= 0 or not lowest_price:
                return float('inf')  # If num_parts is invalid, return an arbitrarily high price
            pieces_per_kr = num_parts / lowest_price
            product['pieces_per_kr'] = pieces_per_kr  # Add the price per piece to the product dictionary
            pieces_per_dollar = pieces_per_kr * 130.66
            product['pieces_per_dollar'] = pieces_per_dollar  # Add the price per piece to the product dictionary
            return pieces_per_kr
        except (ValueError, TypeError):
            return float('inf')  # Return a high value if price or num_parts is not valid

    # Sort products based on price per piece
    products_sorted = sorted(products, key=calculate_pieces_per_kr, reverse=True)
    return products_sorted

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
        with open('data/store_products/boozt_products.json', 'w', encoding='utf-8') as f:
            json.dump(sorted_products, f, ensure_ascii=False, indent=2)
        print("\nSaved all products to data/store_products/boozt_products.json")
