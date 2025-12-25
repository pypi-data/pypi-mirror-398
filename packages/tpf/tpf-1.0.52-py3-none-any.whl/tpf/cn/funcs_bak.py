

"""函数工具集合模块

本模块提供了各种实用函数的集合，包括日期处理、文件路径处理、数学计算等功能。
每个函数都配有详细的文档说明，并自动注册到tools_info和tools_mapping中。
"""

import inspect
import os
import re
import sys
from datetime import datetime

# 全局变量：存储工具信息和函数映射
tools_info = []
tools_mapping = {}


def _register_function(func):
    """注册函数到工具信息列表和映射字典

    自动解析函数的文档字符串，提取参数信息并注册到全局的
    tools_info和tools_mapping中。

    Args:
        func: 要注册的函数对象
    """
    global tools_info, tools_mapping

    # 获取函数的基本信息
    func_name = func.__name__
    docstring = func.__doc__ or ""

    # 从文档字符串中提取描述（第一行）
    description = docstring.strip().split('\n')[0] if docstring else func_name

    # 获取函数签名
    sig = inspect.signature(func)
    parameters = {}

    # 解析参数信息
    for param_name, param in sig.parameters.items():
        param_type = str(param.annotation) if param.annotation != inspect.Parameter.empty else "any"
        default_value = param.default if param.default != inspect.Parameter.empty else "无默认值"

        # 从文档字符串中提取参数说明
        param_desc = _extract_param_description(docstring, param_name)

        parameters[param_name] = (param_type, str(default_value), param_desc)

    # 注册到工具信息列表
    tools_info.append({
        "name": func_name,
        "description": description,
        "parameters": parameters
    })

    # 注册到函数映射字典
    tools_mapping[func_name] = func


def _extract_param_description(docstring, param_name):
    """从文档字符串中提取参数描述

    Args:
        docstring (str): 函数的文档字符串
        param_name (str): 参数名称

    Returns:
        str: 参数描述，如果没有找到则返回空字符串
    """
    if not docstring:
        return ""

    # 查找参数描述模式
    patterns = [
        rf'{param_name}s*([^)]*):s*(.+?)(?=\\n\\n|\\n\\w|\\Z)',
        rf'Args:s*{param_name}s*([^)]*):s*(.+?)(?=\\n\\n|\\n\\w|\\Z)',
        rf'参数:s*{param_name}s*([^)]*):s*(.+?)(?=\\n\\n|\\n\\w|\\Z)',
    ]

    for pattern in patterns:
        match = re.search(pattern, docstring, re.DOTALL)
        if match:
            return match.group(1).strip()

    return ""


def date_extract(text):
    """从文本中提取日期并格式化为标准格式

    支持多种日期格式的识别和转换：
    - MM/DD/YYYY 格式
    - DD-MMM-YYYY 格式
    - YYYY年MM月DD日 格式

    Args:
        text (str): 包含日期信息的文本

    Returns:
        str: 处理后的文本，提取的日期被格式化为 "YYYY-MM-DD"

    Examples:
        >>> date_extract("今天是2023年1月1日")
        '2023-01-01'
        >>> date_extract("会议日期: 12/25/2023")
        '会议日期: 2023-12-25'
        >>> date_extract("截止日期: 25-Dec-2023")
        '截止日期: 2023-12-25'
    """
    # 定义支持的日期格式模式
    patterns = [
        r'\d{1,2}\/\d{1,2}\/\d{4}',        # MM/DD/YYYY
        r'\d{1,2}-\w{3}-\d{4}',            # DD-MMM-YYYY
        r'\d{4}年\d{1,2}月\d{1,2}日',      # YYYY年MM月DD日
    ]

    for pattern in patterns:
        try:
            text = re.sub(pattern,
                       lambda x: datetime.strptime(x.group(), '%Y年%m月%d日').strftime('%Y-%m-%d'),
                       text)
        except ValueError:
            # 如果转换失败，保持原样
            continue

    return text


# 注册date_extract函数
_register_function(date_extract)



def get_current_file_path_dir():
    """获取当前执行文件的绝对路径所在的目录

    通过检查调用栈来获取主执行文件的目录路径，
    适用于各种Python执行环境。

    Args:
        无参数

    Returns:
        str: 当前执行文件所在目录的绝对路径

    Examples:
        >>> dir_path = get_current_file_path_dir()
        >>> print(dir_path)  # 输出类似 /home/user/project/
    """
    # 获取调用栈中最顶层的帧信息（即主执行文件）
    frame = inspect.stack()[-1]
    filename = frame.filename
    abs_path = os.path.abspath(filename)
    # 返回文件所在目录的路径
    return os.path.dirname(abs_path)



# 注册get_current_file_path_dir函数
_register_function(get_current_file_path_dir)



def get_current_exec_process_path():
    """获取当前进程所在主执行文件的绝对路径

    支持正常Python脚本执行和PyInstaller打包后的可执行文件。
    能够适应不同的运行环境。

    Args:
        无参数

    Returns:
        str: 当前执行文件的绝对路径，如果无法获取则返回None

    Examples:
        >>> path = get_current_exec_process_path()
        >>> print(path)
        '/home/user/project/main.py'
    """
    try:
        # 判断是否为PyInstaller打包后的可执行文件
        if getattr(sys, 'frozen', False):
            # 如果是打包后的可执行文件，返回可执行文件路径
            return os.path.abspath(sys.executable)
        else:
            # 正常Python脚本执行，返回脚本文件路径
            return os.path.abspath(sys.argv[0])
    except Exception as e:
        print(f"获取文件路径时出错: {e}")
        return None


