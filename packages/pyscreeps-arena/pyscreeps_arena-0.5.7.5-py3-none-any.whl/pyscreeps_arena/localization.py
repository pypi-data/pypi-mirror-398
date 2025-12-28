from pyscreeps_arena.core import *


TEMPLATE = {
    'en': "English",
    'cn': "中文",
}
LOC_DONE = {
    "en": Fore.GREEN + "[DONE]" + Fore.RESET,
    "cn": Fore.GREEN + "[完成]" + Fore.RESET,
}
LOC_DIR_NOT_EXISTS = {
    'en': "{} dir not exists. got: {}",
    'cn': "{} 目录不存在。传入: {}",
}
LOC_FILE_NOT_EXISTS = {
    'en': "{} File not exists: {}. You can ignore if it's a not used file.",
    'cn': "{} 文件不存在: {}. 如果它是一个未使用的文件，您可以忽略它。",
}
LOC_FILE_READ_FAILED = {
    'en': "Failed to read file: {}({})\nDetails:\n{}",
    'cn': "读取文件失败: {}({})\n详细信息:\n{}",
}
LOC_PREPROCESSING = {
    'en': "Preprocessing ...",
    'cn': "预处理中 ...",
}
LOC_PREPROCESSING_FINISH = {
    'en': "Preprocessing finished.",
    'cn': "预处理完成。",
}
LOC_IMPORT_STAR_ERROR = {
    'en': "Only 'from xxx import *' is allowed, but found 'import {}'." + Fore.LIGHTBLUE_EX + "Maybe you can use 'from {} import *' instead." + Fore.RESET,
    'cn': "只允许'from xxx import *'，但是发现了'import {}'。" + Fore.LIGHTBLUE_EX + "也许你可以使用'from {} import *'代替之。" + Fore.RESET,
}
LOC_IMPORT_STAR2_ERROR = {
    'en': "Only 'from xxx import *' is allowed, but found 'from {} import {}'." + Fore.LIGHTBLUE_EX + "Maybe you can use 'from {} import *' instead." + Fore.RESET,
    'cn': "只允许'from xxx import *'，但是发现了'from {} import {}'。 " + Fore.LIGHTBLUE_EX + "也许你可以使用'from {} import *'代替之。" + Fore.RESET,
}
LOC_CHAIN_FILE_NOT_EXISTS = {
    'en': "During search chain-import at {}, lineno {}:\n\tfile not exists: {}",
    'cn': "在搜索链式导入时，位于 {}，行号 {}:\n\t文件不存在: {}",
}
LOC_TRANSCRYPTING = {
    'en': "Transcrypting ... # cmd:{}",
    'cn': "转译中 ... # cmd命令:{}",
}
LOC_TRANSCRYPTING_FINISH = {
    'en': "Transcrypting finished.",
    'cn': "转译完成。",
}
LOC_TRANSCRYPTING_ERROR = {
    'en': "Transcrypting error: see details above.",
    'cn': "转译出错: 请查看上面的详细信息。",
}

