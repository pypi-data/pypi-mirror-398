import os.path

from pyscreeps_arena.core import *
from pyscreeps_arena.localization import *

import re
import shutil
import chardet
import subprocess
import pyperclip
from colorama import Fore
from typing import List, Optional, Tuple, Union

WAIT = Fore.YELLOW + ">>>" + Fore.RESET
GREEN = Fore.GREEN + "{}" + Fore.RESET
python_version_info = sys.version_info
python_version_info = f"{python_version_info.major}.{python_version_info.minor}.{python_version_info.micro}"


def replace_src_prefix(file_list):
    """
    将列表中以'./src.'开头的字符串替换为'./'

    参数:
        file_list: 字符串列表

    返回:
        替换后的新列表
    """
    _ = []
    
    for item in file_list:
        if isinstance(item, str) and item.startswith('./src.'):
            _new = item.replace('./src.', './', 1)
            if _new in file_list:
                continue
        _.append(item)
    
    return _

# def InsertPragmaBefore(content:str) -> str:
#     """
#     在content的开头插入__pragma__('noalias', 'undefined')等内容 |
#         Insert __pragma__('noalias', 'undefined') at the beginning of content
#     :param content: str
#     :return: str
#     """
#     return PYFILE_PRAGMA_INSERTS + "\n" + content
class Compiler_Const:
    PROTO_DEFINES_DIRS = ["builtin", "library"]
    FILE_STRONG_REPLACE = {
        "std": {
            "==": "===",
            "!=": "!==",
        }
    }
    PYFILE_IGNORE_CHECK_FNAMES = ['builtin/const.py', 'builtin/proto.py', 'builtin/utils.py']

    PYFILE_PRAGMA_INSERTS = """
    # __pragma__('noalias', 'undefined')
    # __pragma__('noalias', 'Infinity')
    # __pragma__('noalias', 'clear')
    # __pragma__('noalias', 'get')
    """

    TOTAL_INSERT_AT_HEAD = """
import { createConstructionSite, findClosestByPath, findClosestByRange, findInRange, findPath, getCpuTime, getDirection, getHeapStatistics, getObjectById, getObjects, getObjectsByPrototype, getRange, getTerrainAt, getTicks,} from 'game/utils';
import { ConstructionSite as GameConstructionSite, Creep as GameCreep, GameObject as GameObjectProto, OwnedStructure, Resource as GameResource, Source as GameSource, Structure as GameStructure, StructureContainer as GameStructureContainer, StructureExtension as GameStructureExtension, StructureRampart as GameStructureRampart, StructureRoad as GameStructureRoad, StructureSpawn as GameStructureSpawn, StructureWall as GameStructureWall, StructureTower as GameStructureTower, Flag as GameFlag} from 'game/prototypes';
import { ATTACK, ATTACK_POWER, BODYPART_COST, BODYPART_HITS, BOTTOM, BOTTOM_LEFT, BOTTOM_RIGHT, BUILD_POWER, CARRY, CARRY_CAPACITY, CONSTRUCTION_COST, CONSTRUCTION_COST_ROAD_SWAMP_RATIO, CONSTRUCTION_COST_ROAD_WALL_RATIO, CONTAINER_CAPACITY, CONTAINER_HITS, CREEP_SPAWN_TIME, DISMANTLE_COST, DISMANTLE_POWER, ERR_BUSY, ERR_FULL, ERR_INVALID_ARGS, ERR_INVALID_TARGET, ERR_NAME_EXISTS, ERR_NOT_ENOUGH_ENERGY, ERR_NOT_ENOUGH_EXTENSIONS, ERR_NOT_ENOUGH_RESOURCES, ERR_NOT_FOUND, ERR_NOT_IN_RANGE, ERR_NOT_OWNER, ERR_NO_BODYPART, ERR_NO_PATH, ERR_TIRED, EXTENSION_ENERGY_CAPACITY, EXTENSION_HITS, HARVEST_POWER, HEAL, HEAL_POWER, LEFT, MAX_CONSTRUCTION_SITES, MAX_CREEP_SIZE, MOVE, OBSTACLE_OBJECT_TYPES, OK, RAMPART_HITS, RAMPART_HITS_MAX, RANGED_ATTACK, RANGED_ATTACK_DISTANCE_RATE, RANGED_ATTACK_POWER, RANGED_HEAL_POWER, REPAIR_COST, REPAIR_POWER, RESOURCES_ALL, RESOURCE_DECAY, RESOURCE_ENERGY, RIGHT, ROAD_HITS, ROAD_WEAROUT, SOURCE_ENERGY_REGEN, SPAWN_ENERGY_CAPACITY, SPAWN_HITS, STRUCTURE_PROTOTYPES, TERRAIN_PLAIN, TERRAIN_SWAMP, TERRAIN_WALL, TOP, TOP_LEFT, TOP_RIGHT, TOUGH, TOWER_CAPACITY, TOWER_COOLDOWN, TOWER_ENERGY_COST, TOWER_FALLOFF, TOWER_FALLOFF_RANGE, TOWER_HITS, TOWER_OPTIMAL_RANGE, TOWER_POWER_ATTACK, TOWER_POWER_HEAL, TOWER_POWER_REPAIR, TOWER_RANGE, WALL_HITS, WALL_HITS_MAX, WORK} from 'game/constants';

import {arenaInfo} from "game";
import {Visual} from "game/visual"
import {searchPath, CostMatrix} from "game/path-finder"
    """

    TOTAL_INSERT_BEFORE_MAIN = """
    """

    TOTAL_APPEND_ATEND = """
export var sch = Scheduler();
var monitor = Monitor(1);
know.now = 0;

StageMachineLogicMeta.__types__ = [];  // 清空js首次构造时引入的数据
__init_before_k__();
let knowCost = 0;
let monitorCost = 0;
let stepCost = 0;
let timeLine = 0;
export var loop = function () {
	get.handle();
	know.now = get.now;
	timeLine = get.cpu_us();
    know.handle();
    knowCost = get.cpu_us() - timeLine;

    timeLine = get.cpu_us();
    monitor.handle();
    monitorCost = get.cpu_us() - timeLine;
    for (const creep of know.creeps){
        creep.handle();
    }
    if (know.now === 1) {
	    std.show_welcome();
		init (know);
		
	}
	step (know);
    timeLine = get.cpu_us();
	if (get._SCH_FLAG) sch.handle();
	stepCost = get.cpu_us() - timeLine;
	std.show_usage ();
	print("knowCost:", knowCost, "monitorCost:", monitorCost, "stepCost:", stepCost);
	if (know.draw) know.draw();
};
    """

    TOTAL_SIMPLE_REPLACE_WITH = {
    }

    PYFILE_WORD_WARNING_CHECK = {
        r"\.\s*get\s*\(": LOC_PYFILE_WORD_WARNING_CHECK_GET,
        r"import\s+math\s*": LOC_PYFILE_WORD_WARNING_CHECK_MATH,
        r"\.\s*clear\s*\(": LOC_PYFILE_WORD_WARNING_CHECK_CLEAR,
        r"\[\s*-\s*1\s*\]": LOC_PYFILE_WORD_WARNING_INDEX_MINUS_ONE,
    }

    PYFILE_EXIST_WARNING_CHECK = {
        r"__pragma__\s*\(\s*['\"]noalias['\"]\s*,\s*['\"]undefined['\"]\s*\)": "Strongly suggest to add '__pragma__('noalias', 'undefined')'.",
        r"__pragma__\s*\(\s*['\"]noalias['\"]\s*,\s*['\"]Infinity['\"]\s*\)": "Strongly suggest to add '__pragma__('noalias', 'Infinity')'.",
        r"__pragma__\s*\(\s*['\"]noalias['\"]\s*,\s*['\"]clear['\"]\s*\)": "Strongly suggest to add '__pragma__('noalias', 'clear')'.",
        r"__pragma__\s*\(\s*['\"]noalias['\"]\s*,\s*['\"]get['\"]\s*\)": "Strongly suggest to add '__pragma__('noalias', 'get')'.",
    }

    JS_VM = "org.transcrypt.__runtime__.js"

    BUILTIN_TRANS = ["engine.js", "stage.js"]  # 记录buildin中会被transcrypt的文件
    OTHER_IGNORE_WITH = "./builtin"

    JS_IMPORT_PAT = re.compile(r'from\s+[\'\"]([^\']+)[\'\"]')
    JS_EXPORT_PAT = re.compile(r'export\s+{([^}]+)}')
    PY_IMPORT_PAT = re.compile(r'from\s+(.+)(?=\s+import)\s+import\s+\*')
    INSERT_PAT = re.compile(r'#\s*insert\s+([^\n]*)')  # 因为被判定的string为单line，所以不需要考虑多行的情况

    TRANSCRYPT_ERROR_REPLACE = {
        # 由于transcrypt的问题，导致编译后的js代码中存在一些错误，需要进行替换
        r"new\s+set\s*\(": r"set(",
    }

    ARENA_IMPORTS_GETTER = {
        const.ARENA_GREEN: lambda: f"""
const ARENA_COLOR_TYPE = "GREEN";
class GameAreaEffect{{
    constructor(){{ 
    }}
}};
class GameConstructionBoost{{
    constructor(){{ 
    }}
}};
import {{ Portal as GamePortal}} from 'arena/season_{config.season}/{const.ARENA_GREEN}/{"advanced" if config.level in ["advance", "advanced"] else "basic"}/prototypes';
        """,
# import {Portal} from 'arena/season_1/portal_exploration/basic/prototypes';
        
        const.ARENA_BLUE: lambda: f"""
const ARENA_COLOR_TYPE = "BLUE";
const GameScoreCollector = GameStructureSpawn;
class GameAreaEffect{{
    constructor(){{ 
    }}
}};
class GamePortal{{
    constructor(){{ 
    }}
}};
class GameConstructionBoost{{
    constructor(){{ 
    }}
}};
        """,
        const.ARENA_RED: lambda: f"""
const ARENA_COLOR_TYPE = "RED";
class GamePortal{{
    constructor(){{ 
    }}
}};
import {{ ConstructionBoost as GameConstructionBoost, AreaEffect as GameAreaEffect }} from 'arena/season_{config.season}/{const.ARENA_RED}/{"advanced" if config.level in ["advance", "advanced"] else "basic"}/prototypes';
import {{ EFFECT_CONSTRUCTION_BOOST, EFFECT_SLOWDOWN }} from 'arena/season_{config.season}/{const.ARENA_RED}/{"advanced" if config.level in ["advance", "advanced"] else "basic"}/constants';

        """,
        const.ARENA_GRAY: lambda: f"""
const ARENA_COLOR_TYPE = "GRAY";
class GameAreaEffect{{
    constructor(){{ 
    }}
}};
class GamePortal{{
    constructor(){{ 
    }}
}};
class GameConstructionBoost{{
    constructor(){{ 
    }}
}};
        """,
    }


