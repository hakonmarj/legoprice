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
import traceback
from utils.price_utils import parse_price_isk
try:
    import requests
except Exception:
    requests = None


def log_unresolved_products(products):
    missing = [p for p in products if not p.get('lego_set_number')]
    print(f"Unresolved set numbers: {len(missing)}/{len(products)}")
    for product in missing:
        print(f"  - {product.get('name', '')} | {product.get('coolshop_url') or 'no-url'}")

def extract_products_from_soup(soup, lego_data):
    # Tag-agnostic selector: matches <div class="product__card"> and <article class="product__card">
    product_cards = soup.select(".product__card")
    products = []

    for card in product_cards:
        # Get the full title from the title attribute of the link
        title_link = card.select_one("a.product__card-link")
        title = title_link.get('title', '') if title_link else ''
        if not title:
            title_tag = card.select_one("h3.product__card-title")
            title = title_tag.get_text(strip=True) if title_tag else ""
        href = title_link.get('href', '') if title_link else ''
        if href and href.startswith('/'):
            href = f"https://www.coolshop.is{href}"

        card_text = card.get_text(" ", strip=True).lower()
        if 'ekki til á lager' in card_text:
            continue
            
        price_tag = card.select_one("div.product__card-price")
        price = price_tag.get_text(strip=True).replace(' kr', '').replace('.', '').replace(',', '.').strip() if price_tag else None

        # Skip items with no price (sold out or unavailable)
        if not price:
            continue

        # Extract LEGO set number from title only
        set_numbers = re.findall(r'(\d{5})', title)
        lego_set_number = set_numbers[-1] if set_numbers else None
        if lego_set_number and lego_set_number not in lego_data:
            lego_set_number = None

        product = {
            "coolshop_price": price,
            "lowest_price": price,
            "original_coolshop_price": price,
            "lego_set_number": lego_set_number,
            "name": title,  # Store the full title for reference
            "coolshop_url": href or None,
        }

        if lego_set_number and lego_set_number in lego_data:
            product.update(lego_data[lego_set_number])
        else:
            product['num_parts'] = '-1'

        products.append(product)

    log_unresolved_products(products)
    return products

def load_lego_data(csv_filename):
    """Load LEGO set data from a CSV file into a dictionary."""
    lego_data = {}
    seen_set_numbers = set()  # Track which set numbers we've already processed
    
    with open(csv_filename, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for row in reader:
            set_num = row[0].strip().split('-')[0]
            # Only add the first occurrence of each set number
            if set_num not in seen_set_numbers:
                lego_data[set_num] = {
                    'name': row[1].strip(),
                    'num_parts': row[4].strip(),
                }
                seen_set_numbers.add(set_num)
    return lego_data

def create_driver():
    """Create a new Selenium WebDriver instance with anti-scraping techniques."""
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")  # Set a reasonable window size

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.54 Safari/537.36"
    ]
    options.add_argument(f"user-agent={random.choice(user_agents)}")

    driver = webdriver.Chrome(options=options)
    return driver

