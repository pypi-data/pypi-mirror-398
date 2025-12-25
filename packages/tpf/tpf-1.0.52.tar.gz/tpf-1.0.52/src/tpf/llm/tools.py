"""工具列表
获取文件绝对路径
天气预报

"""        
import re,sys
import json

def get_abs_path(file_path="."):
    """获取文件的绝对路径
    """
    import os
    abs_path = os.path.abspath(file_path) #获取当前文件的绝对路径
    return abs_path


def dcn_start_service():
    from tpf.dc import dcn 
    dcn.start_service()

#f_get_abs_path = {"name":"get_abs_path","desc":"获取文件的绝对路径","arguments":"python字典对象,其key为file_path，其值value为用户问题中的路径"}

# 给出工具定义，使用json格式详细描述函数的功能以及参数的个数与类型
tools_json = [
    # 每一个列表元素项，就是一个工具定义
    {
        # 类型标注（固定格式）
        "type": "function",
        # 函数定义
        "function": {
            # 函数名称（帮助我们去查找本地的函数在哪里，函数映射ID）
            "name": "get_abs_path",
            # 函数描述（帮助模型去理解函数的作用，适用场景，可以理解为Prompt的一部分）
            "description": "获取文件的绝对路径",
            # 函数依赖参数的定义（帮助模型去理解如果要做参数生成，应该怎么生成）
            "parameters": {
                # 参数形式
                "type": "object", # 对应输出JSON String
                # 参数结构
                "properties": {
                    # 参数名，参数类型
                    "file_path": {"type": "string"}, # 用户问题中的文件路径
                },
                # 必须保证生成的参数列表（每个元素对应上面properties的参数名）
                "required": ["file_path"],
                "additionalProperties": False 
            },
            # 格式是否严格（默认为True）
            "strict": True
        }
    },
    {
        # 类型标注（固定格式）
        "type": "function",
        # 函数定义
        "function": {
            # 函数名称（帮助我们去查找本地的函数在哪里，函数映射ID）
            "name": "dcn_start_service",
            # 函数描述（帮助模型去理解函数的作用，适用场景，可以理解为Prompt的一部分）
            "description": "启动本地dcn服务",
            # 函数依赖参数的定义（帮助模型去理解如果要做参数生成，应该怎么生成）
            "parameters": {
            },
            # 格式是否严格（默认为True）
            "strict": True
        }
    },
    # 每一个列表元素项，就是一个工具定义
    {
        # 类型标注（固定格式）
        "type": "function",
        # 函数定义
        "function": {
            # 函数名称（帮助我们去查找本地的函数在哪里，函数映射ID）
            "name": "get_weather",
            # 函数描述（帮助模型去理解函数的作用，适用场景，可以理解为Prompt的一部分）
            "description": "Get current temperature for provided coordinates in celsius.",
            # 函数依赖参数的定义（帮助模型去理解如果要做参数生成，应该怎么生成）
            "parameters": {
                # 参数形式
                "type": "object", # 对应输出JSON String
                # 参数结构
                "properties": {
                    # 参数名，参数类型
                    "latitude": {"type": "number"},
                    # 参数名，参数类型
                    "longitude": {"type": "number"}
                },
                # 必须保证生成的参数列表（每个元素对应上面properties的参数名）
                "required": ["latitude", "longitude"],
                "additionalProperties": False
            },
            # 格式是否严格（默认为True）
            "strict": True
        }
    }
]


class Tools():
    def __init__(self):
        self.tool_list = []
        self.func_name_list = []
    
         
        # self.tool_list.append(f_get_abs_path) 
    def func_name_desc(self):
        self.func_name_list.append({
            "name": "get_weather",
            "description": "Get current temperature for provided coordinates in celsius."
        })
        self.func_name_list.append({
            "name": "get_abs_path",
            "description": "获取文件的绝对路径",
            "arguments":["file_path"]
        })
        return self.func_name_list
        
        
    def addTool(self,f_json):
        """添加工具
        
        examples
        ------------------------
        f_get_abs_path = {"name":"get_abs_path","desc":"获取文件的绝对路径","arguments":"名为file_path，其value为路径"}
        addTool(f_get_abs_path)
        
        
        """
        self.tool_list.append(f_json) 
        
    def tools(self):
        return self.tool_list
    
    
    def func_list(self):
        """文本格式的函数列表"""
        # func_list = f"""
        # # 可调用的函数/工具 列表
        # {self.tool_list}
        # """
        return self.tool_list
    
    
    def get_json_str(self,txt):
        """从文本中解析出json"""
        # json_pattern = r'```json\n([\s\S]*?)\n```'
        json_pattern = r'```json([\s\S]*?)```'
        match = re.search(json_pattern, txt)
        json_str = ""
        if match:
            json_str = match.group(1).strip()
        return json_str

    def parse_json(self,content):
        try:
            json_str = self.get_json_str(content)
            json_dict = json.loads(json_str)
            is_parse_ok = True 
        except Exception as e:
            print(e)
            is_parse_ok = False 
            
        if is_parse_ok:
            return json_dict
        return content

    
    
    


