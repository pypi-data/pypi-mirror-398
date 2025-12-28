# -*- coding: utf-8 -*-
"""
QPSA Co Variable Component - 对称变量组件
"""
from typing import List, Dict, Any
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QSpacerItem,
                             QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QSize
from PyQt6.QtGui import QPalette, QColor

from pyscreeps_arena.ui.qmapv import QPSACellObject

# Import configuration from build.py
import sys
import os
# Add the project root directory to Python path
from pyscreeps_arena import config

# Language mapping
LANG = {
    'cn': {
        'symmetric': '对称',
    },
    'en': {
        'symmetric': 'Symmetric',
    }
}

def lang(key: str) -> str:
    """Helper function to get translated text"""
    return LANG[config.language if hasattr(config, 'language') and config.language in LANG else 'cn'][key]


class QPSACoVariable(QWidget):
    """Co-variable component with symmetric option."""
    
    # Class variable to track instance count
    _instance_count = 0
    
    # Signals
    onItemChanged = pyqtSignal()  # Emitted when any item is added or removed
    removeRequested = pyqtSignal()  # Emitted when remove button is clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dual = False
        self._true_objects = []
        self._false_objects = []
        self._show_remove_btn = False  # New property to control remove button
        
        # Increment instance count and get the current number
        QPSACoVariable._instance_count += 1
        self._instance_number = QPSACoVariable._instance_count
        
        self._init_ui()
        
    def _init_ui(self):
        """Initialize UI components."""
        # Main vertical layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(4, 4, 4, 4)  # Reduced margins
        main_layout.setSpacing(3)  # Reduced spacing
        
        # First row - input, checkbox, and remove button in 7:3:2 ratio
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(2)  # Reduced spacing
        
        # Input box with placeholder (70%)
        self._input = QLineEdit()
        self._input.setPlaceholderText(f"VAR{self._instance_number}")
        self._input.setStyleSheet("font-size: 11px;")  # Reduced font size
        self._input.setFixedHeight(24)  # Reduced height
        top_row.addWidget(self._input, 7)
        
        # Button-style checkbox for dual mode (30%)
        self._dual_button = QPushButton(lang('symmetric'))
        self._dual_button.setCheckable(True)
        self._dual_button.setFixedHeight(24)  # Reduced from 22 to 18
        self._dual_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #ccc;
                border-radius: 2px;
                background-color: #f0f0f0;
                font-size: 9px;
                padding: 1px;
            }
            QPushButton:checked {
                background-color: #e3f2fd;
                border-color: #2196f3;
            }
        """)
        self._dual_button.clicked.connect(self._on_dual_changed)
        top_row.addWidget(self._dual_button, 3)
        
        # Remove button (20% - shown based on property)
        self._remove_btn = QPushButton("⛔")
        self._remove_btn.setFixedHeight(24)
        self._remove_btn.setFixedWidth(24)  # Make it square
        self._remove_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #ff6b6b;
                border-radius: 12px;
                background-color: #ffe6e6;
                color: #ff6b6b;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff6b6b;
                color: white;
            }
            QPushButton:pressed {
                background-color: #ff5252;
            }
        """)
        self._remove_btn.clicked.connect(self._on_remove_clicked)
        self._remove_btn.setVisible(self._show_remove_btn)
        top_row.addWidget(self._remove_btn, 2)
        
        main_layout.addLayout(top_row)
        
        # Second row - QPSACellObject components
        objects_widget = QWidget()
        self._objects_layout = QVBoxLayout(objects_widget)
        self._objects_layout.setContentsMargins(0, 0, 0, 0)
        self._objects_layout.setSpacing(2)  # Reduced spacing
        
        # True objects section
        self._true_objects_widget = QPSACellObject()
        self._true_objects_widget.objectAdded.connect(self._on_item_changed)
        self._true_objects_widget.objectRemoved.connect(self._on_item_changed)
        self._true_objects_widget.itemChanged.connect(self._on_item_changed)
        self._objects_layout.addWidget(self._true_objects_widget)
        
        # Separator for dual mode
        self._mid_separator = QFrame()
        self._mid_separator.setFrameShape(QFrame.Shape.HLine)
        self._mid_separator.setFrameShadow(QFrame.Shadow.Sunken)
        self._mid_separator.setVisible(False)
        self._objects_layout.addWidget(self._mid_separator)
        
        # False objects section (for dual mode)
        self._false_objects_widget = QPSACellObject()
        self._false_objects_widget.objectAdded.connect(self._on_item_changed)
        self._false_objects_widget.objectRemoved.connect(self._on_item_changed)
        self._false_objects_widget.itemChanged.connect(self._on_item_changed)
        # Set background color to #FFF0F5 (light red) for the list content
        self._false_objects_widget.set_list_background_color("#FFF0F5")
        self._false_objects_widget.setVisible(False)
        self._objects_layout.addWidget(self._false_objects_widget)
        
        main_layout.addWidget(objects_widget)
        
        self.setLayout(main_layout)
        self.setMinimumWidth(182)
        self.setMaximumWidth(182)
        
    @pyqtSlot(bool)
    def _on_dual_changed(self, checked: bool):
        """Handle dual mode toggle."""
        self._dual = checked
        self._false_objects_widget.setVisible(checked)
        self._mid_separator.setVisible(checked)
        self._on_item_changed()
    
    @pyqtSlot()
    def _on_remove_clicked(self):
        """Handle remove button click."""
        self.removeRequested.emit()  # Request removal from parent
    
    @pyqtSlot()
    def _on_item_changed(self):
        """Handle item changes in QPSACellObject components."""
        # Update internal lists
        self._true_objects = self._true_objects_widget.objects
        if self._dual:
            self._false_objects = self._false_objects_widget.objects
        else:
            self._false_objects = []
        
        # Emit callback
        self.onItemChanged.emit()
    
    # Properties
    @property
    def dual(self) -> bool:
        """Get/set dual mode status."""
        return self._dual
    
    @dual.setter
    def dual(self, value: bool):
        """Set dual mode status."""
        self._dual = value
        self._dual_button.setChecked(value)
        self._false_objects_widget.setVisible(value)
        self._mid_separator.setVisible(value)
        self._on_item_changed()
        
        # Recalculate height by updating size hint and notifying parent
        self.updateGeometry()
        if self.parent():
            # Notify parent layout to recalculate
            self.parent().updateGeometry()
            
            # If this is in a QListWidget, update the item size
            if hasattr(self.parent(), 'parent') and self.parent().parent():
                list_widget = self.parent().parent()
                if hasattr(list_widget, 'itemWidget'):
                    # Find the corresponding item and update its size hint
                    for i in range(list_widget.count()):
                        item = list_widget.item(i)
                        if item and list_widget.itemWidget(item) == self:
                            item.setSizeHint(self.sizeHint())
                            print(f"[DEBUG] Updated item size hint for dual mode: {self.sizeHint()}")
                            break
    
    @property
    def trueObjects(self) -> List[Dict[str, Any]]:
        """Get true objects list."""
        return self._true_objects.copy()
    
    @trueObjects.setter
    def trueObjects(self, value: List[Dict[str, Any]]):
        """Set true objects list."""
        # Clear current objects
        self._true_objects_widget.clear_objects()
        # Add new objects
        for obj in value:
            self._true_objects_widget.add_object(obj)
        self._on_item_changed()
    
    @property
    def falseObjects(self) -> List[Dict[str, Any]]:
        """Get false objects list."""
        return self._false_objects.copy()
    
    @falseObjects.setter
    def falseObjects(self, value: List[Dict[str, Any]]):
        """Set false objects list."""
        # Clear current objects
        self._false_objects_widget.clear_objects()
        # Add new objects
        for obj in value:
            self._false_objects_widget.add_object(obj)
        self._on_item_changed()
    
    @property
    def showRemoveButton(self) -> bool:
        """Get/set whether to show the remove button."""
        return self._show_remove_btn
    
    @showRemoveButton.setter
    def showRemoveButton(self, value: bool):
        """Set whether to show the remove button."""
        self._show_remove_btn = value
        self._remove_btn.setVisible(value)
    
    def reset(self):
        """Reset component to default state."""
        self._input.clear()
        self.dual = False
        self._true_objects_widget.clear_objects()
        self._false_objects_widget.clear_objects()
    
    def sizeHint(self):
        """Calculate preferred size based on dual mode."""
        # Base height for single mode
        base_height = 120
        
        # Add height for dual mode (additional objects widget)
        if self._dual:
            base_height += 80  # Additional space for false objects
            
        # Add height based on content
        true_count = len(self._true_objects_widget.objects)
        false_count = len(self._false_objects_widget.objects) if self._dual else 0
        
        # Estimate height based on object count (roughly 25px per object)
        content_height = max(true_count, false_count) * 25
        total_height = base_height + content_height
        
        # Keep width fixed
        return QSize(182, min(total_height, 400))  # Cap at 400px max height
    
    @property
    def data(self) -> Dict[str, Any]:
        """Get component data as a dictionary."""
        # Use placeholder text as key if input is empty
        key = self._input.text() if self._input.text() else self._input.placeholderText()
        return {
            'key': key,
            'dual': self._dual,
            'pos': self._true_objects.copy(),
            'neg': self._false_objects.copy()
        }
    
    # Static method to get current instance count
    @staticmethod
    def get_instance_count() -> int:
        """Get current instance count."""
        return QPSACoVariable._instance_count
