import yfinance as yf
from typing import Optional, Dict,List
import time

class StockService:
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 60  # Cache for 1 minute
    
    def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """Fetch stock data from Yahoo Finance"""
        try:
            # Check cache first
            cache_key = symbol.upper()
            current_time = time.time()
            
            if (cache_key in self.cache and 
                current_time - self.cache[cache_key]['timestamp'] < self.cache_timeout):
                return self.cache[cache_key]['data']
            
            # Fetch from yfinance
            stock = yf.Ticker(symbol)
            info = stock.info
            hist = stock.history(period="2d")
            
            if hist.empty:
                return None
            
            current_price = hist['Close'].iloc[-1]
            
            # Calculate change
            change = 0
            change_percent = 0
            if len(hist) > 1:
                prev_price = hist['Close'].iloc[-2]
                change = current_price - prev_price
                change_percent = (change / prev_price) * 100 if prev_price > 0 else 0
            
            stock_data = {
                'symbol': symbol.upper(),
                'price': round(current_price, 2),
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'company_name': info.get('longName', symbol.upper()),
                'market_cap': info.get('marketCap', 0),
                'volume': info.get('volume', 0)
            }
            
            # Cache the data
            self.cache[cache_key] = {
                'data': stock_data,
                'timestamp': current_time
            }
            
            return stock_data
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None
    
    def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Optional[Dict]]:
        """Fetch data for multiple stocks"""
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_stock_data(symbol)
        return results