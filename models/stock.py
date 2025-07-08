from datetime import datetime, timedelta
import json

class Stock:
    def __init__(self, symbol, quantity, initial_price, purchase_price=None):
        self.symbol = symbol.upper()
        self.quantity = quantity
        self.initial_price = initial_price
        self.purchase_price = purchase_price if purchase_price is not None else initial_price
        self.current_price = initial_price
        self.change = 0
        self.change_percent = 0
        self.last_updated = datetime.now()
        self.purchase_date = datetime.now()
        
      
        self.daily_high = initial_price
        self.daily_low = initial_price
        self.volume = 0
        self.market_cap = 0
        self.pe_ratio = 0
        self.dividend_yield = 0
        
        self.price_history = []
        self.alerts = []
        self.notes = ""
      
        self.price_history.append({
            'timestamp': datetime.now(),
            'price': initial_price,
            'change': 0,
            'change_percent': 0
        })
    
    def update_price(self, new_price, volume=None, daily_high=None, daily_low=None):
        old_price = self.current_price
        self.current_price = new_price
        
       
        self.change = new_price - self.initial_price
        if self.initial_price > 0:
            self.change_percent = (self.change / self.initial_price) * 100
        
        
        if daily_high is not None:
            self.daily_high = daily_high
        else:
            self.daily_high = max(self.daily_high, new_price)
            
        if daily_low is not None:
            self.daily_low = daily_low
        else:
            self.daily_low = min(self.daily_low, new_price)
            
        if volume is not None:
            self.volume = volume
            
        self.last_updated = datetime.now()
        
        
        self.price_history.append({
            'timestamp': datetime.now(),
            'price': new_price,
            'change': new_price - old_price,
            'change_percent': ((new_price - old_price) / old_price * 100) if old_price > 0 else 0
        })
        
        
        if len(self.price_history) > 100:
            self.price_history = self.price_history[-100:]
    
    def update_fundamentals(self, market_cap=None, pe_ratio=None, dividend_yield=None):
        if market_cap is not None:
            self.market_cap = market_cap
        if pe_ratio is not None:
            self.pe_ratio = pe_ratio
        if dividend_yield is not None:
            self.dividend_yield = dividend_yield
    
    def get_current_value(self):
        return self.quantity * self.current_price
    
    def get_initial_value(self):
        return self.quantity * self.initial_price
    
    def get_purchase_value(self):
        return self.quantity * self.purchase_price
    
    def get_total_gain_loss(self):
        return (self.current_price - self.purchase_price) * self.quantity
    
    def get_total_gain_loss_percent(self):
        if self.purchase_price > 0:
            return ((self.current_price - self.purchase_price) / self.purchase_price) * 100
        return 0
    
    def get_day_gain_loss(self):
        if len(self.price_history) >= 2:
            today_start = self.price_history[-2]['price'] 
            return (self.current_price - today_start) * self.quantity
        return 0
    
    def get_day_gain_loss_percent(self):
        if len(self.price_history) >= 2:
            today_start = self.price_history[-2]['price']
            if today_start > 0:
                return ((self.current_price - today_start) / today_start) * 100
        return 0
    
    def get_price_range(self):
        return {
            'high': self.daily_high,
            'low': self.daily_low,
            'range': self.daily_high - self.daily_low,
            'range_percent': ((self.daily_high - self.daily_low) / self.daily_low * 100) if self.daily_low > 0 else 0
        }
    
    def get_performance_metrics(self):
        return {
            'current_price': self.current_price,
            'purchase_price': self.purchase_price,
            'current_value': self.get_current_value(),
            'purchase_value': self.get_purchase_value(),
            'total_gain_loss': self.get_total_gain_loss(),
            'total_gain_loss_percent': self.get_total_gain_loss_percent(),
            'day_gain_loss': self.get_day_gain_loss(),
            'day_gain_loss_percent': self.get_day_gain_loss_percent(),
            'price_range': self.get_price_range(),
            'volume': self.volume,
            'market_cap': self.market_cap,
            'pe_ratio': self.pe_ratio,
            'dividend_yield': self.dividend_yield
        }
    
    def add_alert(self, alert_type, threshold, message=""):
        alert = {
            'type': alert_type,  
            'threshold': threshold,
            'message': message,
            'created': datetime.now(),
            'triggered': False
        }
        self.alerts.append(alert)
    
    def check_alerts(self):
        triggered_alerts = []
        
        for alert in self.alerts:
            if alert['triggered']:
                continue
                
            should_trigger = False
            
            if alert['type'] == 'above' and self.current_price >= alert['threshold']:
                should_trigger = True
            elif alert['type'] == 'below' and self.current_price <= alert['threshold']:
                should_trigger = True
            elif alert['type'] == 'change_percent' and abs(self.change_percent) >= alert['threshold']:
                should_trigger = True
            
            if should_trigger:
                alert['triggered'] = True
                alert['triggered_at'] = datetime.now()
                triggered_alerts.append(alert)
        
        return triggered_alerts
    
    def get_recent_price_history(self, days=7):
        if not self.price_history:
            return []
        
 
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_history = [
            entry for entry in self.price_history 
            if entry['timestamp'] >= cutoff_date
        ]
        
        return recent_history
    
    def reset_daily_metrics(self):
        self.daily_high = self.current_price
        self.daily_low = self.current_price
        self.volume = 0
    
    def add_quantity(self, quantity, price=None):
        if price is None:
            price = self.current_price
            
      
        current_value = self.quantity * self.purchase_price
        new_value = quantity * price
        total_quantity = self.quantity + quantity
        
        if total_quantity > 0:
            self.purchase_price = (current_value + new_value) / total_quantity
        
        self.quantity = total_quantity
    
    def remove_quantity(self, quantity):
        if quantity >= self.quantity:
            self.quantity = 0
        else:
            self.quantity -= quantity
    
    def split_stock(self, ratio):
        self.quantity *= ratio
        self.purchase_price /= ratio
        self.current_price /= ratio
        self.initial_price /= ratio
        
  
        for entry in self.price_history:
            entry['price'] /= ratio
    
    def to_dict(self):
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'initial_price': self.initial_price,
            'purchase_price': self.purchase_price,
            'current_price': self.current_price,
            'change': self.change,
            'change_percent': self.change_percent,
            'last_updated': self.last_updated.isoformat(),
            'purchase_date': self.purchase_date.isoformat(),
            'daily_high': self.daily_high,
            'daily_low': self.daily_low,
            'volume': self.volume,
            'market_cap': self.market_cap,
            'pe_ratio': self.pe_ratio,
            'dividend_yield': self.dividend_yield,
            'price_history': [
                {
                    'timestamp': entry['timestamp'].isoformat(),
                    'price': entry['price'],
                    'change': entry['change'],
                    'change_percent': entry['change_percent']
                } for entry in self.price_history
            ],
            'alerts': self.alerts,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create stock from dictionary"""
        stock = cls(
            symbol=data['symbol'],
            quantity=data['quantity'],
            initial_price=data['initial_price'],
            purchase_price=data.get('purchase_price', data['initial_price'])
        )
        
        stock.current_price = data['current_price']
        stock.change = data['change']
        stock.change_percent = data['change_percent']
        stock.last_updated = datetime.fromisoformat(data['last_updated'])
        stock.purchase_date = datetime.fromisoformat(data['purchase_date'])
        
     
        stock.daily_high = data.get('daily_high', stock.current_price)
        stock.daily_low = data.get('daily_low', stock.current_price)
        stock.volume = data.get('volume', 0)
        stock.market_cap = data.get('market_cap', 0)
        stock.pe_ratio = data.get('pe_ratio', 0)
        stock.dividend_yield = data.get('dividend_yield', 0)
        stock.notes = data.get('notes', "")

        if 'price_history' in data:
            stock.price_history = [
                {
                    'timestamp': datetime.fromisoformat(entry['timestamp']),
                    'price': entry['price'],
                    'change': entry['change'],
                    'change_percent': entry['change_percent']
                } for entry in data['price_history']
            ]
        
   
        if 'alerts' in data:
            stock.alerts = data['alerts']
        
        return stock
    
    def __str__(self):
        return f"{self.symbol}: {self.quantity} shares @ ${self.current_price:.2f} ({self.change_percent:+.2f}%)"
    
    def __repr__(self):
        return f"Stock(symbol='{self.symbol}', quantity={self.quantity}, current_price={self.current_price:.2f})"