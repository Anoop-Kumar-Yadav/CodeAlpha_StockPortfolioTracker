from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QLabel, QFrame, QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPainter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
from datetime import datetime

import os

from models.portfolio import Portfolio
from services.stock_service import StockService
from services.data_service import DataService
from ui.dialogs import AddStockDialog
from utils.helpers import format_currency, format_percentage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.portfolio = Portfolio()
        self.stock_service = StockService()
        self.data_service = DataService()
        
        # Timer for auto-refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        
        self.init_ui()
        self.load_portfolio()
        
    def init_ui(self):
        self.setWindowTitle("Live Stock Portfolio Tracker")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Title
        title_label = QLabel("📈 Live Stock Portfolio Tracker")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50; padding: 10px;")
        main_layout.addWidget(title_label)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.add_stock_btn = QPushButton("➕ Add Stock")
        self.add_stock_btn.clicked.connect(self.add_stock)
        self.add_stock_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        
        self.remove_stock_btn = QPushButton("🗑️ Remove Stock")
        self.remove_stock_btn.clicked.connect(self.remove_stock)
        self.remove_stock_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        self.save_btn = QPushButton("💾 Save Portfolio")
        self.save_btn.clicked.connect(self.save_portfolio)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        
        self.auto_refresh_btn = QPushButton("⏰ Auto Refresh (30s)")
        self.auto_refresh_btn.clicked.connect(self.toggle_auto_refresh)
        self.auto_refresh_btn.setCheckable(True)
        self.auto_refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:checked {
                background-color: #d35400;
            }
        """)
        
        button_layout.addWidget(self.add_stock_btn)
        button_layout.addWidget(self.remove_stock_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.auto_refresh_btn)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # Content layout (table and chart side by side)
        content_layout = QHBoxLayout()
        
        # Left side - Portfolio table
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        
        # Portfolio summary
        self.summary_label = QLabel("Portfolio Summary")
        self.summary_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        left_layout.addWidget(self.summary_label)
        
        self.total_value_label = QLabel("Total Value: $0.00")
        self.total_value_label.setFont(QFont("Arial", 12))
        self.total_value_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        left_layout.addWidget(self.total_value_label)
        
        self.last_updated_label = QLabel("Last Updated: Never")
        self.last_updated_label.setFont(QFont("Arial", 10))
        self.last_updated_label.setStyleSheet("color: #7f8c8d;")
        left_layout.addWidget(self.last_updated_label)
        
        # Portfolio table
        self.portfolio_table = QTableWidget()
        self.portfolio_table.setColumnCount(6)
        self.portfolio_table.setHorizontalHeaderLabels([
            "Symbol", "Quantity", "Price", "Value", "Change", "Change %"
        ])
        
        # Set table styling
        self.portfolio_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        # Set column widths
        header = self.portfolio_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        left_layout.addWidget(self.portfolio_table)
        
        # Right side - Chart
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        
        chart_label = QLabel("Portfolio Distribution")
        chart_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        right_layout.addWidget(chart_label)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        right_layout.addWidget(self.canvas)
        
        # Add widgets to content layout
        content_layout.addWidget(left_widget, 1)
        content_layout.addWidget(right_widget, 1)
        
        main_layout.addLayout(content_layout)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
    def add_stock(self):
        dialog = AddStockDialog(self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            symbol, quantity = dialog.get_data()
            if symbol and quantity > 0:
                try:
                    # Fetch stock data
                    stock_data = self.stock_service.get_stock_data(symbol)
                    if stock_data:
                        self.portfolio.add_stock(symbol, quantity, stock_data['price'])
                        self.update_display()
                        self.statusBar().showMessage(f"Added {quantity} shares of {symbol}")
                    else:
                        QMessageBox.warning(self, "Error", f"Could not fetch data for {symbol}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to add stock: {str(e)}")
    
    def remove_stock(self):
        current_row = self.portfolio_table.currentRow()
        if current_row >= 0:
            symbol = self.portfolio_table.item(current_row, 0).text()
            reply = QMessageBox.question(
                self, "Remove Stock", 
                f"Are you sure you want to remove {symbol}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.portfolio.remove_stock(symbol)
                self.update_display()
                self.statusBar().showMessage(f"Removed {symbol}")
        else:
            QMessageBox.information(self, "No Selection", "Please select a stock to remove")
    
    def refresh_data(self):
        if not self.portfolio.stocks:
            return
            
        self.statusBar().showMessage("Refreshing data...")
        self.refresh_btn.setEnabled(False)
        
        try:
            # Update all stock prices
            for stock in self.portfolio.stocks:
                stock_data = self.stock_service.get_stock_data(stock.symbol)
                if stock_data:
                    stock.update_price(stock_data['price'])
                    stock.change = stock_data.get('change', 0)
                    stock.change_percent = stock_data.get('change_percent', 0)
            
            self.update_display()
            self.last_updated_label.setText(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.statusBar().showMessage("Data refreshed successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh data: {str(e)}")
            self.statusBar().showMessage("Refresh failed")
        finally:
            self.refresh_btn.setEnabled(True)
    
    def toggle_auto_refresh(self):
        if self.auto_refresh_btn.isChecked():
            self.refresh_timer.start(30000)  # 30 seconds
            self.auto_refresh_btn.setText("⏰ Auto Refresh (ON)")
            self.statusBar().showMessage("Auto refresh enabled (30s)")
        else:
            self.refresh_timer.stop()
            self.auto_refresh_btn.setText("⏰ Auto Refresh (OFF)")
            self.statusBar().showMessage("Auto refresh disabled")
    
    def update_display(self):
        self.update_table()
        self.update_chart()
    
    def update_table(self):
        self.portfolio_table.setRowCount(len(self.portfolio.stocks))
        
        total_value = 0
        for i, stock in enumerate(self.portfolio.stocks):
            value = stock.quantity * stock.current_price
            total_value += value
            
            # Symbol
            self.portfolio_table.setItem(i, 0, QTableWidgetItem(stock.symbol))
            
            # Quantity
            self.portfolio_table.setItem(i, 1, QTableWidgetItem(str(stock.quantity)))
            
            # Price
            price_item = QTableWidgetItem(format_currency(stock.current_price))
            self.portfolio_table.setItem(i, 2, price_item)
            
            # Value
            value_item = QTableWidgetItem(format_currency(value))
            self.portfolio_table.setItem(i, 3, value_item)
            
            # Change
            change_item = QTableWidgetItem(format_currency(stock.change))
            if stock.change >= 0:
                change_item.setBackground(Qt.GlobalColor.green)
            else:
                change_item.setBackground(Qt.GlobalColor.red)
            self.portfolio_table.setItem(i, 4, change_item)
            
            # Change %
            change_percent_item = QTableWidgetItem(format_percentage(stock.change_percent))
            if stock.change_percent >= 0:
                change_percent_item.setBackground(Qt.GlobalColor.green)
            else:
                change_percent_item.setBackground(Qt.GlobalColor.red)
            self.portfolio_table.setItem(i, 5, change_percent_item)
        
        # Update total value
        self.total_value_label.setText(f"Total Value: {format_currency(total_value)}")
    
    def update_chart(self):
        self.figure.clear()
        
        if not self.portfolio.stocks:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No stocks in portfolio', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14)
            ax.set_xticks([])
            ax.set_yticks([])
            self.canvas.draw()
            return
        
        # Prepare data for chart
        symbols = [stock.symbol for stock in self.portfolio.stocks]
        values = [stock.quantity * stock.current_price for stock in self.portfolio.stocks]
        
        # Create bar chart
        ax = self.figure.add_subplot(111)
        bars = ax.bar(symbols, values, color=['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6'])
        
        # Customize chart
        ax.set_title('Portfolio Distribution by Stock Value', fontsize=14, fontweight='bold')
        ax.set_xlabel('Stock Symbol', fontsize=12)
        ax.set_ylabel('Value ($)', fontsize=12)
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'${value:.2f}', ha='center', va='bottom', fontsize=10)
        
        # Rotate x-axis labels if needed
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # Adjust layout
        self.figure.tight_layout()
        self.canvas.draw()
    
    def save_portfolio(self):
        try:
            filename = f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            self.data_service.save_portfolio_to_csv(self.portfolio, filename)
            QMessageBox.information(self, "Success", f"Portfolio saved to {filename}")
            self.statusBar().showMessage(f"Portfolio saved to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save portfolio: {str(e)}")
    
    def load_portfolio(self):
        # Try to load the most recent portfolio file
        try:
            portfolio_files = [f for f in os.listdir('.') if f.startswith('portfolio_') and f.endswith('.csv')]
            if portfolio_files:
                latest_file = max(portfolio_files)
                loaded_portfolio = self.data_service.load_portfolio_from_csv(latest_file)
                if loaded_portfolio:
                    self.portfolio = loaded_portfolio
                    self.update_display()
                    self.statusBar().showMessage(f"Loaded portfolio from {latest_file}")
        except Exception as e:
            self.statusBar().showMessage("No previous portfolio found")
