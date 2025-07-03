import pandas as pd
import csv
from typing import Optional
from datetime import datetime
from models.portfolio import Portfolio
from models.stock import Stock

class DataService:
    def save_portfolio_to_csv(self, portfolio: Portfolio, filename: str):
        """Save portfolio to CSV file"""
        data = []
        total_value = 0
        
        for stock in portfolio.stocks:
            value = stock.quantity * stock.current_price
            total_value += value
            
            data.append({
                'Symbol': stock.symbol,
                'Quantity': stock.quantity,
                'Initial Price': stock.initial_price,
                'Current Price': stock.current_price,
                'Value': value,
                'Change': stock.change,
                'Change %': stock.change_percent,
                'Last Updated': stock.last_updated.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Add total row
        data.append({
            'Symbol': 'TOTAL',
            'Quantity': '',
            'Initial Price': '',
            'Current Price': '',
            'Value': total_value,
            'Change': '',
            'Change %': '',
            'Last Updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
    
    def load_portfolio_from_csv(self, filename: str) -> Optional[Portfolio]:
        """Load portfolio from CSV file"""
        try:
            df = pd.read_csv(filename)
            portfolio = Portfolio()
            
            for _, row in df.iterrows():
                if row['Symbol'] == 'TOTAL':
                    continue
                
                stock = Stock(
                    row['Symbol'],
                    int(row['Quantity']),
                    float(row['Initial Price'])
                )
                stock.current_price = float(row['Current Price'])
                stock.change = float(row['Change']) if pd.notna(row['Change']) else 0
                stock.change_percent = float(row['Change %']) if pd.notna(row['Change %']) else 0
                
                portfolio.stocks.append(stock)
            
            return portfolio
            
        except Exception as e:
            print(f"Error loading portfolio: {e}")
            return None