from typing import List, Optional
from models.stock import Stock

class Portfolio:
    def __init__(self):
        self.stocks: List[Stock] = []
    
    def add_stock(self, symbol: str, quantity: int, price: float):
        # Check if stock already exists
        existing_stock = self.get_stock(symbol)
        if existing_stock:
            # Update quantity
            existing_stock.quantity += quantity
        else:
            # Add new stock
            stock = Stock(symbol, quantity, price)
            self.stocks.append(stock)
    
    def remove_stock(self, symbol: str):
        self.stocks = [stock for stock in self.stocks if stock.symbol != symbol.upper()]
    
    def get_stock(self, symbol: str) -> Optional[Stock]:
        for stock in self.stocks:
            if stock.symbol == symbol.upper():
                return stock
        return None
    
    def get_total_value(self) -> float:
        return sum(stock.get_current_value() for stock in self.stocks)
    
    def get_total_gain_loss(self) -> float:
        return sum(stock.get_total_gain_loss() for stock in self.stocks)
    
    def is_empty(self) -> bool:
        return len(self.stocks) == 0
    
    def __len__(self):
        return len(self.stocks)