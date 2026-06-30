import json
from pathlib import Path
from utils.price_utils import parse_price_isk, format_price_isk, is_valid_set_number


STORES = ['hagkaup', 'coolshop', 'kubbabudin', 'boozt', 'kidsworld']

def load_store_data(store_name):
    """Load the JSON data from a store's output file."""
    file_path = Path("data/store_products") / f"{store_name}_products.json"
    if not file_path.exists():
        print(f"Warning: No data found for {store_name}")
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def aggregate_cheapest_prices():
    """Aggregate LEGO set prices from all stores and find the cheapest price."""
    aggregated_data = {}

    for store in STORES:
        store_data = load_store_data(store)
        price_field = f"{store}_price"

        for product in store_data:
            set_num = str(product.get('lego_set_number') or '').strip()
            if not is_valid_set_number(set_num):
                continue

            normalized_price = format_price_isk(product.get(price_field))
            parsed_price = parse_price_isk(normalized_price)
            if parsed_price is None:
                continue
            
            if set_num not in aggregated_data:
                aggregated_data[set_num] = {
                    'lego_set_number': set_num,
                    'name': product.get('name', ''),
                    'num_parts': product.get('num_parts', '-1'),
                    'prices': {store: normalized_price},
                    'lowest_price': normalized_price,
                    'lowest_price_isk': parsed_price,
                    'lowest_price_store': store,
                }
            else:
                row = aggregated_data[set_num]
                row['prices'][store] = normalized_price
                if row.get('lowest_price_isk') is None or parsed_price < row['lowest_price_isk']:
                    row['lowest_price'] = normalized_price
                    row['lowest_price_isk'] = parsed_price
                    row['lowest_price_store'] = store

                if (not row.get('name') or row.get('name') == 'Unknown') and product.get('name'):
                    row['name'] = product.get('name')

                try:
                    current_parts = int(row.get('num_parts', -1))
                except (TypeError, ValueError):
                    current_parts = -1

                try:
                    incoming_parts = int(product.get('num_parts', -1))
                except (TypeError, ValueError):
                    incoming_parts = -1

                if incoming_parts > current_parts:
                    row['num_parts'] = str(incoming_parts)

    aggregated_list = [
        item for item in aggregated_data.values()
        if item.get('lowest_price_isk') is not None
    ]
    aggregated_list.sort(key=lambda item: item['lowest_price_isk'])

    output_path = Path('data/aggregated_cheapest_prices.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(aggregated_list, f, ensure_ascii=False, indent=2)

    print(f"\nTotal {len(aggregated_list)} unique LEGO sets aggregated by cheapest price.")
    print("Aggregated data saved to data/aggregated_cheapest_prices.json")

if __name__ == "__main__":
    aggregate_cheapest_prices()