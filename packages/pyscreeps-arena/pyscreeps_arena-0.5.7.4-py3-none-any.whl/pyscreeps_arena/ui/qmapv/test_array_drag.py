#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for array format drag and drop functionality
"""

import sys
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QListWidget)
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal
from PyQt6.QtGui import QDrag, QPixmap

# Add the parent directory to the path to import our modules
sys.path.insert(0, 'f:\\Python\\Python312\\Lib\\site-packages\\pyscreeps_arena\\ui\\qmapv')

from qco import QPSACellObject
from qcinfo import QPSACellInfo


class DragSourceWidget(QWidget):
    """Widget that can initiate drag operations with array format."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()
        
        # Create test data
        self.test_array = [
            {
                "x": 10,
                "y": 20,
                "type": "Creep",
                "method": "move",
                "id": "creep1",
                "name": "Worker1"
            },
            {
                "x": 15,
                "y": 25,
                "type": "Structure",
                "method": "build",
                "id": "struct1",
                "name": "Spawn1"
            },
            {
                "x": 30,
                "y": 40,
                "type": "Resource",
                "method": "harvest",
                "id": "res1",
                "name": "Energy1"
            }
        ]
        
        self.test_single = {
            "x": 50,
            "y": 60,
            "type": "Tower",
            "method": "attack",
            "id": "tower1",
            "name": "Defense1"
        }
        
        # Add buttons to trigger drag operations
        btn_array = QPushButton("Drag Array [{}]")
        btn_array.clicked.connect(lambda: self._start_drag(self.test_array))
        layout.addWidget(btn_array)
        
        btn_single = QPushButton("Drag Single {}")
        btn_single.clicked.connect(lambda: self._start_drag(self.test_single))
        layout.addWidget(btn_single)
        
        # Add labels to show what will be dragged
        label_array = QLabel(f"Array: {json.dumps(self.test_array, indent=2)}")
        label_array.setWordWrap(True)
        layout.addWidget(label_array)
        
        label_single = QLabel(f"Single: {json.dumps(self.test_single, indent=2)}")
        label_single.setWordWrap(True)
        layout.addWidget(label_single)
        
        self.setLayout(layout)
        
    def _start_drag(self, data):
        """Start a drag operation with the given data."""
        print(f"[DEBUG] Starting drag with data: {data}")
        
        # Create mime data
        mime_data = QMimeData()
        json_str = json.dumps(data)
        mime_data.setText(json_str)
        mime_data.setData("application/json", json_str.encode('utf-8'))
        
        # Create drag object
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        
        # Start drag operation
        result = drag.exec(Qt.DropAction.CopyAction)
        print(f"[DEBUG] Drag result: {result}")


class TestWindow(QMainWindow):
    """Main test window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Array Format Drag & Drop Test")
        self.setGeometry(100, 100, 800, 600)
        self._init_ui()
        
    def _init_ui(self):
        """Initialize UI."""
        central_widget = QWidget()
        layout = QHBoxLayout()
        
        # Left side - drag source
        drag_source = DragSourceWidget()
        layout.addWidget(drag_source)
        
        # Right side - drop targets
        right_layout = QVBoxLayout()
        
        # QPSACellObject drop target
        cell_object_label = QLabel("QPSACellObject (Drop Here):")
        right_layout.addWidget(cell_object_label)
        
        self.cell_object = QPSACellObject()
        self.cell_object.setMinimumHeight(200)
        right_layout.addWidget(self.cell_object)
        
        # QPSACellInfo drop target
        cell_info_label = QLabel("QPSACellInfo (Drop Here):")
        right_layout.addWidget(cell_info_label)
        
        self.cell_info = QPSACellInfo()
        right_layout.addWidget(self.cell_info)
        
        # Status label
        self.status_label = QLabel("Status: Ready")
        right_layout.addWidget(self.status_label)
        
        # Clear buttons
        clear_layout = QHBoxLayout()
        btn_clear_object = QPushButton("Clear QPSACellObject")
        btn_clear_object.clicked.connect(self.cell_object.clear_objects)
        clear_layout.addWidget(btn_clear_object)
        
        btn_clear_info = QPushButton("Clear QPSACellInfo")
        btn_clear_info.clicked.connect(self._clear_cell_info)
        clear_layout.addWidget(btn_clear_info)
        
        right_layout.addLayout(clear_layout)
        
        layout.addLayout(right_layout)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # Connect signals
        self.cell_object.objectAdded.connect(self._on_object_added)
        self.cell_object.objectRemoved.connect(self._on_object_removed)
        
    def _clear_cell_info(self):
        """Clear QPSACellInfo objects."""
        self.cell_info.objects = []
        self.status_label.setText("Status: QPSACellInfo cleared")
        
    def _on_object_added(self, obj_data):
        """Handle object added to QPSACellObject."""
        self.status_label.setText(f"Status: Object added - {obj_data.get('name', 'Unknown')}")
        
    def _on_object_removed(self, obj_id):
        """Handle object removed from QPSACellObject."""
        self.status_label.setText(f"Status: Object removed - {obj_id}")


def main():
    """Main function."""
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()