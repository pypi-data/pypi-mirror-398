# -*- coding: utf-8 -*-
"""
Test script for QPSACellInfo component
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
from pyscreeps_arena.ui.qmapv.qcinfo import QPSACellInfo
from pyscreeps_arena.ui.qmapv.qmapv import CellInfo


class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QPSACellInfo Component Test")
        self.setGeometry(100, 100, 400, 500)
        self._init_ui()
        
    def _init_ui(self):
        """Initialize test UI."""
        layout = QVBoxLayout()
        
        # Create the cell info component
        self.cell_info = QPSACellInfo()
        layout.addWidget(self.cell_info)
        
        # Add test buttons
        button_layout = QHBoxLayout()
        
        # Test button 1 - Plain terrain with objects
        btn1 = QPushButton("Test Plain Cell")
        btn1.clicked.connect(self.test_plain_cell)
        button_layout.addWidget(btn1)
        
        # Test button 2 - Swamp terrain
        btn2 = QPushButton("Test Swamp Cell")
        btn2.clicked.connect(self.test_swamp_cell)
        button_layout.addWidget(btn2)
        
        # Test button 3 - Wall terrain
        btn3 = QPushButton("Test Wall Cell")
        btn3.clicked.connect(self.test_wall_cell)
        button_layout.addWidget(btn3)
        
        # Test button 4 - Empty cell
        btn4 = QPushButton("Test Empty Cell")
        btn4.clicked.connect(self.test_empty_cell)
        button_layout.addWidget(btn4)
        
        layout.addLayout(button_layout)
        
        # Connect signals for testing
        self.cell_info.itemSelected.connect(self.on_item_selected)
        self.cell_info.itemCancelSelected.connect(self.on_item_cancel_selected)
        self.cell_info.itemSelectChanged.connect(self.on_item_select_changed)
        
        self.setLayout(layout)
        
    def test_plain_cell(self):
        """Test with plain terrain cell."""
        print("[DEBUG] Testing plain cell")  # 调试输出
        
        # Create test cell info
        cell_data = CellInfo(15, 25)
        cell_data.terrain = '2'  # Plain
        
        # Add some test objects
        cell_data.add_object({
            'id': 'obj1',
            'type': 'StructureRoad',
            'name': 'Road'
        })
        cell_data.add_object({
            'id': 'obj2', 
            'type': 'StructureSpawn',
            'name': 'Spawn'
        })
        cell_data.add_object({
            'id': 'obj3',
            'type': 'Creep',
            'name': 'Worker'
        })
        
        # Set cell data
        self.cell_info.data = cell_data
        
        # Test selection states
        self.cell_info.selects = {
            'obj1': True,
            'obj2': False,
            'obj3': True
        }
        
    def test_swamp_cell(self):
        """Test with swamp terrain cell."""
        print("[DEBUG] Testing swamp cell")  # 调试输出
        
        # Create test cell info
        cell_data = CellInfo(30, 40)
        cell_data.terrain = 'A'  # Swamp
        
        # Add some test objects
        cell_data.add_object({
            'id': 'swamp_obj1',
            'type': 'StructureRoad',
            'name': 'Swamp Road'
        })
        
        # Set cell data
        self.cell_info.data = cell_data
        
    def test_wall_cell(self):
        """Test with wall terrain cell."""
        print("[DEBUG] Testing wall cell")  # 调试输出
        
        # Create test cell info
        cell_data = CellInfo(50, 60)
        cell_data.terrain = 'X'  # Wall
        
        # Add some test objects
        cell_data.add_object({
            'id': 'wall_obj1',
            'type': 'StructureWall',
            'name': 'Wall'
        })
        
        # Set cell data
        self.cell_info.data = cell_data
        
    def test_empty_cell(self):
        """Test with empty cell."""
        print("[DEBUG] Testing empty cell")  # 调试输出
        
        # Create test cell info
        cell_data = CellInfo(75, 85)
        cell_data.terrain = '2'  # Plain
        
        # Set cell data (no objects)
        self.cell_info.data = cell_data
        
    def on_item_selected(self, obj_id):
        """Handle item selected signal."""
        print(f"[DEBUG] Item selected: {obj_id}")  # 调试输出
        
    def on_item_cancel_selected(self, obj_id):
        """Handle item cancel selected signal."""
        print(f"[DEBUG] Item cancel selected: {obj_id}")  # 调试输出
        
    def on_item_select_changed(self, obj_id, selected):
        """Handle item select changed signal."""
        print(f"[DEBUG] Item select changed: {obj_id} -> {selected}")  # 调试输出


def main():
    """Main function."""
    app = QApplication(sys.argv)
    
    # Create and show test window
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()