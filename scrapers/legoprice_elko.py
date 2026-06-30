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


def log_unresolved_products(products):
    missing = [p for p in products if not p.get('lego_set_number')]
    print(f"Unresolved set numbers: {len(missing)}/{len(products)}")
    for product in missing:
        print(f"  - {product.get('name', '')} | {product.get('elko_url') or product.get('url') or 'no-url'}")


def extract_set_number_from_title_end(title):
    text = str(title or '').strip()
    if not text:
        return None
    match = re.search(r"(\d{5,6})\s*$", text)
    if match:
        return match.group(1)
    return None


def extract_set_number_from_title(title):
    text = str(title or '').strip()
    if not text:
        return None

    match = re.search(r"\b(\d{5,6})\s+LEGO(?:\d{5,6}|[A-Z])", text, flags=re.IGNORECASE)
    if match:
        return match.group(1)

    match = re.search(r"\b(\d{5,6})\s*(?:\||$)", text)
    if match:
        return match.group(1)

    return extract_set_number_from_title_end(text)


def extract_price_text(text):
    matches = re.findall(r"(\d{1,3}(?:\.\d{3})*)\s*KR\.?", str(text or ''), flags=re.IGNORECASE)
    if not matches:
        return None
    return format_price_isk(f"{matches[-1]} kr")


def find_card_text_for_price(link):
    node = link
    for _ in range(7):
        if node is None:
            break
        text = ' '.join(node.stripped_strings)
        if extract_price_text(text):
            return text
        node = node.parent
    return ' '.join(link.stripped_strings)


def extract_products_from_soup(soup, lego_data):
    products = []
    product_links = soup.select('a[href*="/vorur/"]')

    for link in product_links:
        href = (link.get('href') or '').strip()
        if not href:
            continue
        product_url = href
        if product_url.startswith('/'):
            product_url = f"https://elko.is{product_url}"

        text = ' '.join(link.stripped_strings)
        if 'lego' not in text.lower():
            continue

        card_text = find_card_text_for_price(link)
        price_text = extract_price_text(card_text)
        if not price_text:
            continue
        # Skip out-of-stock items — Elko marks them with 'Uppselt' badge text
        if 'uppselt' in card_text.lower():
            continue

        title_text = re.sub(r"\d[\d\.\s]*\s*KR\.?", "", text, flags=re.IGNORECASE)
        title_text = re.sub(r"\s+", " ", title_text).strip(' |')
        if not title_text:
            continue

        lego_set_number = extract_set_number_from_title(title_text)
        if not lego_set_number:
            lego_set_number = extract_set_number(title_text)
        if not lego_set_number:
            lego_set_number = extract_set_number(product_url)
        if lego_set_number and lego_set_number not in lego_data:
            lego_set_number = None

        product = {
            "elko_price": price_text,
            "lowest_price": price_text,
            "lego_set_number": lego_set_number,
            "name": title_text,
            "url": product_url,
            "elko_url": product_url,
        }

        enrich_with_lego_data(product, lego_data, title_fallback=title_text)
        products.append(product)

    return products


def load_lego_data(csv_filename):
    lego_data = {}
    with open(csv_filename, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            set_num = row[0].strip().split('-')[0]
            lego_data[set_num] = {
                'name': row[1].strip(),
                'year': row[2].strip(),
                'theme_id': row[3].strip(),
                'num_parts': row[4].strip(),
                'img_url': row[5].strip(),
            }
    return lego_data


def create_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    ]
    options.add_argument(f"user-agent={random.choice(user_agents)}")
    return webdriver.Chrome(options=options)


def accept_cookies_if_present(driver):
    selectors = [
        "//button[contains(., 'Leyfa vafrakökur')]",
        "//button[contains(., 'Leyfa')]",
        "//button[contains(., 'Samþykkja')]",
    ]
    for selector in selectors:
        try:
            button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, selector))
            )
            driver.execute_script("arguments[0].click();", button)
            time.sleep(0.3)
            return
        except Exception:
            continue


def detect_total_pages(page_source):
    match = re.search(r"Síða\s+\d+\s+af\s+(\d+)", page_source)
    if match:
        return max(1, int(match.group(1)))
    return 1


def fetch_all_pages(csv_filename):
    base_url = "https://elko.is/voruflokkar/lego-67009"
    lego_data = load_lego_data(csv_filename)
    driver = create_driver()
    all_products = []

    try:
        driver.get(base_url)
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        accept_cookies_if_present(driver)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/vorur/"]'))
        )

        total_pages = detect_total_pages(driver.page_source)
        print(f"Found {total_pages} pages to scrape")

        for page_num in range(1, total_pages + 1):
            page_url = base_url if page_num == 1 else f"{base_url}?page={page_num}"
            print(f"Scraping page {page_num}/{total_pages}: {page_url}")
            driver.get(page_url)
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            accept_cookies_if_present(driver)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/vorur/"]'))
            )

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            page_products = extract_products_from_soup(soup, lego_data)
            all_products.extend(page_products)
            print(f"Found {len(page_products)} products on page {page_num}")
            time.sleep(random.uniform(0.2, 0.7))
    finally:
        driver.quit()

    all_products = dedupe_products(all_products, ['lego_set_number', 'elko_price', 'name'])
    log_unresolved_products(all_products)
    return all_products


def sort_by_pieces_per_kr(products):
    def calculate_value(product):
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

    return sorted(products, key=calculate_value, reverse=True)


if __name__ == "__main__":
    csv_filename = "data/sets.csv"
    products = fetch_all_pages(csv_filename)
    print(f"\nTotal {len(products)} LEGO products found.")

    sorted_products = sort_by_pieces_per_kr(products)

    if sorted_products:
        with open('data/store_products/elko_products.json', 'w', encoding='utf-8') as f:
            json.dump(sorted_products, f, ensure_ascii=False, indent=2)
        print("Saved all products to data/store_products/elko_products.json")