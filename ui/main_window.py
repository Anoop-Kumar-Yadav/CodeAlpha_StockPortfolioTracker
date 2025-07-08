from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QLabel, QFrame, QMessageBox, QHeaderView, QTabWidget,
                             QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
                             QProgressBar, QTextEdit, QSplitter, QGroupBox,
                             QGridLayout, QScrollArea, QSystemTrayIcon, QMenu,
                             QSlider, QCheckBox, QDateEdit, QTimeEdit, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QDate, QTime, QSize
from PyQt6.QtGui import QFont, QPixmap, QPainter, QIcon, QAction, QColor, QPalette
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import os

from models.portfolio import Portfolio
from services.stock_service import StockService
from services.data_service import DataService
from ui.dialogs import AddStockDialog
from utils.helpers import format_currency, format_percentage

class AnimatedButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.original_geometry = None
        
    def enterEvent(self, event):
        if self.original_geometry is None:
            self.original_geometry = self.geometry()
        
        expanded = QRect(
            self.original_geometry.x() - 2,
            self.original_geometry.y() - 2,
            self.original_geometry.width() + 4,
            self.original_geometry.height() + 4
        )
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(expanded)
        self.animation.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        if self.original_geometry:
            self.animation.setStartValue(self.geometry())
            self.animation.setEndValue(self.original_geometry)
            self.animation.start()
        super().leaveEvent(event)