class Compiler_Utils(Compiler_Const):
    last_output = False  # 一个小标志位，我只想输出一次此类告警信息

    @staticmethod
    def auto_read(fpath: str) -> str:
        """
        读取文件内容，自动应用编码
        :param fpath: str 文件路径
        """
        if not os.path.exists(fpath):
            if not Compiler_Utils.last_output:
                Compiler_Utils.last_output = True
                print()
            core.warn('Compiler_Utils.auto_read', core.lformat(LOC_FILE_NOT_EXISTS, ["", fpath]), end='', head='\n', ln=config.language)
            return ""

        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(fpath, 'r', encoding='gbk') as f:
                    return f.read()
            except UnicodeDecodeError:
                # 如果使用检测到的编码读取失败，尝试使用chardet检测编码
                try:
                    with open(fpath, 'rb') as f:  # 以二进制模式打开文件
                        raw_data = f.read()  # 读取文件的原始数据
                        result = chardet.detect(raw_data)  # 使用chardet检测编码
                        encoding = result['encoding']  # 获取检测到的编码
                    with open(fpath, 'r', encoding=encoding) as f:  # 使用检测到的编码打开文件
                        return f.read()
                except UnicodeDecodeError as e:
                    core.error('Compiler_Utils.auto_read', core.lformat(LOC_FILE_READ_FAILED, [fpath, "UnicodeError", e]), end='', head='\n', ln=config.language)
                    quit(-1)

    def copy_to(self) -> list:
        """
        复制src到build目录 | copy all files in src to build
        * 注意到src下的文件应当全部为py文件 |  all files in src should be py files
        """
        # copy to build dir
        # print(Fore.YELLOW + '>>> ' + Fore.RESET + ' copying to build dir: %s ...' % self.build_dir, end='')
        # LOC_COPYING_TO_BUILD_DIR

        core.lprint(WAIT, core.lformat(LOC_COPYING_TO_BUILD_DIR, [self.build_dir]), end="", ln=config.language)

        if os.path.exists(self.build_dir):
            shutil.rmtree(self.build_dir)
        shutil.copytree(self.src_dir, self.build_dir)
        shutil.copytree(self.src_dir, os.path.join(self.build_dir, "src"))
        srcs = []  # src下所有python文件的路径 | paths of all python files under src
        for root, dirs, files in os.walk(self.build_dir):
            for file in files:
                if file.endswith('.py'):
                    srcs.append(os.path.join(root, file))
        # add libs
        for lib in self.PROTO_DEFINES_DIRS:
            shutil.copytree(lib, os.path.join(self.build_dir, lib))

        # overwrite last to [Done]
        # print(Fore.GREEN + '\r[1/6][Done]' + Fore.RESET + ' copying to build dir: %s' % self.build_dir)

        core.lprint(GREEN.format('[1/6]'), LOC_DONE, " ", core.lformat(LOC_COPYING_TO_BUILD_DIR_FINISH, [self.build_dir]), sep="", head="\r", ln=config.language)
        return srcs

    @staticmethod
    def potential_check(fpath: str, fname: str) -> bool:
        """
        检查某个py文件内是否有潜在问题 | check if there are potential problems in a py file

        如果有的话，输出[Warn][{file_name}/{line_io}]{detail} | if there are, output [Warn][{file_name}/{line_io}]{detail}

        Returns:
            bool: 是否有警告
        """
        # 文件路径检查
        # if fpath.endswith('__init__.py') and fpath.find("builtin") == -1:
        #     core.error("potential_check", LOC_NOT_SUPPORT_PYFILE_INIT, ln=config.language, ecode=-1, head='\n')
        if fname in Compiler.PYFILE_IGNORE_CHECK_FNAMES:
            return False

        # # 文件内容检查
        content = Compiler.auto_read(fpath)
        warn_flag = False
        # # 内容关键字检查
        for pat, detail in Compiler.PYFILE_WORD_WARNING_CHECK.items():
            for i, line in enumerate(content.split('\n')):
                m = re.search(pat, line)
                if m:
                    # 检查m前面同一行内是否有#，如果有则忽略
                    comment = re.search(r'#', line[:m.start()])

                    # 检查m后面同一行内是否有#\s*ignore;，如果有则忽略
                    ignore = re.search(r'#\s*>\s*ignore', line[m.end():])

                    if not comment and not ignore:
                        warn_flag = True
                        core.warn('Compiler.potential_check', f'[{os.path.basename(os.path.dirname(fpath))}/{fname} line:{i + 1}]:', detail, end='', head='\n', ln=config.language)
        return warn_flag

    @staticmethod
    def preprocess_if_block(source_code: str, variables: dict[str, object]) -> str:
        """
        预处理if块，将 # > if, # > elif, # > else, # > endif 替换为实际的程序内容 |
        pre-process if blocks by replacing # > if, # > elif, # > else, # > endif with actual code.
        """
        lines = source_code.split('\n')  # 按行分割源代码 | split source code into lines
        stack = []  # 初始化一个栈，用于跟踪if条件 | initialize a stack to track if conditions
        result = []  # 初始化一个列表，用于存储处理后的代码行 | initialize a list to store processed code lines

        for i, line in enumerate(lines):  # 遍历源代码的每一行 | iterate over each line of source code
            striped = line.strip()  # 去掉行首尾的空格和换行符 | strip leading and trailing whitespace
            # 使用正则表达式匹配不同的条件语句 | use regex to match different conditional statements
            if_match = re.match(r'#\s*>\s*if\s+([^:.]*)$', striped)  # 匹配 '# > if' 语句 | match '# > if' statement
            elif_match = re.match(r'#\s*>\s*elif\s+([^:.]*)$', striped)  # 匹配 '# > elif' 语句 | match '# > elif' statement
            else_match = re.match(r'#\s*>\s*else$', striped)  # 匹配 '# > else' 语句 | match '# > else' statement
            endif_match = re.match(r'#\s*>\s*endif$', striped)  # 匹配 '# > endif' 语句 | match '# > endif' statement

            if if_match:  # 如果当前行是 '# > if' 语句 | if it's a '# > if' statement
                condition = if_match.group(1)  # 提取条件表达式 | extract the condition expression
                stack.append(eval(condition, variables))  # 评估条件表达式并将其结果压入栈中 | evaluate condition and push result onto stack
            elif elif_match and stack:  # 如果当前行是 '# > elif' 语句，并且栈不为空 | if it's a '# > elif' and stack isn't empty
                condition = elif_match.group(1)  # 提取条件表达式 | extract the condition expression
                stack[-1] = eval(condition, variables)  # 评估条件表达式并更新栈顶 | evaluate condition and update the top of the stack
            elif else_match and stack:  # 如果当前行是 '# > else' 语句，并且栈不为空 | if it's a '# > else' and stack isn't empty
                stack[-1] = not stack[-1]  # 将栈顶元素取反 | negate the top of the stack
            elif endif_match:  # 如果当前行是 '# > endif' 语句 | if it's a '# > endif' statement
                stack.pop()  # 弹出栈顶元素 | pop the top of the stack
            else:  # 如果当前行不是条件语句 | if it's not a conditional statement
                if not stack or all(stack):  # 如果栈为空，或者栈中所有元素均为真 | if stack is empty or all elements are True
                    result.append(line)  # 将当前行加入结果列表中 | add the current line to the result

        return '\n'.join(result)  # 将处理后的所有代码行连接成一个字符串，并返回最终结果 | join all processed lines into a string and return

    def expand_folder_imports(self, fpath: str, project_path: str = None):
        """
        扩展文件夹导入语句：将 `from folder import *` 替换为 `from folder.module import *`
        仅在文件夹没有 __init__.py 时执行此操作

        :param fpath: 要处理的文件路径
        :param project_path: 项目根路径，用于解析相对导入，默认为 None（使用文件所在目录）
        """
        if not os.path.exists(fpath):
            return

        content = self.auto_read(fpath)
        lines = content.split('\n')
        new_lines = []
        changed = False

        for line in lines:
            m = self.PY_IMPORT_PAT.match(line)
            if not m:
                new_lines.append(line)
                continue

            original_target = m.group(1)
            target = original_target
            target_path = project_path or os.path.dirname(fpath)

            # 处理相对路径（向前定位）
            if target.startswith('.'):
                target_path = os.path.dirname(fpath)
                count = 0
                for c in target:
                    if c == '.':
                        count += 1
                    else:
                        break

                # 向上移动目录
                if count > 1:
                    for _ in range(count - 1):
                        target_path = os.path.dirname(target_path)

                # 移除开头的点
                target = target[count:]

            # 如果 target 为空，跳过
            if not target:
                new_lines.append(line)
                continue

            # 向后定位，构建完整路径
            temp_target = target
            while (_idx := temp_target.find('.')) != -1:
                part = temp_target[:_idx]
                target_path = os.path.join(target_path, part)
                temp_target = temp_target[_idx + 1:]

            # 最终的文件夹路径
            final_dir_path = os.path.join(target_path, temp_target) if temp_target else target_path

            # 检查是否是文件夹且没有 __init__.py
            if os.path.isdir(final_dir_path):
                init_path = os.path.join(final_dir_path, '__init__.py')
                if not os.path.exists(init_path):
                    # 找到所有 .py 文件（排除 __init__.py）| 如果包含子目录，产生一个警告
                    # try:
                    #     py_files = [f for f in os.listdir(final_dir_path) if f.endswith('.py') and f != '__init__.py']
                    # except (FileNotFoundError, PermissionError):
                    py_files = []
                    for item in os.listdir(final_dir_path):
                        _path = os.path.join(final_dir_path, item)
                        if os.path.isfile(_path) and item.endswith('.py') and item != '__init__.py':
                            py_files.append(item)
                        elif os.path.isdir(_path):
                            rel = os.path.relpath(final_dir_path, project_path)
                            core.warn(f'Compiler.expand_folder_imports', core.lformat(LOC_DIR_UNDER_NONINIT_DIR, [item, rel]), end='', head='\n', ln=config.language )
                            

                    # 为每个 .py 文件生成导入语句
                    if py_files:
                        for py_file in py_files:
                            module_name = py_file[:-3]
                            new_import = f"from {original_target}.{module_name} import *"
                            new_lines.append(new_import)
                        changed = True
                        continue

            # 保留原行
            new_lines.append(line)

        # 如果文件有修改，写回
        if changed:
            new_content = '\n'.join(new_lines)
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_content)


    def find_chain_import(self, fpath: str, search_dirs: list[str], project_path: str = None, records: dict[str, None] = None) -> list[str]:
        r"""
        查找文件中的所有import语句，并返回所有import的文件路径 | find all import statements in a file and return the paths of all imported files
        PY_IMPORT_PAT: re.compile(r'\s+from\s+(.+)(?=\s+import)\s+import\s+\*')
        :param fpath: str 目标文件路径 | target file path
        :param search_dirs: list[str] 搜索目录 | search directories
        :param project_path=None: str python项目中的概念，指根文件所在的目录。如果不指定，默认使用第一次调用时给定的fpath，并且稍后的递归会全部使用此路径 |
            concept in python-project, refers to the directory where the root file is located. If not specified, the fpath given at the first call is used by default, and all subsequent recursions will use this path
        :param records=None: dict[str, None] 记录已经查找过的文件路径，避免重复查找 | record the file paths that have been searched to avoid duplicate searches
        """
        if records is None:
            records = {}
        if not os.path.exists(fpath):
            core.error('Compiler.find_chain_import', core.lformat(LOC_FILE_NOT_EXISTS, ["py", fpath]), head='\n', ln=config.language)
        imps = []
        content = self.auto_read(fpath)
        project_path = project_path or os.path.dirname(fpath)
        for no, line in enumerate(content.split('\n')):
            m = self.PY_IMPORT_PAT.match(line)
            if m:
                target = m.group(1)
                target_path = project_path

                ## 向前定位 | locate forward
                if target.startswith('.'):
                    target_path = os.path.dirname(fpath)  # 因为使用了相对路径，所以需要先定位到当前文件所在的目录 |
                    #                                       because relative path is used, need to locate the directory where the current file is located first
                    count = 0
                    for c in target:
                        if c == '.':
                            count += 1
                        else:
                            break
                    if count > 1:
                        for _ in range(count - 1):
                            target_path = os.path.dirname(target_path)

                ## 向后定位 | locate backward
                while (_idx := target.find('.')) != -1:
                    first_name = target[:_idx]
                    target_path = os.path.join(target_path, first_name)
                    target = target[_idx + 1:]

                ## 检查是否存在 | check if exists
                this_path = os.path.join(target_path, target)
                if os.path.isdir(this_path):
                    this_path = os.path.join(this_path, '__init__.py')
                else:
                    this_path += '.py'

                if not os.path.exists(this_path):
                    core.error('Compiler.find_chain_import', core.lformat(LOC_CHAIN_FILE_NOT_EXISTS, [fpath, no + 1, this_path]), head='\n', ln=config.language)
                if this_path not in records:
                    records[this_path] = None
                    tmp = self.find_chain_import(this_path, search_dirs, project_path, records) + [this_path]
                    imps.extend(tmp)

        return imps

    def find_chain_import2(self, fpath: str, search_dirs: list[str], project_path: str = None, records: dict[str, None] = None) -> list[str]:
        r"""
        查找文件中的所有import语句，并返回所有import的文件路径 | find all import statements in a file and return the paths of all imported files
        PY_IMPORT_PAT: re.compile(r'\s+from\s+(.+)(?=\s+import)\s+import\s+\*')
        :param fpath: str 目标文件路径 | target file path
        :param search_dirs: list[str] 搜索目录 | search directories
        :param project_path=None: str python项目中的概念，指根文件所在的目录。如果不指定，默认使用第一次调用时给定的fpath，并且稍后的递归会全部使用此路径 |
            concept in python-project, refers to the directory where the root file is located. If not specified, the fpath given at the first call is used by default, and all subsequent recursions will use this path
        :param records=None: dict[str, None] 记录已经查找过的文件路径，避免重复查找 | record the file paths that have been searched to avoid duplicate searches
        """
        if records is None:
            records = {}
        if not os.path.exists(fpath):
            core.error('Compiler.find_chain_import', core.lformat(LOC_FILE_NOT_EXISTS, [fpath]), head='\n', ln=config.language)
        imps = []
        content = self.auto_read(fpath)
        project_path = project_path or os.path.dirname(fpath)

        # 添加根目录和 src 目录到 search_dirs
        root_dir = os.path.dirname(project_path)  # 根目录
        src_dir = os.path.join(root_dir, 'src')  # src 目录
        if root_dir not in search_dirs:
            search_dirs = [root_dir] + search_dirs
        if src_dir not in search_dirs:
            search_dirs = [src_dir] + search_dirs

        for no, line in enumerate(content.split('\n')):
            m = self.PY_IMPORT_PAT.match(line)
            if m:
                target = m.group(1)
                target_path = project_path

                ## 向前定位 | locate forward
                if target.startswith('.'):
                    target_path = os.path.dirname(fpath)  # 因为使用了相对路径，所以需要先定位到当前文件所在的目录 |
                    # because relative path is used, need to locate the directory where the current file is located first
                    count = 0
                    for c in target:
                        if c == '.':
                            count += 1
                        else:
                            break
                    if count > 1:
                        for _ in range(count - 1):
                            target_path = os.path.dirname(target_path)

                ## 向后定位 | locate backward
                while (_idx := target.find('.')) != -1:
                    first_name = target[:_idx]
                    target_path = os.path.join(target_path, first_name)
                    target = target[_idx + 1:]

                ## 检查是否存在 | check if exists
                this_path = os.path.join(target_path, target)
                if os.path.isdir(this_path):
                    this_path = os.path.join(this_path, '__init__.py')
                else:
                    this_path += '.py'

                if not os.path.exists(this_path):
                    # 如果当前路径不存在，尝试在 search_dirs 中查找
                    for search_dir in search_dirs:
                        search_path = os.path.join(search_dir, target.replace('.', os.sep)) + ('.py' if not os.path.isdir(this_path) else os.sep + '__init__.py')
                        if os.path.exists(search_path):
                            this_path = search_path
                            break
                    else:
                        core.error('Compiler.find_chain_import', core.lformat(LOC_CHAIN_FILE_NOT_EXISTS, [fpath, no + 1, this_path]), head='\n', ln=config.language)
                if this_path not in records:
                    records[this_path] = None
                    tmp = self.find_chain_import(this_path, search_dirs, project_path, records) + [this_path]
                    imps.extend(tmp)

        return imps

    @staticmethod
    def relist_pyimports_to_jsimports(base_dir:str, pyimps:list[str]) -> list[str]:
        """
        将python的imports路径列表转换为js的imports路径列表 | convert a list of python imports paths to a list of js imports paths
        """
        jsimps = []
        for pyimp in pyimps:
            rel_path_nodes:list[str] = os.path.relpath(pyimp, base_dir).replace('\\', '/').split('/')
            if rel_path_nodes[-1] == '__init__.py':
                rel_path_nodes.pop()
            else:
                rel_path_nodes[-1] = rel_path_nodes[-1][:-3]
            jsimps.append('./' + '.'.join(rel_path_nodes) + '.js')
        return jsimps

    # ---------- 自定义函数 ---------- #

    @staticmethod
    def stage_recursive_replace(content: str) -> str:
        """
        移除 '@recursive' 装饰器行，并在文末添加对应的 _recursiveLogin 调用。

        对于类方法: _recursiveLogin("ClassName", "method_name")
        对于普通函数: _recursiveLogin("", "function_name")
        """
        calls_to_add = []
        deletions = []

        # 1. 收集所有类定义的位置和缩进
        class_pattern = re.compile(r'^(\s*)class\s+(\w+)', re.MULTILINE)
        classes = [(m.start(), len(m.group(1)), m.group(2))
                   for m in class_pattern.finditer(content)]

        # 2. 查找所有 @recursive 装饰器
        decorator_pattern = re.compile(r'^\s*@\s*recursive\s*$\n?', re.MULTILINE)

        for dec_match in decorator_pattern.finditer(content):
            dec_end = dec_match.end()

            # 查找接下来的函数定义（跳过可能的空行）
            after_decorator = content[dec_end:]
            func_match = re.search(r'^(\s*)def\s+([^\s\(]+)', after_decorator, re.MULTILINE)

            if not func_match:
                continue

            func_indent_len = len(func_match.group(1))
            func_name = func_match.group(2)

            # 3. 确定类名：查找装饰器前最近的、缩进小于函数缩进的类
            class_name = ""
            for cls_pos, cls_indent_len, cls_name in reversed(classes):
                if cls_pos < dec_match.start() and func_indent_len > cls_indent_len:
                    class_name = cls_name
                    break

            # 4. 记录删除位置和调用信息
            deletions.append((dec_match.start(), dec_end))
            calls_to_add.append(f'_recursiveLogin("{class_name}", "{func_name}")')

        # 5. 应用删除（倒序避免位置偏移）
        if not deletions:
            return content

        result = content
        for start, end in sorted(deletions, key=lambda x: x[0], reverse=True):
            result = result[:start] + result[end:]

        # 6. 在文末添加调用
        if calls_to_add:
            result = '\n'.join(calls_to_add) + '\n' + result

        return result
    
    @staticmethod
    def process_mate_code(code):
        # 用于存储匹配到的信息
        mate_assignments = []
        # 匹配变量赋值为Mate()的正则表达式，允许变量定义中包含或不包含类型注解
        assign_pattern = re.compile(r'(\w+)\s*(?:\:\s*\w*)?\s*=\s*Mate\s*\(')
        # 匹配类定义的正则表达式
        class_pattern = re.compile(r'class\s+(\w+)')
        # 用于记录当前所在的类名
        current_class = None
        # 将代码按行分割
        lines = code.split('\n')
        # 遍历每一行
        for i, line in enumerate(lines):
            # 匹配类定义
            class_match = class_pattern.match(line)
            if class_match:
                current_class = class_match.group(1)
            # 匹配变量赋值为Mate()
            assign_match = assign_pattern.search(line)
            if assign_match:
                # 检查group(1)前面同一行内是否有#，如果有则忽略
                comment = re.search(r'#', line[:assign_match.start()])
                if comment:
                    continue
                variable_name = assign_match.group(1)
                # 存储匹配到的信息
                mate_assignments += [(variable_name, current_class)]

        output_strings = []
        for variable_name, class_name in mate_assignments:
            output_string = f"# > insert Object.defineProperty ({class_name}, '{variable_name}', property.call ({class_name}, {class_name}.{variable_name}._MateGet_, {class_name}.{variable_name}._MateSet_));"
            output_strings.append(output_string)
        
        return code + '\n'.join(output_strings)


    @staticmethod
    def remove_long_docstring(content:str) -> str:
        """
        移除长注释 | remove long docstring
        """
        code = re.sub(r'"""[^"]*"""', '', content)
        code = re.sub(r"'''[^']*'''", '', code)
        return code

    @classmethod
    def _collect_logical_line(cls, lines: List[str], start_idx: int) -> Tuple[str, int]:
        """收集从start_idx开始的逻辑行（处理多行语句，直到遇到:结尾）"""
        if start_idx >= len(lines):
            return "", start_idx

        parts = [lines[start_idx].rstrip()]
        i = start_idx

        # 持续收集直到找到以:结尾的行
        while i < len(lines) and not parts[-1].endswith(':'):
            i += 1
            if i < len(lines):
                parts.append(lines[i].rstrip())

        return " ".join(parts), i

    @classmethod
    def _convert_block(cls, lines: List[str], match_counter: Optional[List[int]] = None) -> List[str]:
        if match_counter is None:
            match_counter = [0]

        result = []
        i = 0

        while i < len(lines):
            line = lines[i].rstrip()

            # 检测match语句（支持多行）
            if re.match(r'^\s*match\s+', line):
                full_match, end_idx = cls._collect_logical_line(lines, i)

                match_stmt = re.match(r'^(\s*)match\s+(.+?)\s*:', full_match)
                if not match_stmt:
                    result.append(line)
                    i += 1
                    continue

                indent = match_stmt.group(1)
                subject = match_stmt.group(2).strip()
                i = end_idx + 1  # 跳过match语句

                # 生成临时变量
                var_name = f"__MATCH_{match_counter[0]}__"
                match_counter[0] += 1
                result.append(f"{indent}{var_name} = {subject}")

                # 解析case语句
                cases: List[Tuple[str, List[str]]] = []
                case_indent = None

                while i < len(lines):
                    case_line = lines[i].rstrip()

                    # 缩进检查 - case必须比match缩进更多
                    if not case_line.startswith(indent + '    ') and case_line.strip():
                        if re.match(r'^\s*case\s+', case_line):
                            raise MatchCaseError(f"第 {i + 1} 行: case 缩进必须大于 match")
                        break

                    # 检测case语句（不再使用_collect_logical_line，而是单独处理每一行）
                    case_match = re.match(r'^(\s+)case\s+(.+?)\s*:', case_line)
                    if case_match:
                        curr_case_indent = case_match.group(1)
                        case_val = case_match.group(2).strip()

                        # 验证缩进 - 允许不同的case缩进（用于嵌套）
                        if len(curr_case_indent) <= len(indent):
                            raise MatchCaseError(f"第 {i + 1} 行: case 缩进必须大于 match")

                        # 不再强制要求所有case缩进一致，允许嵌套情况下的不同缩进
                        if case_indent is None:
                            case_indent = curr_case_indent

                        # 提取内联代码（如果有）
                        inline_code = ""
                        if ':' in case_line:
                            after_colon = case_line.split(':', 1)[1].strip()
                            if after_colon:
                                inline_code = after_colon

                        i += 1

                        # 收集case块
                        block_lines = []
                        if inline_code:
                            block_lines.append(f"{curr_case_indent}    {inline_code}")

                        while i < len(lines):
                            block_line = lines[i].rstrip()
                            if not block_line.strip():
                                block_lines.append(block_line)
                                i += 1
                                continue

                            # 检查是否是下一个case或者缩进回到当前match级别
                            if re.match(r'^\s*case\s+', block_line):
                                # 检查这个case是否属于当前match还是父级match
                                next_case_indent = re.match(r'^\s*', block_line).group(0)
                                if len(next_case_indent) <= len(indent):
                                    # 属于父级match，退出当前match的处理
                                    break
                                # 仍然属于当前match，继续收集
                                if block_line.startswith(curr_case_indent + '    '):
                                    block_lines.append(block_line)
                                    i += 1
                                    continue
                                else:
                                    break

                            if block_line.startswith(indent) and not block_line.startswith(curr_case_indent):
                                break

                            if block_line.startswith(curr_case_indent + '    '):
                                block_lines.append(block_line)
                                i += 1
                                continue

                            break

                        cases.append((case_val, block_lines))
                    else:
                        break

                # 验证case
                seen = set()
                for idx, (val, _) in enumerate(cases):
                    if val == '_':
                        if idx != len(cases) - 1:
                            raise MatchCaseError(f"第 {i + 1} 行附近: case _ 必须在最后")
                    else:
                        if val in seen:
                            raise MatchCaseError(f"第 {i + 1} 行附近: 重复的 case 值 '{val}'")
                        seen.add(val)

                # 生成if/elif/else
                for idx, (case_val, blk_lines) in enumerate(cases):
                    keyword = "else" if case_val == '_' else ("if" if idx == 0 else "elif")
                    if keyword == "else":
                        result.append(f"{indent}else:")
                    else:
                        result.append(f"{indent}{keyword} {var_name} == {case_val}:")

                    if blk_lines:
                        # 递归处理block_lines，以支持嵌套match
                        converted_blk_lines = cls._convert_block(blk_lines, match_counter)
                        result.extend(converted_blk_lines)

                continue

            result.append(line)
            i += 1

        return result

    @classmethod
    def convert_match_to_if(cls, code: str) -> str:
        lines = code.split('\n')
        converted_lines = cls._convert_block(lines, [0])
        return '\n'.join(converted_lines)


