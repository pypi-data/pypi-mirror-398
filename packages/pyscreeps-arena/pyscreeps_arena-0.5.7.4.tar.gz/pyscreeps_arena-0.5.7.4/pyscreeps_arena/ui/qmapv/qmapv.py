# -*- coding: utf-8 -*-
"""
QPSA Map Viewer - 地图查看器组件
"""
import json
import os
import tempfile
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFileDialog, QGraphicsView, 
                             QGraphicsScene, QGraphicsPixmapItem, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF, QMimeData
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QBrush, QDrag
from PIL import Image, ImageDraw
import math

# Import configuration from build.py
import sys
import os
# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pyscreeps_arena import config

# Language mapping
LANG = {
    'cn': {
        'no_map_preview': '没有地图可预览，请选择',
        'open_map': '打开地图',
        'map_file_filter': 'JSON文件 (*.json)',
        'all_files': '所有文件 (*)',
        'error': '错误',
        'invalid_json': '无效的JSON文件',
        'load_error': '加载地图失败',
        'file_not_found': '文件未找到',
        'invalid_map_data': '无效的地图数据',
    },
    'en': {
        'no_map_preview': 'No map to preview, please select',
        'open_map': 'Open Map',
        'map_file_filter': 'JSON Files (*.json)',
        'all_files': 'All Files (*)',
        'error': 'Error',
        'invalid_json': 'Invalid JSON file',
        'load_error': 'Failed to load map',
        'file_not_found': 'File not found',
        'invalid_map_data': 'Invalid map data',
    }
}

def lang(key: str) -> str:
    """Helper function to get translated text"""
    return LANG[config.language if hasattr(config, 'language') and config.language in LANG else 'cn'][key]


class CellInfo:
    """Cell information container."""
    
    def __init__(self, x: int, y: int):
        self._x = x
        self._y = y
        self._objects: List[Dict[str, Any]] = []
        self._terrain: str = '2'  # Default to plain terrain
    
    @property
    def x(self) -> int:
        return self._x
    
    @property
    def y(self) -> int:
        return self._y
    
    @property
    def objects(self) -> List[Dict[str, Any]]:
        return self._objects.copy()
    
    @property
    def terrain(self) -> str:
        return self._terrain
    
    @terrain.setter
    def terrain(self, value: str):
        self._terrain = value
    
    @property
    def cost(self) -> int:
        """
        Get movement cost for this cell.
        
        :return: int Movement cost (1=plain+road, 2=plain/swamp+road, 10=swamp, 255=wall)
        """
        # Check if there's a road in this cell
        has_road = any(obj.get('type') == 'StructureRoad' for obj in self._objects)
        
        # Base terrain cost
        if self._terrain == '2':  # plain
            base_cost = 2
        elif self._terrain == 'A':  # swamp
            base_cost = 10
        elif self._terrain == 'X':  # wall
            base_cost = 255
        else:
            base_cost = 2  # Default to plain cost
        
        # Apply road reduction
        if has_road:
            if self._terrain == '2':  # plain + road
                return 1
            elif self._terrain == 'A':  # swamp + road
                return 2
        
        return base_cost
    
    def add_object(self, obj: Dict[str, Any]):
        """Add an object to this cell."""
        self._objects.append(obj)
    
    def clear_objects(self):
        """Clear all objects from this cell."""
        self._objects.clear()
    
    def __repr__(self):
        return f"CellInfo(x={self._x}, y={self._y}, objects={len(self._objects)})"


