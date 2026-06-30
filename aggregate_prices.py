import json
from pathlib import Path
from utils.price_utils import parse_price_isk, format_price_isk, is_valid_set_number


STORES = ['hagkaup', 'coolshop', 'kubbabudin', 'boozt', 'kidsworld', 'elko']


def load_store_data(store_name):
    file_path = Path('data/store_products') / f'{store_name}_products.json'
    if not file_path.exists():
        print(f'Warning: No data found for {store_name}')
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_pieces_per_kr(product):
    prices = []
    for store in STORES:
        value = product.get(f'{store}_price')
        parsed = parse_price_isk(value)
        if parsed is not None:
            prices.append(parsed)

    if not prices:
        return float('inf'), float('inf')

    lowest_price = min(prices)
    try:
        num_parts = int(product.get('num_parts', -1))
    except (TypeError, ValueError):
        return float('inf'), float('inf')

    if num_parts <= 0:
        return float('inf'), float('inf')

    pieces_per_kr = num_parts / lowest_price
    pieces_per_dollar = pieces_per_kr * 130.66
    return pieces_per_kr, pieces_per_dollar


def aggregate_prices():
    aggregated_data = {}

    for store in STORES:
        store_data = load_store_data(store)
        price_field = f'{store}_price'
        url_field = f'{store}_url'

        for product in store_data:
            set_num = str(product.get('lego_set_number') or '').strip()
            if not is_valid_set_number(set_num):
                continue

            normalized_price = format_price_isk(product.get(price_field))
            if normalized_price is None:
                continue

            if set_num not in aggregated_data:
                aggregated_data[set_num] = {
                    'lego_set_number': set_num,
                    'name': product.get('name', ''),
                    'num_parts': product.get('num_parts', '-1'),
                    'lowest_price': None,
                    'lowest_price_isk': None,
                    'lowest_price_store': None,
                }
                for s in STORES:
                    aggregated_data[set_num][f'{s}_price'] = None
                    aggregated_data[set_num][f'{s}_url'] = None

            row = aggregated_data[set_num]
            row[price_field] = normalized_price

            candidate_url = product.get(url_field) or product.get('url')
            if candidate_url and not row.get(url_field):
                row[url_field] = candidate_url

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

            parsed_price = parse_price_isk(normalized_price)
            if parsed_price is None:
                continue
            if row.get('lowest_price_isk') is None or parsed_price < row['lowest_price_isk']:
                row['lowest_price'] = normalized_price
                row['lowest_price_isk'] = parsed_price
                row['lowest_price_store'] = store

    aggregated_list = []
    for product in aggregated_data.values():
        try:
            parts = int(product.get('num_parts', 0))
        except (TypeError, ValueError):
            parts = 0
        if parts <= 0:
            continue

        pieces_per_kr, pieces_per_dollar = calculate_pieces_per_kr(product)
        product['pieces_per_kr'] = pieces_per_kr
        product['pieces_per_dollar'] = pieces_per_dollar
        aggregated_list.append(product)

    aggregated_list.sort(key=lambda x: x.get('pieces_per_kr', float('inf')), reverse=True)

    output_path = Path('data/aggregated_products.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(aggregated_list, f, ensure_ascii=False, indent=2)

    print(f'\nTotal {len(aggregated_list)} unique LEGO sets found across all stores.')
    print('Aggregated data saved to data/aggregated_products.json')


if __name__ == '__main__':
    aggregate_prices()
