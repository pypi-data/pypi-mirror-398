# -*- coding: utf-8 -*-
"""
QPSA Cell Object Component - 单元格对象组件
"""
from typing import List, Dict, Any, Optional
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QListWidget, QListWidgetItem, QFrame,
                             QSpacerItem, QSizePolicy, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QMimeData
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPixmap, QDrag


class QPSACellObjectItem(QWidget):
    """List item widget with remove button."""
    
    # Signals
    removeClicked = pyqtSignal(str)  # object_id
    
    def __init__(self, obj_id: str, obj_type: str, obj_name: str, 
                 x: int, y: int, method: str, image: Optional[QPixmap] = None, parent=None):
        super().__init__(parent)
        self._id = obj_id
        self._type = obj_type
        self._name = obj_name
        self._x = x
        self._y = y
        self._method = method
        self._image = image
        self._init_ui()
        
    def _init_ui(self):
        """Initialize UI components."""
        # Main horizontal layout
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)  # Reduced margins
        layout.setSpacing(2)  # Reduced spacing
        
        # Left side - shape/icon
        self._icon_label = QLabel()
        self._icon_label.setFixedSize(20, 20)  # Reduced from 30x30
        self._icon_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: #f0f0f0;
            }
        """)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_icon()
        layout.addWidget(self._icon_label)
        
        # Middle section - vertical layout for type, id and coordinates
        middle_layout = QVBoxLayout()
        middle_layout.setSpacing(1)  # Reduced spacing
        middle_layout.setContentsMargins(0, 0, 0, 0)
        
        # Type and name label (first row)
        type_name_label = QLabel(f"{self._type}: {self._name}")
        type_name_label.setStyleSheet("font-weight: bold; font-size: 9px;")  # Reduced font size
        type_name_label.setWordWrap(False)
        middle_layout.addWidget(type_name_label)
        
        # ID label (second row)
        id_label = QLabel(f"ID: {self._id}")
        id_label.setStyleSheet("font-size: 8px; color: #666;")  # Reduced font size
        id_label.setWordWrap(False)
        middle_layout.addWidget(id_label)
        
        # Coordinates and method label (third row)
        coord_method_label = QLabel(f"({self._x}, {self._y}) | {self._method}")
        coord_method_label.setStyleSheet("font-size: 8px; color: #888;")  # Reduced font size
        coord_method_label.setWordWrap(False)
        middle_layout.addWidget(coord_method_label)
        
        layout.addLayout(middle_layout)
        
        # Add spacer to push button to the right
        layout.addStretch()
        
        # Right side - remove button with red circle and cross
        self._remove_btn = QPushButton("✕")  # Changed to simpler symbol
        self._remove_btn.setFixedSize(16, 16)  # Reduced from 24x24
        self._remove_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #ff6b6b;
                border-radius: 8px;
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
        layout.addWidget(self._remove_btn)
        
        self.setLayout(layout)
        
        # self.setMinimumWidth(160)  # Reduced from 200
    
    def _update_icon(self):
        """Update the icon based on current image."""
        if self._image and not self._image.isNull():
            # Get the label size and use 90% of it for the image
            label_width = self._icon_label.width()
            label_height = self._icon_label.height()
            
            # Calculate 90% of container size
            target_width = int(label_width * 0.9)
            target_height = int(label_height * 0.9)
            
            # Scale image to fit the label with 90% size
            scaled_image = self._image.scaled(
                target_width, target_height, Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self._icon_label.setPixmap(scaled_image)
            self._icon_label.setText("")
        else:
            # Use placeholder text if no image
            self._icon_label.setPixmap(QPixmap())
            self._icon_label.setText("◆")  # Placeholder shape
    
    @pyqtSlot()
    def _on_remove_clicked(self):
        """Handle remove button click."""
        self.removeClicked.emit(self._id)
    
    # Properties
    @property
    def id(self) -> str:
        """Get object ID."""
        return self._id
    
    @property
    def image(self) -> Optional[QPixmap]:
        """Get object image/screenshot."""
        return self._image


class QPSACellObject(QWidget):
    """Cell object component that accepts drag and drop."""
    
    # Signals
    objectAdded = pyqtSignal(object)              # Emitted when an object is added
    objectRemoved = pyqtSignal(str)               # Emitted when an object is removed
    itemChanged = pyqtSignal()                    # Emitted when any item is added or removed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._objects = []  # List to store objects
        self._init_ui()
        self._drag_start_pos = None
        self._dragging_item = None
        
        # Install event filter on the list widget to capture mouse events
        self._objects_list.viewport().installEventFilter(self)
        
    def _init_ui(self):
        """Initialize UI components."""
        # Main vertical layout
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)  # Reduced margins
        layout.setSpacing(2)  # Reduced spacing
        
        # Title label
        # title_label = QLabel("Cell Objects")
        # title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        # layout.addWidget(title_label)
        
        # Objects list
        self._objects_list = QListWidget()
        self._objects_list.setFrameStyle(QFrame.Shape.Box)
        self._objects_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: white;
            }
            QListWidget::item {
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
        """)
        
        # Set widget to accept drops
        self.setAcceptDrops(True)
        
        # Disable list widget's own drag handling to use our custom implementation
        self._objects_list.setDragEnabled(False)  # Disable default drag handling
        self._objects_list.setDropIndicatorShown(True)
        self._objects_list.setDragDropMode(QListWidget.DragDropMode.NoDragDrop)  # No default drag drop
        self._objects_list.setAcceptDrops(False)
        
        layout.addWidget(self._objects_list)
        
        self.setLayout(layout)
        
        # Set minimum size - reduced from original
        self.setMinimumWidth(175)  # Reduced from 200
        self.setMaximumWidth(175)   # Reduced from 300
        self.setMinimumHeight(80)   # Reduced from 150
        self.setMaximumHeight(120)   # Reduced from 150
    
    # Drag and drop functionality
    def dragEnterEvent(self, event):
        """Handle drag enter event."""
        print(f"[DEBUG] Drag enter: hasText={event.mimeData().hasText()}, hasJSON={event.mimeData().hasFormat('application/json')}")
        if event.mimeData().hasText() or event.mimeData().hasFormat("application/json"):
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        """Handle drag move event."""
        event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handle drop event to add object."""
        mime_data = event.mimeData()
        json_data = None
        image = None
        
        print(f"[DEBUG] Drop received: hasText={event.mimeData().hasText()}, hasJSON={event.mimeData().hasFormat('application/json')}, hasImage={event.mimeData().hasImage()}")
        
        # Try to get JSON data from different sources
        if mime_data.hasFormat("application/json"):
            try:
                json_bytes = mime_data.data("application/json")
                json_str = json_bytes.data().decode('utf-8')
                print(f"[DEBUG] JSON data: {json_str}")
                json_data = json.loads(json_str)
            except Exception as e:
                print(f"[DEBUG] Failed to parse JSON data: {e}")
        elif mime_data.hasText():
            try:
                json_str = mime_data.text()
                print(f"[DEBUG] Text data: {json_str}")
                json_data = json.loads(json_str)
            except Exception as e:
                print(f"[DEBUG] Failed to parse text as JSON: {e}")
        
        # Try to get image data if available
        if mime_data.hasImage():
            try:
                image = QPixmap(mime_data.imageData())
                print(f"[DEBUG] Image data received: {image.size()}")
            except Exception as e:
                print(f"[DEBUG] Failed to get image data: {e}")
        
        if json_data:
            # Handle both single object and array of objects
            if isinstance(json_data, list):
                # Array format: [{x, y, type, method, id, name}, ...]
                print(f"[DEBUG] Received array of {len(json_data)} objects")
                for obj in json_data:
                    self.add_object(obj, image)
                event.acceptProposedAction()
                print(f"[DEBUG] Array of objects added successfully")
            elif isinstance(json_data, dict):
                # Single object format: {x, y, type, method, id, name}
                self.add_object(json_data, image)
                event.acceptProposedAction()
                print(f"[DEBUG] Single object added successfully: {json_data}")
            else:
                print(f"[DEBUG] Invalid JSON format: expected dict or list, got {type(json_data)}")
        else:
            print(f"[DEBUG] No valid JSON data found")
    
    def add_object(self, obj_data: Dict[str, Any], image: Optional[QPixmap] = None):
        """Add an object to the list, rejecting duplicates with same x, y, type."""
        # Extract required fields
        obj_id = obj_data.get('id', 'unknown')
        obj_type = obj_data.get('type', 'Unknown')
        obj_name = obj_data.get('name', obj_id)
        x = obj_data.get('x', 0)
        y = obj_data.get('y', 0)
        method = obj_data.get('method', '')
        
        # Check for duplicates with same x, y, type
        for existing_obj in self._objects:
            existing_x = existing_obj.get('x', 0)
            existing_y = existing_obj.get('y', 0)
            existing_type = existing_obj.get('type', 'Unknown')
            if existing_x == x and existing_y == y and existing_type == obj_type:
                print(f"[DEBUG] Rejected duplicate object: {obj_type} at ({x}, {y})")
                return  # Reject duplicate
        
        # Create custom widget for the object
        item_widget = QPSACellObjectItem(
            obj_id, obj_type, obj_name, x, y, method, image
        )
        item_widget.removeClicked.connect(self._on_remove_clicked)
        
        # Create list widget item and set our custom widget
        list_item = QListWidgetItem()
        list_item.setSizeHint(item_widget.sizeHint())
        
        self._objects_list.addItem(list_item)
        self._objects_list.setItemWidget(list_item, item_widget)
        
        # Add to internal list
        self._objects.append(obj_data)
        
        # Emit signals
        self.objectAdded.emit(obj_data)
        self.itemChanged.emit()
        print(f"[DEBUG] Added object: {obj_type} at ({x}, {y})")
    
    @pyqtSlot(str)
    def _on_remove_clicked(self, obj_id: str):
        """Handle remove button click."""
        # Find and remove the item from the list
        for i in range(self._objects_list.count()):
            list_item = self._objects_list.item(i)
            widget = self._objects_list.itemWidget(list_item)
            if isinstance(widget, QPSACellObjectItem) and widget.id == obj_id:
                # Remove from internal list
                for obj in self._objects:
                    if obj.get('id') == obj_id:
                        self._objects.remove(obj)
                        break
                
                # Remove from UI
                self._objects_list.takeItem(i)
                
                # Emit signals
                self.objectRemoved.emit(obj_id)
                self.itemChanged.emit()
                break
    
    # Public properties
    @property
    def objects(self) -> List[Dict[str, Any]]:
        """Get all objects."""
        return self._objects.copy()
    
    def clear_objects(self):
        """Clear all objects."""
        self._objects_list.clear()
        self._objects.clear()
        
    def remove_object(self, obj_id: str):
        """Remove an object by ID."""
        self._on_remove_clicked(obj_id)
    
    def set_list_background_color(self, color: str):
        """Set the background color of the internal list widget."""
        # Use triple quotes for multi-line f-string
        style_sheet = f"""
            QListWidget {{
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: {color};
            }}
            QListWidget::item {{
                border-bottom: 1px solid #eee;
            }}
            QListWidget::item:selected {{
                background-color: #e3f2fd;
            }}
        """
        self._objects_list.setStyleSheet(style_sheet)
    
    def eventFilter(self, obj, event):
        """Handle mouse events for the list widget viewport."""
        if obj == self._objects_list.viewport():
            if event.type() == event.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    # Store drag start position and item
                    self._drag_start_pos = event.pos()
                    # Get the item under the mouse
                    item = self._objects_list.itemAt(event.pos())
                    self._dragging_item = item
            elif event.type() == event.Type.MouseMove:
                if event.buttons() & Qt.MouseButton.LeftButton:
                    if self._drag_start_pos is not None and self._dragging_item is not None:
                        # Calculate drag distance
                        drag_distance = (event.pos() - self._drag_start_pos).manhattanLength()
                        if drag_distance > 20:  # Minimum drag distance
                            widget = self._objects_list.itemWidget(self._dragging_item)
                            if isinstance(widget, QPSACellObjectItem):
                                # Find the corresponding object data
                                for obj_data in self._objects:
                                    if obj_data.get('id') == widget.id:
                                        self._initiate_drag(obj_data, widget.image)
                                        # Reset drag state
                                        self._drag_start_pos = None
                                        self._dragging_item = None
                                        break
            elif event.type() == event.Type.MouseButtonRelease:
                # Reset drag state
                self._drag_start_pos = None
                self._dragging_item = None
        return False  # Let the event propagate
    
    def _initiate_drag(self, obj_data: Dict[str, Any], image: Optional[QPixmap]):
        """Initiate drag operation with object data and image."""
        print(f"[DEBUG] Initiating drag for object: {obj_data.get('type')} at ({obj_data.get('x')}, {obj_data.get('y')})")
        
        # Create JSON data with required fields
        drag_json = {
            'x': obj_data.get('x', 0),
            'y': obj_data.get('y', 0),
            'id': obj_data.get('id', 'unknown'),
            'name': obj_data.get('name', obj_data.get('id', 'unknown')),
            'method': obj_data.get('method', ''),
            'type': obj_data.get('type', 'Unknown')
        }
        
        # Convert to JSON string
        json_str = json.dumps(drag_json, ensure_ascii=False)
        print(f"[DEBUG] Drag JSON: {json_str}")
        
        # Create MIME data
        mime_data = QMimeData()
        mime_data.setText(json_str)
        mime_data.setData('application/json', json_str.encode('utf-8'))
        
        # Add image if available
        if image and not image.isNull():
            mime_data.setImageData(image)
            print(f"[DEBUG] Adding image to drag: {image.size()}")
        
        # Create drag object
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        
        # Set a simple drag cursor
        # You could set a custom pixmap here if needed
        
        # Start drag operation
        drag.exec(Qt.DropAction.CopyAction)
        print(f"[DEBUG] Drag completed")