class QPSAMapViewer(QWidget):
    """PyScreeps Arena Map Viewer component."""
    
    # Signals
    currentChanged = pyqtSignal(object)  # Current cell under mouse changed (CellInfo or None)
    selectChanged = pyqtSignal(object)     # Selected cell changed (CellInfo or None)
    rightClicked = pyqtSignal(object)      # Right-clicked cell (CellInfo or None)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._map_data: Optional[Dict[str, Any]] = None
        self._map_path: Optional[str] = None
        self._cell_size = 64  # Default cell size changed to 32
        self._current_cell: Optional[CellInfo] = None
        self._selected_cell: Optional[CellInfo] = None
        self._map_width = 0
        self._map_height = 0
        self._cell_info_grid: List[List[CellInfo]] = []
        self._temp_image_path: Optional[str] = None
        
        # Drag functionality
        self._drag_start_pos = None
        self._drag_cell_info = None
        self._original_drag_mode = None
        self._is_dragging = False
        
        # Highlight colors
        self._hover_color = QColor(240, 248, 255, 64)  # #F0F8FF 25% transparent
        self._selection_width = 2
        
        self._init_ui()
        self._init_scene()
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Set minimum size to 1024x1024 and allow expansion
        self.setMinimumSize(1024, 1024)
        self.setSizePolicy(
            self.sizePolicy().Policy.Expanding,
            self.sizePolicy().Policy.Expanding
        )
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Status label
        self._status_label = QLabel(lang('no_map_preview'))
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet("font-size: 14px; color: #666;")
        layout.addWidget(self._status_label)
        
        # Graphics view for map display
        self._graphics_view = QGraphicsView()
        self._graphics_view.setFrameShape(QFrame.Shape.NoFrame)
        self._graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._graphics_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self._graphics_view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        layout.addWidget(self._graphics_view)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self._open_button = QPushButton(lang('open_map'))
        self._open_button.setFixedSize(120, 40)
        self._open_button.clicked.connect(self._open_map_file)
        button_layout.addWidget(self._open_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Initially hide graphics view until map is loaded
        self._graphics_view.hide()
    
    def _init_scene(self):
        """Initialize the graphics scene."""
        self._scene = QGraphicsScene()
        self._graphics_view.setScene(self._scene)
        self._map_item: Optional[QGraphicsPixmapItem] = None
        self._highlight_item: Optional[QGraphicsPixmapItem] = None
        self._selection_item: Optional[QGraphicsPixmapItem] = None
    
    def _open_map_file(self):
        """Open and load a map JSON file."""
        # Set default directory to desktop
        import os
        desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择地图文件",
            desktop_path,
            f"{lang('map_file_filter')};;{lang('all_files')}"
        )
        
        if file_path:
            # Change button text to "render..." while rendering
            self._open_button.setText("render...")
            # Force UI update
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()
            
            try:
                self.load_map(file_path)
            except Exception as e:
                self._show_error(f"{lang('load_error')}: {str(e)}")
                # Restore original button text on error
                self._open_button.setText(lang('open_map'))
    
    def load_map(self, file_path: str):
        """
        Load a map from JSON file.
        
        :param file_path: Path to the map JSON file
        :raises: ValueError if the file format is invalid
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"{lang('file_not_found')}: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                map_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"{lang('invalid_json')}: {e}")
        
        # Validate map format
        if 'map' not in map_data or not isinstance(map_data['map'], list):
            raise ValueError(lang('invalid_map_data'))
        
        if not map_data['map']:
            raise ValueError(lang('invalid_map_data'))
        
        # Validate that all rows have the same length
        row_length = len(map_data['map'][0])
        for i, row in enumerate(map_data['map']):
            if len(row) != row_length:
                raise ValueError(f"{lang('invalid_map_data')}: row {i+1}")
        
        self._map_data = map_data
        self._map_path = file_path
        self._map_height = len(map_data['map'])
        self._map_width = row_length
        
        # Build cell info grid
        self._build_cell_info_grid()
        
        # Render the map
        self._render_map()
        
        # Update UI
        self._update_ui_after_load()
        
        print(f"[DEBUG] Map loaded: {self._map_width}x{self._map_height}")  # 调试输出
    
    def _build_cell_info_grid(self):
        """Build cell information grid from map data."""
        self._cell_info_grid = []
        
        # Get terrain data from map
        terrain_map = self._map_data.get('map', [])
        
        for y in range(self._map_height):
            row = []
            for x in range(self._map_width):
                cell_info = CellInfo(x, y)
                
                # Set terrain if available
                if y < len(terrain_map) and x < len(terrain_map[y]):
                    cell_info.terrain = terrain_map[y][x]
                
                row.append(cell_info)
            self._cell_info_grid.append(row)
        
        # Populate objects from map data
        if 'objects' in self._map_data:
            for obj_type, obj_list in self._map_data['objects'].items():
                # Skip GameObject and Structure base types, but keep their subclasses
                if obj_type in ['GameObject', 'Structure']:
                    print(f"[DEBUG] Skipping base type: {obj_type}")  # 调试输出
                    continue
                    
                for obj in obj_list:
                    x, y = obj['x'], obj['y']
                    if 0 <= x < self._map_width and 0 <= y < self._map_height:
                        obj_copy = obj.copy()
                        obj_copy['type'] = obj_type
                        self._cell_info_grid[y][x].add_object(obj_copy)
    
    def _render_map(self):
        """Render the map using the existing map_render functionality."""
        try:
            # Import the renderer from the existing module
            from ..map_render import MapRender
            
            # Create a temporary file for the rendered image
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                self._temp_image_path = tmp.name
            
            # Render the map
            renderer = MapRender(self._map_path, self._cell_size)
            renderer.render(self._temp_image_path, show_grid=True)
            
            # Load the rendered image
            pixmap = QPixmap(self._temp_image_path)
            
            # Clear existing items
            self._scene.clear()
            self._map_item = None
            self._highlight_item = None
            self._selection_item = None
            
            # Add map to scene
            self._map_item = self._scene.addPixmap(pixmap)
            
            # Set scene rect to match image size
            self._scene.setSceneRect(QRectF(pixmap.rect()))
            
            # Fit the view to the image
            self._graphics_view.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            
            # Set default zoom level to 2.0
            self._graphics_view.scale(2.0, 2.0)
            
            print(f"[DEBUG] Map rendered to temporary file: {self._temp_image_path}")  # 调试输出
            
        except Exception as e:
            raise RuntimeError(f"地图渲染失败: {e}")
    
    def _update_ui_after_load(self):
        """Update UI after successful map load."""
        self._status_label.setText(f"地图已加载: {self._map_width}x{self._map_height}")
        self._status_label.hide()
        self._graphics_view.show()
        
        # Restore original button text after successful loading
        self._open_button.setText(lang('open_map'))
        
        # Enable mouse tracking for hover effects
        self._graphics_view.setMouseTracking(True)
        self._graphics_view.viewport().installEventFilter(self)
        
        # Store current map path for language switching
        self._current_map_path = self._map_path
        
        # Enable key event handling
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Enable drag and drop for the graphics view viewport
        self._graphics_view.viewport().setAcceptDrops(True)
        
    def dragEnterEvent(self, event):
        """Accept drag enter events."""
        print(f"[DEBUG] Drag enter event received")
        event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        """Accept drag move events."""
        event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handle drop events."""
        print(f"[DEBUG] Drop event received")
        event.acceptProposedAction()
        
    def keyPressEvent(self, event):
        """Handle key press events for Ctrl/Alt drag functionality."""
        if event.key() in (Qt.Key.Key_Control, Qt.Key.Key_Alt):
            if self._original_drag_mode is None:
                # Store original drag mode and disable it
                self._original_drag_mode = self._graphics_view.dragMode()
                self._graphics_view.setDragMode(QGraphicsView.DragMode.NoDrag)
                print(f"[DEBUG] Ctrl/Alt pressed: disabled graphics view drag mode (was: {self._original_drag_mode})")
        super().keyPressEvent(event)
    
    def keyReleaseEvent(self, event):
        """Handle key release events to restore drag functionality."""
        if event.key() in (Qt.Key.Key_Control, Qt.Key.Key_Alt):
            # Check if both Ctrl and Alt are released
            modifiers = event.modifiers()
            if not (modifiers & Qt.KeyboardModifier.ControlModifier) and not (modifiers & Qt.KeyboardModifier.AltModifier):
                if self._original_drag_mode is not None:
                    # Restore original drag mode
                    self._graphics_view.setDragMode(self._original_drag_mode)
                    print(f"[DEBUG] Ctrl/Alt released: restored graphics view drag mode to: {self._original_drag_mode}")
                    self._original_drag_mode = None
        super().keyReleaseEvent(event)
    
    def _show_error(self, message: str):
        """Show error message."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self, lang('error'), message)
    
    def _reset_to_default_state(self):
        """Reset to default state with language-appropriate text."""
        self._status_label.setText(lang('no_map_preview'))
        self._status_label.show()
        self._graphics_view.hide()
        self._open_button.setText(lang('open_map'))
    
    def eventFilter(self, obj, event):
        """Handle mouse events for the graphics view."""
        if obj == self._graphics_view.viewport() and self._map_item is not None:
            if event.type() == event.Type.MouseMove:
                self._handle_mouse_move(event.pos())
                # Handle drag initiation during mouse move
                if self._is_dragging and self._drag_start_pos is not None:
                    # Calculate drag distance to determine if it's a valid drag
                    drag_distance = abs(event.pos().x() - self._drag_start_pos.x()) + abs(event.pos().y() - self._drag_start_pos.y())
                    print(f"[DEBUG] Mouse move - drag distance: {drag_distance}, is_dragging: {self._is_dragging}")
                    if drag_distance > 10:  # Minimum drag distance
                        print(f"[DEBUG] Starting drag operation")
                        # Use QApplication to start the drag from the viewport
                        from PyQt6.QtWidgets import QApplication
                        # Force the viewport to have focus for drag operations
                        self._graphics_view.viewport().setFocus()
                        self._initiate_drag(self._drag_cell_info)
                        # Reset drag state after initiating drag
                        self._drag_start_pos = None
                        self._drag_cell_info = None
                        self._is_dragging = False
            elif event.type() == event.Type.MouseButtonPress:
                # Ensure cursor remains cross during and after click
                self._graphics_view.viewport().setCursor(Qt.CursorShape.CrossCursor)
                if event.button() == Qt.MouseButton.LeftButton:
                    # Check if Ctrl or Alt is pressed for drag functionality
                    modifiers = event.modifiers()
                    print(f"[DEBUG] Mouse press - modifiers: {modifiers}")
                    if modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier):
                        # Store drag info for potential drag
                        cell_info = self._get_cell_at_pos(event.pos())
                        if cell_info is not None:
                            self._drag_start_pos = event.pos()
                            self._drag_cell_info = cell_info
                            self._is_dragging = True
                            print(f"[DEBUG] Drag preparation: cell ({cell_info.x}, {cell_info.y})")
                    else:
                        self._handle_mouse_click(event.pos())
                elif event.button() == Qt.MouseButton.RightButton:
                    self._handle_right_click(event.pos())
            elif event.type() == event.Type.MouseButtonRelease:
                if event.button() == Qt.MouseButton.LeftButton:
                    # Reset drag state on mouse release
                    self._drag_start_pos = None
                    self._drag_cell_info = None
                    self._is_dragging = False
            elif event.type() == event.Type.Wheel:
                self._handle_wheel_event(event)
                return True  # Consume the event
            elif event.type() == event.Type.Enter:
                self._graphics_view.viewport().setCursor(Qt.CursorShape.CrossCursor)
            elif event.type() == event.Type.Leave:
                self._graphics_view.viewport().unsetCursor()
        
        return super().eventFilter(obj, event)
    
    def _handle_mouse_move(self, pos):
        """Handle mouse move events."""
        cell_info = self._get_cell_at_pos(pos)
        
        if cell_info != self._current_cell:
            self._current_cell = cell_info
            self._update_highlight()
            self.currentChanged.emit(cell_info)
    
    def _handle_mouse_click(self, pos):
        """Handle mouse click events."""
        cell_info = self._get_cell_at_pos(pos)
        
        if cell_info != self._selected_cell:
            self._selected_cell = cell_info
            self._update_selection()
            self.selectChanged.emit(cell_info)
    
    def _handle_right_click(self, pos):
        """Handle right-click events."""
        cell_info = self._get_cell_at_pos(pos)
        self.rightClicked.emit(cell_info)
    
    def _initiate_drag(self, cell_info: CellInfo):
        """Initiate drag operation with cell data."""
        print(f"[DEBUG] Initiating drag for cell ({cell_info.x}, {cell_info.y})")
        
        # Generate drag data based on cell contents
        if cell_info.objects:
            # If cell has objects, create array of all objects with screenshots
            drag_data = []
            
            # Extract cell screenshot if map image is available
            cell_image = None
            if self.image is not None and not self.image.isNull():
                try:
                    # Calculate cell size based on map image dimensions
                    cell_width = self.image.width() // self._map_width
                    cell_height = self.image.height() // self._map_height
                    
                    # Calculate the position of this cell in the image
                    cell_x_offset = cell_info.x * cell_width
                    cell_y_offset = cell_info.y * cell_height
                    
                    # Extract the cell region
                    if (cell_x_offset + cell_width <= self.image.width() and 
                        cell_y_offset + cell_height <= self.image.height() and
                        cell_x_offset >= 0 and cell_y_offset >= 0):
                        
                        cell_image = self.image.copy(cell_x_offset, cell_y_offset, cell_width, cell_height)
                        print(f"[DEBUG] Extracted cell screenshot for ({cell_info.x}, {cell_info.y}): {cell_image.size()}")
                except Exception as e:
                    print(f"[DEBUG] Failed to extract cell screenshot: {e}")
            
            # Create object data for each object with the same screenshot
            for obj in cell_info.objects:
                obj_data = {
                    "x": cell_info.x,
                    "y": cell_info.y,
                    "type": obj.get('type', 'Unknown'),
                    "method": obj.get('method', ''),
                    "id": obj.get('id', 'unknown'),
                    "name": obj.get('name', obj.get('id', 'unknown'))
                }
                drag_data.append(obj_data)
        else:
            # If cell has no objects, create point data (no screenshot)
            drag_data = {
                "x": cell_info.x,
                "y": cell_info.y,
                "type": "Point",
                "method": "Point",
                "id": f"{cell_info.x}◇{cell_info.y}",
                "name": f"p{cell_info.x}◇{cell_info.y}"
            }
        
        # Convert to JSON string
        json_data = json.dumps(drag_data, ensure_ascii=False, indent=2)
        print(f"[DEBUG] Drag data: {json_data}")
        
        # Create mime data
        mime_data = QMimeData()
        mime_data.setText(json_data)
        mime_data.setData("application/json", json_data.encode('utf-8'))
        
        # Add cell screenshot if available
        if cell_info.objects and cell_image is not None and not cell_image.isNull():
            mime_data.setImageData(cell_image)
            print(f"[DEBUG] Added cell screenshot to drag data")
        
        # Create drag object
        drag = QDrag(self._graphics_view.viewport())
        drag.setMimeData(mime_data)
        
        # Start drag operation
        result = drag.exec(Qt.DropAction.CopyAction | Qt.DropAction.MoveAction)
        print(f"[DEBUG] Drag result: {result}")
        
        return result
    
    def _handle_wheel_event(self, event):
        """Handle mouse wheel events for zooming."""
        if self._map_item is None:
            return
        
        # Get the wheel delta
        delta = event.angleDelta().y()
        
        # Calculate zoom factor
        zoom_factor = 1.1 if delta > 0 else 0.9
        
        # Limit zoom range
        current_scale = self._graphics_view.transform().m11()
        if (current_scale > 5.0 and zoom_factor > 1) or (current_scale < 0.1 and zoom_factor < 1):
            return
        
        # Get the position before scaling
        old_pos = self._graphics_view.mapToScene(event.position().toPoint())
        
        # Apply scaling
        self._graphics_view.scale(zoom_factor, zoom_factor)
        
        # Get the position after scaling
        new_pos = self._graphics_view.mapToScene(event.position().toPoint())
        
        # Adjust the scroll position to keep the mouse position fixed
        delta_pos = new_pos - old_pos
        self._graphics_view.translate(delta_pos.x(), delta_pos.y())
        
        print(f"[DEBUG] Zoom: {current_scale:.2f} -> {self._graphics_view.transform().m11():.2f}")  # 调试输出
    
    def _get_cell_at_pos(self, pos) -> Optional[CellInfo]:
        """Get cell information at the given viewport position."""
        if self._map_item is None:
            return None
        
        # Map viewport position to scene coordinates
        scene_pos = self._graphics_view.mapToScene(pos)
        
        # Convert scene coordinates to cell coordinates
        x = int(scene_pos.x() / self._cell_size)
        y = int(scene_pos.y() / self._cell_size)
        
        # Check bounds
        if 0 <= x < self._map_width and 0 <= y < self._map_height:
            return self._cell_info_grid[y][x]
        
        return None
    
    def _update_highlight(self):
        """Update hover highlight."""
        # Remove existing highlight
        if self._highlight_item is not None:
            self._scene.removeItem(self._highlight_item)
            self._highlight_item = None
        
        # Add new highlight if there's a current cell
        if self._current_cell is not None:
            rect = self._get_cell_rect(self._current_cell.x, self._current_cell.y)
            self._highlight_item = self._scene.addRect(rect, QPen(Qt.PenStyle.NoPen), QBrush(self._hover_color))
            self._highlight_item.setZValue(10)  # Above map, below selection
    
    def _update_selection(self):
        """Update cell selection."""
        # Remove existing selection
        if self._selection_item is not None:
            self._scene.removeItem(self._selection_item)
            self._selection_item = None
        
        # Add new selection if there's a selected cell
        if self._selected_cell is not None:
            rect = self._get_cell_rect(self._selected_cell.x, self._selected_cell.y)
            
            # Calculate contrasting color for the border
            border_color = self._get_contrasting_color()
            pen = QPen(border_color, self._selection_width)
            pen.setStyle(Qt.PenStyle.SolidLine)
            
            self._selection_item = self._scene.addRect(rect, pen)
            self._selection_item.setZValue(20)  # Above everything
    
    def _get_cell_rect(self, x: int, y: int) -> QRectF:
        """Get rectangle for a cell."""
        left = x * self._cell_size
        top = y * self._cell_size
        return QRectF(left, top, self._cell_size, self._cell_size)
    
    def _get_contrasting_color(self) -> QColor:
        """Get a contrasting color for selection border."""
        # Use a bright color that contrasts with most backgrounds
        return QColor(255, 0, 255)  # Magenta
    
    # Public properties
    @property
    def current(self) -> Optional[CellInfo]:
        """Get current cell under mouse cursor."""
        return self._current_cell
    
    @property
    def selected(self) -> Optional[CellInfo]:
        """Get selected cell."""
        return self._selected_cell
    
    @property
    def map_width(self) -> int:
        """Get map width."""
        return self._map_width
    
    @property
    def map_height(self) -> int:
        """Get map height."""
        return self._map_height
    
    @property
    def image(self) -> Optional[QPixmap]:
        """Get the current map image."""
        if self._map_item is not None:
            return self._map_item.pixmap()
        return None
    
    def clear_selection(self):
        """Clear current selection."""
        self._selected_cell = None
        self._update_selection()
        self.selectChanged.emit(None)
    
    def clear_current(self):
        """Clear current hover cell."""
        self._current_cell = None
        self._update_highlight()
        self.currentChanged.emit(None)
    
    def cleanup(self):
        """Clean up temporary files."""
        if self._temp_image_path and os.path.exists(self._temp_image_path):
            try:
                os.remove(self._temp_image_path)
                print(f"[DEBUG] Cleaned up temporary file: {self._temp_image_path}")  # 调试输出
            except Exception as e:
                print(f"[DEBUG] Failed to cleanup temporary file: {e}")  # 调试输出
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()