class StockCard(QFrame):
    def __init__(self, stock, parent=None):
        super().__init__(parent)
        self.stock = stock
        self.setup_ui()
        
    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.Box)
        self.setFixedSize(280, 160)
        self.setStyleSheet("""
            StockCard {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                padding: 8px;
                margin: 4px;
            }
            StockCard:hover {
                border-color: #3498db;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        symbol_layout = QHBoxLayout()
        symbol_label = QLabel(f"📊 {self.stock.symbol}")
        symbol_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        symbol_label.setStyleSheet("color: #2c3e50;")
        
        live_indicator = QLabel("🔴")
        live_indicator.setToolTip("Live data")
        
        symbol_layout.addWidget(symbol_label)
        symbol_layout.addStretch()
        symbol_layout.addWidget(live_indicator)
        
        price_label = QLabel(f"${self.stock.current_price:.2f}")
        price_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        price_label.setStyleSheet("color: #27ae60;")
        
        change_text = f"{self.stock.change:+.2f} ({self.stock.change_percent:+.1f}%)"
        change_label = QLabel(change_text)
        change_label.setFont(QFont("Arial", 10))
        
        if self.stock.change >= 0:
            change_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            change_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            
        quantity_label = QLabel(f"Shares: {self.stock.quantity}")
        quantity_label.setFont(QFont("Arial", 9))
        quantity_label.setStyleSheet("color: #7f8c8d;")
        
        value = self.stock.quantity * self.stock.current_price
        value_label = QLabel(f"Value: ${value:.2f}")
        value_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        value_label.setStyleSheet("color: #34495e;")
        
        layout.addLayout(symbol_layout)
        layout.addWidget(price_label)
        layout.addWidget(change_label)
        layout.addWidget(quantity_label)
        layout.addWidget(value_label)
        
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.portfolio = Portfolio()
        self.stock_service = StockService()
        self.data_service = DataService()
        
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        
        self.dark_theme = False
        self.auto_save_enabled = True
        self.notification_enabled = True
        self.refresh_interval = 30
        
        self.performance_data = []
        self.alerts = []
        
        self.init_ui()
        self.load_portfolio()
        self.setup_system_tray()
        
    def init_ui(self):
        self.setWindowTitle("Stock Portfolio Tracker")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1000, 700)
        
        self.apply_modern_theme()
        
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        central_widget = QWidget()
        main_scroll.setWidget(central_widget)
        self.setCentralWidget(main_scroll)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🚀 Advanced Stock Portfolio Tracker Pro")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50; padding: 10px;")
        
        self.clock_label = QLabel()
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.clock_label.setFont(QFont("Courier", 14, QFont.Weight.Bold))
        self.clock_label.setStyleSheet("color: #3498db; padding: 10px;")
        self.update_clock()
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(self.clock_label)
        main_layout.addLayout(header_layout)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                background-color: #f8f9fa;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #5dade2;
                color: white;
            }
        """)
        
        self.create_dashboard_tab()
        self.create_analytics_tab()
        self.create_alerts_tab()
        self.create_settings_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        self.setup_status_bar()
        
    def apply_modern_theme(self):
        if self.dark_theme:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2c3e50;
                    color: #ecf0f1;
                }
                QWidget {
                    background-color: #34495e;
                    color: #ecf0f1;
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f8f9fa;
                    color: #2c3e50;
                }
                QWidget {
                    background-color: #ffffff;
                    color: #2c3e50;
                }
            """)
            
    def create_dashboard_tab(self):
        dashboard_scroll = QScrollArea()
        dashboard_scroll.setWidgetResizable(True)
        dashboard_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        dashboard_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        dashboard_widget = QWidget()
        dashboard_scroll.setWidget(dashboard_widget)
        
        layout = QVBoxLayout()
        dashboard_widget.setLayout(layout)
        
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        content_layout = QHBoxLayout()
        
        left_widget = self.create_portfolio_overview()
        left_widget.setMaximumWidth(600)
        
        right_widget = self.create_charts_section()
        right_widget.setMinimumWidth(700)
        
        content_layout.addWidget(left_widget, 1)
        content_layout.addWidget(right_widget, 2)
        
        layout.addLayout(content_layout)
        
        self.tab_widget.addTab(dashboard_scroll, "📊 Dashboard")
        
    def create_control_panel(self):
        control_group = QGroupBox("Control Panel")
        control_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarNever)
        scroll_area.setMaximumHeight(100)
        
        scroll_widget = QWidget()
        scroll_area.setWidget(scroll_widget)
        
        layout = QHBoxLayout()
        scroll_widget.setLayout(layout)
        
        self.add_stock_btn = AnimatedButton("➕ Add Stock")
        self.add_stock_btn.clicked.connect(self.add_stock)
        self.add_stock_btn.setStyleSheet(self.get_button_style("#27ae60", "#219a52"))
        
        self.remove_stock_btn = AnimatedButton("🗑️ Remove Stock")
        self.remove_stock_btn.clicked.connect(self.remove_stock)
        self.remove_stock_btn.setStyleSheet(self.get_button_style("#e74c3c", "#c0392b"))
        
        self.refresh_btn = AnimatedButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.refresh_btn.setStyleSheet(self.get_button_style("#3498db", "#2980b9"))
        
        self.quick_buy_btn = AnimatedButton("⚡ Quick Buy")
        self.quick_buy_btn.clicked.connect(self.quick_buy)
        self.quick_buy_btn.setStyleSheet(self.get_button_style("#f39c12", "#e67e22"))
        
        self.export_btn = AnimatedButton("📄 Export")
        self.export_btn.clicked.connect(self.export_portfolio)
        self.export_btn.setStyleSheet(self.get_button_style("#9b59b6", "#8e44ad"))
        
        self.backup_btn = AnimatedButton("☁️ Backup")
        self.backup_btn.clicked.connect(self.backup_portfolio)
        self.backup_btn.setStyleSheet(self.get_button_style("#1abc9c", "#16a085"))
        
        auto_refresh_widget = QWidget()
        auto_refresh_layout = QVBoxLayout()
        auto_refresh_widget.setLayout(auto_refresh_layout)
        
        self.auto_refresh_btn = AnimatedButton("⏰ Auto Refresh")
        self.auto_refresh_btn.clicked.connect(self.toggle_auto_refresh)
        self.auto_refresh_btn.setCheckable(True)
        self.auto_refresh_btn.setStyleSheet(self.get_button_style("#95a5a6", "#7f8c8d"))
        
        self.refresh_slider = QSlider(Qt.Orientation.Horizontal)
        self.refresh_slider.setRange(10, 300)
        self.refresh_slider.setValue(30)
        self.refresh_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.refresh_slider.setTickInterval(30)
        self.refresh_slider.valueChanged.connect(self.update_refresh_interval)
        
        self.refresh_label = QLabel("30s")
        self.refresh_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.refresh_label.setStyleSheet("font-size: 9px; color: #7f8c8d;")
        
        auto_refresh_layout.addWidget(self.auto_refresh_btn)
        auto_refresh_layout.addWidget(self.refresh_slider)
        auto_refresh_layout.addWidget(self.refresh_label)
        
        layout.addWidget(self.add_stock_btn)
        layout.addWidget(self.remove_stock_btn)
        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.quick_buy_btn)
        layout.addWidget(self.export_btn)
        layout.addWidget(self.backup_btn)
        layout.addWidget(auto_refresh_widget)
        layout.addStretch()
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll_area)
        control_group.setLayout(main_layout)
        
        return control_group
        
    def create_portfolio_overview(self):
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        
        metrics_group = QGroupBox("Portfolio Metrics")
        metrics_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }
        """)
        
        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(4)
        
        self.total_value_label = QLabel("Total Value: $0.00")
        self.total_value_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.total_value_label.setStyleSheet("color: #27ae60; padding: 6px;")
        
        self.daily_change_label = QLabel("Daily Change: $0.00 (0.00%)")
        self.daily_change_label.setFont(QFont("Arial", 10))
        self.daily_change_label.setStyleSheet("color: #3498db; padding: 3px;")
        
        self.total_stocks_label = QLabel("Total Stocks: 0")
        self.total_stocks_label.setFont(QFont("Arial", 10))
        self.total_stocks_label.setStyleSheet("color: #9b59b6; padding: 3px;")
        
        self.best_performer_label = QLabel("Best Performer: N/A")
        self.best_performer_label.setFont(QFont("Arial", 10))
        self.best_performer_label.setStyleSheet("color: #27ae60; padding: 3px;")
        
        self.worst_performer_label = QLabel("Worst Performer: N/A")
        self.worst_performer_label.setFont(QFont("Arial", 10))
        self.worst_performer_label.setStyleSheet("color: #e74c3c; padding: 3px;")
        
        self.last_updated_label = QLabel("Last Updated: Never")
        self.last_updated_label.setFont(QFont("Arial", 9))
        self.last_updated_label.setStyleSheet("color: #7f8c8d; padding: 3px;")
        
        metrics_layout.addWidget(self.total_value_label, 0, 0, 1, 2)
        metrics_layout.addWidget(self.daily_change_label, 1, 0)
        metrics_layout.addWidget(self.total_stocks_label, 1, 1)
        metrics_layout.addWidget(self.best_performer_label, 2, 0)
        metrics_layout.addWidget(self.worst_performer_label, 2, 1)
        metrics_layout.addWidget(self.last_updated_label, 3, 0, 1, 2)
        
        metrics_group.setLayout(metrics_layout)
        left_layout.addWidget(metrics_group)
        
        table_group = QGroupBox("Holdings")
        table_layout = QVBoxLayout()
        
        table_scroll = QScrollArea()
        table_scroll.setWidgetResizable(True)
        table_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        table_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.portfolio_table = QTableWidget()
        self.portfolio_table.setColumnCount(8)
        self.portfolio_table.setHorizontalHeaderLabels([
            "Symbol", "Quantity", "Avg Cost", "Current Price", "Value", "Change", "Change %", "Weight %"
        ])
        
        self.portfolio_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                background-color: white;
                gridline-color: #ecf0f1;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f2f6;
            }
            QTableWidget::item:selected {
                background-color: #5dade2;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
                border-right: 1px solid #2c3e50;
            }
        """)
        
        header = self.portfolio_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        table_scroll.setWidget(self.portfolio_table)
        table_layout.addWidget(table_scroll)
        table_group.setLayout(table_layout)
        left_layout.addWidget(table_group)
        
        left_widget.setLayout(left_layout)
        return left_widget
        
    def create_charts_section(self):
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        
        chart_tabs = QTabWidget()
        chart_tabs.setStyleSheet("""
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 6px 12px;
                margin-right: 1px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 10px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        
        distribution_widget = QWidget()
        distribution_layout = QVBoxLayout()
        
        self.distribution_figure = Figure(figsize=(6, 4), dpi=80)
        self.distribution_canvas = FigureCanvas(self.distribution_figure)
        self.distribution_canvas.setMinimumSize(400, 300)
        distribution_layout.addWidget(self.distribution_canvas)
        distribution_widget.setLayout(distribution_layout)
        
        performance_widget = QWidget()
        performance_layout = QVBoxLayout()
        
        self.performance_figure = Figure(figsize=(6, 4), dpi=80)
        self.performance_canvas = FigureCanvas(self.performance_figure)
        self.performance_canvas.setMinimumSize(400, 300)
        performance_layout.addWidget(self.performance_canvas)
        performance_widget.setLayout(performance_layout)
        
        market_widget = QWidget()
        market_layout = QVBoxLayout()
        
        self.market_figure = Figure(figsize=(6, 4), dpi=80)
        self.market_canvas = FigureCanvas(self.market_figure)
        self.market_canvas.setMinimumSize(400, 300)
        market_layout.addWidget(self.market_canvas)
        market_widget.setLayout(market_layout)
        
        chart_tabs.addTab(distribution_widget, "📊 Distribution")
        chart_tabs.addTab(performance_widget, "📈 Performance")
        chart_tabs.addTab(market_widget, "🌍 Market")
        
        right_layout.addWidget(chart_tabs)
        
        cards_group = QGroupBox("Stock Cards")
        cards_layout = QVBoxLayout()
        
        self.cards_scroll = QScrollArea()
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.cards_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.cards_widget = QWidget()
        self.cards_layout = QHBoxLayout()
        self.cards_widget.setLayout(self.cards_layout)
        self.cards_scroll.setWidget(self.cards_widget)
        self.cards_scroll.setMaximumHeight(200)
        
        cards_layout.addWidget(self.cards_scroll)
        cards_group.setLayout(cards_layout)
        right_layout.addWidget(cards_group)
        
        right_widget.setLayout(right_layout)
        return right_widget
        
    def create_analytics_tab(self):
        analytics_scroll = QScrollArea()
        analytics_scroll.setWidgetResizable(True)
        analytics_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        analytics_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        analytics_widget = QWidget()
        analytics_scroll.setWidget(analytics_widget)
        
        layout = QVBoxLayout()
        analytics_widget.setLayout(layout)
        
        perf_group = QGroupBox("Performance Analytics")
        perf_layout = QGridLayout()
        
        perf_label = QLabel("Advanced analytics coming soon...")
        perf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        perf_label.setStyleSheet("font-size: 16px; color: #7f8c8d; padding: 40px;")
        
        perf_layout.addWidget(perf_label)
        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)
        
        self.tab_widget.addTab(analytics_scroll, "📊 Analytics")
        
    def create_alerts_tab(self):
        alerts_scroll = QScrollArea()
        alerts_scroll.setWidgetResizable(True)
        alerts_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        alerts_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        alerts_widget = QWidget()
        alerts_scroll.setWidget(alerts_widget)
        
        layout = QVBoxLayout()
        alerts_widget.setLayout(layout)
        
        alerts_group = QGroupBox("Price Alerts")
        alerts_layout = QVBoxLayout()
        
        alerts_label = QLabel("Price alerts and notifications coming soon...")
        alerts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alerts_label.setStyleSheet("font-size: 16px; color: #7f8c8d; padding: 40px;")
        
        alerts_layout.addWidget(alerts_label)
        alerts_group.setLayout(alerts_layout)
        layout.addWidget(alerts_group)
        
        self.tab_widget.addTab(alerts_scroll, "🔔 Alerts")
        
    def create_settings_tab(self):
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        settings_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        settings_widget = QWidget()
        settings_scroll.setWidget(settings_widget)
        
        layout = QVBoxLayout()
        settings_widget.setLayout(layout)
        
        theme_group = QGroupBox("Appearance")
        theme_layout = QVBoxLayout()
        
        self.dark_theme_cb = QCheckBox("Dark Theme")
        self.dark_theme_cb.setChecked(self.dark_theme)
        self.dark_theme_cb.toggled.connect(self.toggle_theme)
        
        theme_layout.addWidget(self.dark_theme_cb)
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        autosave_group = QGroupBox("Auto-Save")
        autosave_layout = QVBoxLayout()
        
        self.autosave_cb = QCheckBox("Enable Auto-Save")
        self.autosave_cb.setChecked(self.auto_save_enabled)
        self.autosave_cb.toggled.connect(self.toggle_autosave)
        
        autosave_layout.addWidget(self.autosave_cb)
        autosave_group.setLayout(autosave_layout)
        layout.addWidget(autosave_group)
        
        layout.addStretch()
        self.tab_widget.addTab(settings_scroll, "⚙️ Settings")
        
    def setup_status_bar(self):
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        
        self.connection_label = QLabel("🟢 Connected")
        self.connection_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        
        self.statusBar().addWidget(self.connection_label)
        self.statusBar().addPermanentWidget(self.progress_bar)
        self.statusBar().showMessage("Ready - Portfolio Tracker Pro")
        
    def setup_system_tray(self):
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(QIcon("📊"))
            
            tray_menu = QMenu()
            show_action = QAction("Show", self)
            show_action.triggered.connect(self.show)
            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(self.close)
            
            tray_menu.addAction(show_action)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            
    def get_button_style(self, color, hover_color):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
                min-width: 100px;
                max-height: 35px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {hover_color};
                transform: translateY(1px);
            }}
        """
        
    def update_clock(self):
        current_time = datetime.now().strftime("%H:%M:%S")
        current_date = datetime.now().strftime("%Y-%m-%d")
        self.clock_label.setText(f"{current_date} | {current_time}")
        
    def update_refresh_interval(self, value):
        self.refresh_interval = value
        self.refresh_label.setText(f"{value}s")
        if self.refresh_timer.isActive():
            self.refresh_timer.start(value * 1000)
            
    def toggle_theme(self, checked):
        self.dark_theme = checked
        self.apply_modern_theme()
        
    def toggle_autosave(self, checked):
        self.auto_save_enabled = checked
        
    def quick_buy(self):
        QMessageBox.information(self, "Quick Buy", "Quick buy feature coming soon!")
        
    def export_portfolio(self):
        QMessageBox.information(self, "Export", "Export feature coming soon!")
        
    def backup_portfolio(self):
        QMessageBox.information(self, "Backup", "Cloud backup feature coming soon!")
        

    
    def add_stock(self):
        dialog = AddStockDialog(self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            symbol, quantity = dialog.get_data()
            if symbol and quantity > 0:
                try:
                    self.progress_bar.setVisible(True)
                    self.progress_bar.setRange(0, 0) 
                    
                    stock_data = self.stock_service.get_stock_data(symbol)
                    if stock_data:
                        self.portfolio.add_stock(symbol, quantity, stock_data['price'])
                        self.update_display()
                        self.statusBar().showMessage(f"Added {quantity} shares of {symbol}")
                        
                        if self.auto_save_enabled:
                            self.save_portfolio()
                    else:
                        QMessageBox.warning(self, "Error", f"Could not fetch data for {symbol}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to add stock: {str(e)}")
                finally:
                    self.progress_bar.setVisible(False)
    
    def remove_stock(self):
        current_row = self.portfolio_table.currentRow()
        if current_row >= 0:
            symbol = self.portfolio_table.item(current_row, 0).text()
            reply = QMessageBox.question(
                self, "Remove Stock", 
                f"Are you sure you want to remove {symbol} from your portfolio?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.portfolio.remove_stock(symbol)
                self.update_display()
                self.statusBar().showMessage(f"Removed {symbol} from portfolio")
                
                if self.auto_save_enabled:
                    self.save_portfolio()
        else:
            QMessageBox.information(self, "No Selection", "Please select a stock to remove from the table")
    
    def refresh_data(self):
        if not self.portfolio.stocks:
            QMessageBox.information(self, "No Stocks", "Add some stocks to your portfolio first!")
            return
            
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(self.portfolio.stocks))
        self.progress_bar.setValue(0)
        
        self.statusBar().showMessage("Refreshing portfolio data...")
        self.refresh_btn.setEnabled(False)
        self.connection_label.setText("🟡 Updating...")
        self.connection_label.setStyleSheet("color: #f39c12; font-weight: bold;")
        
        try:
            for i, stock in enumerate(self.portfolio.stocks):
                self.progress_bar.setValue(i)
                stock_data = self.stock_service.get_stock_data(stock.symbol)
                if stock_data:
                    stock.update_price(stock_data['price'])
                    stock.change = stock_data.get('change', 0)
                    stock.change_percent = stock_data.get('change_percent', 0)
                    
                   
                    self.performance_data.append({
                        'timestamp': datetime.now(),
                        'symbol': stock.symbol,
                        'price': stock.current_price,
                        'change': stock.change
                    })
            
            self.progress_bar.setValue(len(self.portfolio.stocks))
            self.update_display()
            self.last_updated_label.setText(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.statusBar().showMessage("Portfolio data refreshed successfully")
            self.connection_label.setText("🟢 Connected")
            self.connection_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            
        except Exception as e:
            QMessageBox.critical(self, "Refresh Error", f"Failed to refresh portfolio data: {str(e)}")
            self.statusBar().showMessage("Refresh failed - Check your internet connection")
            self.connection_label.setText("🔴 Error")
            self.connection_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        finally:
            self.progress_bar.setVisible(False)
            self.refresh_btn.setEnabled(True)
    
    def toggle_auto_refresh(self):
        if self.auto_refresh_btn.isChecked():
            self.refresh_timer.start(self.refresh_interval * 1000)
            self.auto_refresh_btn.setText("⏰ Auto Refresh (ON)")
            self.auto_refresh_btn.setStyleSheet(self.get_button_style("#27ae60", "#219a52"))
            self.statusBar().showMessage(f"Auto refresh enabled ({self.refresh_interval}s interval)")
        else:
            self.refresh_timer.stop()
            self.auto_refresh_btn.setText("⏰ Auto Refresh (OFF)")
            self.auto_refresh_btn.setStyleSheet(self.get_button_style("#95a5a6", "#7f8c8d"))
            self.statusBar().showMessage("Auto refresh disabled")
    
    def update_display(self):
        """Enhanced display update with all components"""
        self.update_metrics()
        self.update_table()
        self.update_charts()
        self.update_stock_cards()
    
    def update_metrics(self):
        if not self.portfolio.stocks:
            self.total_value_label.setText("Total Value: $0.00")
            self.daily_change_label.setText("Daily Change: $0.00 (0.00%)")
            self.total_stocks_label.setText("Total Stocks: 0")
            self.best_performer_label.setText("Best Performer: N/A")
            self.worst_performer_label.setText("Worst Performer: N/A")
            return
        
       
        total_value = sum(stock.quantity * stock.current_price for stock in self.portfolio.stocks)
        total_change = sum(stock.change * stock.quantity for stock in self.portfolio.stocks)
        total_change_percent = (total_change / (total_value - total_change)) * 100 if (total_value - total_change) > 0 else 0
        
        
        best_performer = max(self.portfolio.stocks, key=lambda s: s.change_percent)
        worst_performer = min(self.portfolio.stocks, key=lambda s: s.change_percent)
        
       
        self.total_value_label.setText(f"Total Value: {format_currency(total_value)}")
        
        change_text = f"Daily Change: {format_currency(total_change)} ({total_change_percent:+.2f}%)"
        self.daily_change_label.setText(change_text)
        if total_change >= 0:
            self.daily_change_label.setStyleSheet("color: #27ae60; padding: 4px; font-weight: bold;")
        else:
            self.daily_change_label.setStyleSheet("color: #e74c3c; padding: 4px; font-weight: bold;")
        
        self.total_stocks_label.setText(f"Total Stocks: {len(self.portfolio.stocks)}")
        self.best_performer_label.setText(f"Best Performer: {best_performer.symbol} ({best_performer.change_percent:+.2f}%)")
        self.worst_performer_label.setText(f"Worst Performer: {worst_performer.symbol} ({worst_performer.change_percent:+.2f}%)")
    
    def update_table(self):
        self.portfolio_table.setRowCount(len(self.portfolio.stocks))
        
        total_value = sum(stock.quantity * stock.current_price for stock in self.portfolio.stocks)
        
        for i, stock in enumerate(self.portfolio.stocks):
            value = stock.quantity * stock.current_price
            weight = (value / total_value) * 100 if total_value > 0 else 0
            
    
            symbol_item = QTableWidgetItem(stock.symbol)
            symbol_item.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            self.portfolio_table.setItem(i, 0, symbol_item)
            
       
            quantity_item = QTableWidgetItem(str(stock.quantity))
            quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.portfolio_table.setItem(i, 1, quantity_item)
            
            
            avg_cost_item = QTableWidgetItem(format_currency(stock.purchase_price))
            avg_cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.portfolio_table.setItem(i, 2, avg_cost_item)
            
         
            price_item = QTableWidgetItem(format_currency(stock.current_price))
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            if stock.current_price > stock.purchase_price:
                price_item.setBackground(QColor(39, 174, 96, 50)) 
            else:
                price_item.setBackground(QColor(231, 76, 60, 50))  
            self.portfolio_table.setItem(i, 3, price_item)
            
           
            value_item = QTableWidgetItem(format_currency(value))
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            value_item.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            self.portfolio_table.setItem(i, 4, value_item)
            
           
            change_item = QTableWidgetItem(format_currency(stock.change))
            change_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            if stock.change >= 0:
                change_item.setBackground(QColor(39, 174, 96, 100)) 
                change_item.setForeground(QColor(255, 255, 255)) 
            else:
                change_item.setBackground(QColor(231, 76, 60, 100))  
                change_item.setForeground(QColor(255, 255, 255)) 
            self.portfolio_table.setItem(i, 5, change_item)
            
            
            change_percent_item = QTableWidgetItem(format_percentage(stock.change_percent))
            change_percent_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            if stock.change_percent >= 0:
                change_percent_item.setBackground(QColor(39, 174, 96, 100))  
                change_percent_item.setForeground(QColor(255, 255, 255))  
            else:
                change_percent_item.setBackground(QColor(231, 76, 60, 100))  
                change_percent_item.setForeground(QColor(255, 255, 255))  
            self.portfolio_table.setItem(i, 6, change_percent_item)
            
            
            weight_item = QTableWidgetItem(f"{weight:.1f}%")
            weight_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.portfolio_table.setItem(i, 7, weight_item)
    
    def update_charts(self):
        self.update_distribution_chart()
        self.update_performance_chart()
        self.update_market_chart()
    
    def update_distribution_chart(self):
        self.distribution_figure.clear()
        
        if not self.portfolio.stocks:
            ax = self.distribution_figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No stocks in portfolio\nAdd some stocks to see distribution', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14, 
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.7))
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title('Portfolio Distribution', fontsize=16, fontweight='bold', pad=20)
            self.distribution_canvas.draw()
            return
        
        
        fig = self.distribution_figure
        gs = fig.add_gridspec(1, 2, width_ratios=[1, 1])
        
        
        ax1 = fig.add_subplot(gs[0, 0])
        symbols = [stock.symbol for stock in self.portfolio.stocks]
        values = [stock.quantity * stock.current_price for stock in self.portfolio.stocks]
        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#34495e']
        
        wedges, texts, autotexts = ax1.pie(values, labels=symbols, autopct='%1.1f%%', 
                                          colors=colors[:len(symbols)], startangle=90)
        ax1.set_title('Portfolio Distribution', fontsize=14, fontweight='bold')
        
        
        ax2 = fig.add_subplot(gs[0, 1])
        bars = ax2.bar(symbols, values, color=colors[:len(symbols)])
        ax2.set_title('Stock Values', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Value ($)')
        
        
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                   f'${value:.0f}', ha='center', va='bottom', fontsize=9)
        
        
        plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
        
        
        self.distribution_canvas.draw()
    
    def update_performance_chart(self):
        self.performance_figure.clear()
        
        if not self.performance_data:
            ax = self.performance_figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No performance data yet\nRefresh portfolio to start tracking', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7))
            ax.set_title('Portfolio Performance', fontsize=16, fontweight='bold', pad=20)
            self.performance_canvas.draw()
            return
        
        ax = self.performance_figure.add_subplot(111)
        
        
        df = pd.DataFrame(self.performance_data)
        
        for symbol in df['symbol'].unique():
            symbol_data = df[df['symbol'] == symbol]
            ax.plot(symbol_data['timestamp'], symbol_data['price'], 
                   label=symbol, marker='o', linewidth=2, markersize=4)
        
        ax.set_title('Stock Price Performance', fontsize=14, fontweight='bold')
        ax.set_xlabel('Time')
        ax.set_ylabel('Price ($)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        
        import matplotlib.dates as mdates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        self.performance_figure.tight_layout()
        self.performance_canvas.draw()
    
    def update_market_chart(self):
        self.market_figure.clear()
        
        ax = self.market_figure.add_subplot(111)
        
        if not self.portfolio.stocks:
            ax.text(0.5, 0.5, 'Market analysis available\nafter adding stocks', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.7))
            ax.set_title('Market Overview', fontsize=16, fontweight='bold', pad=20)
            self.market_canvas.draw()
            return
        
        
        symbols = [stock.symbol for stock in self.portfolio.stocks]
        changes = [stock.change_percent for stock in self.portfolio.stocks]
        
        colors = ['#27ae60' if change >= 0 else '#e74c3c' for change in changes]
        bars = ax.bar(symbols, changes, color=colors, alpha=0.7)
        
        
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        ax.set_title('Today\'s Performance', fontsize=14, fontweight='bold')
        ax.set_ylabel('Change (%)')
        
        
        for bar, change in zip(bars, changes):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{change:+.1f}%', ha='center', 
                   va='bottom' if height >= 0 else 'top', fontsize=10)
        
        self.market_figure.tight_layout()
        self.market_canvas.draw()
    
    def update_stock_cards(self):
        """Update stock cards in scroll area"""
        
        for i in reversed(range(self.cards_layout.count())):
            child = self.cards_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        
        for stock in self.portfolio.stocks:
            card = StockCard(stock)
            self.cards_layout.addWidget(card)
        
        
        self.cards_layout.addStretch()
    
    def save_portfolio(self):
        try:
            filename = f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            self.data_service.save_portfolio_to_csv(self.portfolio, filename)
            
            if self.notification_enabled:
                self.statusBar().showMessage(f"Portfolio saved to {filename}", 3000)
            
           
            portfolio_files = [f for f in os.listdir('.') if f.startswith('portfolio_') and f.endswith('.csv')]
            if len(portfolio_files) > 10:
                portfolio_files.sort()
                for old_file in portfolio_files[:-10]:
                    os.remove(old_file)
                    
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save portfolio: {str(e)}")
    
    def load_portfolio(self):
        """Enhanced load with error handling"""
        try:
            portfolio_files = [f for f in os.listdir('.') if f.startswith('portfolio_') and f.endswith('.csv')]
            if portfolio_files:
                latest_file = max(portfolio_files)
                loaded_portfolio = self.data_service.load_portfolio_from_csv(latest_file)
                if loaded_portfolio:
                    self.portfolio = loaded_portfolio
                    self.update_display()
                    self.statusBar().showMessage(f"Loaded portfolio from {latest_file}", 3000)
        except Exception as e:
            self.statusBar().showMessage("No previous portfolio found or error loading", 3000)
    
    def closeEvent(self, event):
        """Handle application close with auto-save"""
        if self.auto_save_enabled and self.portfolio.stocks:
            self.save_portfolio()
        
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        
        event.accept()