# 注册get_current_exec_process_path函数
_register_function(get_current_exec_process_path)


def calculate_area(length, width):
    """计算矩形的面积

    提供基础的矩形面积计算功能，包含参数验证。

    Args:
        length (int|float): 矩形的长度，必须为正数
        width (int|float): 矩形的宽度，必须为正数

    Returns:
        int|float: 矩形的面积

    Raises:
        ValueError: 当长度或宽度不是正数时抛出异常

    Examples:
        >>> calculate_area(5, 3)
        15
        >>> calculate_area(2.5, 4)
        10.0
        >>> calculate_area(0, 5)  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ValueError: 长度和宽度必须为正数
    """
    # 参数验证
    if length <= 0 or width <= 0:
        raise ValueError("长度和宽度必须为正数")

    return length * width



# 注册calculate_area函数
_register_function(calculate_area)


def get_tools_info():
    """获取所有已注册的工具信息

    Returns:
        list: 包含所有工具信息的列表
    """
    return tools_info


def get_tools_mapping():
    """获取所有已注册的函数映射

    Returns:
        dict: 函数名称到函数对象的映射字典
    """
    return tools_mapping


def get_function_by_name(name):
    """根据函数名称获取函数对象

    Args:
        name (str): 函数名称

    Returns:
        function: 函数对象，如果不存在则返回None
    """
    return tools_mapping.get(name)



def append_code_to_file(file_path, code_content):
    """
    将Python代码追加到文件末尾
    
    Args:
        file_path (str): 目标文件路径
        code_content (str): 要追加的Python代码文本
    
    Returns:
        bool: 操作成功返回True，失败返回False
    """
    try:
        with open(file_path, 'a', encoding='utf-8') as file:
            # 如果文件不为空且最后一行不是空行，添加一个空行作为分隔
            file.seek(0, 2)  # 移动到文件末尾
            if file.tell() > 0:  # 文件不为空
                file.seek(file.tell() - 1, 0)  # 移动到倒数第一个字符
                if file.read(1) != '\n':
                    file.write('\n')
            
            # 写入代码内容
            file.write(code_content)
            
            # 确保最后一行有换行符
            if not code_content.endswith('\n'):
                file.write('\n')
        return True
    except Exception as e:
        print(f"追加代码到文件时出错: {e}")
        return False

# 注册calculate_area函数
_register_function(append_code_to_file)

def append_code_to_file_simple(file_path, code_content):
    """
    简单版本：将Python代码追加到文件末尾
    
    Args:
        file_path (str): 目标文件路径
        code_content (str): 要追加的Python代码文本
    
    Returns:
        bool: 操作成功返回True，失败返回False
    """
    try:
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write('\n' + code_content)
            # 确保代码块结束有换行
            if not code_content.endswith('\n'):
                file.write('\n')
        return True
    except Exception as e:
        print(f"追加代码到文件时出错: {e}")
        return False

_register_function(append_code_to_file_simple)


def append_code_to_file_safely(file_path, code_content, encoding='utf-8', create_backup=True):
    """
    安全地将Python代码追加到文件尾部
    
    Args:
        file_path (str): 目标文件路径
        code_content (str): 要追加的代码内容
        encoding (str): 文件编码，默认utf-8
        create_backup (bool): 是否创建备份文件，默认True
    
    Returns:
        bool: 操作是否成功
    
    Raises:
        ValueError: 参数无效
        IOError: 文件操作失败
    """
    import os
    import shutil
    from pathlib import Path
    
    # 参数验证
    if not isinstance(file_path, str) or not file_path.strip():
        raise ValueError("file_path must be a non-empty string")
    
    if not isinstance(code_content, str):
        raise ValueError("code_content must be a string")
    
    if not isinstance(encoding, str) or not encoding.strip():
        raise ValueError("encoding must be a non-empty string")
    
    file_path = Path(file_path).resolve()
    
    # 检查目录是否存在，不存在则创建
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 如果文件不存在，创建空文件
    if not file_path.exists():
        file_path.touch()
    
    # 验证是否为文件而非目录
    if not file_path.is_file():
        raise ValueError(f"{file_path} is not a valid file")
    
    # 创建备份
    if create_backup and file_path.exists():
        backup_path = file_path.with_suffix(file_path.suffix + '.bak')
        shutil.copy2(file_path, backup_path)
    
    try:
        # 确保代码内容以换行符结尾
        if code_content and not code_content.endswith(('\n', '\r')):
            content_to_write = code_content + '\n'
        else:
            content_to_write = code_content
        
        # 追加内容到文件
        with open(file_path, 'a', encoding=encoding) as f:
            f.write(content_to_write)
        
        return True
    
    except Exception as e:
        # 如果有备份且操作失败，尝试恢复
        if create_backup and file_path.exists():
            backup_path = file_path.with_suffix(file_path.suffix + '.bak')
            if backup_path.exists():
                shutil.copy2(backup_path, file_path)
        
        raise IOError(f"Failed to append code to file: {str(e)}")
    
_register_function(append_code_to_file_safely)


# ===================
# 模块导出信息
# ===================
__all__ = [
    'date_extract',
    'get_current_file_path_dir',
    'get_current_exec_process_path',
    'calculate_area',
    'get_tools_info',
    'get_tools_mapping',
    'get_function_by_name',
    'tools_info',
    'tools_mapping',
    'append_code_to_file_simple',
    'append_code_to_file_safely'
]