LOC_ANALYZING_AND_REBUILDING_MAIN_JS = {
    'en': "analyzing and rebuilding js files ...",
    'cn': "正在分析和重建js文件 ...",
}
LOC_ANALYZING_AND_REBUILDING_MAIN_JS_FINISH = {
    'en': "analyzing and rebuilding js files finished.",
    'cn': "分析和重建js文件完成。",
}
LOC_GENERATING_TOTAL_MAIN_JS = {
    'en': "generating total main.js ...",
    'cn': "正在生成总的 main.js ...",
}
LOC_GENERATING_TOTAL_MAIN_JS_FINISH = {
    'en': "generating total main.js finished.",
    'cn': "生成总的 main.js 完成。",
}
LOC_EXPORTING_TOTAL_MAIN_JS = {
    'en': "exporting total main.js ...",
    'cn': "正在导出总的 main.js ...",
}
LOC_USR_EXPORT_INFO = {
    'en': "usr export to {}",
    'cn': "用户指定导出到 {}",
}
LOC_COPY_TO_CLIPBOARD = {
    'en': "copy code to clipboard.",
    'cn': "已复制代码内容到剪贴板。",
}
LOC_EXPORT_DIR_PATH_NOT_EXISTS = {
    'en': "export dir path not exists: {}",
    'cn': "目标导出目录不存在: {}",
}
LOC_EXPORTING_TOTAL_MAIN_JS_FINISH = {
    'en': "exporting main.js to target finished.",
    'cn': "已将main.js导出到指定目标。",
}
LOC_CLEAN_BUILD_DIR = {
    'en': "clean build dir ...",
    'cn': "正在清理build目录 ...",
}
LOC_BUILD_DIR_NOT_EXISTS = {
    'en': "build dir not exists",
    'cn': "build目录不存在",
}
LOC_MAIN_MJS_NOT_EXISTS = {
    'en': "main.mjs not exists",
    'cn': "main.mjs 不存在",
}
LOC_CLEAN_BUILD_DIR_FINISH = {
    'en': "clean build dir finished.",
    'cn': "清理build目录完成。",
}
LOC_COPYING_TO_BUILD_DIR = {
    'en': "copying to build dir: {}...",
    'cn': "正在复制到build目录: {}...",
}
LOC_COPYING_TO_BUILD_DIR_FINISH = {
    'en': "copying to build dir finished.",
    'cn': "复制到build目录完成。",
}
LOC_SORT_NUMBER_ERROR = {
    'en': "sort number error: {}, use 65535 instead.",
    'cn': "sort的值错误: {}, 使用 65535 代替。",
}
LOC_PYFILE_WORD_WARNING_CHECK_GET = {
    'en': "Please use 'dict.py_get' instead of general 'dict.get'. (add '# > ignore' same line to ignore it if you sure right).",
    'cn': "请使用 'dict.py_get' 而不是通用的 'dict.get'。 (如果确定你是对的，请在同一行添加 '# > ignore' 来忽略它。)",
}
LOC_PYFILE_WORD_WARNING_CHECK_MATH = {
    'en': "Please remove 'import math' and use 'math' in 'builtin'. (add '# > ignore' same line to ignore it if you sure right).",
    'cn': "请删除 'import math' 并使用 'builtin' 中的 'math'。 (如果确定你是对的，请在同一行添加 '# > ignore' 来忽略它。)",
}
LOC_PYFILE_WORD_WARNING_CHECK_CLEAR = {
    'en': "Please use 'container.py_clear' instead of general 'container.clear'. (add '# > ignore' same line to ignore it if you sure right).",
    'cn': "请使用 'container.py_clear' 而不是通用的 'container.clear'。 (如果确定你是对的，请在同一行添加 '# > ignore' 来忽略它。)",
}
LOC_PYFILE_WORD_WARNING_INDEX_MINUS_ONE = {
    'en': "Index by '[-1]' may not work in js. (add '# > ignore' same line to ignore it if you sure right).",
    'cn': "在 js 中，通过 '[-1]' 索引可能不起作用。 (如果确定你是对的，请在同一行添加 '# > ignore' 来忽略它。)",
}
LOC_NOT_SUPPORT_PYFILE_INIT = {
    'en': 'Not support __init__.py! Please remove it(the init file) and use from directory.xxx import xxxx instead.',
    'cn': '不支持 __init__.py！请删除它(初始化文件)并使用 from directory.xxx import xxxx 代替之。',
}

# V0.5.4
LOC_DIR_UNDER_NONINIT_DIR = {
    'en': "Directory [{}] is located under [{}] without __init__.py, therefore it is ignored.",
    'cn': "目录 [{}] 位于 `无__init__.py`的目录[{}]下，因此被忽略。",
}

if __name__ == '__main__':
    lprint(TEMPLATE)

