from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QLineEdit,
    QCheckBox, QSpinBox, QPushButton, QFrame, QGroupBox,
    QComboBox, QApplication
)
from PyQt6.QtCore import (
    pyqtProperty, pyqtSignal, Qt
)
from pyscreeps_arena.ui.qrecipe.qrecipe import QPSARecipe
from pyscreeps_arena.ui.qcreeplogic.model import CreepLogicSettings
from typing import List, Optional, Union

# Import configuration from build.py
import sys
import os
# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pyscreeps_arena import config

# Language mapping
LANG = {
    'cn': {
        'class_name': '类名',
        'inherit_name': '继承类名',
        'properties': '属性设置',
        'functions': '函数控制',
        'creep_recipe': '爬虫配方',
        'reset': '重置',
        'copy': '复制',
        'name': 'NAME',
        'draw': 'DRAW',
        'layer': 'LAYER',
        'once': 'ONCE',
        'spawnable': 'SPAWNABLE',
        'optimise': 'OPTIMISE',
        'extension': 'EXTENSION',
        'direction': 'DIRECTION',
        'on_loading': 'onLoading',
        'on_start': 'onStart',
        'on_stop': 'onStop',
        'on_changed': 'onChanged',
        'on_killed': 'onKilled',
        'on_draw': 'onDraw',
    },
    'en': {
        'class_name': 'Class Name',
        'inherit_name': 'Inherit Class',
        'properties': 'Properties',
        'functions': 'Functions',
        'creep_recipe': 'Creep Recipe',
        'reset': 'Reset',
        'copy': 'Copy',
        'name': 'NAME',
        'draw': 'DRAW',
        'layer': 'LAYER',
        'once': 'ONCE',
        'spawnable': 'SPAWNABLE',
        'optimise': 'OPTIMISE',
        'extension': 'EXTENSION',
        'direction': 'DIRECTION',
        'on_loading': 'onLoading',
        'on_start': 'onStart',
        'on_stop': 'onStop',
        'on_changed': 'onChanged',
        'on_killed': 'onKilled',
        'on_draw': 'onDraw',
    }
}

def lang(key: str) -> str:
    """Helper function to get translated text"""
    return LANG[config.language if hasattr(config, 'language') and config.language in LANG else 'cn'][key]

# 全局样式常量
CHECKBOX_STYLE = "QCheckBox::indicator { width: 16px; height: 16px; border: 3px solid #555; border-radius: 5px; background-color: white; } QCheckBox::indicator:checked { background-color: #4CAF50; image: url('data:image/svg+xml;utf8,<svg xmlns=\'http://www.w3.org/2000/svg\' width=\'18\' height=\'18\' viewBox=\'0 0 24 24\'><path fill=\'white\' d=\'M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z\'/></svg>'); }"

