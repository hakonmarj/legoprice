import re
import time
import random
import csv
import json
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
try:
    import requests
except Exception:
    requests = None
from utils.price_utils import (
    parse_price_isk,
    format_price_isk,
    extract_set_number,
    enrich_with_lego_data,
    dedupe_products,
)

def find_best_set_match(title, lego_data):
    """Extract a strict LEGO set number from the title."""
    return extract_set_number(title)


def clean_title_from_card(card):
    title = None
    for tag in card.find_all(['h1', 'h2', 'h3', 'p', 'div', 'span']):
        text = tag.get_text(" ", strip=True)
        if not text:
            continue
        if 'lego' in text.lower() and 'kr' not in text.lower() and len(text) > 6:
            title = text
            break

    if not title:
        raw = card.get_text(" ", strip=True)
        title = re.sub(r"\d[\d\.,]*\s*kr\.?", "", raw, flags=re.IGNORECASE)
        title = re.sub(r"\b(Bæta við körfu|Skoða vöru|Setja á óskalista|UPPSELT Á VEF)\b", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\s+", " ", title).strip()
    title = re.sub(r"\b(Bæta við óskalista|Setja á óskalista|Bæta við körfu|Skoða vöru|UPPSELT Á VEF)\b", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def normalize_text(value):
    text = str(value or '').lower()
    text = re.sub(r"[^a-záðéíóúýþæö0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def match_set_by_name(title, lego_data):
    title_text = normalize_text(title)
    if not title_text:
        return None

    title_tokens = [token for token in title_text.split() if len(token) > 2 and token != 'lego']
    if not title_tokens:
        return None

    best_set = None
    best_score = 0.0
    second_best = 0.0

    for set_num, set_info in lego_data.items():
        name_tokens = [token for token in normalize_text(set_info.get('name')).split() if len(token) > 2]
        if not name_tokens:
            continue
        overlap = len(set(title_tokens) & set(name_tokens))
        score = overlap / max(1, len(set(name_tokens)))
        if score > best_score:
            second_best = best_score
            best_score = score
            best_set = set_num
        elif score > second_best:
            second_best = score

    if best_score >= 0.55 and (best_score - second_best) >= 0.15:
        return best_set
    return None


def click_load_more_until_done(driver, max_clicks=60):
    clicks = 0
    misses = 0
    while clicks < max_clicks and misses < 5:
        try:
            button = driver.execute_script(
                """
                const buttons = Array.from(document.querySelectorAll('button'));
                return buttons.find((button) => {
                    const txt = (button.innerText || button.textContent || '').toUpperCase();
                    const disabled = button.disabled || button.getAttribute('disabled') !== null;
                    return !disabled && txt.includes('SJÁ FLEIRI');
                }) || null;
                """
            )

            if not button:
                misses += 1
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(0.5)
                continue

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            time.sleep(0.15)
            driver.execute_script("arguments[0].click();", button)
            clicks += 1
            misses = 0
            print(f"🔄 Clicked 'Sjá fleiri vörur' ({clicks})")
            time.sleep(0.8)
        except Exception:
            misses += 1
            time.sleep(0.4)

    print(f"✅ Load-more loop finished after {clicks} clicks.")


def fetch_set_number_from_url(full_url, user_agent):
    if not requests:
        return full_url, None, "requests_not_available"
    try:
        response = requests.get(
            full_url,
            timeout=20,
            headers={
                "User-Agent": user_agent,
                "Accept-Language": "is-IS,is;q=0.9,en-US;q=0.8,en;q=0.7",
            },
        )
        response.raise_for_status()
        return full_url, extract_set_number(response.text), None
    except Exception as error:
        return full_url, None, str(error)

def extract_products_from_soup(soup, lego_data):
    """Extract product details from the BeautifulSoup object."""
    # Target the main grid container which holds product cards
    product_cards = []
    main = soup.select_one('#main-content')
    if main:
        grid = main.select_one('div.grid')
        if grid:
            # select anchors inside the grid; these are the product cards
            product_cards = grid.find_all('a', recursive=False)
    # Fallback to previous selector if grid selection didn't work
    if not product_cards:
        product_cards = soup.select('a.group')
    products = []

    for card in product_cards:
        title = clean_title_from_card(card)
        card_text = card.get_text(" ", strip=True)
        price = format_price_isk(card_text)
        # Try to find the best matching LEGO set
        lego_set_number = find_best_set_match(title, lego_data)
        if not lego_set_number:
            lego_set_number = match_set_by_name(title, lego_data)
        # Extract product link (relative href) to open later for exact set number
        href = card.get('href') or (card.select_one('a') and card.select_one('a').get('href'))
        product_url = href
        if not lego_set_number and product_url:
            lego_set_number = extract_set_number(product_url)
        product = {
            "hagkaup_price": price,
            "lowest_price": price,
            "lego_set_number": lego_set_number,
            "name": title,
            "url": product_url
        }
        # If we found a matching set, add its details
        enrich_with_lego_data(product, lego_data, title_fallback=title)
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

def scroll_and_collect(driver, lego_data):
    """Scroll through the page and collect all products."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    all_products = []
    max_scroll_attempts = 10
    scroll_attempts = 0
    
    while scroll_attempts < max_scroll_attempts:
        # Scroll to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(3, 5))
        
        # Wait for loading indicator to appear and disappear
        try:
            loading_indicator = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.absolute.top-0.bottom-0.left-0.right-0.flex.items-center.justify-center.transition-opacity.opacity-0"))
            )
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element(loading_indicator)
            )
        except:
            pass
        
        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            scroll_attempts += 1
        else:
            scroll_attempts = 0
        last_height = new_height
        
        # Extract products from current view
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        products = extract_products_from_soup(soup, lego_data)
        all_products.extend(products)
        
        print(f"Found {len(products)} products on current scroll")
        
        # Add a random delay between scrolls
        time.sleep(random.uniform(2, 4))
    
    return all_products

def fetch_all_pages(csv_filename):
    """Fetch all LEGO products from Hagkaup."""
    base_url = "https://www.hagkaup.is/leikfong/kubbar/lego"
    lego_data = load_lego_data(csv_filename)
    
    driver = create_driver()
    
    try:
        # Small jitter before first request
        time.sleep(random.uniform(0.2, 0.8))
        driver.get(base_url)
        WebDriverWait(driver, 12).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        # Try to accept cookie banner if present, including inside iframes
        try:
            # First, try main page
            buttons = driver.find_elements(By.XPATH, "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyzáéíóúýþæö', 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÝÞÆÖ'), 'LEYFA')]")
            if not buttons:
                # Try inside iframes
                for frame in driver.find_elements(By.TAG_NAME, 'iframe'):
                    driver.switch_to.frame(frame)
                    try:
                        buttons = driver.find_elements(By.XPATH, "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyzáéíóúýþæö', 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÝÞÆÖ'), 'LEYFA')]")
                        if buttons:
                            break
                    finally:
                        driver.switch_to.default_content()
            if buttons:
                buttons[0].click()
                print("✅ Clicked cookie consent button.")
                try:
                    WebDriverWait(driver, 8).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#main-content div.grid a"))
                    )
                except Exception:
                    print("⚠️ Product grid did not appear right after cookie click; continuing.")
            else:
                print("⚠️ Cookie consent button not found.")
        except Exception as ce:
            print(f"⚠️ Cookie consent button not found or not clickable: {ce}")
        grid_loaded = False
        for attempt in range(1, 4):
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#main-content div.grid a"))
                )
                grid_loaded = True
                print(f"✅ First page loaded (grid detected) on attempt {attempt}.")
                break
            except Exception:
                if attempt < 3:
                    driver.refresh()
                    WebDriverWait(driver, 10).until(
                        lambda d: d.execute_script("return document.readyState") == "complete"
                    )
        if not grid_loaded:
            print("⚠️ Grid anchor selector not found after retries.")
        # Log the number of product anchors found in the main grid container
        try:
            main_soup = BeautifulSoup(driver.page_source, 'html.parser')
            main_container = main_soup.select_one('#main-content')
            if main_container:
                grid = main_container.select_one('div.grid')
                if grid:
                    anchors = grid.select('a')
                    print(f"Detected {len(anchors)} product anchors inside the main grid.")
                else:
                    anchors = []
                    print("No grid element found inside #main-content; falling back to previous selectors.")
            else:
                anchors = []
                print("No #main-content container found; falling back to previous selectors.")
        except Exception as e:
            print(f"⚠️ Could not inspect grid container: {e}")
        click_load_more_until_done(driver)
        # After scrolling and loading, parse products ONCE from the final page source
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        all_products = extract_products_from_soup(soup, lego_data)
        print(f"Found {len(all_products)} products after all scrolling and loading.")

        base = 'https://www.hagkaup.is'
        user_agent = driver.execute_script("return navigator.userAgent;")
        indexed_jobs = []
        for index, product in enumerate(all_products, start=1):
            url = product.get('url')
            if not url:
                continue
            indexed_jobs.append((index, product, urljoin(base, url)))

        success_count = 0
        failure_count = 0
        futures = {}
        if requests and indexed_jobs:
            worker_count = min(10, len(indexed_jobs))
            with ThreadPoolExecutor(max_workers=worker_count) as executor:
                for index, product, full_url in indexed_jobs:
                    future = executor.submit(fetch_set_number_from_url, full_url, user_agent)
                    futures[future] = (index, product, full_url)

                processed = 0
                for future in as_completed(futures):
                    index, product, full_url = futures[future]
                    _, extracted_set, error = future.result()
                    if extracted_set:
                        product['lego_set_number'] = extracted_set
                        product['product_id'] = f"LEGO{extracted_set}"
                        success_count += 1
                    else:
                        failure_count += 1
                    processed += 1
                    if processed % 10 == 0 or processed == len(indexed_jobs):
                        print(
                            f"Checked {processed}/{len(indexed_jobs)} product URLs "
                            f"(set found: {success_count}, missing/failed: {failure_count})"
                        )
        else:
            for processed, (index, product, full_url) in enumerate(indexed_jobs, start=1):
                try:
                    driver.get(full_url)
                    time.sleep(random.uniform(1.2, 2.2))
                    extracted_set = extract_set_number(driver.page_source)
                    if extracted_set:
                        product['lego_set_number'] = extracted_set
                        product['product_id'] = f"LEGO{extracted_set}"
                        success_count += 1
                    else:
                        failure_count += 1
                except Exception:
                    failure_count += 1

                if processed % 10 == 0 or processed == len(indexed_jobs):
                    print(
                        f"Checked {processed}/{len(indexed_jobs)} product URLs "
                        f"(set found: {success_count}, missing/failed: {failure_count})"
                    )

        all_products = [enrich_with_lego_data(p, lego_data) for p in all_products]
        all_products = dedupe_products(all_products, ['url', 'hagkaup_price', 'name'])
    except Exception as e:
        print(f"❌ Error during scraping: {str(e)}")

        # Try to parse driver.page_source if available
        try:
            snippet = driver.page_source[:500]
            print("Page source snippet:\n" + snippet)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            all_products = extract_products_from_soup(soup, lego_data)
            print(f"⚠️ Fallback: Extracted {len(all_products)} products from current page source.")
            if all_products:
                return all_products
        except Exception as pse:
            print(f"⚠️ Could not parse driver.page_source: {pse}")

        # Final fallback: fetch static HTML via requests/urllib and parse that
        try:
            if requests:
                r = requests.get(base_url, timeout=15)
                text = r.text
                soup = BeautifulSoup(text, 'html.parser')
                all_products = extract_products_from_soup(soup, lego_data)
                print(f"⚠️ Static fetch fallback: Extracted {len(all_products)} products from static HTML.")
                return all_products
            return []
        except Exception as requests_error:
            print(f"⚠️ Static fallback failed: {requests_error}")
            return []
    finally:
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

    print(f"\nTotal {len(products)} LEGO products found.")

    sorted_products = sort_by_pieces_per_kr(products)

    if sorted_products:
        print(f"\nFirst 10 sorted products by price per piece:")
        for product in sorted_products[:10]:
            print(product)
            
        # Save all products to JSON file
        with open('data/store_products/hagkaup_products.json', 'w', encoding='utf-8') as f:
            json.dump(sorted_products, f, ensure_ascii=False, indent=2)
        print("\nSaved all products to data/store_products/hagkaup_products.json")