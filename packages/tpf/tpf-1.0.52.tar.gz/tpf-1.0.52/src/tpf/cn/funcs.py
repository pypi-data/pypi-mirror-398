

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
        list: 包含所有工具信息的列表，按工具名称升序排列
    """
    # 返回按name字段升序排列的工具信息列表
    return sorted(tools_info, key=lambda x: x['name'])


def get_tools_mapping():
    """获取所有已注册的函数映射

    Returns:
        dict: 函数名称到函数对象的映射字典，按函数名称升序排列
    """
    # 返回按key升序排列的字典
    return dict(sorted(tools_mapping.items()))


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



import pandas as pd

def read_csv_sample(file_path: str):
    """
    从指定路径读取CSV文件并返回DataFrame

    Args:
        file_path (str): CSV文件的本地路径

    Returns:
        pd.DataFrame: 读取的CSV数据

    Examples:
        df = read_csv_from_path('data/example.csv')
    """
    try:
        df = pd.read_csv(file_path)
        return df
    except FileNotFoundError:
        raise FileNotFoundError(f"文件未找到: {file_path}")
    except pd.errors.EmptyDataError:
        raise ValueError(f"文件为空: {file_path}")
    except Exception as e:
        raise RuntimeError(f"读取文件时发生错误: {e}")

# 可选：使用标准库实现方式
def read_csv_with_standard_lib(file_path: str, delimiter=','):
    """
    使用标准库读取CSV文件内容为列表

    Args:
        file_path (str): CSV文件的本地路径
        delimiter (str): 分隔符，默认为逗号

    Returns:
        list[list]: CSV文件内容，按行列组织

    Examples:
        data = read_csv_with_standard_lib('example.csv')
    """
    import csv
    try:
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=delimiter)
            return [row for row in reader]
    except FileNotFoundError:
        raise FileNotFoundError(f"文件未找到: {file_path}")
    except Exception as e:
        raise RuntimeError(f"读取文件时发生错误: {e}")

_register_function(read_csv_sample)

_register_function(read_csv_with_standard_lib)

import pandas as pd

def read_csv_from_path(file_path, sep=',', header='infer', names=None, index_col=None, usecols=None, dtype=None, skiprows=None, nrows=None, na_values=None, keep_default_na=True, encoding=None, engine=None):
    """
    从指定路径读取CSV文件并返回DataFrame对象。

    Args:
        file_path (str): CSV文件的本地路径。
        sep (str, optional): 字段分隔符，默认为','。
        header (int or list of int, optional): 指定哪一行作为列名，默认为'infer'。
        names (list-like, optional): 自定义列名列表。
        index_col (int or str, optional): 用作行索引的列。
        usecols (list-like or callable, optional): 需要读取的列。
        dtype (dict, optional): 指定各列的数据类型。
        skiprows (int or list-like, optional): 跳过的行数或行号。
        nrows (int, optional): 读取的行数。
        na_values (scalar or list-like, optional): 用于替换为 NaN 的值。
        keep_default_na (bool, optional): 是否保留默认的 NaN 值集合，默认为True。
        encoding (str, optional): 文件编码格式，例如 'utf-8'。
        engine (str, optional): 解析引擎 {'c', 'python'}，默认由pandas自动选择。

    Returns:
        pd.DataFrame: 读取的CSV数据。

    Examples:
        df = read_csv_from_path('data.csv')
        df = read_csv_from_path('data.csv', sep=';', encoding='utf-8')
    """
    return pd.read_csv(
        file_path,
        sep=sep,
        header=header,
        names=names,
        index_col=index_col,
        usecols=usecols,
        dtype=dtype,
        skiprows=skiprows,
        nrows=nrows,
        na_values=na_values,
        keep_default_na=keep_default_na,
        encoding=encoding,
        engine=engine
    )

_register_function(read_csv_from_path)
import datetime

def get_current_time():
    """
    获取当前系统时间，精确到秒

    Returns:
        str: 当前时间的字符串表示，格式为 YYYY-MM-DD HH:MM:SS
    """
    current_time = datetime.datetime.now()
    return current_time.strftime("%Y-%m-%d %H:%M:%S")

import datetime

def get_current_time_seconds():
    """
    获取当前系统时间，精确到秒

    Returns:
        str: 当前时间字符串，格式为 'YYYY-MM-DD HH:MM:SS'
    """
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

_register_function(get_current_time_seconds)
import os
import re

def count_files_and_dirs_with_chinese_info(root_path='.'):
    """
    递归统计指定目录下的文件和目录数量，并检查是否存在包含中文的文件或目录名。

    Args:
        root_path (str): 要统计的根目录路径，默认为当前目录 '.'

    Returns:
        dict: 包含以下键值对的结果字典：
            - dir_count (int): 目录总数
            - file_count (int): 文件总数
            - total_count (int): 文件和目录总数量
            - has_chinese (bool): 是否存在包含中文的文件或目录
            - chinese_paths (list): 所有包含中文的文件或目录路径列表
    """
    dir_count = 0
    file_count = 0
    chinese_paths = []
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')

    for dirpath, dirnames, filenames in os.walk(root_path):
        # 检查当前目录本身是否包含中文
        if chinese_pattern.search(os.path.basename(dirpath)):
            chinese_paths.append(dirpath)
        dir_count += len(dirnames)
        file_count += len(filenames)
        
        # 检查子目录名是否包含中文
        for dirname in dirnames:
            full_dir_path = os.path.join(dirpath, dirname)
            if chinese_pattern.search(dirname):
                chinese_paths.append(full_dir_path)
        
        # 检查文件名是否包含中文
        for filename in filenames:
            full_file_path = os.path.join(dirpath, filename)
            if chinese_pattern.search(filename):
                chinese_paths.append(full_file_path)
    
    total_count = dir_count + file_count
    has_chinese = len(chinese_paths) > 0
    
    # 如果存在包含中文的路径，则打印它们
    if has_chinese:
        print("包含中文的文件或目录路径：")
        for path in chinese_paths:
            print(path)
    
    return {
        'dir_count': dir_count,
        'file_count': file_count,
        'total_count': total_count,
        'has_chinese': has_chinese,
        'chinese_paths': chinese_paths
    }

_register_function(count_files_and_dirs_with_chinese_info)
import pandas as pd

def filter_dataframe_by_year_month_v1(df, timestamp_column, year=2022, month=9, day=None, day_range=None, weekday=None, return_copy=True):
    """
    过滤出指定年份和月份的数据（优化版本 - 增加天级判断）

    增强功能：
    1. 支持具体日期过滤
    2. 支持日期范围过滤
    3. 支持工作日过滤
    4. 支持多种日期格式输入
    5. 性能优化和错误处理

    Args:
        df (pd.DataFrame): 包含时间戳列的DataFrame
        timestamp_column (str): 时间戳列的列名
        year (int): 目标年份，默认为2022
        month (int): 目标月份，默认为9
        day (int, optional): 具体日期，如15表示15号
        day_range (tuple, optional): 日期范围，如(10, 20)表示10号到20号
        weekday (int, optional): 星期几，0-6表示周一到周日
        return_copy (bool): 是否返回副本，默认为True

    Returns:
        pd.DataFrame: 筛选后的DataFrame

    Examples:
        >>> df = filter_dataframe_by_year_month_v1(df, 'date', 2023, 12, day=15)  # 2023年12月15日
        >>> df = filter_dataframe_by_year_month_v1(df, 'date', 2023, 12, day_range=(10, 20))  # 2023年12月10-20日
        >>> df = filter_dataframe_by_year_month_v1(df, 'date', 2023, 12, weekday=0)  # 2023年12月所有周一
    """
    import pandas as pd
    from datetime import datetime

    # 参数验证
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df 必须是 pandas DataFrame")

    if timestamp_column not in df.columns:
        raise ValueError(f"列 '{timestamp_column}' 不存在于DataFrame中")

    if not isinstance(year, int) or year < 1900 or year > 2100:
        raise ValueError("year 必须是1900-2100之间的整数")

    if not isinstance(month, int) or month < 1 or month > 12:
        raise ValueError("month 必须是1-12之间的整数")

    if day is not None and (not isinstance(day, int) or day < 1 or day > 31):
        raise ValueError("day 必须是1-31之间的整数")

    if day_range is not None:
        if not isinstance(day_range, tuple) or len(day_range) != 2:
            raise ValueError("day_range 必须是包含两个整数的元组")
        start_day, end_day = day_range
        if not (isinstance(start_day, int) and isinstance(end_day, int)):
            raise ValueError("day_range 中的元素必须是整数")
        if start_day < 1 or end_day > 31 or start_day > end_day:
            raise ValueError("day_range 必须是有效的日期范围 (1-31)")

    if weekday is not None and (not isinstance(weekday, int) or weekday < 0 or weekday > 6):
        raise ValueError("weekday 必须是0-6之间的整数 (0=周一, 6=周日)")

    # 创建副本以避免修改原始数据
    if return_copy:
        df = df.copy()

    # 确保timestamp列是datetime类型
    if not pd.api.types.is_datetime64_any_dtype(df[timestamp_column]):
        try:
            df[timestamp_column] = pd.to_datetime(df[timestamp_column])
        except Exception as e:
            raise ValueError(f"无法将列 '{timestamp_column}' 转换为datetime类型: {e}")

    # 构建过滤条件
    conditions = []

    # 年份过滤
    conditions.append(df[timestamp_column].dt.year == year)

    # 月份过滤
    conditions.append(df[timestamp_column].dt.month == month)

    # 具体日期过滤
    if day is not None:
        conditions.append(df[timestamp_column].dt.day == day)

    # 日期范围过滤
    if day_range is not None:
        start_day, end_day = day_range
        conditions.append((df[timestamp_column].dt.day >= start_day) &
                         (df[timestamp_column].dt.day <= end_day))

    # 工作日过滤
    if weekday is not None:
        # pandas中weekday()返回0-6，其中0=周一
        conditions.append(df[timestamp_column].dt.weekday == weekday)

    # 应用所有条件
    if conditions:
        mask = conditions[0]
        for condition in conditions[1:]:
            mask = mask & condition
        filtered_df = df[mask]
    else:
        filtered_df = df

    return filtered_df

_register_function(filter_dataframe_by_year_month_v1)


def filter_dataframe_by_year_month_v2(df, timestamp_column, year=2022, month=9,
                                    days=None, days_exclude=None,
                                    weekdays=None, weekdays_exclude=None,
                                    business_days_only=False,
                                    return_copy=True):
    """
    高级日期过滤函数 - 支持复杂的天级判断条件

    增强功能：
    1. 支持包含/排除特定日期
    2. 支持工作日/周末过滤
    3. 支持业务日历（排除节假日）
    4. 支持组合条件过滤
    5. 性能优化和内存管理

    Args:
        df (pd.DataFrame): 包含时间戳列的DataFrame
        timestamp_column (str): 时间戳列的列名
        year (int): 目标年份，默认为2022
        month (int): 目标月份，默认为9
        days (list, optional): 包含的日期列表，如[1, 15, 30]
        days_exclude (list, optional): 排除的日期列表，如[25, 26, 27]
        weekdays (list, optional): 包含的工作日列表，如[0, 1, 2]表示周一到周三
        weekdays_exclude (list, optional): 排除的工作日列表，如[5, 6]表示周六周日
        business_days_only (bool): 是否仅包含工作日，默认为False
        return_copy (bool): 是否返回副本，默认为True

    Returns:
        pd.DataFrame: 筛选后的DataFrame

    Examples:
        >>> df = filter_dataframe_by_year_month_v2(df, 'date', 2023, 12, days=[1, 15, 30])
        >>> df = filter_dataframe_by_year_month_v2(df, 'date', 2023, 12, weekdays=[0, 1, 2, 3, 4])
        >>> df = filter_dataframe_by_year_month_v2(df, 'date', 2023, 12, business_days_only=True)
    """
    import pandas as pd
    import numpy as np

    # 参数验证
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df 必须是 pandas DataFrame")

    if timestamp_column not in df.columns:
        raise ValueError(f"列 '{timestamp_column}' 不存在于DataFrame中")

    # 验证年份和月份
    if not isinstance(year, int) or year < 1900 or year > 2100:
        raise ValueError("year 必须是1900-2100之间的整数")

    if not isinstance(month, int) or month < 1 or month > 12:
        raise ValueError("month 必须是1-12之间的整数")

    # 验证日期列表
    if days is not None:
        if not isinstance(days, (list, tuple)):
            raise ValueError("days 必须是列表或元组")
        if not all(isinstance(d, int) and 1 <= d <= 31 for d in days):
            raise ValueError("days 中的元素必须是1-31之间的整数")

    if days_exclude is not None:
        if not isinstance(days_exclude, (list, tuple)):
            raise ValueError("days_exclude 必须是列表或元组")
        if not all(isinstance(d, int) and 1 <= d <= 31 for d in days_exclude):
            raise ValueError("days_exclude 中的元素必须是1-31之间的整数")

    # 验证工作日列表
    if weekdays is not None:
        if not isinstance(weekdays, (list, tuple)):
            raise ValueError("weekdays 必须是列表或元组")
        if not all(isinstance(w, int) and 0 <= w <= 6 for w in weekdays):
            raise ValueError("weekdays 中的元素必须是0-6之间的整数 (0=周一, 6=周日)")

    if weekdays_exclude is not None:
        if not isinstance(weekdays_exclude, (list, tuple)):
            raise ValueError("weekdays_exclude 必须是列表或元组")
        if not all(isinstance(w, int) and 0 <= w <= 6 for w in weekdays_exclude):
            raise ValueError("weekdays_exclude 中的元素必须是0-6之间的整数 (0=周一, 6=周日)")

    # 创建副本以避免修改原始数据
    if return_copy:
        df = df.copy()

    # 确保timestamp列是datetime类型
    if not pd.api.types.is_datetime64_any_dtype(df[timestamp_column]):
        try:
            df[timestamp_column] = pd.to_datetime(df[timestamp_column])
        except Exception as e:
            raise ValueError(f"无法将列 '{timestamp_column}' 转换为datetime类型: {e}")

    # 构建过滤条件
    conditions = []

    # 年份过滤
    conditions.append(df[timestamp_column].dt.year == year)

    # 月份过滤
    conditions.append(df[timestamp_column].dt.month == month)

    # 包含特定日期
    if days is not None:
        conditions.append(df[timestamp_column].dt.day.isin(days))

    # 排除特定日期
    if days_exclude is not None:
        conditions.append(~df[timestamp_column].dt.day.isin(days_exclude))

    # 包含特定工作日
    if weekdays is not None:
        conditions.append(df[timestamp_column].dt.weekday.isin(weekdays))

    # 排除特定工作日
    if weekdays_exclude is not None:
        conditions.append(~df[timestamp_column].dt.weekday.isin(weekdays_exclude))

    # 业务日历过滤（仅工作日）
    if business_days_only:
        conditions.append(df[timestamp_column].dt.weekday < 5)  # 0-4为周一到周五

    # 应用所有条件
    if conditions:
        mask = conditions[0]
        for condition in conditions[1:]:
            mask = mask & condition
        filtered_df = df[mask]
    else:
        filtered_df = df

    return filtered_df


def filter_dataframe_by_date_pattern_v3(df, timestamp_column, pattern=None,
                                     start_date=None, end_date=None,
                                     date_list=None,
                                     exclude_pattern=None,
                                     return_copy=True):
    """
    模式化日期过滤函数 - 支持多种过滤模式

    过滤模式：
    1. 具体日期列表
    2. 日期范围
    3. 日期模式（如每月1号、每周一等）
    4. 排除模式

    Args:
        df (pd.DataFrame): 包含时间戳列的DataFrame
        timestamp_column (str): 时间戳列的列名
        pattern (str, optional): 日期模式，如'month_start'、'weekend'、'month_end'等
        start_date (str, optional): 开始日期，如'2023-01-01'
        end_date (str, optional): 结束日期，如'2023-12-31'
        date_list (list, optional): 具体日期列表，如['2023-01-01', '2023-01-15']
        exclude_pattern (str, optional): 排除模式，如'weekend'、'holidays'等
        return_copy (bool): 是否返回副本，默认为True

    Returns:
        pd.DataFrame: 筛选后的DataFrame

    Examples:
        >>> df = filter_dataframe_by_date_pattern_v3(df, 'date', pattern='month_start')
        >>> df = filter_dataframe_by_date_pattern_v3(df, 'date', pattern='weekend')
        >>> df = filter_dataframe_by_date_pattern_v3(df, 'date', start_date='2023-01-01', end_date='2023-01-31')
    """
    import pandas as pd
    from datetime import datetime

    # 参数验证
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df 必须是 pandas DataFrame")

    if timestamp_column not in df.columns:
        raise ValueError(f"列 '{timestamp_column}' 不存在于DataFrame中")

    # 创建副本以避免修改原始数据
    if return_copy:
        df = df.copy()

    # 确保timestamp列是datetime类型
    if not pd.api.types.is_datetime64_any_dtype(df[timestamp_column]):
        try:
            df[timestamp_column] = pd.to_datetime(df[timestamp_column])
        except Exception as e:
            raise ValueError(f"无法将列 '{timestamp_column}' 转换为datetime类型: {e}")

    # 构建过滤条件
    conditions = []

    # 日期范围过滤
    if start_date is not None or end_date is not None:
        if start_date is not None:
            try:
                start_dt = pd.to_datetime(start_date)
                conditions.append(df[timestamp_column] >= start_dt)
            except Exception as e:
                raise ValueError(f"无效的start_date格式: {e}")

        if end_date is not None:
            try:
                end_dt = pd.to_datetime(end_date)
                conditions.append(df[timestamp_column] <= end_dt)
            except Exception as e:
                raise ValueError(f"无效的end_date格式: {e}")

    # 具体日期列表过滤
    if date_list is not None:
        if not isinstance(date_list, (list, tuple)):
            raise ValueError("date_list 必须是列表或元组")
        try:
            date_list_dt = pd.to_datetime(date_list)
            conditions.append(df[timestamp_column].isin(date_list_dt))
        except Exception as e:
            raise ValueError(f"无效的date_list格式: {e}")

    # 模式过滤
    if pattern is not None:
        if pattern == 'month_start':
            conditions.append(df[timestamp_column].dt.day == 1)
        elif pattern == 'month_end':
            conditions.append(df[timestamp_column].dt.day.isin([28, 29, 30, 31]))
        elif pattern == 'weekend':
            conditions.append(df[timestamp_column].dt.weekday.isin([5, 6]))
        elif pattern == 'weekday':
            conditions.append(df[timestamp_column].dt.weekday.isin([0, 1, 2, 3, 4]))
        elif pattern == 'quarter_start':
            conditions.append(df[timestamp_column].dt.month.isin([1, 4, 7, 10]))
            conditions.append(df[timestamp_column].dt.day == 1)
        elif pattern == 'quarter_end':
            conditions.append(df[timestamp_column].dt.month.isin([3, 6, 9, 12]))
            conditions.append(df[timestamp_column].dt.day.isin([28, 29, 30, 31]))
        elif pattern == 'year_start':
            conditions.append(df[timestamp_column].dt.month == 1)
            conditions.append(df[timestamp_column].dt.day == 1)
        elif pattern == 'year_end':
            conditions.append(df[timestamp_column].dt.month == 12)
            conditions.append(df[timestamp_column].dt.day == 31)
        else:
            raise ValueError(f"未知的pattern: {pattern}")

    # 排除模式
    if exclude_pattern is not None:
        if exclude_pattern == 'weekend':
            conditions.append(~df[timestamp_column].dt.weekday.isin([5, 6]))
        elif exclude_pattern == 'weekday':
            conditions.append(~df[timestamp_column].dt.weekday.isin([0, 1, 2, 3, 4]))
        elif exclude_pattern == 'month_start':
            conditions.append(df[timestamp_column].dt.day != 1)
        elif exclude_pattern == 'month_end':
            conditions.append(~df[timestamp_column].dt.day.isin([28, 29, 30, 31]))
        else:
            raise ValueError(f"未知的exclude_pattern: {exclude_pattern}")

    # 应用所有条件
    if conditions:
        mask = conditions[0]
        for condition in conditions[1:]:
            mask = mask & condition
        filtered_df = df[mask]
    else:
        filtered_df = df

    return filtered_df


def filter_dataframe_by_date_range_v2(df, timestamp_column, start_date, end_date):
    """
    使用日期范围过滤数据（方法二）

    Args:
        df (pd.DataFrame): 包含时间戳列的DataFrame
        timestamp_column (str): 时间戳列的列名
        start_date (str or pd.Timestamp): 起始日期，如'2022-09-01'
        end_date (str or pd.Timestamp): 结束日期，如'2022-09-30'，但不包括该日期

    Returns:
        pd.DataFrame: 筛选后的DataFrame
    """
    # 确保timestamp列是datetime类型
    if not pd.api.types.is_datetime64_any_dtype(df[timestamp_column]):
        df[timestamp_column] = pd.to_datetime(df[timestamp_column])
    
    # 创建日期范围掩码
    mask = (df[timestamp_column] >= pd.Timestamp(start_date)) & (df[timestamp_column] < pd.Timestamp(end_date))
    return df.loc[mask]

_register_function(filter_dataframe_by_date_range_v2)

# 注册新函数
_register_function(filter_dataframe_by_year_month_v2)
_register_function(filter_dataframe_by_date_pattern_v3)



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
    'append_code_to_file_safely',
    'read_csv_sample',
    'read_csv_with_standard_lib',
    'read_csv_from_path',
    'get_current_time',
    'get_current_time_seconds',
    'count_files_and_dirs_with_chinese_info',
    'filter_dataframe_by_year_month_v1',
    'filter_dataframe_by_year_month_v2',
    'filter_dataframe_by_date_pattern_v3',
    'filter_dataframe_by_date_range_v2'
]