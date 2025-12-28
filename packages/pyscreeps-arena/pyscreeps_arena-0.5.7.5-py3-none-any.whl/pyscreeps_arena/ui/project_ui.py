# -*- coding: utf-8 -*-
"""
项目创建UI界面
"""
import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtGui import QIcon
from pyscreeps_arena.core import const
from pyscreeps_arena.ui.rs_icon import get_pixmap



class ProjectCreatorUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self._proj_name = ""
        self._proj_path = ""
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI界面"""
        self.setWindowTitle("PyScreeps Arena - 项目创建器")
        self.setWindowIcon(QIcon(get_pixmap()))
        self.setFixedSize(500, 350)
        
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title = QLabel("PyScreeps Arena")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # 项目信息
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(8)
        
        # 版本信息
        version_label = QLabel(f"版本: {const.VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(version_label)
        
        # 作者信息
        author_label = QLabel(f"作者: {const.AUTHOR}")
        author_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(author_label)
        
        # GitHub信息
        github_label = QLabel(f"GitHub: {const.GITHUB_NAME}")
        github_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(github_label)
        
        layout.addWidget(info_widget)
        
        # 分隔线
        separator = QLabel("─" * 50)
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        separator.setStyleSheet("color: #ccc;")
        layout.addWidget(separator)
        
        # 项目输入区域
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        input_layout.setSpacing(12)
        
        # 项目名称输入
        name_layout = QHBoxLayout()
        name_label = QLabel("项目名称:")
        name_label.setFixedWidth(80)
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("输入项目名称...")
        self._name_input.textChanged.connect(self._on_name_changed)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self._name_input)
        input_layout.addLayout(name_layout)
        
        # 项目路径输入
        path_layout = QHBoxLayout()
        path_label = QLabel("保存位置:")
        path_label.setFixedWidth(80)
        self._path_input = QLineEdit()
        self._path_input.setPlaceholderText("选择项目保存位置...")
        self._path_input.setReadOnly(True)
        # 默认桌面路径
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        if os.path.exists(desktop_path):
            self._path_input.setText(desktop_path)
            self._proj_path = desktop_path
        path_layout.addWidget(path_label)
        path_layout.addWidget(self._path_input)
        
        # 浏览按钮
        browse_btn = QPushButton("浏览...")
        browse_btn.setFixedWidth(60)
        browse_btn.clicked.connect(self._browse_path)
        path_layout.addWidget(browse_btn)
        
        input_layout.addLayout(path_layout)
        layout.addWidget(input_widget)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 创建按钮
        self._create_btn = QPushButton("创建项目")
        self._create_btn.setFixedSize(100, 35)
        self._create_btn.clicked.connect(self._create_project)
        self._create_btn.setEnabled(False)
        button_layout.addWidget(self._create_btn)
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(80, 35)
        cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
    def _on_name_changed(self, text):
        """项目名称改变时的处理"""
        self._proj_name = text.strip()
        self._create_btn.setEnabled(bool(self._proj_name and self._proj_path))
        
    def _browse_path(self):
        """浏览选择路径"""
        current_path = self._path_input.text() or os.path.expanduser("~")
        path = QFileDialog.getExistingDirectory(
            self, "选择项目保存位置", current_path
        )
        if path:
            self._path_input.setText(path)
            self._proj_path = path
            self._create_btn.setEnabled(bool(self._proj_name and self._proj_path))
            
    def _create_project(self):
        """创建项目"""
        if not self._proj_name or not self._proj_path:
            return
            
        # 构建完整路径
        full_path = os.path.join(self._proj_path, self._proj_name)
        
        # 检查路径是否已存在
        if os.path.exists(full_path):
            reply = QMessageBox.question(
                self, "路径已存在",
                f"路径 '{full_path}' 已存在。\n是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        try:
            # 创建项目
            self._extract_project_template(full_path)
            
            QMessageBox.information(
                self, "成功",
                f"项目 '{self._proj_name}' 创建成功！\n路径: {full_path}"
            )
            self.close()
            
        except Exception as e:
            QMessageBox.critical(
                self, "错误",
                f"项目创建失败:\n{str(e)}"
            )
            
    def _extract_project_template(self, target_path):
        """提取项目模板"""
        # 获取当前包路径
        this_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_7z_path = os.path.join(this_path, 'project.7z')
        
        if not os.path.exists(project_7z_path):
            raise FileNotFoundError(f"项目模板文件不存在: {project_7z_path}")
            
        # 创建目标目录
        os.makedirs(target_path, exist_ok=True)
        
        # 解压项目模板
        import py7zr
        with py7zr.SevenZipFile(project_7z_path, mode='r') as archive:
            archive.extractall(path=target_path)
            
        print(f"[DEBUG] 项目模板已解压到: {target_path}")  # 调试输出


def run_project_creator():
    """运行项目创建器UI"""
    app = QApplication(sys.argv)
    window = ProjectCreatorUI()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    run_project_creator()
