def format_currency(amount: float) -> str:
    """Format number as currency"""
    return f"${amount:,.2f}"

def format_percentage(percent: float) -> str:
    """Format number as percentage"""
    return f"{percent:+.2f}%"

def validate_stock_symbol(symbol: str) -> bool:
    """Validate stock symbol format"""
    return symbol.isalpha() and 1 <= len(symbol) <= 5

def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 0
    return ((new_value - old_value) / old_value) * 100