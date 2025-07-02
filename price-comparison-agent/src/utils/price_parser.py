def parse_price(price_str):
    """Parses a price string and returns a float value."""
    # Remove any currency symbols and commas
    price_str = price_str.replace('$', '').replace('£', '').replace(',', '').strip()
    try:
        return float(price_str)
    except ValueError:
        return None

def format_price(price):
    """Formats a float price to a standard string representation."""
    if price is not None:
        return f"${price:.2f}"
    return "Invalid price"

def extract_price_from_text(text):
    """Extracts the first price found in a given text."""
    import re
    # Regular expression to find prices
    price_pattern = r'(\$|£)?\d+(?:,\d{3})*(?:\.\d{2})?'
    match = re.search(price_pattern, text)
    if match:
        return parse_price(match.group(0))
    return None