class CompilerBase(Compiler_Utils):

    def __init__(self):
        src_dir = "src"
        build_dir = "build"
        # check
        if not os.path.exists(src_dir):
            core.error('Compiler.__init__', core.lformat(LOC_FILE_NOT_EXISTS, ['src', src_dir]), head='\n', ln=config.language)

        src_dir = os.path.abspath(src_dir)
        build_dir = os.path.abspath(build_dir)
        base_dir = os.path.dirname(src_dir)
        lib_dir = os.path.join(base_dir, 'library')
        built_dir = os.path.join(base_dir, 'builtin')

        # 在builtin文件下搜索需要跳过的文件，计入到PYFILE_IGNORE_CHECK_FNAMES中
        for fname in os.listdir(os.path.join(base_dir, "builtin")):
            if fname.endswith('.py') and fname not in ['const.py', 'proto.py', 'utils.py']:
                self.PYFILE_IGNORE_CHECK_FNAMES.append(f'builtin/{fname}')

        self.src_dir = os.path.abspath(src_dir)
        self.lib_dir = os.path.abspath(lib_dir)
        self.build_dir = os.path.abspath(build_dir)
        self.built_dir = os.path.abspath(built_dir)
        self.target_dir = os.path.join(self.build_dir, '__target__')
        self.build_name = os.path.basename(self.build_dir)

    @property
    def builtin_py(self) -> str:
        """
        返回builtin目录下的__init__.py的路径 | return the path of __init__.py in builtin
        """
        return os.path.join(self.built_dir, '__init__.py')

    @property
    def target_py(self) -> str:
        """
        返回build下的main.py的路径 | return the path of main.py in build
        """
        return os.path.join(self.build_dir, 'main.py')

    @property
    def target_js(self):
        """
        返回build下的main.js的路径 | return the path of main.js in build
        """
        return os.path.join(self.target_dir, 'main.js')


