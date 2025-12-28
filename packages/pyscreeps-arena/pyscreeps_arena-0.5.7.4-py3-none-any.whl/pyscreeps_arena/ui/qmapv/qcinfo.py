# -*- coding: utf-8 -*-
"""
QPSA Cell Info Component - 单元格信息组件
"""
from typing import Optional, List, Dict, Any
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QListWidget, QListWidgetItem, QFrame,
                             QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QRectF, QMimeData
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QBrush, QPainterPath, QMouseEvent, QDrag

from .qmapv import CellInfo


class QPSACellObjectItem(QWidget):
    """Game object item widget for the list."""
    
    def __init__(self, obj_id: str, obj_type: str, obj_name: str, 
                 x: int, y: int, image: Optional[QPixmap] = None, method: str = "", parent=None):
        super().__init__(parent)
        self._id = obj_id
        self._name = obj_name
        self._x = x
        self._y = y
        self._type = obj_type
        self._method = method
        self._image = image
        self._init_ui(obj_type)
        
    def _init_ui(self, obj_type: str):
        """Initialize UI components."""
        # Main horizontal layout
        layout = QHBoxLayout()
        layout.setContentsMargins(3, 3, 3, 3)
        
        # Left side - shape/icon
        self._icon_label = QLabel()
        self._icon_label.setFixedSize(30, 30)  # Increased by 10%
        self._icon_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f0f0f0;
            }
        """)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_icon()
        layout.addWidget(self._icon_label)
        
        # Middle section - vertical layout for type and id
        middle_layout = QVBoxLayout()
        middle_layout.setSpacing(2)
        
        # Type label (first row)
        type_label = QLabel(obj_type)
        type_label.setStyleSheet("font-weight: bold; font-size: 11px;")  # Increased by 10%
        type_label.setWordWrap(False)
        middle_layout.addWidget(type_label)
        
        # ID label (second row)
        id_label = QLabel(self._id)
        id_label.setStyleSheet("font-size: 10px; color: #666;")  # Increased by 10%
        id_label.setWordWrap(False)
        middle_layout.addWidget(id_label)
        
        layout.addLayout(middle_layout)
        
        # Add spacer to push content to the left
        layout.addStretch()
        
        self.setLayout(layout)
        
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
            print(f"[DEBUG] Set icon size to {target_width}x{target_height} (90% of {label_width}x{label_height})")  # 调试输出
        else:
            # Use placeholder text if no image
            self._icon_label.setPixmap(QPixmap())
            self._icon_label.setText("◆")  # Placeholder shape
        
    # Properties
    @property
    def id(self) -> str:
        """Get object ID."""
        return self._id
    
    @property
    def name(self) -> str:
        """Get object name."""
        return self._name
    
    @property
    def image(self) -> Optional[QPixmap]:
        """Get/set object icon image."""
        return self._image
    
    @image.setter
    def image(self, value: Optional[QPixmap]):
        """Set object icon image."""
        self._image = value
        self._update_icon()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press event to start drag."""
        if event.button() == Qt.MouseButton.LeftButton:
            print(f"[DEBUG] Starting drag for object: {self._id}")
            # Create drag data
            drag_data = {
                "x": self._x,
                "y": self._y,
                "type": self._type,
                "method": getattr(self, '_method', ''),  # Use instance method or default empty
                "id": self._id,
                "name": self._name
            }
            
            # Convert to JSON string
            json_data = json.dumps(drag_data, ensure_ascii=False, indent=2)
            print(f"[DEBUG] Drag data: {json_data}")
            
            # Create mime data
            mime_data = QMimeData()
            mime_data.setText(json_data)
            mime_data.setData("application/json", json_data.encode('utf-8'))
            
            # Add pixmap if available
            if self._image and not self._image.isNull():
                print(f"[DEBUG] Adding image to drag data")
                mime_data.setImageData(self._image)
            
            # Create drag object
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            
            # Start drag with multiple drop actions
            drag.exec(Qt.DropAction.CopyAction | Qt.DropAction.MoveAction)
            
            event.accept()


