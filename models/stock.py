from datetime import datetime

class Stock:
    def __init__(self, symbol, quantity, initial_price):
        self.symbol = symbol.upper()
        self.quantity = quantity
        self.initial_price = initial_price
        self.current_price = initial_price
        self.change = 0
        self.change_percent = 0
        self.last_updated = datetime.now()
    
    def update_price(self, new_price):
        self.current_price = new_price
        self.change = new_price - self.initial_price
        if self.initial_price > 0:
            self.change_percent = (self.change / self.initial_price) * 100
        self.last_updated = datetime.now()
    
    def get_current_value(self):
        return self.quantity * self.current_price
    
    def get_total_gain_loss(self):
        return (self.current_price - self.initial_price) * self.quantity
    
    def __str__(self):
        return f"{self.symbol}: {self.quantity} shares @ ${self.current_price:.2f}"