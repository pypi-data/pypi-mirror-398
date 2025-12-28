from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QPushButton,
    QRadioButton, QGroupBox, QLabel, QCheckBox, QScrollArea,
    QFrame, QButtonGroup, QLayout, QSizePolicy
)

# 全局样式常量
CHECKBOX_STYLE = "QCheckBox::indicator { width: 16px; height: 16px; border: 3px solid #555; border-radius: 5px; background-color: white; } QCheckBox::indicator:checked { background-color: #4CAF50; image: url('data:image/svg+xml;utf8,<svg xmlns=\'http://www.w3.org/2000/svg\' width=\'18\' height=\'18\' viewBox=\'0 0 24 24\'><path fill=\'white\' d=\'M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z\'/></svg>'); }"
RADIO_STYLE = "QRadioButton::indicator { width: 16px; height: 16px; border: 3px solid #555; border-radius: 8px; background-color: white; } QRadioButton::indicator:checked { background-color: #4CAF50; }"
from PyQt6.QtGui import QContextMenuEvent, QMouseEvent, QKeyEvent, QDragMoveEvent, QFocusEvent
from typing import Set
from PyQt6.QtCore import (
    Qt, QMimeData, QPoint, pyqtProperty, pyqtSignal,
    QEvent, QRect
)
from PyQt6.QtGui import QDrag
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QFontMetrics,
    QDragEnterEvent, QDropEvent, QPalette
)
import json
from typing import List, Optional
from pyscreeps_arena.ui.qrecipe.model import RecipeModel, PartsVector, CreepInfo
from PyQt6.QtWidgets import QApplication

# Import configuration from build.py
import sys
import os
# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pyscreeps_arena import config

# Language mapping
LANG = {
    'cn': {
        'recipe': '配方表',
        'optimised_recipe': '优化后的配方',
        'static_info': '静态信息',
        'cost': '价 格💲',
        'optimise': '自动优化',
        'yes': '✅',
        'no': '❎',
        'score': '分  数💯',
        'efficiency': '效  率📈',
        'melee': '近  战🔴',
        'ranged': '远  程🔵',
        'heal': '治  疗🟢',
        'work': '工  作🟡',
        'storable': '存  储⚫',
        'attack_power': '攻击力💀',
        'melee_power': '近战力⚔️',
        'ranged_power': '远程力🏹',
        'heal_power': '治疗力💉',
        'motion_ability': '移动率🥾',
        'armor_ratio': '装甲率🛡️',
        'melee_ratio': '站撸率💪',
    },
    'en': {
        'recipe': 'Recipe Table',
        'optimised_recipe': 'Optimised Recipe',
        'static_info': 'Static Info',
        'cost': 'cost💲',
        'optimise': 'Auto Optimise',
        'yes': '✅',
        'no': '❎',
        'score': 'grade💯',
        'efficiency': 'effect📈',
        'melee': 'melee🔴',
        'ranged': 'ranged🔵',
        'heal': 'heal🟢',
        'work': 'work🟡',
        'storable': 'store⚫',
        'attack_power': 'attack`💀',
        'melee_power': 'melee`⚔️',
        'ranged_power': 'ranged`🏹',
        'heal_power': 'heal`💉',
        'motion_ability': 'motion.🥾',
        'armor_ratio': 'armor.🛡️',
        'melee_ratio': 'melee.💪',
    }
}

# config.language = 'en'

def lang(key: str) -> str:
    """Helper function to get translated text"""
    return LANG[config.language if hasattr(config, 'language') and config.language in LANG else 'cn'][key]

