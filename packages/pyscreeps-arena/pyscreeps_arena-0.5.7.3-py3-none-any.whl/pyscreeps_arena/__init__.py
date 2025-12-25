import os
import sys
import shutil
import py7zr
from pyscreeps_arena.core import const, config
from pyscreeps_arena.ui.mapviewer import run_mapviewer
from pyscreeps_arena.ui.project_ui import run_project_creator
from pyscreeps_arena.ui.creeplogic_edit import run_creeplogic_edit

def CMD_NewProject():
    """
    cmd:
        pyscreeps-arena  [project_path]
        arena [project_path]

    * 复制"src" "game" "build.py" 到指定目录

    Returns:

    """
    if len(sys.argv) < 2:
        print("Usage: pyarena new [project_path]\n# or\narena new [project_path]")
        return
    project_path = sys.argv[1]
    if not os.path.exists(project_path):
        os.makedirs(project_path)
    this_path = os.path.dirname(os.path.abspath(__file__))
    extract_7z(os.path.join(this_path, 'project.7z'), project_path)
    print("Project created at", project_path)

def CMD_OpenUI():
    """
    cmd:
        psaui 无参数，启用project ui
        psaui -c/-e 启用creeplogic edit
        psaui -m [-c/-e] 启用mapviewer. 默认cn，可以指定-c/-e
        psaui -h 显示帮助信息

    * 打开UI界面

    Returns:

    """
    try:
        # 显示帮助信息
        if len(sys.argv) > 1 and sys.argv[1] == '-h':
            print("Usage:")
            print("  psaui                 启用project ui")
            print("  psaui -c/-e           启用creeplogic edit (-c: 中文, -e: 英文)")
            print("  psaui -m [-c/-e]      启用mapviewer (-c: 中文, -e: 英文, 默认: 中文)")
            print("  psaui -h              显示帮助信息")
            print("  --------------------------------------------------------------")
            print("  psaui                 run `project ui`")
            print("  psaui -c/-e           run `creeplogic edit` (-c: chinese, -e: english)")
            print("  psaui -m [-c/-e]      run `mapviewer` (-c: chinese, -e: english, default: chinese)")
            print("  psaui -h              Show this help message")

            return
        
        # 检查是否使用mapviewer
        if len(sys.argv) > 1 and sys.argv[1] == '-m':
            # 检查语言参数
            if len(sys.argv) > 2 and sys.argv[2] == '-e':
                from pyscreeps_arena.core import config
                config.language = 'en'
            run_mapviewer()
        # 检查是否使用creeplogic edit
        elif len(sys.argv) > 1 and sys.argv[1] == '-c':
            run_creeplogic_edit()
        elif len(sys.argv) > 1 and sys.argv[1] == '-e':
            from pyscreeps_arena.core import config
            config.language = 'en'
            run_creeplogic_edit()
        # 默认启用project ui
        else:
            run_project_creator()
    except ImportError as e:
        print(f"错误: 无法导入UI模块 - {e}")
        print("请确保已安装PyQt6: pip install PyQt6")
    except Exception as e:
        print(f"错误: 打开UI界面失败 - {e}")

def extract_7z(file_path, output_dir):
    with py7zr.SevenZipFile(file_path, mode='r') as archive:
        archive.extractall(path=output_dir)

if __name__ == '__main__':
    CMD_OpenUI()
