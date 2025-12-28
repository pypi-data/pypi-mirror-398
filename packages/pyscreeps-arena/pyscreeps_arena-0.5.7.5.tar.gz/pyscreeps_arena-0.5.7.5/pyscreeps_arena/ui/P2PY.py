# png_to_py.py - 将PNG图片转换为Python模块（最终验证版）
import base64
import sys
from pathlib import Path
import re


def png_to_py(png_path, py_path=None, var_name=None):
    """
    将PNG图片转换为Python模块文件

    :param png_path: PNG图片路径
    :param py_path: 输出的.py文件路径（默认为图片同名.py）
    :param var_name: 变量名（默认为文件名的大写形式）
    """
    png_file = Path(png_path)

    if not png_file.exists():
        raise FileNotFoundError(f"文件 '{png_path}' 不存在")

    if png_file.suffix.lower() != '.png':
        print(f"[警告] 文件 '{png_path}' 不是PNG格式")
        return False

    # 自动生成输出路径
    if py_path is None:
        py_path = png_file.with_suffix('.py')
    else:
        py_path = Path(py_path)

    # 自动生成变量名
    if var_name is None:
        base_name = png_file.stem.replace('-', '_').replace(' ', '_')
        base_name = re.sub(r'[^0-9a-zA-Z_]', '', base_name)
        if base_name and base_name[0].isdigit():
            base_name = f'ICON_{base_name}'
        var_name = base_name.upper()

    try:
        # 读取PNG文件并转换为base64
        with open(png_file, 'rb') as f:
            png_data = f.read()
            base64_data = base64.b64encode(png_data).decode('utf-8')

        print(f"[DEBUG] 读取PNG文件: {len(png_data)} 字节")
        print(f"[DEBUG] Base64编码长度: {len(base64_data)} 字符")

        # 生成Python代码（关键修复：使用 len({var_name})）
        py_content = f'''# -*- coding: utf-8 -*-
"""
PyQt6资源模块: {png_file.name}
由 png_to_py.py 自动生成
"""

# Base64编码的PNG数据（单行，无换行符）
{var_name} = b"{base64_data}"

def get_pixmap():
    \"\"\"返回QPixmap对象\"\"\"
    from PyQt6.QtGui import QPixmap
    from PyQt6.QtCore import QByteArray

    byte_array = QByteArray.fromBase64({var_name})
    pixmap = QPixmap()
    pixmap.loadFromData(byte_array)
    return pixmap

def get_icon():
    \"\"\"返回QIcon对象\"\"\"
    from PyQt6.QtGui import QIcon
    return QIcon(get_pixmap())

if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)

    print(f"资源模块 {var_name} 已加载")
    print(f"字节数据长度: {{len({var_name})}} 字节")  # ✅ 修复：使用 {var_name}

    # 验证能否正确加载
    pixmap = get_pixmap()
    print(f"QPixmap加载成功: 尺寸 {{pixmap.width()}}x{{pixmap.height()}}")
'''

        # 写入Python文件
        with open(py_path, 'w', encoding='utf-8') as f:
            f.write(py_content)

        print(f"✓ 成功: {png_path} -> {py_path}")
        print(f"  变量名: {var_name}")
        return True

    except Exception as e:
        print(f"错误: 转换失败 - {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = "icon.png"

    png_to_py(target, "rs_icon.py")
