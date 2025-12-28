# -*- coding: utf-8 -*-
"""
QPSA Map Marker Component - 地图标记组件
左右大布局，右边是QPSAMapViewer，左边是信息栏
"""
from typing import List, Dict, Any, Optional
import json
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
                             QListWidget, QListWidgetItem, QFrame, QSpacerItem,
                             QSizePolicy, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QPixmap

from pyscreeps_arena.ui.qmapv.qmapv import QPSAMapViewer
from pyscreeps_arena.ui.qmapv.qcinfo import QPSACellInfo
from pyscreeps_arena.ui.qmapker.qvariable import QPSACoVariable
from pyscreeps_arena.ui.qmapker.to_code import json2code


class AddVariableWidget(QWidget):
    """Special widget with centered + button to add new variable."""
    
    # Signal emitted when add button is clicked
    addRequested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        """Initialize UI components."""
        # Main layout with center alignment
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add button with + symbol
        self._add_button = QPushButton("➕")
        self._add_button.setFixedSize(40, 40)
        self._add_button.setStyleSheet("""
            QPushButton {
                border: 2px dashed #ccc;
                border-radius: 20px;
                background-color: #f9f9f9;
                font-size: 20px;
                color: #666;
            }
            QPushButton:hover {
                border-color: #2196f3;
                background-color: #e3f2fd;
                color: #2196f3;
            }
            QPushButton:pressed {
                background-color: #bbdefb;
            }
        """)
        self._add_button.clicked.connect(self.addRequested.emit)
        layout.addWidget(self._add_button)
        
        self.setLayout(layout)


