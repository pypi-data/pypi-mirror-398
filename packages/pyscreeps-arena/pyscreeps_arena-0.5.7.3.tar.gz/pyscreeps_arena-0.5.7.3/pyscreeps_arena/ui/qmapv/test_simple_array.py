#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test script for array format drag and drop functionality
"""

import sys
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QListWidget, 
                             QListWidgetItem, QFrame, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal
from PyQt6.QtGui import QDrag, QPixmap, QPainter, QPen, QColor, QBrush


class SimpleDropTarget(QWidget):
    """Simple drop target widget to test array format."""
    
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        self._objects = []
        self._init_ui()
        self.setAcceptDrops(True)
        
    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()
        
        # Title label
        self.title_label = QLabel(f"{self.name} Drop Target")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.title_label)
        
        # Objects list
        self.objects_list = QListWidget()
        self.objects_list.setFrameStyle(QFrame.Shape.Box)
        self.objects_list.setMaximumHeight(150)
        self.objects_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::item {
                border-bottom: 1px solid #eee;
            }
        """)
        layout.addWidget(self.objects_list)
        
        # Status label
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("font-size: 10px; color: #666;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        self.setMinimumWidth(250)
        self.setMaximumWidth(250)
        
    def dragEnterEvent(self, event):
        """Accept drag enter events."""
        print(f"[DEBUG] {self.name} drag enter: hasText={event.mimeData().hasText()}")
        if event.mimeData().hasText() or event.mimeData().hasFormat("application/json"):
            event.acceptProposedAction()
            self.status_label.setText("Status: Drag enter accepted")
    
    def dropEvent(self, event):
        """Handle drop event to add objects."""
        mime_data = event.mimeData()
        json_data = None
        
        print(f"[DEBUG] {self.name} drop received: hasText={event.mimeData().hasText()}")
        
        # Try to get JSON data from different sources
        if mime_data.hasFormat("application/json"):
            try:
                json_bytes = mime_data.data("application/json")
                json_str = json_bytes.data().decode('utf-8')
                print(f"[DEBUG] {self.name} JSON data: {json_str}")
                json_data = json.loads(json_str)
            except Exception as e:
                print(f"[DEBUG] {self.name} failed to parse JSON data: {e}")
        elif mime_data.hasText():
            try:
                json_str = mime_data.text()
                print(f"[DEBUG] {self.name} text data: {json_str}")
                json_data = json.loads(json_str)
            except Exception as e:
                print(f"[DEBUG] {self.name} failed to parse text as JSON: {e}")
        
        if json_data:
            # Handle both single object and array of objects
            if isinstance(json_data, list):
                # Array format: [{x, y, type, method, id, name}, ...]
                print(f"[DEBUG] {self.name} received array of {len(json_data)} objects")
                for obj in json_data:
                    self._add_object_to_list(obj)
                event.acceptProposedAction()
                self.status_label.setText(f"Status: Added {len(json_data)} objects from array")
                print(f"[DEBUG] {self.name} array of objects added successfully")
            elif isinstance(json_data, dict):
                # Single object format: {x, y, type, method, id, name}
                self._add_object_to_list(json_data)
                event.acceptProposedAction()
                self.status_label.setText(f"Status: Added single object: {json_data.get('name', 'Unknown')}")
                print(f"[DEBUG] {self.name} single object added successfully: {json_data}")
            else:
                print(f"[DEBUG] {self.name} invalid JSON format: expected dict or list, got {type(json_data)}")
                self.status_label.setText(f"Status: Invalid format: {type(json_data)}")
        else:
            print(f"[DEBUG] {self.name} no valid JSON data found")
            self.status_label.setText("Status: No valid JSON data")
    
    def _add_object_to_list(self, obj_data: dict):
        """Add a single object to the objects list."""
        # Extract required fields
        obj_id = obj_data.get('id', 'unknown')
        obj_type = obj_data.get('type', 'Unknown')
        obj_name = obj_data.get('name', obj_id)
        x = obj_data.get('x', 0)
        y = obj_data.get('y', 0)
        method = obj_data.get('method', '')
        
        # Check for duplicates with same id
        for existing_obj in self._objects:
            existing_id = existing_obj.get('id', 'unknown')
            if existing_id == obj_id:
                print(f"[DEBUG] {self.name} rejected duplicate object: {obj_id}")
                return  # Reject duplicate
        
        # Add the new object
        new_obj = {
            'id': obj_id,
            'type': obj_type,
            'name': obj_name,
            'x': x,
            'y': y,
            'method': method
        }
        
        self._objects.append(new_obj)
        print(f"[DEBUG] {self.name} added object: {new_obj}")
        
        # Add to list widget
        list_item_text = f"{obj_type}: {obj_name} ({x}, {y})"
        self.objects_list.addItem(list_item_text)


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
        
        # First drop target
        self.drop_target1 = SimpleDropTarget("Target1")
        right_layout.addWidget(self.drop_target1)
        
        # Second drop target
        self.drop_target2 = SimpleDropTarget("Target2")
        right_layout.addWidget(self.drop_target2)
        
        # Clear buttons
        clear_layout = QHBoxLayout()
        btn_clear1 = QPushButton("Clear Target1")
        btn_clear1.clicked.connect(self._clear_target1)
        clear_layout.addWidget(btn_clear1)
        
        btn_clear2 = QPushButton("Clear Target2")
        btn_clear2.clicked.connect(self._clear_target2)
        clear_layout.addWidget(btn_clear2)
        
        right_layout.addLayout(clear_layout)
        
        layout.addLayout(right_layout)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
    def _clear_target1(self):
        """Clear first target."""
        self.drop_target1.objects_list.clear()
        self.drop_target1._objects = []
        self.drop_target1.status_label.setText("Status: Cleared")
        
    def _clear_target2(self):
        """Clear second target."""
        self.drop_target2.objects_list.clear()
        self.drop_target2._objects = []
        self.drop_target2.status_label.setText("Status: Cleared")


def main():
    """Main function."""
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()