class CoordinateLabel(QLabel):
    """Custom coordinate label that supports drag and drop."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._x = 0
        self._y = 0
        
    def set_coordinates(self, x: int, y: int):
        """Set coordinates and update display."""
        self._x = x
        self._y = y
        self.setText(f"{{x: {x}, y: {y}}}")
        
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press event to start drag."""
        if event.button() == Qt.MouseButton.LeftButton:
            print(f"[DEBUG] Starting drag for coordinates: ({self._x}, {self._y})")
            # Create drag data for Point type
            drag_data = {
                "x": self._x,
                "y": self._y,
                "type": "Point",
                "method": "Point",
                "id": f"{self._x}◇{self._y}",
                "name": f"p{self._x}◇{self._y}"
            }
            
            # Convert to JSON string
            json_data = json.dumps(drag_data, ensure_ascii=False, indent=2)
            print(f"[DEBUG] Drag data: {json_data}")
            
            # Create mime data
            mime_data = QMimeData()
            mime_data.setText(json_data)
            mime_data.setData("application/json", json_data.encode('utf-8'))
            
            # Create drag object
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            
            # Start drag with multiple drop actions
            drag.exec(Qt.DropAction.CopyAction | Qt.DropAction.MoveAction)
            
            event.accept()


class QPSACellInfo(QWidget):
    """Cell information display component."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: Optional[CellInfo] = None
        self._x: int = 0
        self._y: int = 0
        self._objects: List[Dict[str, Any]] = []
        self._image: Optional[QPixmap] = None  # Map image for object icons
        self._init_ui()
        
    def _init_ui(self):
        """Initialize UI components."""
        # Main vertical layout
        layout = QVBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)  # Further reduced margins
        layout.setSpacing(4)  # Further reduced spacing
        
        # First row - coordinates
        self._coord_label = CoordinateLabel()
        self._coord_label.setStyleSheet("font-family: monospace; font-size: 21px; font-weight: bold;")
        self._coord_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._coord_label)
        
        # Second row - terrain info with rounded rectangle
        terrain_frame = QFrame()
        terrain_frame.setFrameStyle(QFrame.Shape.NoFrame)
        terrain_layout = QHBoxLayout()
        terrain_layout.setContentsMargins(0, 0, 0, 0)
        
        # Terrain type label
        self._terrain_label = QLabel("Plain")
        self._terrain_label.setFixedWidth(50)  # Reduced from 60
        self._terrain_label.setStyleSheet("font-size: 12px;")
        terrain_layout.addWidget(self._terrain_label)
        
        # Terrain color indicator (custom painted widget)
        self._terrain_indicator = TerrainIndicator()
        self._terrain_indicator.setFixedSize(30, 16)  # Reduced from 40x20 (保持不变)
        terrain_layout.addWidget(self._terrain_indicator)
        
        # Spacer
        terrain_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Policy.Expanding))  # Reduced from 20
        
        # Cost label
        self._cost_label = QLabel("Cost: 2")
        self._cost_label.setStyleSheet("font-size: 12px; color: #666;")
        terrain_layout.addWidget(self._cost_label)
        
        terrain_frame.setLayout(terrain_layout)
        layout.addWidget(terrain_frame)
        
        # Third row - objects list
        self._objects_list = QListWidget()
        self._objects_list.setFrameStyle(QFrame.Shape.Box)
        self._objects_list.setMaximumHeight(80)  # Approximately 2 items high
        self._objects_list.setStyleSheet("""
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
        # Enable drag functionality
        self._objects_list.setDragEnabled(True)
        self._objects_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        
        # Enable drop functionality for the widget
        self.setAcceptDrops(True)
        
        layout.addWidget(self._objects_list)
        
        self.setLayout(layout)
        
        # Set minimum size - further reduced to match list item width
        self.setMinimumWidth(180)  # Further reduced from 180 (10% reduction)
        self.setMaximumWidth(180)
        self.setMinimumHeight(200)  # Increased for larger font
        self.setMaximumHeight(200)
        
        
    def _update_coord_display(self):
        """Update coordinate display."""
        if self._data:
            self._coord_label.set_coordinates(self._data.x, self._data.y)
        else:
            self._coord_label.set_coordinates(0, 0)
            
    def _update_terrain_display(self):
        """Update terrain display."""
        if self._data:
            terrain_map = {
                '2': 'Plain',
                'A': 'Swamp', 
                'X': 'TWall'
            }
            terrain_type = terrain_map.get(self._data.terrain, 'Plain')
            self._terrain_label.setText(terrain_type)
            
            # Update terrain color
            terrain_colors = {
                '2': QColor(144, 238, 144),    # Light green for plain
                'A': QColor(160, 82, 45),      # Brown for swamp
                'X': QColor(128, 128, 128)   # Gray for wall
            }
            color = terrain_colors.get(self._data.terrain, QColor(144, 238, 144))
            self._terrain_indicator.set_color(color)
            
            # Update cost
            cost = self._data.cost
            self._cost_label.setText(f"Cost: {cost}")
        else:
            self._terrain_label.setText("Plain")
            self._terrain_indicator.set_color(QColor(144, 238, 144))
            self._cost_label.setText("Cost: 2")
            
    def _update_objects_list(self):
        """Update objects list display."""
        self._objects_list.clear()
        
        if self._objects:
            for obj in self._objects:
                obj_id = obj.get('id', 'unknown')
                obj_type = obj.get('type', 'Unknown')
                obj_name = obj.get('name', obj_id)
                
                # Extract object icon from map image if available
                obj_image = None
                if self._image and not self._image.isNull() and self._data:
                    # Calculate cell size based on map image dimensions
                    # Assuming map is 100x100 cells (default from qmapv)
                    map_width = 100
                    map_height = 100
                    
                    cell_width = self._image.width() // map_width
                    cell_height = self._image.height() // map_height
                    
                    # Calculate the position of this cell in the image
                    cell_x_offset = self._data.x * cell_width
                    cell_y_offset = self._data.y * cell_height
                    
                    # Extract the entire cell region
                    if (cell_x_offset + cell_width <= self._image.width() and 
                        cell_y_offset + cell_height <= self._image.height() and
                        cell_x_offset >= 0 and cell_y_offset >= 0):
                        # Extract the full cell
                        cell_image = self._image.copy(cell_x_offset, cell_y_offset, cell_width, cell_height)
                        obj_image = cell_image
                
                # Get method from object data if available
                method = obj.get('method', '')
                
                # Create custom widget for the object
                item_widget = QPSACellObjectItem(
                    obj_id, obj_type, obj_name, self._x, self._y, obj_image, method
                )
                
                # Create list widget item and set our custom widget
                list_item = QListWidgetItem()
                list_item.setSizeHint(item_widget.sizeHint())
                
                self._objects_list.addItem(list_item)
                self._objects_list.setItemWidget(list_item, item_widget)
        
    # Public properties
    @property
    def data(self) -> Optional[CellInfo]:
        """Get/set cell data."""
        return self._data
    
    @data.setter
    def data(self, value: Optional[CellInfo]):
        """Set cell data and update display."""
        self._data = value
        if value:
            self._x = value.x
            self._y = value.y
            self._objects = value.objects
        else:
            self._x = 0
            self._y = 0
            self._objects = []
            
        self._update_coord_display()
        self._update_terrain_display()
        self._update_objects_list()
        
    @property
    def x(self) -> int:
        """Get X coordinate."""
        return self._x
    
    @x.setter
    def x(self, value: int):
        """Set X coordinate."""
        self._x = value
        self._update_coord_display()
        
    @property
    def y(self) -> int:
        """Get Y coordinate."""
        return self._y
    
    @y.setter
    def y(self, value: int):
        """Set Y coordinate."""
        self._y = value
        self._update_coord_display()
        
    @property
    def objects(self) -> List[Dict[str, Any]]:
        """Get objects list."""
        return self._objects.copy()
    
    @objects.setter
    def objects(self, value: List[Dict[str, Any]]):
        """Set objects list."""
        self._objects = value
        self._update_objects_list()
        
    @property
    def image(self) -> Optional[QPixmap]:
        """Get/set map image for object icons."""
        return self._image
    
    @image.setter
    def image(self, value: Optional[QPixmap]):
        """Set map image for object icons."""
        self._image = value
        self._update_objects_list()
    
    # Drag and drop functionality
    def dragEnterEvent(self, event):
        """Accept drag enter events."""
        print(f"[DEBUG] QPSACellInfo drag enter: hasText={event.mimeData().hasText()}")
        if event.mimeData().hasText() or event.mimeData().hasFormat("application/json"):
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handle drop event to add objects."""
        mime_data = event.mimeData()
        json_data = None
        image = None
        
        print(f"[DEBUG] QPSACellInfo drop received: hasText={event.mimeData().hasText()}, hasJSON={event.mimeData().hasFormat('application/json')}, hasImage={event.mimeData().hasImage()}")
        
        # Try to get JSON data from different sources
        if mime_data.hasFormat("application/json"):
            try:
                json_bytes = mime_data.data("application/json")
                json_str = json_bytes.data().decode('utf-8')
                print(f"[DEBUG] QPSACellInfo JSON data: {json_str}")
                json_data = json.loads(json_str)
            except Exception as e:
                print(f"[DEBUG] QPSACellInfo failed to parse JSON data: {e}")
        elif mime_data.hasText():
            try:
                json_str = mime_data.text()
                print(f"[DEBUG] QPSACellInfo text data: {json_str}")
                json_data = json.loads(json_str)
            except Exception as e:
                print(f"[DEBUG] QPSACellInfo failed to parse text as JSON: {e}")
        
        # Try to get image data if available
        if mime_data.hasImage():
            try:
                image = QPixmap(mime_data.imageData())
                print(f"[DEBUG] QPSACellInfo image data received: {image.size()}")
            except Exception as e:
                print(f"[DEBUG] QPSACellInfo failed to get image data: {e}")
        
        if json_data:
            # Handle both single object and array of objects
            if isinstance(json_data, list):
                # Array format: [{x, y, type, method, id, name}, ...]
                print(f"[DEBUG] QPSACellInfo received array of {len(json_data)} objects")
                for obj in json_data:
                    self._add_object_to_list(obj, image)
                event.acceptProposedAction()
                print(f"[DEBUG] QPSACellInfo array of objects added successfully")
            elif isinstance(json_data, dict):
                # Single object format: {x, y, type, method, id, name}
                self._add_object_to_list(json_data, image)
                event.acceptProposedAction()
                print(f"[DEBUG] QPSACellInfo single object added successfully: {json_data}")
            else:
                print(f"[DEBUG] QPSACellInfo invalid JSON format: expected dict or list, got {type(json_data)}")
        else:
            print(f"[DEBUG] QPSACellInfo no valid JSON data found")
    
    def _add_object_to_list(self, obj_data: dict, image: Optional[QPixmap] = None):
        """Add a single object to the objects list."""
        # Extract required fields
        obj_id = obj_data.get('id', 'unknown')
        obj_type = obj_data.get('type', 'Unknown')
        obj_name = obj_data.get('name', obj_id)
        x = obj_data.get('x', self._x)  # Use current cell x if not specified
        y = obj_data.get('y', self._y)  # Use current cell y if not specified
        method = obj_data.get('method', '')
        
        # Check for duplicates with same id
        for existing_obj in self._objects:
            existing_id = existing_obj.get('id', 'unknown')
            if existing_id == obj_id:
                print(f"[DEBUG] QPSACellInfo rejected duplicate object: {obj_id}")
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
        print(f"[DEBUG] QPSACellInfo added object: {new_obj}")
        
        # Update the display
        self._update_objects_list()


class TerrainIndicator(QWidget):
    """Custom widget for displaying terrain color indicator."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = QColor(144, 238, 144)  # Default light green
        
    def set_color(self, color: QColor):
        """Set the terrain color."""
        self._color = color
        self.update()
        
    def paintEvent(self, event):
        """Custom paint event to draw rounded rectangle."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw rounded rectangle with border
        rect = self.rect()
        
        # Border
        painter.setPen(QPen(QColor(139, 115, 85), 1))  # #8B7355
        
        # Fill
        painter.setBrush(QBrush(self._color))
        
        # Draw rounded rectangle
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 4, 4)
        
    def sizeHint(self):
        """Preferred size."""
        return self.minimumSize()