class Compiler(CompilerBase):
    def pre_compile(self):
        """
        预编译 | Precompile
        """
        src_paths: list[str] = self.copy_to()  # 复制src到build目录 | copy all files in src to build
        # 获取src目录下的所有.py文件的路径 | get the paths of all .py files under src

        core.lprint(WAIT, LOC_PREPROCESSING, end="", ln=config.language)
        py_fpath, py_names, warn_flag = [], [], False
        for root, dirs, files in os.walk(self.build_dir):
            for file in files:
                if file.endswith('.py'):
                    fpath: str = str(os.path.join(root, file))

                    # 将PYFILE_PRAGMA_INSERTS.replace("\t", "").replace("    ", "")插入到文件开头
                    content = self.auto_read(fpath)
                    content = self.PYFILE_PRAGMA_INSERTS.replace("\t", "").replace("    ", "") + content
                    # content = self.remove_long_docstring(content)  # 移除长注释 | remove long docstring

                    with open(fpath, 'w', encoding='utf-8') as f:  # 注意，这里修改的是build目录下的文件，不是源文件 | Note that the file under the build directory is modified here, not the source file
                        f.write(content)

                    # 得到src目录后面的内容
                    rel_name = os.path.relpath(fpath, self.build_dir).replace('\\', '/')
                    py_names.append(rel_name.replace('/', '.'))
                    py_fpath.append(fpath)
                    warn_flag |= self.potential_check(fpath, rel_name)
        if warn_flag:
            print()  # 换行

        _usubs_ = []  # update_subclass
        _pre_import_, _pre_imp_detail_ = [], {}  # > import
        _imports = []  # chain import
        _pre_sort_ = {}  # > sort
        _pre_define_ = {}  # > define
        _js_replace_, _insert_id_ = {}, 0  # > insert

        # -------------------------------- ONLY IMPORT * -------------------------------- #
        # 只允许from xxx import *的情况 | only allow from xxx import *
        for i, fpath in enumerate(py_fpath):
            content = self.auto_read(fpath)
            for line in content.split('\n'):
                # 1. 检查 import xxx的情况 | check import xxx
                m = re.match(r'\s*import\s+([^\s]+)', line)
                if m:
                    core.error('Compiler.pre_compile', core.lformat(LOC_IMPORT_STAR_ERROR, [m.group(1), m.group(1)]), head='\n', ln=config.language)
                # 2. 检查 from xxx import yyys的情况(yyys不能是*) | check from xxx import yyys(yyys can't be *)
                m = re.match(r'\n\s*from\s+([^\s]+)\s+import\s+([^\s]+)', line)
                if m and (not m.group(2) or m.group(2)[0] != '*'):
                    core.error('Compiler.pre_compile', core.lformat(LOC_IMPORT_STAR2_ERROR, [m.group(1), m.group(2), m.group(1)]), head='\n', ln=config.language)

            self.expand_folder_imports(fpath, self.build_dir)

        # -------------------------------- EXPAND IMPORT * -------------------------------- #
        _imports = self.find_chain_import(self.target_py, [os.path.dirname(self.src_dir), self.src_dir])
        _js_imports = self.relist_pyimports_to_jsimports(self.build_dir, _imports)

        # ----------------------------------- REMOVE ----------------------------------- #
        # 移除所有# > remove所在行的内容
        # | remove all # > remove in .py files
        for fpath in py_fpath:
            content = self.auto_read(fpath)
            new_content = ""
            for line in content.split('\n'):
                if not re.search(r'#\s*>\s*remove', line):
                    new_content += line + '\n'

            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_content)

        # ------------------------------------ SORT ------------------------------------ #
        # 获取所有.py文件中的所有# > sort的内容，并记录下来(不存在则默认为65535)
        # | get all # > sort in .py files, and record them (default 65535 if not exists)
        for i, fpath in enumerate(py_fpath):
            fname = py_names[i]
            if fname.endswith('__init__.py'):
                fname = fname[:-12] + '.js'
            else:
                fname = fname[:-3] + '.js'
            content = self.auto_read(fpath)
            m = re.search(r'#\s*>\s*sort\s+(\d+)', content)
            if m:
                try:
                    sort_num = int(m.group(1))
                except ValueError:
                    core.warn('Compiler.pre_compile', core.lformat(LOC_SORT_NUMBER_ERROR, [m.group(1)]), end='', head='\n', ln=config.language)
                    sort_num = 65535
                _pre_sort_[fname] = sort_num
            else:
                _pre_sort_[fname] = 65535

        # ------------------------------------ 自定义:mate & match ------------------------------------ #
        for fpath in py_fpath:
            content = self.auto_read(fpath)
            content = self.process_mate_code(content)  # 调用process_mate_code
            content = self.convert_match_to_if(content)  # 调用convert_match_to_if
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(content)

        # ------------------------------------ DEFINE ------------------------------------ #
        # 扫描所有# > define的内容，然后在.py中移除这些行，并记录下来
        # | get all # > define in .py files, and record them
        for fpath in py_fpath:
            content = self.auto_read(fpath)
            new_content = ""
            for line in content.split('\n'):
                # re.compile(r'#\s*define\s+([^\s]+)\s+([^\n]*)')
                m = re.search(r'#\s*>\s*define\s+([^\s]+)\s+([^\n]*)', line)
                if m:
                    _pre_define_[m.group(1)] = m.group(2)
                    new_content += '\n'
                else:
                    new_content += line + '\n'

            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_content)

        # 按照keys的顺序，先用前面的key对应的内容去依次替换后面的key对应的value中
        # | replace the value of the key with the content of the previous key in order
        _def_keys = list(_pre_define_.keys())
        _keys_len = len(_def_keys)
        for i in range(_keys_len - 1):
            for j in range(i + 1, _keys_len):
                _pre_define_[_def_keys[j]] = _pre_define_[_def_keys[j]].replace(_def_keys[i], _pre_define_[_def_keys[i]])

        # ------------------------------------ DEFINE:REPLACE ------------------------------------ #
        # 将刚才记录的define替换到.py中(注意优先替换更长的串)(因此先排序)
        # | replace the defined content to .py files (replace the longer string first)
        _def_keys.sort(key=lambda x: len(x), reverse=True)
        for fpath in py_fpath:
            content = self.auto_read(fpath)

            for key in _def_keys:
                content = re.sub(r'[^_A-Za-z0-9]' + key, self._kfc_wrapper(_pre_define_[key]), content)

            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(content)

        # ------------------------------------ IF BLOCK ------------------------------------ #
        # 预处理if块，将 # > if, # > elif, # > else, # > endif 替换为实际的程序内容
        # | preprocess if block, replace # > if, # > elif, # > else, # > endif to actual code
        for fpath in py_fpath:
            content = self.auto_read(fpath)

            content = self.preprocess_if_block(content, _pre_define_)

            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(content)

        # ------------------------------------ INSERT ------------------------------------ #
        # 扫描所有# > insert的内容，然后在.py中将整行替换为# __pragma__("js", __JS_INSERT_{id})
        # | get all # > insert in .py files, and replace the whole line with # __pragma__("js", __JS_INSERT_{id})
        for fpath in py_fpath:
            content = self.auto_read(fpath)
            new_content = ""
            for line in content.split('\n'):
                # re.compile(r'#\s*insert\s*([^\n]*)')
                # '# > insert if(obj && obj.body) for(var p of obj.body) if (p.type == MOVE) return true;'
                m = re.search(r'#\s*>\s*insert\s+([^\n]*)', line)
                if m:
                    _sign_index_ = line.find('#')  # 必然存在
                    _js_key_ = f"__JS_INSERT_{_insert_id_:08d}"
                    _js_replace_[_js_key_] = m.group(1)

                    new_content += line[:_sign_index_] + f'# __pragma__("js", "{_js_key_}")\n'
                    _insert_id_ += 1
                else:
                    new_content += line + '\n'

            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_content)

        # ------------------------------------ 自定义:调用stage_recursive_replace ------------------------------------ #
        for fpath in py_fpath:
            content = self.auto_read(fpath)
            content = self.stage_recursive_replace(content)  # 调用stage_recursive_replace
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(content)


        core.lprint(GREEN.format('[2/6]'), LOC_DONE, " ", LOC_PREPROCESSING_FINISH, sep="", head="\r", ln=config.language)
        return _imports, _js_imports, _pre_sort_, _pre_define_, _js_replace_

    def transcrypt_cmd(self):
        # 执行cmd命令: python -m transcrypt -b -m -n -s -e 6 target | execute cmd: python -m transcrypt -b -m -n -s -e 6 target
        # 并获取cmd得到的输出 | and get the output of the cmd
        cmd = 'python -m transcrypt -b -m -n -s -e 6 %s' % self.target_py
        core.lprint(WAIT, core.lformat(LOC_TRANSCRYPTING, [cmd]), end="", ln=config.language)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if 'Error while compiling' in stdout.decode():
            print('\r' + stdout.decode())
            core.error('Compiler.transcrypt_cmd', LOC_TRANSCRYPTING_ERROR, indent=1, head='\n', ln=config.language)
        core.lprint(GREEN.format('[3/6]'), LOC_DONE, " ", LOC_TRANSCRYPTING_FINISH, sep="", head="\r", ln=config.language)

    @staticmethod
    def _keep_lbracket(matched) -> str:
        """
        如果第一个字符是{, 则返回'{'，否则返回'' | if the first char is {, return '{', else return ''
        :param matched:
        :return:
        """
        return '{' if matched.group(0)[0] == '{' else ''

    @staticmethod
    def _keep_first_char(matched: re.Match) -> str:
        """
        保留第一个字符 | keep the first char
        :param matched: re.match object | re.match对象
        :return:
        """
        return matched.group(0)[0]

    @staticmethod
    def _kfc_wrapper(replace: str) -> callable:
        """
        获取一个保留第一个字符的函数 | get a function to keep the first char
        :param replace: str
        :return: function
        """

        def _kfc(matched) -> str:
            return matched.group(0)[0] + replace

        return _kfc

    def analyze_rebuild_main_js(self, defs: dict[str, object], modules=None) -> tuple[str, list[str]]:
        """
        分析main.js中导入的模块名称和先后顺序, 并重新生成main.js | analyze the module names and order imported in main.js, and rebuild main.js
        * 主要移除非SYSTEM_MODULES_IGNORE中的模块导入语句 | mainly remove the module import statements that are not in SYSTEM_MODULES_IGNORE
        :param defs: dict{define: value} 定义的变量 | defined variables
        :return: imports : str, modules (names: str)
                imports是一段用于放在js主体开头的import语句 | imports is a string of import statements to be placed at the beginning of the js body
                modules是一个list，包含了所有的模块名称 | modules is a list containing all module names
                                    其中的内容可能是这样的: ['./game.utils.js', './game.proto.js', './game.const.js', ...]
        """

        # create undefined
        imports = ""

        # if defs.get('USE_TUTORIAL_FLAG', '0') == '0' and defs.get('USE_ARENA_FLAG', '0') == '0':
        #     imports += 'var Flag = undefined;\n'
        # if defs.get('USE_SCORE_COLLECTOR', '0') == '0':
        #     imports += 'var ScoreController = undefined;\nvar RESOURCE_SCORE = undefined;\n'
        # imports += '\n'

        core.lprint(WAIT, LOC_ANALYZING_AND_REBUILDING_MAIN_JS, end="", ln=config.language)

        content = self.auto_read(self.target_js)
        if modules is None: modules = []
        new_modules, new_content = [],""
        for line in content.split('\n'):
            m = re.search(self.JS_IMPORT_PAT, line)
            if not m:
                new_content += line + '\n'
                continue
            # remove ignore if in SYSTEM_MODULES_IGNORE
            module = m.group(1)

            _ignore = False
            if module in modules: _ignore = True
            if module in new_modules: _ignore = True
            if not _ignore: new_modules.append(module)

        # conbine modules
        modules = new_modules + modules
        new_modules = []
        for module in modules:
            _ignore = False
            if not _ignore and module.startswith(self.OTHER_IGNORE_WITH): _ignore = True
            for keeps in self.BUILTIN_TRANS:
                if module.endswith(keeps): _ignore = False
            if not _ignore: new_modules.append(module)
        modules = new_modules

        # save raw main.js
        with open(self.target_js[:-3] + ".raw.js", 'w', encoding='utf-8') as f:
            f.write(content)

        # write rebuild main.js
        with open(self.target_js, 'w', encoding='utf-8') as f:
            f.write(new_content)

        core.lprint(GREEN.format('[4/6]'), LOC_DONE, " ", LOC_ANALYZING_AND_REBUILDING_MAIN_JS_FINISH, sep="", head="\r", ln=config.language)

        return imports, modules

    @staticmethod
    def remove_js_import(raw) -> str:
        """
        移除js中的import行
        :param raw:
        :return:
        """
        return re.sub(r'import[^\n]*\n', '', raw)

    def generate_total_js(self, usr_modules, t_imps: list[str], f_sorts, f_replaces, g_replaces) -> str:
        """
        生成总的main.js
        按照如下顺序组合:
            ./org.transcrypt.__runtime__.js
            ./game.const.js  # IGNORE
            ./game.proto.js  # IGNORE
            ./game.utils.js  # IGNORE
            {usr_modules}
        :param usr_modules: list[str]  # js vm + 用户自定义模块
        :param t_imps: list[str]  # main前需要导入的模块
        :param f_sorts: dict{module_name: sort_priority}
        :param f_replaces: dict{module_name: dict{old: new}}
        :param g_replaces: dict{old: new}
        :return: str
        """
        arena_name = const.ARENA_NAMES.get(config.arena, const.ARENA_NAMES['green'])  # like green -> spawn_and_swamp
        self.TOTAL_INSERT_AT_HEAD += self.ARENA_IMPORTS_GETTER[arena_name]()  # add arena imports
        total_js = f"const __VERSION__ = '{const.VERSION}';\nconst __PYTHON_VERSION__ = '{python_version_info}';" + self.TOTAL_INSERT_AT_HEAD + f"\nexport var LANGUAGE = '{config.language}';\n"
        total_js += f"const __AUTHOR__ = '{const.AUTHOR}';\nconst __AUTHOR_CN__ = '{const.BILIBILI_NAME}';"

        core.lprint(WAIT, LOC_GENERATING_TOTAL_MAIN_JS, end="", ln=config.language)

        # TODO: IMPS donot work

        # resort modules
        f_sorts[self.JS_VM] = -1

        for i in range(len(usr_modules)):
            for j in range(i + 1, len(usr_modules)):
                if f_sorts[usr_modules[i][2:]] > f_sorts[usr_modules[j][2:]]:
                    usr_modules[i], usr_modules[j] = usr_modules[j], usr_modules[i]

        # write modules
        for module in usr_modules:
            content = self.auto_read(os.path.join(self.target_dir, module))
            content = self.remove_js_import(content)
            for old, new in f_replaces.get(module, {}).items():
                content = re.sub(old, new, content)
            for old, new in self.TRANSCRYPT_ERROR_REPLACE.items():
                content = re.sub(old, new, content)
            total_js += f"\n// ---------------------------------------- Module:{module} "
            total_js += "----------------------------------------\n\n"
            total_js += content + '\n'

        total_js += self.TOTAL_INSERT_BEFORE_MAIN

        # write main.js
        content = self.auto_read(self.target_js)
        for old, new in self.TRANSCRYPT_ERROR_REPLACE.items():
            content = re.sub(old, new, content)
        total_js += content

        # TOTAL_APPEND_ATEND
        total_js += self.TOTAL_APPEND_ATEND

        # replace export-pat
        total_js = re.sub(self.JS_EXPORT_PAT, "", total_js)

        # global replace
        for old, new in g_replaces.items():
            total_js = re.sub(old, new, total_js)

        core.lprint(GREEN.format('[5/6]'), LOC_DONE, " ", LOC_GENERATING_TOTAL_MAIN_JS_FINISH, sep="", head="\r", ln=config.language)

        # REPACE
        for old, new in self.TOTAL_SIMPLE_REPLACE_WITH.items():
            total_js = total_js.replace(old, new)

        return total_js

    def __parse_js_file_sort(self, fpath):
        """
        解析js文件中的sort
        :param fpath:
        :return:
        """
        content = self.auto_read(fpath)
        m = re.search(r'//\s*>\s*sort\s+(\d+)', content)
        if m:
            return int(m.group(1))
        return 65535

    def find_add_pure_js_files(self, sorts, modules):
        """
        找到所有的纯js文件，并添加到modules中
        :param sorts:
        :param modules:
        :return:
        """
        for root, dirs, files in os.walk(self.lib_dir):
            for file in files:
                if file.endswith('.js') and file not in modules:
                    fpath = str(os.path.join(root, file))
                    fname = file.replace('\\', '/')
                    # copy file to target
                    shutil.copy(fpath, os.path.join(self.target_dir, fname))
                    sorts[fname] = self.__parse_js_file_sort(fpath)
                    modules.append("./" + fname)

    def compile(self, paste=False):
        """
        编译
        :param paste: 是否复制到剪贴板
        :return:
        """
        imps, jimps, sorts, defs, reps = self.pre_compile()
        self.transcrypt_cmd()
        imports, modules = self.analyze_rebuild_main_js(defs, jimps)
        self.find_add_pure_js_files(sorts, modules)
        total_js = imports + "\n" + self.generate_total_js(replace_src_prefix(modules), imps, sorts, self.FILE_STRONG_REPLACE, reps)

        core.lprint(WAIT, LOC_EXPORTING_TOTAL_MAIN_JS, end="", ln=config.language)

        # ensure exported main.mjs path
        build_main_mjs = os.path.join(self.build_dir, 'main.mjs')

        mjs_path = config.target if config.target is not None else config.TARGET_GETTER()
        if not mjs_path.endswith('js'):
            mjs_path = os.path.join(mjs_path, 'main.mjs')

        # write main.mjs
        with open(build_main_mjs, 'w', encoding='utf-8') as f:
            f.write(total_js)

        # export main.mjs
        dir_path = os.path.dirname(mjs_path)
        if not os.path.exists(dir_path):
            core.error('Compiler.compile', core.lformat(LOC_EXPORT_DIR_PATH_NOT_EXISTS, [dir_path]), head='\n', ln=config.language)
        with open(mjs_path, 'w', encoding='utf-8') as f:
            f.write(total_js)

        core.lprint(GREEN.format('[6/6]'), LOC_DONE, " ", LOC_EXPORTING_TOTAL_MAIN_JS_FINISH, sep="", head="\r", ln=config.language)

        if mjs_path != build_main_mjs:
            core.lprint(Fore.LIGHTBLUE_EX + '[Info] ' + Fore.RESET, core.lformat(LOC_USR_EXPORT_INFO, [mjs_path]), ln=config.language)

        # copy to clipboard
        if paste:
            pyperclip.copy(total_js)
            core.lprint(LOC_DONE, " ", LOC_COPY_TO_CLIPBOARD, ln=config.language)

    def clean(self):
        """
        清除build目录下除了main.mjs之外的所有文件和目录
        * 先复制main.mjs到src目录下，然后删除build目录，再将main.mjs剪切回build目录
        :return:
        """
        core.lprint(WAIT, LOC_CLEAN_BUILD_DIR, end="", ln=config.language)
        if not os.path.exists(self.build_dir):
            core.error('Compiler.clean', LOC_BUILD_DIR_NOT_EXISTS, indent=1, head='\n', ln=config.language)

        if not os.path.exists(os.path.join(self.build_dir, 'main.mjs')):
            core.error('Compiler.clean', LOC_MAIN_MJS_NOT_EXISTS, indent=1, head='\n', ln=config.language)

        # copy main.mjs to src
        shutil.copy(os.path.join(self.build_dir, 'main.mjs'), os.path.join(self.src_dir, 'main.mjs'))

        # remove build dir
        shutil.rmtree(self.build_dir)

        # create build dir
        os.makedirs(self.build_dir)

        # move main.mjs to build dir
        shutil.move(os.path.join(self.src_dir, 'main.mjs'), os.path.join(self.build_dir, 'main.mjs'))

        core.lprint(GREEN.format('[Done]'), LOC_CLEAN_BUILD_DIR_FINISH, head="\r", ln=config.language)

    def clear(self):
        """
        清除build目录下所有文件和目录
        :return:
        """
        core.lprint(WAIT, LOC_CLEAN_BUILD_DIR, end="", ln=config.language)
        if not os.path.exists(self.build_dir):
            core.lprint(LOC_BUILD_DIR_NOT_EXISTS, ln=config.language)

        shutil.rmtree(self.build_dir)
        os.makedirs(self.build_dir)

        core.lprint(GREEN.format('[Done]'), LOC_CLEAN_BUILD_DIR_FINISH, head="\r", ln=config.language)


if __name__ == '__main__':
    # compiler = Compiler('src', 'library', 'build')
    # compiler.compile()
    # compiler.clean()
    test = """
    
def patrolling(self, c: Creep):
    e = self.center.nearest(k.civilian.enemies, 5)
    if e:
        match c.test(e,
            int(c.hpPer <= 0.9) * 2, 
            int(c.info.melee) * -3
        ):
            case True: c.move(e, SWAMP_MOTION)
            case False: c.move(self.bpos, SWAMP_MOTION)
    
    """
    print(f"res=\n{Compiler.convert_match_to_if(test)}")