class QPSACreepLogic(QWidget):
    """
    爬虫逻辑设置组件，用于配置爬虫的基本属性和行为。
    """
    
    # 定义信号
    onChanged = pyqtSignal()
    onReset = pyqtSignal()
    onCopy = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # 模型
        self._settings = CreepLogicSettings()
        
        # QPSARecipe组件
        self._qrecipe = QPSARecipe()
        self._qrecipe.onChanged.connect(self._on_recipe_changed)
        
        # 初始化UI
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 1. 类名和继承类名行
        class_row = QHBoxLayout()
        class_row.setSpacing(10)
        
        # 左边：类名
        class_name_group = QWidget()
        class_name_layout = QVBoxLayout(class_name_group)
        class_name_layout.setContentsMargins(0, 0, 0, 0)
        class_name_label = QLabel(lang('class_name'))
        self._class_name_edit = QLineEdit()
        self._class_name_edit.setPlaceholderText("MyCreep")  # 类名默认为MyCreep的placeholder
        class_name_layout.addWidget(class_name_label)
        class_name_layout.addWidget(self._class_name_edit)
        class_name_group.setFixedWidth(240)  # 3:2比例，总宽度600的话
        
        # 右边：继承类名
        inherit_name_group = QWidget()
        inherit_name_layout = QVBoxLayout(inherit_name_group)
        inherit_name_layout.setContentsMargins(0, 0, 0, 0)
        inherit_name_label = QLabel(lang('inherit_name'))
        self._inherit_name_edit = QLineEdit("CreepLogic")
        inherit_name_layout.addWidget(inherit_name_label)
        inherit_name_layout.addWidget(self._inherit_name_edit)
        inherit_name_group.setFixedWidth(160)  # 3:2比例
        
        class_row.addWidget(class_name_group)
        class_row.addWidget(inherit_name_group)
        class_row.addStretch()
        main_layout.addLayout(class_row)
        
        # 2. 属性字段行（参考engine.py设计，除了RECIPE）
        properties_group = QGroupBox(lang('properties'))
        properties_layout = QGridLayout(properties_group)
        properties_layout.setSpacing(15)
        
        # 设置列宽比例为1:1
        properties_layout.setColumnStretch(0, 1)  # 标签列
        properties_layout.setColumnStretch(1, 1)  # 控件列
        properties_layout.setColumnStretch(2, 1)  # 标签列
        properties_layout.setColumnStretch(3, 1)  # 控件列
        
        # 设置固定宽度
        label_width = 80
        
        # 第一列
        # NAME属性
        name_label = QLabel(lang('name'))
        name_label.setFixedWidth(label_width)
        self._name_edit = QLineEdit()
        # 设置初始PlaceHolder与默认类名一致
        default_class_name = self._class_name_edit.text().strip() or "MyCreep"
        self._name_edit.setPlaceholderText(default_class_name)
        properties_layout.addWidget(name_label, 0, 0)
        properties_layout.addWidget(self._name_edit, 0, 1)
        
        # Draw属性
        draw_label = QLabel(lang('draw'))
        draw_label.setFixedWidth(label_width)
        self._draw_checkbox = QCheckBox()
        # 增加复选框大小
        self._draw_checkbox.setStyleSheet(CHECKBOX_STYLE)
        properties_layout.addWidget(draw_label, 1, 0)
        properties_layout.addWidget(self._draw_checkbox, 1, 1)
        
        # Layer属性
        layer_label = QLabel(lang('layer'))
        layer_label.setFixedWidth(label_width)
        self._layer_spinbox = QSpinBox()
        self._layer_spinbox.setRange(0, 100)
        self._layer_spinbox.setValue(10)
        properties_layout.addWidget(layer_label, 2, 0)
        properties_layout.addWidget(self._layer_spinbox, 2, 1)
        
        # Once属性
        once_label = QLabel(lang('once'))
        once_label.setFixedWidth(label_width)
        self._once_checkbox = QCheckBox()
        self._once_checkbox.setChecked(True)
        # 增加复选框大小
        self._once_checkbox.setStyleSheet(CHECKBOX_STYLE)
        properties_layout.addWidget(once_label, 3, 0)
        properties_layout.addWidget(self._once_checkbox, 3, 1)
        
        # 第二列
        # Spawnable属性
        spawnable_label = QLabel(lang('spawnable'))
        spawnable_label.setFixedWidth(label_width)
        self._spawnable_checkbox = QCheckBox()
        self._spawnable_checkbox.setChecked(True)
        # 增加复选框大小
        self._spawnable_checkbox.setStyleSheet(CHECKBOX_STYLE)
        properties_layout.addWidget(spawnable_label, 0, 2)
        properties_layout.addWidget(self._spawnable_checkbox, 0, 3)
        
        # Optimise属性
        optimise_label = QLabel(lang('optimise'))
        optimise_label.setFixedWidth(label_width)
        self._optimise_checkbox = QCheckBox()
        self._optimise_checkbox.setChecked(True)
        # 增加复选框大小
        self._optimise_checkbox.setStyleSheet(CHECKBOX_STYLE)
        # 连接信号，实现与QPSARecipe的'自动优化'同步
        self._optimise_checkbox.stateChanged.connect(self._on_optimise_changed)
        properties_layout.addWidget(optimise_label, 1, 2)
        properties_layout.addWidget(self._optimise_checkbox, 1, 3)
        
        # Extension属性
        extension_label = QLabel(lang('extension'))
        extension_label.setFixedWidth(label_width)
        self._extension_checkbox = QCheckBox()
        self._extension_checkbox.setChecked(True)
        # 增加复选框大小
        self._extension_checkbox.setStyleSheet(CHECKBOX_STYLE)
        properties_layout.addWidget(extension_label, 2, 2)
        properties_layout.addWidget(self._extension_checkbox, 2, 3)
        
        # Direction属性
        direction_label = QLabel(lang('direction'))
        direction_label.setFixedWidth(label_width)
        # 使用QComboBox显示方向符号
        self._direction_combo = QComboBox()
        self._direction_combo.addItem("None", None)
        self._direction_combo.addItem("IN", 9)  # IN_DIRECT
        self._direction_combo.addItem("OUT", 10)  # OUT_DIRECT
        self._direction_combo.addItem("↑", 1)  # TOP
        self._direction_combo.addItem("↗", 2)  # TOP_RIGHT
        self._direction_combo.addItem("→", 3)  # RIGHT
        self._direction_combo.addItem("↘", 4)  # BOTTOM_RIGHT
        self._direction_combo.addItem("↓", 5)  # BOTTOM
        self._direction_combo.addItem("↙", 6)  # BOTTOM_LEFT
        self._direction_combo.addItem("←", 7)  # LEFT
        self._direction_combo.addItem("↖", 8)  # TOP_LEFT
        self._direction_combo.currentIndexChanged.connect(self._on_settings_changed)
        properties_layout.addWidget(direction_label, 3, 2)
        properties_layout.addWidget(self._direction_combo, 3, 3)
        
        main_layout.addWidget(properties_group)
        
        # 3.5 函数控制行
        functions_group = QGroupBox(lang('functions'))
        functions_layout = QGridLayout(functions_group)
        functions_layout.setHorizontalSpacing(20)  # 水平间距20px
        functions_layout.setVerticalSpacing(10)  # 垂直间距10px
        
        # onLoading复选框
        self._on_loading_checkbox = QCheckBox(lang('on_loading'))
        self._on_loading_checkbox.setChecked(True)  # 默认开启
        self._on_loading_checkbox.setStyleSheet(CHECKBOX_STYLE)
        functions_layout.addWidget(self._on_loading_checkbox, 0, 0)
        
        # onStart复选框
        self._on_start_checkbox = QCheckBox(lang('on_start'))
        self._on_start_checkbox.setChecked(False)  # 默认关闭
        self._on_start_checkbox.setStyleSheet(CHECKBOX_STYLE)
        functions_layout.addWidget(self._on_start_checkbox, 0, 1)
        
        # onStop复选框
        self._on_stop_checkbox = QCheckBox(lang('on_stop'))
        self._on_stop_checkbox.setChecked(False)  # 默认关闭
        self._on_stop_checkbox.setStyleSheet(CHECKBOX_STYLE)
        functions_layout.addWidget(self._on_stop_checkbox, 0, 2)
        
        # onChanged复选框
        self._on_changed_checkbox = QCheckBox(lang('on_changed'))
        self._on_changed_checkbox.setChecked(False)  # 默认关闭
        self._on_changed_checkbox.setStyleSheet(CHECKBOX_STYLE)
        functions_layout.addWidget(self._on_changed_checkbox, 1, 0)
        
        # onKilled复选框
        self._on_killed_checkbox = QCheckBox(lang('on_killed'))
        self._on_killed_checkbox.setChecked(False)  # 默认关闭
        self._on_killed_checkbox.setStyleSheet(CHECKBOX_STYLE)
        functions_layout.addWidget(self._on_killed_checkbox, 1, 1)
        
        # onDraw复选框
        self._on_draw_checkbox = QCheckBox(lang('on_draw'))
        self._on_draw_checkbox.setChecked(False)  # 默认关闭
        self._on_draw_checkbox.setStyleSheet(CHECKBOX_STYLE)
        functions_layout.addWidget(self._on_draw_checkbox, 1, 2)
        main_layout.addWidget(functions_group)
        
        # 4. QPSARecipe组件
        recipe_group = QGroupBox(lang('creep_recipe'))
        recipe_layout = QVBoxLayout(recipe_group)
        recipe_layout.addWidget(self._qrecipe)
        main_layout.addWidget(recipe_group)
        
        # 5. 按钮行
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(10)
        
        # Reset按钮
        self._reset_button = QPushButton(lang('reset'))
        self._reset_button.clicked.connect(self._on_reset_clicked)
        
        # Copy按钮
        self._copy_button = QPushButton(lang('copy'))
        self._copy_button.clicked.connect(self._on_copy_clicked)
        
        buttons_row.addWidget(self._reset_button)
        buttons_row.addWidget(self._copy_button)
        buttons_row.addStretch()
        main_layout.addLayout(buttons_row)
        
        # 连接信号
        self._connect_signals()
        
    def _connect_signals(self):
        """
        连接所有信号
        """
        # 类名和继承类名信号
        self._class_name_edit.textChanged.connect(self._on_settings_changed)
        self._class_name_edit.textChanged.connect(self._on_class_name_changed)
        self._inherit_name_edit.textChanged.connect(self._on_settings_changed)
        
        # NAME字段信号
        self._name_edit.textChanged.connect(self._on_settings_changed)
        
        # 属性字段信号
        self._draw_checkbox.stateChanged.connect(self._on_settings_changed)
        self._layer_spinbox.valueChanged.connect(self._on_settings_changed)
        self._once_checkbox.stateChanged.connect(self._on_settings_changed)
        self._spawnable_checkbox.stateChanged.connect(self._on_settings_changed)
        self._extension_checkbox.stateChanged.connect(self._on_settings_changed)
        
        # 连接QPSARecipe的onChanged信号，用于同步optimise设置
        self._qrecipe.onChanged.connect(self._on_qrecipe_changed)
        
    def _on_settings_changed(self):
        """
        设置改变时更新模型并发出信号
        """
        self._update_settings()
        self.onChanged.emit()
        
    def _on_class_name_changed(self):
        """
        类名改变时更新NAME的PlaceHolder
        """
        # 获取当前类名或默认值
        class_name = self._class_name_edit.text().strip() or "MyCreep"
        # 更新NAME的PlaceHolder与类名一致
        self._name_edit.setPlaceholderText(class_name)
        
    def _on_recipe_changed(self):
        """
        配方改变时更新模型并发出信号
        """
        self._settings.recipe = self._qrecipe.recipe
        self.onChanged.emit()
        
    def _on_optimise_changed(self, state):
        """
        OPTIMISE复选框改变时同步QPSARecipe的'自动优化'设置
        """
        optimise = state == Qt.CheckState.Checked.value
        self._settings.optimise = optimise
        # 同步QPSARecipe的optimise设置
        self._qrecipe.optimise = optimise
        self.onChanged.emit()
        
    def _on_qrecipe_changed(self):
        """
        QPSARecipe改变时同步optimise设置
        """
        # 只有当QPSARecipe的optimise设置与当前不同时才更新
        if self._qrecipe.optimise != self._settings.optimise:
            self._settings.optimise = self._qrecipe.optimise
            self._optimise_checkbox.setChecked(self._qrecipe.optimise)
            self.onChanged.emit()
        
    def _on_reset_clicked(self):
        """
        Reset按钮点击事件
        """
        self.reset()
        self.onReset.emit()
        
    def _on_copy_clicked(self):
        """
        Copy按钮点击事件
        """
        # 生成Python代码
        python_code = self.generate_python_code()
        # 将代码复制到剪贴板
        clipboard = QApplication.clipboard()
        clipboard.setText(python_code)
        self.onCopy.emit()
        
    def generate_python_code(self) -> str:
        """
        生成Python代码，以class <classname>(inherit)开始
        """
        self._update_settings()
        
        # 获取类名和继承类名
        class_name = self._class_name_edit.text().strip() or "MyCreep"
        inherit_name = self._inherit_name_edit.text().strip() or "CreepLogic"
        
        # 构建类定义
        code_lines = []
        code_lines.append(f"class {class_name}({inherit_name}):")
        name_value = self._settings.name if self._settings.name else class_name
        code_lines.append(f"    NAME = \"{name_value}\"")
        
        # 添加属性
        if self._settings.draw:
            code_lines.append(f"    DRAW = {self._settings.draw}")
        if self._settings.layer != 10:
            code_lines.append(f"    LAYER = {self._settings.layer}")
        if self._settings.link is not None:
            if isinstance(self._settings.link, list):
                code_lines.append(f"    LINK = {self._settings.link}")
            else:
                code_lines.append(f"    LINK = \"{self._settings.link}\"")
        if not self._settings.once:
            code_lines.append(f"    ONCE = {self._settings.once}")
        if not self._settings.spawnable:
            code_lines.append(f"    SPAWNABLE = {self._settings.spawnable}")
        
        # 添加配方，使用qrecipe的.string属性
        recipe_string = self._qrecipe.string
        if recipe_string:
            code_lines.append(f"    RECIPE = \"{recipe_string}\"")
        
        if not self._settings.optimise:
            code_lines.append(f"    OPTIMISE = {self._settings.optimise}")
        if not self._settings.extension:
            code_lines.append(f"    EXTENSION = {self._settings.extension}")
        if self._settings.direction is not None:
            # 方向映射：数字 -> 常量名称
            direction_map = {
                1: "TOP",
                2: "TOP_RIGHT",
                3: "RIGHT",
                4: "BOTTOM_RIGHT",
                5: "BOTTOM",
                6: "BOTTOM_LEFT",
                7: "LEFT",
                8: "TOP_LEFT",
                9: "IN_DIRECT",
                10: "OUT_DIRECT"
            }
            direction_name = direction_map.get(self._settings.direction, self._settings.direction)
            code_lines.append(f"    DIRECTION = {direction_name}")
        
        # 添加空行和基本方法框架
        # 根据复选框状态决定是否生成onLoading方法
        if self._on_loading_checkbox.isChecked():
            code_lines.append("")
            code_lines.append("    def onLoading(self, c: Creep | None, k: GlobalKnowledge, *refs: \"CreepLogic\") -> None:")
            code_lines.append("        # 初始化逻辑")
            code_lines.append("        pass")
        
        # 根据复选框状态决定是否生成onStart方法
        if self._on_start_checkbox.isChecked():
            code_lines.append("")
            code_lines.append("    def onStart(self, c: Creep, k: GlobalKnowledge, *refs: \"CreepLogic\") -> None:")
            code_lines.append("        # 启动逻辑")
            code_lines.append("        pass")
        
        # 必生成onStep方法
        code_lines.append("")
        code_lines.append("    def onStep(self, c: Creep, k: GlobalKnowledge, *refs):")
        code_lines.append("        # 主逻辑")
        code_lines.append("        pass")
        
        # 根据复选框状态决定是否生成onStop方法
        if self._on_stop_checkbox.isChecked():
            code_lines.append("")
            code_lines.append("    def onStop(self, c: Creep | None, k: GlobalKnowledge, *refs: \"CreepLogic\") -> None:")
            code_lines.append("        # 停止逻辑")
            code_lines.append("        pass")
        
        # 根据复选框状态决定是否生成onChanged方法
        if self._on_changed_checkbox.isChecked():
            code_lines.append("")
            code_lines.append("    def onChanged(self, src: str, dst: str, inst: any, k: GlobalKnowledge):")
            code_lines.append("        # 状态变化逻辑")
            code_lines.append("        pass")
        
        # 根据复选框状态决定是否生成onKilled方法
        if self._on_killed_checkbox.isChecked():
            code_lines.append("")
            code_lines.append("    def onKilled(self, c: Creep | None, k: GlobalKnowledge, *refs: \"CreepLogic\") -> None:")
            code_lines.append("        # 被杀死逻辑")
            code_lines.append("        pass")
        
        # 根据复选框状态决定是否生成onDraw方法
        if self._on_draw_checkbox.isChecked():
            code_lines.append("")
            code_lines.append("    def onDraw(self, c: Creep, v: View, k: GlobalKnowledge, *refs: \"CreepLogic\") -> None:")
            code_lines.append("        # 绘制逻辑")
            code_lines.append("        pass")
        
        # 合并所有行
        return "\n".join(code_lines)
        
    def _update_settings(self):
        """
        从UI更新模型
        """
        # 更新NAME
        self._settings.name = self._name_edit.text()
        
        # 更新属性
        self._settings.draw = self._draw_checkbox.isChecked()
        self._settings.layer = self._layer_spinbox.value()
        
        # 移除LINK的设定
        self._settings.link = None
        
        self._settings.once = self._once_checkbox.isChecked()
        self._settings.spawnable = self._spawnable_checkbox.isChecked()
        self._settings.optimise = self._optimise_checkbox.isChecked()
        self._settings.extension = self._extension_checkbox.isChecked()
        
        # 处理DIRECTION
        direction_val = self._direction_combo.currentData()
        self._settings.direction = direction_val
        
    def reset(self):
        """
        重置所有设置为默认值
        """
        # 重置模型
        self._settings = CreepLogicSettings()
        
        # 重置UI
        self._class_name_edit.clear()
        self._inherit_name_edit.setText("CreepLogic")
        self._name_edit.clear()
        
        # 重置属性
        self._draw_checkbox.setChecked(False)
        self._layer_spinbox.setValue(10)
        # 移除LINK的设定，无需重置
        self._once_checkbox.setChecked(True)
        self._spawnable_checkbox.setChecked(True)
        self._qrecipe.recipe = ["MOVE"]
        self._optimise_checkbox.setChecked(True)
        # 同步QPSARecipe的optimise设置
        self._qrecipe.optimise = True
        self._extension_checkbox.setChecked(True)
        self._direction_combo.setCurrentIndex(0)
        
        # 重置函数控制复选框
        self._on_loading_checkbox.setChecked(True)
        self._on_start_checkbox.setChecked(False)
        self._on_stop_checkbox.setChecked(False)
        self._on_changed_checkbox.setChecked(False)
        self._on_killed_checkbox.setChecked(False)
        self._on_draw_checkbox.setChecked(False)
        
        self.onChanged.emit()
        
    def get_settings(self) -> CreepLogicSettings:
        """
        获取当前设置
        """
        self._update_settings()
        return self._settings
        
    def set_settings(self, settings: CreepLogicSettings):
        """
        设置当前配置
        """
        self._settings = settings
        
        # 更新UI
        self._name_edit.setText(settings.name)
        
        # 更新属性
        self._draw_checkbox.setChecked(settings.draw)
        self._layer_spinbox.setValue(settings.layer)
        
        # 移除LINK的设定，无需更新
        
        self._once_checkbox.setChecked(settings.once)
        self._spawnable_checkbox.setChecked(settings.spawnable)
        self._qrecipe.recipe = settings.recipe if isinstance(settings.recipe, list) else ["MOVE"]
        self._optimise_checkbox.setChecked(settings.optimise)
        # 同步QPSARecipe的optimise设置
        self._qrecipe.optimise = settings.optimise
        self._extension_checkbox.setChecked(settings.extension)
        
        # 更新DIRECTION
        for i in range(self._direction_combo.count()):
            if self._direction_combo.itemData(i) == settings.direction:
                self._direction_combo.setCurrentIndex(i)
                break
        
        self.onChanged.emit()
        
    # Properties
    @pyqtProperty(str)
    def name(self) -> str:
        return self._settings.name
    
    @name.setter
    def name(self, value: str):
        self._settings.name = value
        self._name_edit.setText(value)
        self.onChanged.emit()
    
    @pyqtProperty(bool)
    def draw(self) -> bool:
        return self._settings.draw
    
    @draw.setter
    def draw(self, value: bool):
        self._settings.draw = value
        self._draw_checkbox.setChecked(value)
        self.onChanged.emit()
    
    @pyqtProperty(int)
    def layer(self) -> int:
        return self._settings.layer
    
    @layer.setter
    def layer(self, value: int):
        self._settings.layer = value
        self._layer_spinbox.setValue(value)
        self.onChanged.emit()
    
    @pyqtProperty(object)
    def link(self) -> Union[List[str], str, None]:
        return self._settings.link
    
    @link.setter
    def link(self, value: Union[List[str], str, None]):
        self._settings.link = value
        if value is None:
            self._link_edit.clear()
        elif isinstance(value, list):
            self._link_edit.setText(", ".join(value))
        else:
            self._link_edit.setText(value)
        self.onChanged.emit()
    
    @pyqtProperty(bool)
    def once(self) -> bool:
        return self._settings.once
    
    @once.setter
    def once(self, value: bool):
        self._settings.once = value
        self._once_checkbox.setChecked(value)
        self.onChanged.emit()
    
    @pyqtProperty(bool)
    def spawnable(self) -> bool:
        return self._settings.spawnable
    
    @spawnable.setter
    def spawnable(self, value: bool):
        self._settings.spawnable = value
        self._spawnable_checkbox.setChecked(value)
        self.onChanged.emit()
    
    @pyqtProperty(list)
    def recipe(self) -> List[str]:
        return self._settings.recipe if isinstance(self._settings.recipe, list) else ["MOVE"]
    
    @recipe.setter
    def recipe(self, value: List[str]):
        self._settings.recipe = value
        self._qrecipe.recipe = value
        self.onChanged.emit()
    
    @pyqtProperty(bool)
    def optimise(self) -> bool:
        return self._settings.optimise
    
    @optimise.setter
    def optimise(self, value: bool):
        self._settings.optimise = value
        self._optimise_checkbox.setChecked(value)
        self.onChanged.emit()
    
    @pyqtProperty(bool)
    def extension(self) -> bool:
        return self._settings.extension
    
    @extension.setter
    def extension(self, value: bool):
        self._settings.extension = value
        self._extension_checkbox.setChecked(value)
        self.onChanged.emit()
    
    @pyqtProperty(object)
    def direction(self) -> Optional[int]:
        return self._settings.direction
    
    @direction.setter
    def direction(self, value: Optional[int]):
        self._settings.direction = value
        for i in range(self._direction_combo.count()):
            if self._direction_combo.itemData(i) == value:
                self._direction_combo.setCurrentIndex(i)
                break
        self.onChanged.emit()
    
    @pyqtProperty(object)
    def qrecipe(self) -> QPSARecipe:
        return self._qrecipe
    
    def to_dict(self) -> dict:
        """
        将设置转换为字典格式
        """
        self._update_settings()
        return {
            "class_name": self._class_name_edit.text(),
            "inherit_name": self._inherit_name_edit.text(),
            **self._settings.to_dict()
        }
    
    def from_dict(self, data: dict):
        """
        从字典格式加载设置
        """
        # 加载类名和继承类名
        self._class_name_edit.setText(data.get("class_name", ""))
        self._inherit_name_edit.setText(data.get("inherit_name", "CreepLogic"))
        
        # 加载设置
        self._settings = CreepLogicSettings.from_dict(data)
        self.set_settings(self._settings)


if __name__ == "__main__":
    """
    直接运行组件的主程序入口点
    """
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
    
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("QPSACreepLogic Demo")
            # 使用resize方法替换setWidth和setHeight
            self.resize(380, 700)
            
            # 中央部件
            central_widget = QWidget()
            main_layout = QVBoxLayout(central_widget)
            
            # 添加QPSACreepLogic组件
            self.creep_logic_widget = QPSACreepLogic()
            main_layout.addWidget(self.creep_logic_widget)
            
            self.setCentralWidget(central_widget)
    
    # 创建应用程序和窗口
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())



