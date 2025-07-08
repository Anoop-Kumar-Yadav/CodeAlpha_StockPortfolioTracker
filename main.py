import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QDir
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)

    app.setApplicationName("Stock Portfolio Tracker")
    app.setApplicationVersion("1.0.0")

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()