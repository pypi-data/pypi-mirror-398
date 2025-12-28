#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for compact QPSACoVariable component
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import Qt
from pyscreeps_arena.ui.qmapker.qvariable import QPSACoVariable


def test_compact_variable():
    """Test the compact QPSACoVariable component."""
    app = QApplication(sys.argv)
    
    # Create main window
    window = QWidget()
    window.setWindowTitle("Compact QPSACoVariable Test")
    window.resize(400, 300)
    
    # Create layout
    layout = QVBoxLayout()
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(5)
    
    # Add title
    title = QLabel("Compact QPSACoVariable Components")
    title.setStyleSheet("font-weight: bold; font-size: 14px;")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(title)
    
    # Create multiple compact QPSACoVariable components
    for i in range(3):
        variable = QPSACoVariable()
        variable._input.setText(f"Test{i+1}")
        layout.addWidget(variable)
    
    # Add button to test dual mode
    def toggle_dual():
        for widget in window.findChildren(QPSACoVariable):
            widget.dual = not widget.dual
    
    test_button = QPushButton("Toggle Dual Mode")
    test_button.clicked.connect(toggle_dual)
    layout.addWidget(test_button)
    
    # Add stretch to push everything up
    layout.addStretch()
    
    window.setLayout(layout)
    window.show()
    
    print("[DEBUG] Compact QPSACoVariable test window initialized")
    sys.exit(app.exec())


if __name__ == "__main__":
    test_compact_variable()