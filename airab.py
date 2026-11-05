#!/usr/bin/env python3
"""
AIrab - Local AI Chat App
Run: python airab.py
"""
import sys
from PyQt6.QtWidgets import QApplication
from src.main_window import AIRabWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AIRabWindow()
    window.show()
    sys.exit(app.exec())
