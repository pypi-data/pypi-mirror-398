# -*- coding: utf-8 -*-
"""
Test script for QPSACoVariable component
"""
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from pyscreeps_arena.ui.qmapker.qvariable import QPSACoVariable


class TestWindow(QMainWindow):
    """Test window to display QPSACoVariable component."""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
        
    def _init_ui(self):
        """Initialize UI."""
        self.setWindowTitle("QPSACoVariable Test")
        self.setGeometry(100, 100, 800, 400)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Add multiple QPSACoVariable components to test instance counting
        for i in range(3):
            co_var = QPSACoVariable()
            co_var.onItemChanged.connect(self._on_item_changed)
            main_layout.addWidget(co_var)
    
    def _on_item_changed(self):
        """Handle item changed signal."""
        print("Item changed!")


def main():
    """Main function."""
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
