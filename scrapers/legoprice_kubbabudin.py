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
    enrich_with_lego_data,
    dedupe_products,
    extract_set_number,
)

def extract_products_from_soup(soup, lego_data):
    """Extract product details from the BeautifulSoup object."""
    product_cards = soup.select("div.product__BaseProductCardViewWrapper-sc-18rnnrl-0")
    products = []

    for card in product_cards:
        card_text = card.get_text(" ", strip=True)
        title_tag = card.select_one("h3, h2, .product-title, a")
        title_text = title_tag.get_text(" ", strip=True) if title_tag else card_text

        # ✅ Extract current (discounted or regular) price
        price_tag = card.select_one("strong.typopgraphy__DisplayBold24-sc-1qfpj1g-17.gXvSFa.price.rz-tg-display-bold-24")
        price = format_price_isk(price_tag.get_text(strip=True)) if price_tag else format_price_isk(card_text)

        # ✅ Extract original price if discounted
        original_price_tag = card.select_one("span.regular-price strike")
        original_price = format_price_isk(original_price_tag.get_text(strip=True)) if original_price_tag else None

        if not original_price:
            original_price = price

        # ✅ Extract LEGO set number from the SKU
        lego_set_number = None
        sku_tag = card.select_one("div.typopgraphy__Text16-sc-1qfpj1g-23.dtZOIa.sku.rz-tg-text-16")
        if sku_tag:
            sku_text = sku_tag.get_text(strip=True)
            if sku_text.startswith('LEGO'):
                lego_set_number = sku_text[4:].replace('ST', '')
        if not lego_set_number:
            lego_set_number = extract_set_number(card_text)

        product = {
            "kubbabudin_price": price,
            "lowest_price": price,
            "original_kubbabudin_price": original_price,
            "lego_set_number": lego_set_number,
            "name": title_text,
        }

        products.append(product)

    return products

def load_lego_data(csv_filename):
    """Load LEGO set data from a CSV file into a dictionary."""
    lego_data = {}
    with open(csv_filename, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            set_num = row[0].strip().split('-')[0]
            lego_data[set_num] = {
                'name': row[1].strip(),
                'num_parts': row[4].strip(),
            }
    return lego_data

def create_driver():
    """Create a new Selenium WebDriver instance with anti-scraping techniques."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.54 Safari/537.36"
    ]
    options.add_argument(f"user-agent={random.choice(user_agents)}")

    driver = webdriver.Chrome(options=options)
    return driver

def fetch_all_pages(csv_filename):
    """Fetch all pages of LEGO products and enrich data from CSV."""
    base_url = "https://kubbabudin.is/lego-pemu.html/facet=page-"
    lego_data = load_lego_data(csv_filename)
    driver = create_driver()
    driver.get(base_url + "1/sort-positionDesc")

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.pagination__BasePaginationWrapper-o7ce97-0'))
        )
        print("✅ First page loaded.")
    except:
        print("❌ Timed out waiting for the first page to load.")
        driver.quit()
        return []

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    pagination_buttons = driver.find_elements(By.CSS_SELECTOR, 'button')
    total_pages = 1
    for button in pagination_buttons:
        page_number = button.text.strip()
        if page_number.isdigit():
            total_pages = max(total_pages, int(page_number))

    print(f"Total pages found: {total_pages}")
    all_products = []

    for page_num in range(1, total_pages + 1):
        print(f"Scraping page {page_num}...")
        driver.get(base_url + str(page_num) + "/sort-positionDesc")
        time.sleep(random.uniform(3, 6))

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.product__BaseProductCardViewWrapper-sc-18rnnrl-0'))
            )
        except:
            print(f"❌ Timed out waiting for products on page {page_num}.")
            continue

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        products_on_page = extract_products_from_soup(soup, lego_data)

        print(f"Found {len(products_on_page)} products on page {page_num}")

        all_products.extend(products_on_page)

    all_products = [enrich_with_lego_data(product, lego_data, title_fallback=product.get('name')) for product in all_products]
    all_products = dedupe_products(all_products, ['lego_set_number', 'kubbabudin_price', 'name'])

    driver.quit()
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

    print(f"\nTotal {len(products)} LEGO products found across all pages.")

    sorted_products = sort_by_pieces_per_kr(products)

    if sorted_products:
        print(f"\nFirst 10 sorted products by price per piece:")
        for product in sorted_products[:10]:
            print(product)
            
        # Save all products to JSON file
        with open('data/store_products/kubbabudin_products.json', 'w', encoding='utf-8') as f:
            json.dump(sorted_products, f, ensure_ascii=False, indent=2)
        print("\nSaved all products to data/store_products/kubbabudin_products.json")
