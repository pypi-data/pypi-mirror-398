#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for drag functionality in QPSAMapViewer
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDropEvent
from ui.qmapv.qmapv import QPSAMapViewer, CellInfo

class DropTarget(QWidget):
    """A simple drop target to test drag functionality."""
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.label = QLabel("Drop target - drag data will appear here")
        
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.text_edit)
        self.setLayout(layout)
        
        self.setWindowTitle("Drag Test Target")
        self.resize(400, 300)
    
    def dragEnterEvent(self, event):
        """Accept drag enter events."""
        print(f"[TEST] Drag enter event received: hasText={event.mimeData().hasText()}")
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handle drop events."""
        print(f"[TEST] Drop event received")
        if event.mimeData().hasText():
            text = event.mimeData().text()
            self.text_edit.setPlainText(text)
            print(f"[TEST] Received text: {text}")
            event.acceptProposedAction()

def test_drag_functionality():
    """Test the drag functionality."""
    app = QApplication(sys.argv)
    
    # Create main window
    main_window = QWidget()
    main_window.setWindowTitle("Drag Test")
    main_window.resize(1200, 800)
    
    # Create layout
    layout = QHBoxLayout()
    
    # Create map viewer
    map_viewer = QPSAMapViewer()
    
    # Create a simple test map with some cells
    # For testing, we'll manually add some cell info
    test_cells = [
        CellInfo(10, 10),
        CellInfo(15, 15),  # Empty cell for point testing
        CellInfo(20, 20)
    ]
    
    # Add objects to test cells
    test_cells[0]._objects = [
        {"type": "Source", "method": "Source", "id": "source1", "name": "Source 1"},
        {"type": "Mineral", "method": "Mineral", "id": "mineral1", "name": "Mineral 1"}
    ]
    test_cells[2]._objects = [
        {"type": "Controller", "method": "Controller", "id": "ctrl1", "name": "Controller 1"}
    ]
    
    # Set up the map viewer with test data
    # Note: This is a simplified test - in real usage you'd load an actual map
    
    # Create drop target
    drop_target = DropTarget()
    
    # Add widgets to layout
    layout.addWidget(map_viewer, 2)
    layout.addWidget(drop_target, 1)
    
    main_window.setLayout(layout)
    
    # Show windows
    main_window.show()
    drop_target.show()
    
    print("[TEST] Drag test started!")
    print("[TEST] Instructions:")
    print("[TEST] 1. Hold Ctrl or Alt key")
    print("[TEST] 2. Click and drag on the map")
    print("[TEST] 3. Drop on the right panel")
    print("[TEST] 4. Check the debug output")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_drag_functionality()