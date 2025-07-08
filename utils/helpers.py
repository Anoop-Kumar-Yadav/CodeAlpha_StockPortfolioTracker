def format_currency(amount: float) -> str:
    return f"${amount:,.2f}"

def format_percentage(percent: float) -> str:
    return f"{percent:+.2f}%"

def validate_stock_symbol(symbol: str) -> bool:
    return symbol.isalpha() and 1 <= len(symbol) <= 5

def calculate_percentage_change(old_value: float, new_value: float) -> float:
    if old_value == 0:
        return 0
    return ((new_value - old_value) / old_value) * 100