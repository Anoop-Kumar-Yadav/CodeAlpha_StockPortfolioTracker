import sys
import requests
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QSpinBox, QPushButton, QFormLayout,
                             QComboBox, QCompleter, QFrame, QGroupBox, QTextEdit,
                             QApplication, QProgressBar, QMessageBox)
from PyQt6.QtCore import Qt, QStringListModel, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor

class StockDataFetcher(QThread):
    """Thread to fetch stock data without blocking UI"""
    data_received = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, symbol):
        super().__init__()
        self.symbol = symbol
        
    def run(self):
        try:
            # Using Alpha Vantage free API (you'll need to get a free API key)
            # Alternative: Using Yahoo Finance via yfinance library
            
            # Method 1: Using yfinance (install with: pip install yfinance)
            try:
                import yfinance as yf
                ticker = yf.Ticker(self.symbol)
                info = ticker.info
                
                # Get current price
                hist = ticker.history(period="1d")
                current_price = hist['Close'].iloc[-1] if not hist.empty else 0
                
                data = {
                    'symbol': self.symbol,
                    'name': info.get('longName', 'N/A'),
                    'current_price': current_price,
                    'market_cap': info.get('marketCap', 'N/A'),
                    'pe_ratio': info.get('trailingPE', 'N/A'),
                    'dividend_yield': info.get('dividendYield', 'N/A'),
                    'beta': info.get('beta', 'N/A'),
                    'sector': info.get('sector', 'N/A'),
                    'industry': info.get('industry', 'N/A'),
                    'description': info.get('longBusinessSummary', 'N/A')[:200] + '...' if info.get('longBusinessSummary') else 'N/A'
                }
                self.data_received.emit(data)
                
            except ImportError:
                # Method 2: Using Alpha Vantage API (free tier available)
                # Get free API key from: https://www.alphavantage.co/support/#api-key
                API_KEY = "GQ5DS63MNI7EZ9UD"  # Replace with your actual API key
                
                # Company overview
                overview_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={self.symbol}&apikey={API_KEY}"
                quote_url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={self.symbol}&apikey={API_KEY}"
                
                overview_response = requests.get(overview_url, timeout=10)
                quote_response = requests.get(quote_url, timeout=10)
                
                if overview_response.status_code == 200 and quote_response.status_code == 200:
                    overview_data = overview_response.json()
                    quote_data = quote_response.json()
                    
                    if "Global Quote" in quote_data:
                        quote_info = quote_data["Global Quote"]
                        current_price = float(quote_info.get("05. price", 0))
                    else:
                        current_price = 0
                    
                    data = {
                        'symbol': self.symbol,
                        'name': overview_data.get('Name', 'N/A'),
                        'current_price': current_price,
                        'market_cap': overview_data.get('MarketCapitalization', 'N/A'),
                        'pe_ratio': overview_data.get('PERatio', 'N/A'),
                        'dividend_yield': overview_data.get('DividendYield', 'N/A'),
                        'beta': overview_data.get('Beta', 'N/A'),
                        'sector': overview_data.get('Sector', 'N/A'),
                        'industry': overview_data.get('Industry', 'N/A'),
                        'description': overview_data.get('Description', 'N/A')[:200] + '...' if overview_data.get('Description') else 'N/A'
                    }
                    self.data_received.emit(data)
                else:
                    self.error_occurred.emit("Failed to fetch data from API")
                    
        except Exception as e:
            self.error_occurred.emit(str(e))

class AddStockDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Stock to Portfolio")
        self.setModal(True)
        self.setFixedSize(600, 650)
        
        # Set modern styling with better visibility
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #212529;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                background-color: #f8f9fa;
                color: #495057;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #495057;
                font-size: 12px;
            }
            QLabel {
                color: #495057;
                font-weight: 500;
                font-size: 11px;
            }
            QLineEdit, QSpinBox, QComboBox {
                padding: 8px 12px;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                font-size: 12px;
                background-color: white;
                color: #212529;
                selection-background-color: #007bff;
                selection-color: white;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border-color: #007bff;
                outline: none;
            }
            QComboBox {
                color: #212529;
                background-color: white;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
                background-color: #f8f9fa;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }
            QComboBox::down-arrow {
                image: none;
                border: 3px solid #6c757d;
                width: 0px;
                height: 0px;
                border-top-color: #6c757d;
                border-left-color: transparent;
                border-right-color: transparent;
                border-bottom-color: transparent;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #212529;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                selection-background-color: #007bff;
                selection-color: white;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px;
                border: none;
                color: #212529;
                background-color: white;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #007bff;
                color: white;
            }
            QTextEdit {
                border: 2px solid #e9ecef;
                border-radius: 6px;
                background-color: white;
                color: #212529;
                font-size: 11px;
                padding: 8px;
            }
            QPushButton {
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
                min-width: 80px;
            }
            QPushButton#addButton {
                background-color: #28a745;
                color: white;
            }
            QPushButton#addButton:hover {
                background-color: #218838;
            }
            QPushButton#addButton:pressed {
                background-color: #1e7e34;
            }
            QPushButton#cancelButton {
                background-color: #6c757d;
                color: white;
            }
            QPushButton#cancelButton:hover {
                background-color: #545b62;
            }
            QPushButton#cancelButton:pressed {
                background-color: #3d4142;
            }
            QProgressBar {
                border: 2px solid #dee2e6;
                border-radius: 6px;
                text-align: center;
                background-color: #f8f9fa;
                color: #495057;
            }
            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 4px;
            }
        """)
        
        # Popular companies list
        self.companies = {
            "Apple Inc.": "AAPL",
            "Microsoft Corporation": "MSFT",
            "Amazon.com Inc.": "AMZN",
            "Alphabet Inc. (Google)": "GOOGL",
            "Tesla Inc.": "TSLA",
            "Meta Platforms Inc.": "META",
            "NVIDIA Corporation": "NVDA",
            "Netflix Inc.": "NFLX",
            "Adobe Inc.": "ADBE",
            "Salesforce Inc.": "CRM",
            "PayPal Holdings Inc.": "PYPL",
            "Intel Corporation": "INTC",
            "Advanced Micro Devices": "AMD",
            "Cisco Systems Inc.": "CSCO",
            "Oracle Corporation": "ORCL",
            "IBM Corporation": "IBM",
            "Johnson & Johnson": "JNJ",
            "Procter & Gamble": "PG",
            "Coca-Cola Company": "KO",
            "PepsiCo Inc.": "PEP",
            "McDonald's Corporation": "MCD",
            "Nike Inc.": "NKE",
            "Walmart Inc.": "WMT",
            "JPMorgan Chase & Co.": "JPM",
            "Bank of America": "BAC",
            "Visa Inc.": "V",
            "Mastercard Inc.": "MA",
            "Disney Company": "DIS",
            "Boeing Company": "BA",
            "Pfizer Inc.": "PFE"
        }
        
        self.current_stock_data = {}
        self.fetch_thread = None
        
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Add Stock to Your Portfolio")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #212529;
                margin-bottom: 10px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Stock selection group
        stock_group = QGroupBox("Stock Selection")
        stock_layout = QFormLayout()
        stock_layout.setSpacing(12)
        
        # Company dropdown
        self.company_combo = QComboBox()
        self.company_combo.setEditable(True)
        self.company_combo.setPlaceholderText("Search or select a company...")
        
        # Add companies to dropdown
        company_list = [""] + list(self.companies.keys())
        self.company_combo.addItems(company_list)
        
        # Setup auto-completion
        completer = QCompleter(company_list)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.company_combo.setCompleter(completer)
        
        # Connect selection
        self.company_combo.currentTextChanged.connect(self.on_company_selected)
        
        stock_layout.addRow("Company:", self.company_combo)
        
        # Stock symbol
        self.symbol_edit = QLineEdit()
        self.symbol_edit.setPlaceholderText("Enter stock symbol (e.g., AAPL)")
        self.symbol_edit.textChanged.connect(self.on_symbol_changed)
        stock_layout.addRow("Symbol:", self.symbol_edit)
        
        # Progress bar for data fetching
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        stock_layout.addRow("", self.progress_bar)
        
        stock_group.setLayout(stock_layout)
        main_layout.addWidget(stock_group)
        
        # Company details group
        details_group = QGroupBox("Company Details")
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(200)
        self.details_text.setReadOnly(True)
        self.details_text.setText("Select a company to view details...")
        details_layout.addWidget(self.details_text)
        
        details_group.setLayout(details_layout)
        main_layout.addWidget(details_group)
        
        # Quantity group
        quantity_group = QGroupBox("Purchase Details")
        quantity_layout = QFormLayout()
        
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(10000)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setSuffix(" shares")
        quantity_layout.addRow("Shares:", self.quantity_spin)
        
        # Estimated value
        self.estimated_value_label = QLabel("$0.00")
        self.estimated_value_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #28a745;
            }
        """)
        quantity_layout.addRow("Estimated Value:", self.estimated_value_label)
        
        # Connect quantity change to update estimated value
        self.quantity_spin.valueChanged.connect(self.update_estimated_value)
        
        quantity_group.setLayout(quantity_layout)
        main_layout.addWidget(quantity_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.ok_button = QPushButton("Add Stock")
        self.ok_button.setObjectName("addButton")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)
        self.ok_button.setEnabled(False)  # Disabled until valid stock is selected
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def on_company_selected(self, company_name):
        """Handle company selection from dropdown"""
        if company_name in self.companies:
            symbol = self.companies[company_name]
            self.symbol_edit.setText(symbol)
            self.fetch_stock_data(symbol)
    
    def on_symbol_changed(self, symbol):
        """Handle manual symbol entry"""
        if symbol and len(symbol) >= 2:
            # Delay fetching to avoid too many API calls
            if hasattr(self, 'fetch_timer'):
                self.fetch_timer.stop()
            
            self.fetch_timer = QTimer()
            self.fetch_timer.setSingleShot(True)
            self.fetch_timer.timeout.connect(lambda: self.fetch_stock_data(symbol))
            self.fetch_timer.start(1000)  # Wait 1 second after user stops typing
        else:
            self.details_text.setText("Enter a valid stock symbol...")
            self.ok_button.setEnabled(False)
    
    def fetch_stock_data(self, symbol):
        """Fetch stock data in background thread"""
        if self.fetch_thread and self.fetch_thread.isRunning():
            self.fetch_thread.terminate()
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.details_text.setText("Fetching company data...")
        
        self.fetch_thread = StockDataFetcher(symbol.upper())
        self.fetch_thread.data_received.connect(self.on_data_received)
        self.fetch_thread.error_occurred.connect(self.on_error_occurred)
        self.fetch_thread.start()
    
    def on_data_received(self, data):
        """Handle received stock data"""
        self.progress_bar.setVisible(False)
        self.current_stock_data = data
        
        # Format company details
        details = f"""
<b>Company:</b> {data.get('name', 'N/A')}<br>
<b>Symbol:</b> {data.get('symbol', 'N/A')}<br>
<b>Current Price:</b> ${data.get('current_price', 0):.2f}<br>
<b>Market Cap:</b> {self.format_market_cap(data.get('market_cap', 'N/A'))}<br>
<b>P/E Ratio:</b> {data.get('pe_ratio', 'N/A')}<br>
<b>Dividend Yield:</b> {self.format_percentage(data.get('dividend_yield', 'N/A'))}<br>
<b>Beta:</b> {data.get('beta', 'N/A')}<br>
<b>Sector:</b> {data.get('sector', 'N/A')}<br>
<b>Industry:</b> {data.get('industry', 'N/A')}<br><br>
<b>Description:</b><br>
{data.get('description', 'N/A')}
        """
        
        self.details_text.setHtml(details)
        self.ok_button.setEnabled(True)
        self.update_estimated_value()
    
    def on_error_occurred(self, error):
        """Handle errors during data fetching"""
        self.progress_bar.setVisible(False)
        self.details_text.setText(f"Error fetching data: {error}")
        self.ok_button.setEnabled(False)
        
        # Show error message
        QMessageBox.warning(self, "Data Fetch Error", 
                          f"Could not fetch data for this stock:\n{error}\n\n"
                          "Please check the symbol and try again.")
    
    def format_market_cap(self, market_cap):
        """Format market cap for display"""
        if market_cap == 'N/A' or not market_cap:
            return 'N/A'
        
        try:
            cap = float(market_cap)
            if cap >= 1e12:
                return f"${cap/1e12:.2f}T"
            elif cap >= 1e9:
                return f"${cap/1e9:.2f}B"
            elif cap >= 1e6:
                return f"${cap/1e6:.2f}M"
            else:
                return f"${cap:,.0f}"
        except:
            return str(market_cap)
    
    def format_percentage(self, value):
        """Format percentage for display"""
        if value == 'N/A' or not value:
            return 'N/A'
        
        try:
            return f"{float(value)*100:.2f}%"
        except:
            return str(value)
    
    def update_estimated_value(self):
        """Update estimated value based on quantity and current price"""
        if self.current_stock_data and 'current_price' in self.current_stock_data:
            try:
                price = float(self.current_stock_data['current_price'])
                quantity = self.quantity_spin.value()
                total_value = price * quantity
                self.estimated_value_label.setText(f"${total_value:,.2f}")
            except:
                self.estimated_value_label.setText("$0.00")
        else:
            self.estimated_value_label.setText("$0.00")
    
    def get_data(self):
        """Return the selected stock data"""
        symbol = self.symbol_edit.text().strip().upper()
        quantity = self.quantity_spin.value()
        return symbol, quantity
    
    def get_stock_details(self):
        """Return complete stock details"""
        return self.current_stock_data
    
    def closeEvent(self, event):
        """Clean up when dialog is closed"""
        if self.fetch_thread and self.fetch_thread.isRunning():
            self.fetch_thread.terminate()
        event.accept()

