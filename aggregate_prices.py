import json
import re
from pathlib import Path

def load_store_data(store_name):
    """Load the JSON data from a store's output file."""
    file_path = Path(f"{store_name}_products.json")
    if not file_path.exists():
        print(f"Warning: No data found for {store_name}")
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_pieces_per_kr(product):
    """Calculate pieces per króna and pieces per dollar based on the lowest available price."""
    try:
        # Find the lowest non-None price
        prices = []
        
        # Handle Coolshop price
        coolshop_price = product.get('coolshop_price')
        if coolshop_price:
            prices.append(float(coolshop_price.replace(' kr', '').replace('.', '').replace(',', '.').strip()))
            
        # Handle Kubbabudin price
        kubbabudin_price = product.get('kubbabudin_price')
        if kubbabudin_price:
            prices.append(float(kubbabudin_price.replace(' kr', '').replace('.', '').replace(',', '.').strip()))
            
        # Handle Boozt price
        boozt_price = product.get('boozt_price')
        if boozt_price:
            prices.append(float(boozt_price.replace(' kr', '').replace('.', '').replace(',', '.').strip()))
            
        if not prices:
            return float('inf'), float('inf')
        
        lowest_price = min(prices)
        num_parts = int(product.get('num_parts', -1))
        if num_parts <= 0:
            return float('inf'), float('inf')
            
        pieces_per_kr = num_parts / (lowest_price * 1000)
        pieces_per_dollar = pieces_per_kr * 130.66  # Assuming 1 USD = 130.66 ISK
        return pieces_per_kr, pieces_per_dollar
    except (ValueError, TypeError):
        return float('inf'), float('inf')

def aggregate_prices():
    """Aggregate prices from all three stores and calculate best values."""
    # Load data from all stores
    coolshop_data = load_store_data('coolshop')
    kubbabudin_data = load_store_data('kubbabudin')
    boozt_data = load_store_data('boozt')
    
    # Create a dictionary to store aggregated data by set number
    aggregated_data = {}
    
    # Process Coolshop data
    for product in coolshop_data:
        set_num = product.get('lego_set_number')
        if not set_num:
            continue
            
        if set_num not in aggregated_data:
            aggregated_data[set_num] = {
                'lego_set_number': set_num,
                'name': product.get('name', ''),
                'num_parts': product.get('num_parts', '-1'),
                'coolshop_price': product.get('coolshop_price'),
                'kubbabudin_price': None,
                'boozt_price': None,
                'lowest_price': None
            }
        else:
            aggregated_data[set_num]['coolshop_price'] = product.get('coolshop_price')
    
    # Process Kubbabudin data
    for product in kubbabudin_data:
        set_num = product.get('lego_set_number')
        if not set_num:
            continue
            
        if set_num not in aggregated_data:
            aggregated_data[set_num] = {
                'lego_set_number': set_num,
                'name': product.get('name', ''),
                'num_parts': product.get('num_parts', '-1'),
                'coolshop_price': None,
                'kubbabudin_price': product.get('kubbabudin_price'),
                'boozt_price': None,
                'lowest_price': None
            }
        else:
            aggregated_data[set_num]['kubbabudin_price'] = product.get('kubbabudin_price')
    
    # Process Boozt data
    for product in boozt_data:
        set_num = product.get('lego_set_number')
        if not set_num:
            continue
            
        if set_num not in aggregated_data:
            aggregated_data[set_num] = {
                'lego_set_number': set_num,
                'name': product.get('name', ''),
                'num_parts': product.get('num_parts', '-1'),
                'coolshop_price': None,
                'kubbabudin_price': None,
                'boozt_price': product.get('boozt_price'),
                'lowest_price': None
            }
        else:
            aggregated_data[set_num]['boozt_price'] = product.get('boozt_price')
    
    # Calculate lowest price and value metrics for each set
    for set_num, data in aggregated_data.items():
        prices = [
            data['coolshop_price'],
            data['kubbabudin_price'],
            data['boozt_price']
        ]
        valid_prices = [p for p in prices if p is not None]
        if valid_prices:
            data['lowest_price'] = min(valid_prices)
            pieces_per_kr, pieces_per_dollar = calculate_pieces_per_kr(data)
            data['pieces_per_kr'] = pieces_per_kr
            data['pieces_per_dollar'] = pieces_per_dollar
    
    # Convert to list and filter out products with 0 or invalid brick counts
    aggregated_list = [
        product for product in aggregated_data.values()
        if product.get('num_parts') and product.get('num_parts') != '-1' 
        and int(product.get('num_parts', 0)) > 0
    ]
    
    # Sort by pieces per kr
    aggregated_list.sort(key=lambda x: x.get('pieces_per_kr', float('inf')), reverse=True)
    
    # Save to JSON file
    with open('aggregated_products.json', 'w', encoding='utf-8') as f:
        json.dump(aggregated_list, f, ensure_ascii=False, indent=2)
    
    # Print summary
    print(f"\nTotal {len(aggregated_list)} unique LEGO sets found across all stores.")
    print("\nTop 10 sets by value (pieces per kr):")
    for product in aggregated_list[:50]:
        print(f"\nSet {product['lego_set_number']}: {product['name']}")
        print(f"Pieces: {product['num_parts']}")
        print(f"Prices:")
        print(f"  Coolshop: {product['coolshop_price'] or 'Not available'}")
        print(f"  Kubbabudin: {product['kubbabudin_price'] or 'Not available'}")
        print(f"  Boozt: {product['boozt_price'] or 'Not available'}")
        print(f"  Lowest price: {product['lowest_price']}")
        print(f"  Pieces per kr: {product['pieces_per_kr']:.6f}")
        print(f"  Pieces per dollar: {product['pieces_per_dollar']:.6f}")

if __name__ == "__main__":
    aggregate_prices() 