class QPSAMapMarker(QWidget):
    """Map marker component with left info panel and right map viewer."""
    
    # Signals
    onVariableChanged = pyqtSignal()  # Emitted when any variable is changed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._variables: List[QPSACoVariable] = []
        self._selected_cell_info: Optional[Dict[str, Any]] = None
        self._init_ui()
        
    def _init_ui(self):
        """Initialize UI components."""
        # Main horizontal layout (left-right)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(8)
        
        # Left panel (info栏)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        
        # First row - selected cell info
        self._cell_info = QPSACellInfo()
        self._cell_info.setMinimumWidth(200)
        # self._cell_info.setMaximumHeight(200)
        left_layout.addWidget(self._cell_info)
        
        # Second row - variables list
        self._variables_list = QListWidget()
        self._variables_list.setFrameStyle(QFrame.Shape.Box)
        self._variables_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::item {
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
        """)
        self._variables_list.setSpacing(4)
        self._variables_list.setMinimumWidth(200)
        # self._variables_list.setMaximumHeight(200)
        left_layout.addWidget(self._variables_list)
        
        # Third row - control buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)
        
        # Reset button
        self._reset_button = QPushButton("Reset")
        self._reset_button.setFixedHeight(30)
        self._reset_button.setFixedWidth(80)
        self._reset_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f44336;
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        self._reset_button.clicked.connect(self._on_reset_clicked)
        button_layout.addWidget(self._reset_button)
        
        # Copy button
        self._copy_button = QPushButton("Copy")
        self._copy_button.setFixedHeight(30)
        self._copy_button.setFixedWidth(80) 
        self._copy_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #2196f3;
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:pressed {
                background-color: #1565c0;
            }
        """)
        self._copy_button.clicked.connect(self._on_copy_clicked)
        button_layout.addWidget(self._copy_button)
        
        button_layout.addStretch()
        left_layout.addLayout(button_layout)
        
        # Add initial add widget
        self._add_add_widget()
        
        main_layout.addWidget(left_panel, 1)  # Left panel takes 1/4 space
        
        # Right panel - map viewer
        self._map_viewer = QPSAMapViewer()
        main_layout.addWidget(self._map_viewer, 3)  # Map viewer takes 3/4 space
        
        self.setLayout(main_layout)
        
        # Connect map viewer signals
        self._map_viewer.selectChanged.connect(self._on_cell_selected)
        
    def _add_add_widget(self):
        """Add the special add widget to the list."""
        add_widget = AddVariableWidget()
        add_widget.addRequested.connect(self._on_add_variable)
        
        # Create list item
        list_item = QListWidgetItem()
        list_item.setSizeHint(add_widget.sizeHint())
        
        self._variables_list.addItem(list_item)
        self._variables_list.setItemWidget(list_item, add_widget)
        
    def _add_variable_widget(self, variable: QPSACoVariable):
        """Add a variable widget to the list."""
        # Create list item first
        list_item = QListWidgetItem()
        list_item.setSizeHint(variable.sizeHint())
        
        # Connect variable signals
        variable.onItemChanged.connect(self._on_variable_changed)
        variable.removeRequested.connect(lambda: self._on_remove_variable(variable))
        
        # Connect to dual button clicks to update size
        variable._dual_button.clicked.connect(lambda: self._on_variable_dual_changed(variable, list_item))
        
        self._variables_list.insertItem(self._variables_list.count() - 1, list_item)
        self._variables_list.setItemWidget(list_item, variable)
        
        self._variables.append(variable)
        
    @pyqtSlot()
    def _on_add_variable(self):
        """Handle add variable button click."""
        print("[DEBUG] Adding new variable")
        new_variable = QPSACoVariable()
        new_variable.showRemoveButton = True  # Set remove button to be visible
        self._add_variable_widget(new_variable)
        
    def _on_remove_variable(self, variable: QPSACoVariable):
        """Handle remove variable request."""
        print("[DEBUG] Removing variable")
        
        # Find the variable in the list
        if variable in self._variables:
            # Find the corresponding list item
            for i in range(self._variables_list.count()):
                item = self._variables_list.item(i)
                if item:
                    widget = self._variables_list.itemWidget(item)
                    if widget == variable:
                        # Remove from list
                        self._variables_list.takeItem(i)
                        # Remove from variables list
                        self._variables.remove(variable)
                        # Delete the widget
                        variable.deleteLater()
                        print(f"[DEBUG] Variable removed at index {i}")
                        break
        
        self.onVariableChanged.emit()
        
    def _on_variable_dual_changed(self, variable: QPSACoVariable, list_item: QListWidgetItem):
        """Handle dual mode change for a variable."""
        # Update the list item size hint when dual mode changes
        new_size = variable.sizeHint()
        list_item.setSizeHint(new_size)
        print(f"[DEBUG] Dual mode changed, updated item size: {new_size}")
    
    @pyqtSlot()
    def _on_copy_clicked(self):
        """Handle copy button click to copy variables to clipboard as Python code."""
        print("[DEBUG] Copying variables to clipboard as Python code")
        
        # Get variables data
        variables_data = self.variables
        print(f"[DEBUG] Variables data: {variables_data}")
        
        # Convert to Python code using json2code function
        try:
            code = json2code(variables_data)
            print(f"[DEBUG] Generated code: {code}")
            
            # Copy to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(code)
            print("[DEBUG] Python code copied to clipboard")
        except Exception as e:
            print(f"[DEBUG] Error generating code: {e}")
            # Fallback to JSON if code generation fails
            json_str = json.dumps(variables_data, ensure_ascii=False, indent=2)
            clipboard = QApplication.clipboard()
            clipboard.setText(json_str)
            print("[DEBUG] JSON fallback copied to clipboard")
        
    @pyqtSlot()
    def _on_reset_clicked(self):
        """Handle reset button click."""
        print("[DEBUG] Resetting info panel")
        
        # Clear cell info
        self._cell_info.data = None
        self._selected_cell_info = None
        
        # Clear all variables
        for variable in self._variables:
            variable.reset()
            
        # Remove all variable widgets from list (keep only add widget)
        while self._variables_list.count() > 1:
            item = self._variables_list.takeItem(0)
            if item:
                widget = self._variables_list.itemWidget(item)
                if widget and widget != self._variables_list.itemWidget(self._variables_list.item(self._variables_list.count() - 1)):
                    widget.deleteLater()
        
        self._variables.clear()
        
    @pyqtSlot(object)
    def _on_cell_selected(self, cell_info):
        """Handle cell selection from map viewer."""
        print(f"[DEBUG] Cell selected: {cell_info}")
        if cell_info:
            self._cell_info.data = cell_info
            # Transfer screenshot to QPSACellInfo
            self._cell_info.image = self._map_viewer.image
            self._selected_cell_info = {
                'x': cell_info.x,
                'y': cell_info.y,
                'terrain': cell_info.terrain,
                'objects': cell_info.objects.copy() if cell_info.objects else []
            }
        else:
            self._cell_info.data = None
            self._selected_cell_info = None
            
    @pyqtSlot()
    def _on_variable_changed(self):
        """Handle variable changes."""
        print("[DEBUG] Variable changed")
        self.onVariableChanged.emit()
        
    # Properties
    @property
    def variables(self) -> List[Dict[str, Any]]:
        """Get all variables as list of dictionaries."""
        return [var.data for var in self._variables]
        
    @property
    def selectedCellInfo(self) -> Optional[Dict[str, Any]]:
        """Get selected cell information."""
        return self._selected_cell_info.copy() if self._selected_cell_info else None
        
    @property
    def mapViewer(self) -> QPSAMapViewer:
        """Get the map viewer component."""
        return self._map_viewer