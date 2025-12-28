#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for QPSAMapMarker component
"""
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt
from pyscreeps_arena.ui.qmapker.qmapmarker import QPSAMapMarker
from pyscreeps_arena.core import config
config.language = 'en'

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QPSAMapMarker Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("QPSAMapMarker Component Test")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Create map marker component
        self.map_marker = QPSAMapMarker()
        layout.addWidget(self.map_marker)
        
        # Status label
        self.status_label = QLabel("Select a cell on the map to see its info")
        self.status_label.setStyleSheet("font-size: 12px; color: #666; padding: 10px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Connect signals
        self.map_marker.onVariableChanged.connect(self.on_variable_changed)
        
        central_widget.setLayout(layout)
        
        print("[DEBUG] QPSAMapMarker test window initialized")
        
    def on_variable_changed(self):
        """Handle variable changes."""
        variables = self.map_marker.variables
        self.status_label.setText(f"Variables updated: {len(variables)} variables")
        print(f"[DEBUG] Variables changed: {len(variables)} variables")
        
        # Print variable details
        for i, variable in enumerate(variables):
            print(f"  Variable {i+1}: {len(variable['pos'])} true objects, {len(variable['neg'])} false objects")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())


    