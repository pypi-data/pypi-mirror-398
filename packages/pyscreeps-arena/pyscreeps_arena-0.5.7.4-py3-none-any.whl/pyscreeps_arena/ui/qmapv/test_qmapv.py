# -*- coding: utf-8 -*-
"""
QPSA Map Viewer Test Application
"""
import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QTextEdit, QSplitter, QPushButton)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ui.qmapv import QPSAMapViewer, CellInfo
from ui.qmapv.qcinfo import QPSACellInfo
from ui.qmapv.qco import QPSACellObject
from pyscreeps_arena import config


class MapViewerDemo(QMainWindow):
    """Demo application for QPSAMapViewer."""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the UI."""
        self.setWindowTitle("QPSA Map Viewer Demo")
        self.setGeometry(100, 100, 1400, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Map viewer
        self._map_viewer = QPSAMapViewer()
        self._map_viewer.currentChanged.connect(self._on_current_changed)
        self._map_viewer.selectChanged.connect(self._on_select_changed)
        self._map_viewer.rightClicked.connect(self._on_right_clicked)
        splitter.addWidget(self._map_viewer)
        
        # Right panel - Info panel with QPSACellInfo components
        info_panel = QWidget()
        info_layout = QVBoxLayout(info_panel)
        
        # Current cell info (hover)
        current_group = QWidget()
        current_layout = QVBoxLayout(current_group)
        
        current_label = QLabel("当前单元格 (鼠标悬停)")
        current_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        current_layout.addWidget(current_label)
        
        self._current_cell_info = QPSACellInfo()
        self._current_cell_info.setMaximumHeight(180)  # Updated height constraint
        current_layout.addWidget(self._current_cell_info)
        
        info_layout.addWidget(current_group)
        
        # Selected cell info (click)
        selected_group = QWidget()
        selected_layout = QVBoxLayout(selected_group)
        
        selected_label = QLabel("选中单元格 (鼠标点击)")
        selected_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        selected_layout.addWidget(selected_label)
        
        self._selected_cell_info = QPSACellInfo()
        self._selected_cell_info.setMaximumHeight(200)
        selected_layout.addWidget(self._selected_cell_info)
        
        info_layout.addWidget(selected_group)
        
        # Right-clicked cell info
        right_click_group = QWidget()
        right_click_layout = QVBoxLayout(right_click_group)
        
        right_click_label = QLabel("右键点击单元格")
        right_click_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        right_click_layout.addWidget(right_click_label)
        
        self._right_click_cell_info = QPSACellInfo()
        self._right_click_cell_info.setMaximumHeight(200)
        right_click_layout.addWidget(self._right_click_cell_info)
        
        info_layout.addWidget(right_click_group)
        
        # Language toggle button
        self._lang_button = QPushButton("切换语言 (CN/EN)")
        self._lang_button.clicked.connect(self._toggle_language)
        info_layout.addWidget(self._lang_button)
        
        # Instructions
        instructions = QLabel(
            "使用说明:\n"
            "1. 点击'打开地图'按钮选择JSON文件\n"
            "2. 鼠标悬停查看单元格信息\n"
            "3. 鼠标点击选择单元格\n"
            "4. 鼠标右键点击触发右键事件\n"
            "5. 使用鼠标滚轮缩放地图\n"
            "6. 拖拽地图进行平移\n"
            "\n"
            "注意: GameObject和Structure基础类型已被过滤，\n"
            "但它们的子类(如StructureSpawn等)会正常显示"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("font-size: 11px; color: #666; padding: 10px;")
        # Cell objects component for drag and drop test
        objects_group = QWidget()
        objects_layout = QVBoxLayout(objects_group)
        
        objects_label = QLabel("拖拽对象列表")
        objects_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        objects_layout.addWidget(objects_label)
        
        self._cell_objects = QPSACellObject()
        self._cell_objects.setMinimumHeight(200)
        objects_layout.addWidget(self._cell_objects)
        
        info_layout.addWidget(objects_group)
        
        info_layout.addWidget(instructions)
        
        info_layout.addStretch()
        
        splitter.addWidget(info_panel)
        splitter.setSizes([1024, 376])
        
        main_layout.addWidget(splitter)
        
        # Try to load default map if available
        default_map = os.path.join(os.path.dirname(__file__), '..', '..', 'map.json')
        if os.path.exists(default_map):
            try:
                self._map_viewer.load_map(default_map)
            except Exception as e:
                print(f"[DEBUG] Failed to load default map: {e}")  # 调试输出
    
    @pyqtSlot(object)
    def _on_current_changed(self, cell_info):
        """Handle current cell change."""
        self._current_cell_info.data = cell_info
        # Set map image for object icons
        self._current_cell_info.image = self._map_viewer.image
        print(f"[DEBUG] Current cell updated: {cell_info}")  # 调试输出
    
    @pyqtSlot(object)
    def _on_select_changed(self, cell_info):
        """Handle selected cell change."""
        self._selected_cell_info.data = cell_info
        # Set map image for object icons
        self._selected_cell_info.image = self._map_viewer.image
        print(f"[DEBUG] Selected cell updated: {cell_info}")  # 调试输出
    
    @pyqtSlot(object)
    def _on_right_clicked(self, cell_info):
        """Handle right-click events."""
        self._right_click_cell_info.data = cell_info
        # Set map image for object icons
        self._right_click_cell_info.image = self._map_viewer.image
        print(f"[DEBUG] Right-click cell updated: {cell_info}")  # 调试输出
    
    @pyqtSlot(str)
    def _on_item_selected(self, obj_id):
        """Handle object selection in QPSACellInfo."""
        print(f"[DEBUG] Object selected: {obj_id}")  # 调试输出
    
    @pyqtSlot(str)
    def _on_item_cancel_selected(self, obj_id):
        """Handle object deselection in QPSACellInfo."""
        print(f"[DEBUG] Object deselected: {obj_id}")  # 调试输出
    
    @pyqtSlot(str, bool)
    def _on_item_select_changed(self, obj_id, selected):
        """Handle object selection change in QPSACellInfo."""
        print(f"[DEBUG] Object selection changed: {obj_id} -> {selected}")  # 调试输出
    
    @pyqtSlot()
    def _toggle_language(self):
        """Toggle language between CN and EN."""
        config.language = 'en' if config.language == 'cn' else 'cn'
        print(f"[DEBUG] Language switched to: {config.language}")  # 调试输出：查看语言切换
        
        # Update button text
        self._lang_button.setText("切换语言 (CN/EN)" if config.language == 'cn' else "Switch Language (CN/EN)")
        
        # Reload current map to refresh UI text
        current_map = self._map_viewer._current_map_path if hasattr(self._map_viewer, '_current_map_path') else None
        if current_map and os.path.exists(current_map):
            self._map_viewer.load_map(current_map)
        else:
            # Reset to default state to show new language
            self._map_viewer._reset_to_default_state()
    
    def closeEvent(self, event):
        """Clean up when closing."""
        self._map_viewer.cleanup()
        event.accept()


def main():
    """Main function."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show demo
    demo = MapViewerDemo()
    demo.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()