class QPSABodyPart(QWidget):
    def __init__(self, part_type: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.part_type = part_type
        self.color = QColor(PartsVector.COLORS.get(part_type, '#9B9B9B'))
        self.is_selected = False
        self.index = -1  # Index in the recipe list
        self.drag_start_position = QPoint()  # Initialize drag start position
        
        self.setFixedSize(30, 30)
        self.setAcceptDrops(True)  # Enable drop for reordering
        self.setCursor(Qt.CursorShape.PointingHandCursor)  # For selectable parts
        
    def mousePressEvent(self, event):
        # This method is overridden in QPSARecipe for recipe parts
        # but kept here for top row draggable parts
        if self.cursor().shape() == Qt.CursorShape.OpenHandCursor:
            # Only handle drag start for top row draggable parts
            if event.button() == Qt.MouseButton.LeftButton:
                self.drag_start_position = event.pos()
        else:
            # Handle click for selectable parts
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        # Handle drag for reordering selected parts
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        
        # Only allow dragging selected parts in recipe area
        if self.is_selected and self.cursor().shape() != Qt.CursorShape.OpenHandCursor:
            distance = (event.pos() - self.drag_start_position).manhattanLength()
            from PyQt6.QtWidgets import QApplication
            if distance < QApplication.startDragDistance():
                return
            
            # Create drag data with the selected indices
            mime_data = QMimeData()
            drag_data = {
                "type": "recipe_part_reorder",
                "selected_indices": list(self.parent().parent().selected_indices),
                "source_index": self.index
            }
            mime_data.setText(json.dumps(drag_data))
            
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            
            # Create drag pixmap with visual feedback
            drag.setPixmap(self.grab())
            drag.setHotSpot(QPoint(15, 15))
            
            drag.exec(Qt.DropAction.MoveAction)
        else:
            # Original drag behavior for top row parts
            super().mouseMoveEvent(event)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = QRect(5, 5, 20, 20)
        base_rect = QRect(5, 5, 20, 20)
        
        if self.is_selected:
            # For selected state, draw thicker outline with inverted color
            # Create inverted color for outline
            r, g, b, a = self.color.getRgb()
            inverted_color = QColor(255 - r, 255 - g, 255 - b, a)
            
            # Draw main circle with original color and default stroke
            painter.setBrush(QBrush(self.color))
            painter.setPen(QPen(QColor("#CDC5BF"), 1))
            painter.drawEllipse(rect)
            
            # Draw thicker selection outline with inverted color
            outline_rect = QRect(2, 2, 26, 26)
            painter.setPen(QPen(inverted_color, 3))
            painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            painter.drawEllipse(outline_rect)
        else:
            # Normal state - draw circle with default 1px #CDC5BF stroke
            painter.setBrush(QBrush(self.color))
            painter.setPen(QPen(QColor("#CDC5BF"), 1))
            painter.drawEllipse(rect)
    
    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.update()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Always set drag_start_position to avoid AttributeError in mouseMoveEvent
            self.drag_start_position = event.pos()
    
    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        
        # Only allow dragging from the source parts, not from recipe area parts
        # Source parts have OpenHandCursor, recipe parts have PointingHandCursor
        if self.cursor().shape() != Qt.CursorShape.OpenHandCursor:
            return
        
        distance = (event.pos() - self.drag_start_position).manhattanLength()
        if distance < QApplication.startDragDistance():
            return
        
        # Create drag data
        mime_data = QMimeData()
        part_data = json.dumps([self.part_type])
        mime_data.setText(part_data)
        
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        
        # Create drag pixmap
        drag.setPixmap(self.grab())
        drag.setHotSpot(QPoint(15, 15))
        
        drag.exec(Qt.DropAction.CopyAction)

class QPSARecipe(QWidget):
    onChanged = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Model
        self.model = RecipeModel()
        
        # Set focus policy to accept keyboard events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # UI Setup
        self.init_ui()
        
        # Property storage
        self._recipe: List[str] = []
        self._preview: str = "[]"
        self._string: str = ""
        self._optimise: bool = True
        self._cost: int = 0
        self._grade: int = 0
        self._effect: float = 0.0
        self._multiplier: int = 1  # Only affects drag-and-drop operations
        
        # Selection management
        self.selected_indices: Set[int] = set()
        self.last_selected_index: int = -1
        
        # Update initial values
        self.update_info()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 1. Body Part Types (Top row) - Draggable parts
        self.part_types = ['WORK', 'ATTACK', 'RANGED_ATTACK', 'HEAL', 'TOUGH', 'CARRY', 'MOVE']
        part_layout = QHBoxLayout()
        part_layout.setSpacing(10)
        
        for part_type in self.part_types:
            part_widget = QPSABodyPart(part_type)
            part_widget.setCursor(Qt.CursorShape.OpenHandCursor)  # Set draggable cursor
            part_layout.addWidget(part_widget)
        
        part_layout.addStretch()
        main_layout.addLayout(part_layout)
        
        # 2. Multiplier Selection (Second row)
        multiplier_group = QGroupBox()
        multiplier_layout = QHBoxLayout(multiplier_group)
        multiplier_layout.setSpacing(15)
        
        self.multiplier_group = QButtonGroup(self)
        multipliers = ['x1', 'x2', 'x4', 'x5', 'x10']
        
        for i, multiplier in enumerate(multipliers):
            radio = QRadioButton(multiplier)
            # Set NoFocus policy for radio buttons so they don't steal keyboard events
            radio.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            radio.setStyleSheet(RADIO_STYLE)
            self.multiplier_group.addButton(radio, i)
            multiplier_layout.addWidget(radio)
        
        # Set default to x1
        self.multiplier_group.button(0).setChecked(True)
        self.multiplier_group.buttonClicked.connect(self.on_multiplier_changed)
        multiplier_layout.addStretch()
        main_layout.addWidget(multiplier_group)
        
        # 3. Recipe Table (Third row) - Entire area accepts drops
        recipe_group = QGroupBox(lang('recipe'))
        recipe_layout = QVBoxLayout(recipe_group)
        
        # Create a single widget that accepts drops
        self.recipe_area = QWidget()
        self.recipe_area.setFixedSize(320, 170)  # 10 columns * 30px + 5px spacing, 5 rows * 30px + 5px spacing
        self.recipe_area.setStyleSheet("background-color: #f5f5f5; border: 1px dashed #ccc; border-radius: 5px;")
        self.recipe_area.setAcceptDrops(True)
        self.recipe_area.installEventFilter(self)
        
        # Create a vertical layout for the recipe area
        # This will hold 5 horizontal layouts (one for each row)
        self.recipe_main_layout = QVBoxLayout(self.recipe_area)
        self.recipe_main_layout.setSpacing(5)
        self.recipe_main_layout.setContentsMargins(5, 5, 5, 5)
        self.recipe_main_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # Create 5 horizontal layouts (one for each row, max 10 parts per row)
        self.recipe_row_layouts: List[QHBoxLayout] = []
        for _ in range(5):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(5)
            row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.recipe_main_layout.addLayout(row_layout)
            self.recipe_row_layouts.append(row_layout)
        
        # Store references to displayed part widgets
        self.displayed_parts: List[QPSABodyPart] = []
        
        recipe_layout.addWidget(self.recipe_area)
        main_layout.addWidget(recipe_group)
        
        # 4. Cost and Optimise (Fourth row)
        control_layout = QHBoxLayout()
        
        # Left: Cost
        self.cost_label = QLabel(f"{lang('cost')}: 0")
        control_layout.addWidget(self.cost_label)
        control_layout.addStretch()
        
        # Right: Optimise checkbox
        self.optimise_checkbox = QCheckBox(lang('optimise'))
        self.optimise_checkbox.setChecked(True)
        self.optimise_checkbox.setStyleSheet(CHECKBOX_STYLE)
        self.optimise_checkbox.stateChanged.connect(self.on_optimise_changed)
        control_layout.addWidget(self.optimise_checkbox)
        
        main_layout.addLayout(control_layout)
        
        # 5. Optimised Recipe (Fifth row) - same layout as recipe area, fixed height, no scrollbars
        self.optimised_group = QGroupBox(lang('optimised_recipe'))
        self.optimised_layout = QVBoxLayout(self.optimised_group)
        self.optimised_layout.setSpacing(5)
        
        # Create a display area for optimised recipe - same size as recipe area
        self.optimised_display = QWidget()
        self.optimised_display.setFixedSize(320, 170)  # Same size as recipe area
        self.optimised_display.setStyleSheet("background-color: #f5f5f5; border: 1px dashed #ccc; border-radius: 5px;")
        
        # Create main layout for optimised recipe - vertical with horizontal rows
        self.optimised_main_layout = QVBoxLayout(self.optimised_display)
        self.optimised_main_layout.setSpacing(5)
        self.optimised_main_layout.setContentsMargins(5, 5, 5, 5)
        self.optimised_main_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # Create 5 horizontal layouts for optimised recipe rows (max 10 per row)
        self.optimised_row_layouts: List[QHBoxLayout] = []
        for _ in range(5):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(5)
            row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.optimised_main_layout.addLayout(row_layout)
            self.optimised_row_layouts.append(row_layout)
        
        # No scroll area, just add the fixed-size widget directly
        self.optimised_layout.addWidget(self.optimised_display)
        main_layout.addWidget(self.optimised_group)
        
        # 6. Static Info (Sixth row)
        info_group = QGroupBox(lang('static_info'))
        info_layout = QGridLayout(info_group)
        info_layout.setSpacing(10)
        
        # Info labels with emojis - use language mapping
        info_labels = [
            (lang('score'), "grade"),
            (lang('efficiency'), "effect"),
            (lang('melee'), "melee"),
            (lang('ranged'), "ranged"),
            (lang('heal'), "heal"),
            (lang('work'), "work"),
            (lang('storable'), "storable"),
            (lang('attack_power'), "attack_power"),
            (lang('melee_power'), "melee_power"),
            (lang('ranged_power'), "ranged_power"),
            (lang('heal_power'), "heal_power"),
            (lang('motion_ability'), "motion_ability"),
            (lang('armor_ratio'), "armor_ratio"),
            (lang('melee_ratio'), "melee_ratio"),
        ]
        
        self.info_display = {}
        for i, (label_text, key) in enumerate(info_labels):
            label = QLabel(f"{label_text}: ")
            value = QLabel("0")
            value.setObjectName(f"info_{key}")
            info_layout.addWidget(label, i // 2, (i % 2) * 2)
            info_layout.addWidget(value, i // 2, (i % 2) * 2 + 1)
            self.info_display[key] = value
        
        main_layout.addWidget(info_group)
    
    def eventFilter(self, obj: QWidget, event: QEvent) -> bool:
        if isinstance(obj, QPSABodyPart):
            # Handle drag events for reordering parts
            if event.type() == QEvent.Type.DragEnter:
                return self.on_part_drag_enter(event, obj)
            elif event.type() == QEvent.Type.DragMove:
                return self.on_part_drag_move(event, obj)
            elif event.type() == QEvent.Type.Drop:
                return self.on_part_drop(event, obj)
        elif obj == self.recipe_area:
            if event.type() == QEvent.Type.DragEnter:
                return self.on_drag_enter_event(event)
            elif event.type() == QEvent.Type.Drop:
                return self.on_drop_event(event, obj)
        return super().eventFilter(obj, event)
    
    def on_drag_enter_event(self, event: QDragEnterEvent) -> bool:
        if event.mimeData().hasText():
            event.acceptProposedAction()
            return True
        return False
    
    def on_drop_event(self, event: QDropEvent, target_area: QWidget) -> bool:
        # Parse dropped data
        text = event.mimeData().text()
        try:
            parts = json.loads(text)
            if isinstance(parts, list) and parts:
                part_type = parts[0]
                
                # Apply multiplier to this single part drop
                new_parts = [part_type] * self._multiplier
                
                # Calculate how many parts we can add without exceeding 50
                available_slots = 50 - len(self._recipe)
                if available_slots <= 0:
                    return False
                
                # Only take what fits
                new_parts = new_parts[:available_slots]
                
                # Calculate insertion position based on drop coordinates
                # Get drop position in target_area coordinates
                drop_local = event.position().toPoint()
                
                # Simplified insertion logic: iterate through all parts and find insertion point
                insertion_index = len(self._recipe)
                
                # Iterate through each part widget to determine insertion position
                for i, part_widget in enumerate(self.displayed_parts):
                    # Get part widget's geometry
                    part_geo = part_widget.geometry()
                    # Get part's global position
                    part_global = part_widget.mapToGlobal(QPoint(0, 0))
                    # Convert to target_area's local coordinates
                    part_local = target_area.mapFromGlobal(part_global)
                    
                    # Check if drop is above or below the part row
                    if drop_local.y() < part_local.y() or drop_local.y() > part_local.y() + 30:
                        continue  # Skip if not in the same row
                    
                    # Check if drop is to the left or right of the part
                    part_mid_x = part_local.x() + 15  # 30px width / 2
                    if drop_local.x() < part_mid_x:
                        # Drop is to the left, insert before this part
                        insertion_index = i
                        break
                    else:
                        # Drop is to the right, insert after this part
                        insertion_index = i + 1
                
                # Create new recipe with parts inserted at calculated position
                updated_recipe = self._recipe.copy()
                # Insert all new parts at once to maintain their order
                for i in range(len(new_parts)):
                    updated_recipe.insert(insertion_index + i, new_parts[i])
                
                # Update model and UI
                self.recipe = updated_recipe
                event.acceptProposedAction()
                return True
        except json.JSONDecodeError:
            pass
        return False
    
    def on_part_drag_enter(self, event: QDragEnterEvent, target_part: QPSABodyPart) -> bool:
        # Check if this is a recipe part reorder drag (JSON object) or top-row part drag (JSON list)
        if event.mimeData().hasText():
            text = event.mimeData().text()
            try:
                # Try to parse as JSON
                data = json.loads(text)
                # Only accept recipe part reorder drags (JSON objects), not top-row part drags (JSON lists)
                if isinstance(data, dict) and data.get("type") == "recipe_part_reorder":
                    event.acceptProposedAction()
                    return True
            except json.JSONDecodeError:
                pass
        return False
    
    def on_part_drag_move(self, event: QDragMoveEvent, target_part: QPSABodyPart) -> bool:
        # Allow drop on parts for reordering (JSON objects only)
        if event.mimeData().hasText():
            text = event.mimeData().text()
            try:
                data = json.loads(text)
                if isinstance(data, dict) and data.get("type") == "recipe_part_reorder":
                    event.acceptProposedAction()
                    return True
            except json.JSONDecodeError:
                pass
        return False
    
    def on_part_drop(self, event: QDropEvent, target_part: QPSABodyPart) -> bool:
        # Handle dropping selected parts onto another part to reorder
        text = event.mimeData().text()
        try:
            drag_data = json.loads(text)
            # Only handle recipe_part_reorder JSON objects, not top-row JSON lists
            if isinstance(drag_data, dict) and drag_data.get("type") == "recipe_part_reorder":
                selected_indices = drag_data["selected_indices"]
                source_index = drag_data["source_index"]
                target_index = target_part.index
                
                if not selected_indices:  # No selected parts to move
                    return False
                
                # Create recipe copy, remove selected parts in reverse order
                new_recipe = self._recipe.copy()
                selected_parts = []
                for index in sorted(selected_indices, reverse=True):
                    selected_parts.append(new_recipe.pop(index))
                
                # Reverse to maintain original order when inserting
                selected_parts.reverse()
                
                # Insert at target position
                for part in selected_parts:
                    new_recipe.insert(target_index, part)
                
                # Update recipe and selection
                self.recipe = new_recipe
                
                # Update selection to moved parts
                new_selected = set()
                for i in range(len(selected_parts)):
                    new_selected.add(target_index + i)
                self.selected_indices = new_selected
                self.last_selected_index = max(new_selected)
                self.update_selection_display()
                
                event.acceptProposedAction()
                return True
        except json.JSONDecodeError:
            pass
        return False
    
    def contextMenuEvent(self, event: QContextMenuEvent):
        # Clear all parts when right-clicking on the recipe area
        if self.recipe_area.geometry().contains(self.mapFromGlobal(event.globalPos())):
            self.recipe = []
    
    def mousePressEvent(self, event: QMouseEvent):
        # Ensure this widget has focus when clicked anywhere on it
        self.setFocus()
        
        # Check if clicked on recipe area's blank space
        if self.recipe_area.geometry().contains(event.pos()):
            # Convert to recipe area's local coordinates
            local_pos = self.recipe_area.mapFrom(self, event.pos())
            
            # Check if clicked on any part widget
            clicked_on_part = False
            for part_widget in self.displayed_parts:
                if part_widget.geometry().contains(part_widget.parent().mapFrom(self.recipe_area, local_pos)):
                    clicked_on_part = True
                    break
            
            # If clicked on blank space, clear selection
            if not clicked_on_part:
                self.selected_indices.clear()
                self.last_selected_index = -1
                self.update_selection_display()
        
        super().mousePressEvent(event)
    
    def focusInEvent(self, event: QFocusEvent):
        # Highlight the recipe area when focused to indicate keyboard events are handled here
        self.recipe_area.setStyleSheet("background-color: #f0f0f0; border: 2px solid #aaa; border-radius: 5px;")
        super().focusInEvent(event)
    
    def focusOutEvent(self, event: QFocusEvent):
        # Restore normal styling when focus is lost
        self.recipe_area.setStyleSheet("background-color: #f5f5f5; border: 1px dashed #ccc; border-radius: 5px;")
        super().focusOutEvent(event)
    
    def keyPressEvent(self, event: QKeyEvent):
        # Prevent event propagation for arrow keys - handle them here
        if event.key() in [Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Delete, Qt.Key.Key_Backspace]:
            handled = False
            
            if event.key() in [Qt.Key.Key_Delete, Qt.Key.Key_Backspace]:
                # Handle Delete and Backspace keys to remove selected parts
                if self.selected_indices:
                    # Create a new recipe without the selected indices
                    new_recipe = []
                    for i, part in enumerate(self._recipe):
                        if i not in self.selected_indices:
                            new_recipe.append(part)
                    
                    # Update recipe and reset selection
                    self.recipe = new_recipe
                    handled = True
            
            elif event.key() == Qt.Key.Key_Left:
                # Handle left arrow key
                if self.selected_indices:
                    # Move selected parts one position to the left if possible
                    self._move_selected_parts(-1)
                    handled = True
            
            elif event.key() == Qt.Key.Key_Right:
                # Handle right arrow key
                if self.selected_indices:
                    # Move selected parts one position to the right if possible
                    self._move_selected_parts(1)
                    handled = True
            
            if handled:
                # Stop event from propagating to other widgets
                event.accept()
                return
        
        # For other keys, let parent handle
        super().keyPressEvent(event)
    
    def _move_selected_parts(self, direction: int):
        """Move selected parts in the recipe by direction (-1 for left, 1 for right)
        Always moves by 1 position, regardless of how many parts are selected
        """
        if not self.selected_indices:
            return
        
        # Get sorted list of selected indices
        sorted_indices = sorted(self.selected_indices)
        
        # Check if movement is possible
        if direction == -1:
            # Left: check if first selected index is at position 0
            if sorted_indices[0] == 0:
                return  # Cannot move further left
            # Calculate new start index: move entire selection left by 1
            new_start_index = sorted_indices[0] - 1
        else:  # direction == 1
            # Right: check if last selected index is at last position
            if sorted_indices[-1] == len(self._recipe) - 1:
                return  # Cannot move further right
            # Calculate new start index: move entire selection right by 1
            new_start_index = sorted_indices[0] + 1
        
        # Create a copy of the current recipe
        new_recipe = self._recipe.copy()
        
        # Remove selected parts from their original positions (in reverse order to maintain indices)
        selected_parts = []
        for index in reversed(sorted_indices):
            selected_parts.append(new_recipe.pop(index))
        
        # Reverse the selected parts to maintain their original order
        selected_parts.reverse()
        
        # Ensure new_start_index is within bounds
        new_start_index = max(0, min(new_start_index, len(new_recipe)))
        
        # Insert selected parts at the new position (moved by exactly 1)
        insert_pos = new_start_index
        for part in selected_parts:
            new_recipe.insert(insert_pos, part)
            insert_pos += 1
        
        # Update recipe
        self.recipe = new_recipe
        
        # Update selection to new positions
        new_selected = set()
        for i in range(len(selected_parts)):
            new_selected.add(new_start_index + i)
        self.selected_indices = new_selected
        self.last_selected_index = max(new_selected) if new_selected else -1
        
        self.update_selection_display()
    
    def on_multiplier_changed(self):
        # Get selected multiplier - only affects drag-and-drop operations
        index = self.multiplier_group.checkedId()
        multipliers = [1, 2, 4, 5, 10]
        self._multiplier = multipliers[index]
        # No need to update info since multiplier doesn't affect existing recipe
        self.onChanged.emit()
    
    def on_optimise_changed(self, state: int):
        optimise = state == Qt.CheckState.Checked.value
        self.model.set_optimise(optimise)
        self._optimise = optimise
        self.update_info()
        self.onChanged.emit()
    
    def update_info(self):
        # Update cost label
        creep_info = self.model.get_creep_info()
        self.cost_label.setText(f"{lang('cost')}: {creep_info.cost}")
        self._cost = creep_info.cost
        
        # Update optimised recipe display
        self.update_optimised_display()
        
        # Update static info with ✅/❌ for boolean values
        self.info_display["grade"].setText(str(creep_info.grade))
        self.info_display["effect"].setText(f"{creep_info.effect:.2f}%")
        self.info_display["melee"].setText("✅" if creep_info.melee else "❌")
        self.info_display["ranged"].setText("✅" if creep_info.ranged else "❌")
        self.info_display["heal"].setText("✅" if creep_info.heal else "❌")
        self.info_display["work"].setText("✅" if creep_info.work else "❌")
        self.info_display["storable"].setText("✅" if creep_info.storable else "❌")
        self.info_display["attack_power"].setText(str(creep_info.attack_power))
        self.info_display["melee_power"].setText(str(creep_info.melee_power))
        self.info_display["ranged_power"].setText(str(creep_info.ranged_power))
        self.info_display["heal_power"].setText(str(creep_info.heal_power))
        self.info_display["motion_ability"].setText(f"{creep_info.motion_ability:.2f}")
        self.info_display["armor_ratio"].setText(f"{creep_info.armor_ratio:.2f}")
        self.info_display["melee_ratio"].setText(f"{int(creep_info.melee_ratio)}")
        
        # Update properties
        self._grade = creep_info.grade
        self._effect = creep_info.effect
        
        # Update preview and string representation
        final_recipe = self.model.get_final_recipe()
        self._preview = str(final_recipe).replace("'", "\"").replace('"', "'")
        self._string = creep_info.get_recipe_string()
    
    def update_optimised_display(self):
        # Clear all items from each optimised row layout
        for row_layout in self.optimised_row_layouts:
            for i in reversed(range(row_layout.count())):
                item = row_layout.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()
        
        # Display optimised recipe with same top-left layout as recipe area
        final_recipe = self.model.get_final_recipe()
        
        # Add parts from top-left corner, 10 per row, no auto-centering
        for i, part_type in enumerate(final_recipe):
            row = i // 10
            col = i % 10
            if row < 5 and col < 10:  # Keep within 5 rows, 10 columns
                part_widget = QPSABodyPart(part_type)
                part_widget.setCursor(Qt.CursorShape.ArrowCursor)
                part_widget.setAcceptDrops(False)
                # Add to the appropriate row layout
                self.optimised_row_layouts[row].addWidget(part_widget)
    
    # Properties
    @pyqtProperty(list)
    def recipe(self) -> List[str]:
        return self._recipe
    
    @recipe.setter
    def recipe(self, value: List[str]):
        # Limit recipe to maximum 50 parts
        self._recipe = value[:50]
        self.model.update_recipe(self._recipe)
        self.update_recipe_display()
        self.update_info()
        self.onChanged.emit()
    
    @pyqtProperty(str)
    def preview(self) -> str:
        return self._preview
    
    @pyqtProperty(str)
    def string(self) -> str:
        return self._string
    
    @pyqtProperty(bool)
    def optimise(self) -> bool:
        return self._optimise
    
    @optimise.setter
    def optimise(self, value: bool):
        self._optimise = value
        self.optimise_checkbox.setChecked(value)
        self.model.set_optimise(value)
        self.update_info()
        self.onChanged.emit()
    
    @pyqtProperty(int)
    def cost(self) -> int:
        return self._cost
    
    @pyqtProperty(int)
    def grade(self) -> int:
        return self._grade
    
    @pyqtProperty(float)
    def effect(self) -> float:
        return self._effect
    
    def update_recipe_display(self):
        # Clear existing part widgets
        for widget in self.displayed_parts:
            widget.deleteLater()
        self.displayed_parts.clear()
        
        # Clear all items from each row layout
        for row_layout in self.recipe_row_layouts:
            for i in reversed(range(row_layout.count())):
                item = row_layout.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()
        
        # Clear selection when updating display
        self.selected_indices.clear()
        self.last_selected_index = -1
        
        # Fill with recipe - up to 50 parts (10x5 grid)
        # Add parts from top-left corner, no auto-centering
        for i, part_type in enumerate(self._recipe[:50]):
            row = i // 10
            col = i % 10
            if row < 5 and col < 10:
                part_widget = QPSABodyPart(part_type)
                part_widget.index = i  # Set index for selection management
                part_widget.setCursor(Qt.CursorShape.PointingHandCursor)  # For selectable parts
                # Install event filter for drag-and-drop reordering
                part_widget.installEventFilter(self)
                # Connect click event for selection
                original_mouse_press = part_widget.mousePressEvent
                def custom_mouse_press(event, w=part_widget, original=original_mouse_press):
                    # Call original to set drag_start_position
                    original(event)
                    # Then handle selection
                    self.on_part_clicked(event, w)
                part_widget.mousePressEvent = custom_mouse_press
                # Add to the appropriate row layout
                self.recipe_row_layouts[row].addWidget(part_widget)
                self.displayed_parts.append(part_widget)
        
        # Update selection display
        self.update_selection_display()
    
    def on_part_clicked(self, event: QMouseEvent, part_widget: QPSABodyPart):
        # Get clicked index
        clicked_index = part_widget.index
        
        # Check modifier keys
        is_control_down = event.modifiers() & Qt.KeyboardModifier.ControlModifier
        is_shift_down = event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        
        if is_shift_down and self.last_selected_index >= 0:
            # SHIFT selection - select range from last selected to current
            start = min(self.last_selected_index, clicked_index)
            end = max(self.last_selected_index, clicked_index)
            
            if is_control_down:
                # CONTROL+SHIFT - toggle range selection
                for i in range(start, end + 1):
                    if i in self.selected_indices:
                        self.selected_indices.remove(i)
                    else:
                        self.selected_indices.add(i)
            else:
                # Just SHIFT - select entire range, replacing current selection
                self.selected_indices = set(range(start, end + 1))
        elif is_control_down:
            # CONTROL selection - toggle clicked item
            if clicked_index in self.selected_indices:
                self.selected_indices.remove(clicked_index)
            else:
                self.selected_indices.add(clicked_index)
        else:
            # Single click - select only clicked item
            self.selected_indices = {clicked_index}
        
        # Update last selected index
        self.last_selected_index = clicked_index
        
        # Update display
        self.update_selection_display()
    
    def update_selection_display(self):
        # Update selected state for all displayed parts
        for widget in self.displayed_parts:
            widget.set_selected(widget.index in self.selected_indices)

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("QPSARecipe Test")
    layout = QVBoxLayout(window)
    
    recipe_widget = QPSARecipe()
    layout.addWidget(recipe_widget)
    
    # Test display
    test_recipe = ['WORK', 'WORK', 'WORK', 'MOVE', 'MOVE', 'MOVE']
    recipe_widget.recipe = test_recipe
    
    window.resize(400, 600)
    window.show()
    sys.exit(app.exec())