def scroll_and_collect(driver):
    """Scroll down the page to load all products until no more new content appears."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    last_product_count = 0
    current_product_count = 0
    scroll_attempts = 0
    max_attempts = 30
    timeout = 10
    scroll_pause_time = 1.5
    max_products = 1000  # Limit to 1000 products
    seen_products = set()

    while scroll_attempts < max_attempts and current_product_count < max_products:
        # Use generic class selector to match product cards regardless of tag
        current_product_count = len(driver.find_elements(By.CSS_SELECTOR, '.product__card'))
        if current_product_count == last_product_count:
            scroll_attempts += 1
        else:
            scroll_attempts = 0
        last_product_count = current_product_count

        # Check for "Hlaða fleiri vörum" button when we have 100 products
        if current_product_count >= max_products:
            print(f"\nReached maximum product limit of {max_products}")
            break
            
        if current_product_count % 100 == 0 and current_product_count > 0:
            print(f"\nReached {current_product_count} products, looking for load more button...")
            
            # First scroll to the very bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.6)
            
            try:
                # Find the button using the exact class structure
                load_more_button = driver.find_element(By.XPATH, 
                    "//span[contains(@class, 'cool-typography') and contains(text(), 'Hlaða fleiri vörum')]/..")
                
                print("Found load more button, attempting to click...")
                
                # Scroll the button into view and click
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_more_button)
                time.sleep(0.3)
                
                # Try to click with JavaScript first
                try:
                    driver.execute_script("arguments[0].click();", load_more_button)
                    print("Clicked load more button with JavaScript")
                except:
                    # Fall back to regular click
                    load_more_button.click()
                    print("Clicked load more button normally")
                
                WebDriverWait(driver, timeout).until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, '.product__card')) >= current_product_count
                )
                
                # Reset scroll attempts since we're loading more products
                scroll_attempts = 0
                continue
                
            except Exception as e:
                print(f"Could not find or click load more button: {str(e)}")

        # Regular scrolling logic
        current_height = driver.execute_script("return window.pageYOffset")
        scroll_amount = min(1000, last_height - current_height)
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        
        try:
            WebDriverWait(driver, timeout).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.loading, .spinner, .loader, [data-loading="true"]'))
            )
        except:
            pass

        time.sleep(scroll_pause_time)

        current_product_count = len(driver.find_elements(By.CSS_SELECTOR, '.product__card'))
        print(f"Products found: {current_product_count}")

        new_height = driver.execute_script("return document.body.scrollHeight")
        current_position = driver.execute_script("return window.pageYOffset + window.innerHeight")
        
        if current_position >= new_height and current_product_count == last_product_count:
            print("⚡ Reached bottom of page with no new products.")
            break

        if current_product_count == last_product_count:
            scroll_attempts += 1
            if scroll_attempts >= 3:
                print("⚡ No new products loaded after multiple attempts. Trying 'Hlaða fleiri vörum' button before giving up...")
                # Before giving up, try to find and click the 'Hlaða fleiri vörum' button
                try:
                    # Match the span text and click its parent (the clickable element)
                    load_more = driver.find_element(By.XPATH, "//span[contains(normalize-space(.), 'Hlaða fleiri vörum')]/..")
                    print("Found 'Hlaða fleiri vörum' element, attempting to click...")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_more)
                    time.sleep(0.2)
                    try:
                        driver.execute_script("arguments[0].click();", load_more)
                        print("Clicked load-more with JS")
                    except Exception:
                        load_more.click()
                        print("Clicked load-more with .click()")
                    WebDriverWait(driver, timeout).until(
                        lambda d: len(d.find_elements(By.CSS_SELECTOR, '.product__card')) >= current_product_count
                    )
                    # Reset attempts and continue scrolling to pick up new items
                    scroll_attempts = 0
                    last_product_count = current_product_count
                    continue
                except Exception as e:
                    print(f"Could not find or click 'Hlaða fleiri vörum' button: {e}")
                    print("No load-more button found; giving up on scrolling.")
                    break
        else:
            scroll_attempts = 0

        last_product_count = current_product_count
        last_height = new_height
        print(f"Scrolling... Attempt #{scroll_attempts + 1}")

    print(f"Finished scrolling after {scroll_attempts + 1} attempts. Found {current_product_count} products.")

    # After scrolling, deduplicate
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    products = extract_products_from_soup(soup, load_lego_data('data/sets.csv'))
    unique = []
    seen = set()
    for p in products:
        key = (p.get('lego_set_number'), p.get('name'))
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique

    # End of scroll_and_collect

def fetch_all_products(csv_filename):
    """Fetch all LEGO products from the coolshop site and enrich data from CSV."""
    base_url = "https://www.coolshop.is/leikfoeng/byggingaleikfoeng/bygginga-kubbasett/merki=lego/"
    lego_data = load_lego_data(csv_filename)
    driver = create_driver()
    
    print(f"\nTrying URL: {base_url}")
    driver.get(base_url)
    
    try:
        # Wait for and handle cookie consent banner with multiple selectors
        try:
            print("Waiting for cookie banner to appear...")
            time.sleep(0.6)
            
            # Try different selectors for the cookie consent button
            selectors = [
                "//button[contains(text(), 'Samþykkja allt')]",  # Correct text
                "//button[contains(@class, 'cookie')]",
                "//button[contains(@class, 'consent')]",
                "//div[contains(@class, 'cookie')]//button",
                "//div[contains(@class, 'consent')]//button"
            ]
            
            cookie_button = None
            for selector in selectors:
                try:
                    print(f"Trying selector: {selector}")
                    cookie_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if cookie_button:
                        print(f"Found button with selector: {selector}")
                        break
                except:
                    continue
            
            if cookie_button:
                # Scroll to the button if needed
                driver.execute_script("arguments[0].scrollIntoView(true);", cookie_button)
                time.sleep(0.2)
                
                # Try clicking with JavaScript if regular click fails
                try:
                    cookie_button.click()
                except:
                    driver.execute_script("arguments[0].click();", cookie_button)
                
                print("✅ Clicked cookie consent button")
                try:
                    WebDriverWait(driver, 5).until_not(
                        EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Samþykkja allt')]") )
                    )
                except Exception:
                    pass
            else:
                print("⚠️ Could not find cookie consent button with any selector")
        except Exception as e:
            print(f"⚠️ Error handling cookie consent: {str(e)}")

        # Wait for initial products (try longer + retry after refresh)
        try:
            # Quick debug: how many product cards are currently present in the DOM?
            try:
                dom_count = len(driver.find_elements(By.CSS_SELECTOR, '.product__card'))
                print(f"Debug: DOM currently has {dom_count} elements with class 'product__card'")
            except Exception:
                pass
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.product__card'))
            )
            print("✅ Initial page loaded")
        except Exception as e:
            print("⚠️ Timed out waiting for initial products (30s):", repr(e))
            traceback.print_exc()
            # Retry: refresh the page and try once more
            try:
                print("Refreshing page and retrying...")
                driver.refresh()
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.product__card'))
                )
                print("✅ Initial page loaded after refresh")
            except Exception as e2:
                print("⚠️ Still could not find product cards after refresh:", repr(e2))
                traceback.print_exc()
                raise
        # If the page is taking long to load, try closing common overlays and re-check
        try:
            # Try to close modal or overlays that may block products
            overlay_selectors = ["div.modal", "div.overlay", "div.cookie-banner", "div#onetrust-consent-sdk", "div#cookieModal", "div[data-modal='true']"]
            closed_overlay = False
            for sel in overlay_selectors:
                try:
                    elems = driver.find_elements(By.CSS_SELECTOR, sel)
                    if elems:
                        for el in elems:
                            try:
                                close_btn = el.find_element(By.XPATH, ".//button[contains(., '×') or contains(., 'X') or contains(., 'Loka') or contains(., 'Nei takk') or contains(., 'Close')]")
                                driver.execute_script("arguments[0].click();", close_btn)
                                print(f"Closed overlay using selector {sel}")
                                time.sleep(0.2)
                                closed_overlay = True
                                break
                            except Exception:
                                continue
                    if closed_overlay:
                        break
                except Exception:
                    continue
            # If we closed an overlay then wait again for product cards
            if closed_overlay:
                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.product__card'))
                    )
                    print("✅ Found product cards after closing an overlay")
                except Exception:
                    pass
        except Exception as e:
            print("⚠️ Error while attempting to close overlays:", repr(e))
            traceback.print_exc()

        # Scroll to load all products
        try:
            scroll_and_collect(driver)
        except Exception as e:
            print("⚠️ Error while scrolling to load products:", repr(e))
            traceback.print_exc()
            raise

        # Extract products from the page
        try:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            products = extract_products_from_soup(soup, lego_data)
            print(f"\nExtracted {len(products)} products")
        except Exception as e:
            print("⚠️ Error parsing products from page source:", repr(e))
            traceback.print_exc()
            raise
        
    except Exception as e:
        print(f"Error during product loading: {str(e)}")
        return []
    finally:
        driver.quit()
    
    return products

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
    products = fetch_all_products(csv_filename)

    print(f"\nTotal {len(products)} LEGO products found.")

    sorted_products = sort_by_pieces_per_kr(products)

    if sorted_products:
        print(f"\nFirst 10 sorted products by price per piece:")
        for product in sorted_products[:10]:
            print(product)
            
        # Save all products to JSON file
        with open('data/store_products/coolshop_products.json', 'w', encoding='utf-8') as f:
            json.dump(sorted_products, f, ensure_ascii=False, indent=2)
        print("\nSaved all products to data/store_products/coolshop_products.json")
