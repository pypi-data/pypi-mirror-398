

import inspect
import os

import re
from datetime import datetime

tools_info = []
tools_mapping = {}

def date_extract(text):
    """从文本中提取日期
    函数名称: date_extract
    函数描述: 提取日期
    参数描述:
        text (str): 待处理的文本
    返回参数:
        str: 处理后的文本，提取的日期被格式化为 "YYYY-MM-DD"
    Examples:
        >>> text = "今天是2023年1月1日"
        >>> print(date_extract(text))
        2023-01-01
        >>> text = "今天是2023/1/1"
    """
    patterns = [
       r'\d{1,2}\/\d{1,2}\/\d{4}',       # "MM/DD/YYYY"
       r'\d{1,2}-\w{3}-\d{4}',           # "DD-MMM-YYYY"
       r'\d{4}年\d{1,2}月\d{1,2}日',     # "YYYY 年 MM 月 DD 日"
    ]
    for pattern in patterns:
        text = re.sub(pattern, lambda x: datetime.strptime(x.group(), '%Y年%m月%d日').strftime('%Y-%m-%d'), text)
    return text


# 函数信息
tools_info.append({
    "name": "date_extract",
    "description": "从文本中提取日期并格式化为YYYY-MM-DD",
    "parameters": {
        "text": ("str", "无默认值", "待处理的文本，包含需要提取的日期信息")
    }
})

# 函数映射
tools_mapping["date_extract"] = date_extract



def get_current_file_path_dir():
    """
    函数名称: get_current_file_path_dir
    函数描述: 获取当前执行文件的绝对路径所在的目录
    参数描述: 无参数
    返回参数: 
        str: 当前执行文件的绝对路径字符串
    Examples:
        >>> path = get_current_file_path_dir()
        >>> print(path)  # 输出类似 /home/user/project/main.py
    """
    # 获取调用栈中最顶层的帧信息（即主执行文件）
    frame = inspect.stack()[-1]
    filename = frame.filename
    fil1 = os.path.abspath(filename)
    return fil1.removesuffix(filename)



func_info = {
    "name": "要调用函数的名称",
    "description": "函数功能描述",
    "parameters": {
        "param1": ("number","默认值或建议值", "param1的取值范围或取值各类，param1的说明"),
        "param2": ("str","默认值或建议值","param2的取值范围或取值各类，param2的说明" ),
        "paramn":  ("number","默认值或建议值", "paramn的取值范围或取值各类，paramn的说明"),
    },
}

tools_info.append({
    "name": "get_current_file_path_dir",
    "description": "获取当前执行文件的绝对路径所在的目录",
    "parameters": {},
})



tools_mapping["get_current_file_path_dir"] = get_current_file_path_dir



import sys,os
def get_current_exec_process_path():
    """
    获取当前进程所在主执行文件的绝对路径
    
    函数描述:
        获取当前正在执行的Python脚本文件的绝对路径
        
    参数描述:
        此函数无需任何参数
        
    返回参数:
        str: 当前执行文件的绝对路径，如果无法获取则返回None
        
    Examples:
        >>> path = get_current_file_path()
        >>> print(path)
        '/home/user/current_script.py'
    """
    try:
        # 获取主模块的文件路径（适用于直接执行和冻结环境）
        if getattr(sys, 'frozen', False):
            # 如果是PyInstaller打包后的可执行文件
            return os.path.abspath(sys.executable)
        else:
            # 正常Python脚本执行
            return os.path.abspath(sys.argv[0])
    except Exception as e:
        print(f"获取文件路径时出错: {e}")
        return None


# 函数信息
tools_info.append({
    "name": "get_current_exec_process_path",
    "description": "获取当前进程所在主执行文件的绝对路径",
    "parameters": {},
})

# 函数映射
tools_mapping["get_current_exec_process_path"] = get_current_exec_process_path


def calculate_area(length, width):
    """
    计算矩形的面积
    
    参数:
        length (number): 矩形的长度，必须为正数
        width (number): 矩形的宽度，必须为正数
        
    返回:
        number: 矩形的面积
        
    Examples:
        >>> calculate_area-5, 3)
        15
        >>> calculate_area(2.5, 4)
        10.0
    """
    if length <= 0 or width <= 0:
        raise ValueError("长度和宽度必须为正数")
    return length * width



# 初始化工具列表和映射字典（如果尚未定义）
try:
    tools_info
except NameError:
    tools_info = []

try:
    tools_mapping
except NameError:
    tools_mapping = {}
    
# 函数信息
tools_info.append({
    "name": "calculate_area",
    "description": "计算矩形的面积",
    "parameters": {
        "length": ("number", "无默认值", "矩形的长度，必须为正数"),
        "width": ("number", "无默认值", "矩形的宽度，必须为正数")
    }
})

# 函数映射
tools_mapping["calculate_area"] = calculate_area







