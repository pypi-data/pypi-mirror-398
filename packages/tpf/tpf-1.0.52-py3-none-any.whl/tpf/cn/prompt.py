

def wanshan_func(func_name):
    p = f"""
    进入/ai/wks/aitpf/src/tpf/cn目录；
    为funcs.py中的{func_name}函数添加func_info并追
   加到tools_info，添加函数映射到tools_mapping，可
   参数其他函数的添加风格，追加到该函数的后面
    """
    return p



def return_json1():
    
    output_format = """
    输出格式：json格式，包含在```json ```标记中，
    1. query字段，string类型，其value为用户的问题
    2. result字段，string类型，其value为最终回复结果
    3. thinking字段，list类型，
    3.1 列表元素为大模型的思考步骤，按思考顺序整理为list列表；
    3.2 若无思考步骤，则列表为空
    
    """
    return output_format


class Prompt:
    func_info = {
            "name": "要调用函数的名称",
            "description": "函数功能描述",
            "parameters": {
                "param1": ("number","默认值或建议值", "param1的取值范围或取值各类，param1的说明"),
                "param2": ("str","默认值或建议值","param2的取值范围或取值各类，param2的说明" ),
                "paramn":  ("number","默认值或建议值", "paramn的取值范围或取值各类，paramn的说明"),
            },
        }
    def __init__(self):
        pass

    def return_json1(self):
        """从文本中提取json格式的输出格式说明

        主要逻辑：
        1. 格式定义：定义函数调用需求分析的JSON输出格式规范
        2. 字段说明：详细说明每个字段的结构、类型和要求
        3. 格式返回：返回完整的格式说明字符串供AI模型参考

        Returns:
            str: 包含详细JSON输出格式规范的字符串
        """
        # 1. 格式定义：定义函数调用需求分析的JSON输出格式规范
        output_format = f"""
        输出格式：json格式，包含在```json ```标记中，
        1. query字段，string类型，其value为用户的问题
        2. result字段，string类型，其value为最终回复结果
          2.1 检查value中的各种引号是否匹配，不要出现"Unterminated string starting"类似的错误
        3. thinking字段，list类型，每个元素为一个元组
        3.1 列表元素为大模型的思考步骤，按思考顺序整理为list列表；
            3.1.1 元组首个元素为思考内容，
            3.1.2 第2个元素为该步骤是否需要函数调用，需要为1，不需要则为0
                3.1.2.1 若元组第2个元素为1,即该步骤需要函数调用，则按{self.func_info}格式给出所需要的函数信息，并将函数信息写入到元组第3个元素的位置上
                3.1.2.2 若元组第2个元素为0,即该步骤不需要函数调用，则元组第3个元素值为空''
        3.2 若无思考步骤，则列表为空
        4. tools_num,int类型，其值为3.1中思考步骤中需要函数调用的元素个数；
          4.1 若3.1中思考步骤中有n个元素需要函数调用，则tools_num=n
          4.2 若3.1中思考步骤有0个元素需要函数调用,或者无思考步骤,则tools_num=0

        """
        # 2. 格式返回：返回完整的格式说明字符串供AI模型参考
        return output_format
    
    def is_need_func_call(self, query):
        """函数调用需求分析提示生成器

        主要逻辑：
        1. 示例构建：创建包含具体示例的JSON格式示范
        2. 提示组装：构建结构化的提示文本，包含任务说明、用户问题和格式要求
        3. 格式引用：引用预定义的JSON输出格式规范
        4. 返回提示：生成完整的分析提示供AI模型使用

        Args:
            query: 用户提出的问题字符串

        Returns:
            str: 完整的分析提示，包含任务说明、用户问题、输出格式和示例
        """
        # 1. 示例构建：创建具体的函数调用分析示例
        examples = """
        用户问题：当前文件的绝对路径是什么
        输出：
        ```json
        {
        'query': '当前文件的绝对路径是什么',
        'result': True,
        'thinking': [
            ['理解用户的问题：用户想知道当前文件的绝对路径。', 0, ''],
            ['判断是否需要函数调用：作为AI，无法直接访问文件系统，因此需要函数调用来获取路径信息。', 0, ''],
            ['定义函数 get_current_file_path 来获取路径。',1,{
                'name': 'get_current_file_path',
                'description': '获取当前执行文件的绝对路径',
                'parameters': {}
            }]
        ],
        'tools_num':1
        }
        """
        
        output_format = f"""
        输出格式：json格式，包含在```json ```标记中，
        1. query字段，string类型，其value为用户的问题
        2. result字段，bool类型，需要函数返回True,不需要返回False
        3. thinking字段，list类型，每个元素为一个元组
        3.1 列表元素为大模型的思考步骤，按思考顺序整理为list列表；
            3.1.1 元组首个元素为思考内容，
            3.1.2 第2个元素为该步骤是否需要函数调用，需要为1，不需要则为0
                3.1.2.1 若元组第2个元素为1,即该步骤需要函数调用，则按{self.func_info}格式给出所需要的函数信息，并将函数信息写入到元组第3个元素的位置上
                3.1.2.2 若元组第2个元素为0,即该步骤不需要函数调用，则元组第3个元素值为空''
        3.2 若无思考步骤，则列表为空
        4. tools_num,int类型，其值为3.1中思考步骤中需要函数调用的元素个数；
          4.1 若3.1中思考步骤中有n个元素需要函数调用，则tools_num=n
          4.2 若3.1中思考步骤有0个元素需要函数调用,或者无思考步骤,则tools_num=0

        """

        # 2. 提示组装：构建完整的分析提示文本
        prompt1 = f"""
        你是任务是分析用户的问题是否需要函数调用：
        1.充分理解用户的问题：拆解用户的问题，需要多少步操作能解决，理解每一步操作，再整体综合理解
        2.判断回答用户的问题，或者要解决用户的问题，是否需要额外的函数调用
          2.1 如果不需要额外的函数调用，则直接回复
          2.2 如果需要额外的函数调用，则说明在哪一步需要函数调用，并按格式{self.func_info}指出所需要的函数说明
          2.3 尝试自主实现该函数，首先写好函数注释，包括函数的功能，参数说明：参数类型，默认值或建议值，取值范围及功能说明


        用户问题：
        {query}


        {output_format}

        # 4. 示例参考：提供具体的分析示例供AI参考
        examples:
        {examples}
        ```

        """

        return prompt1 
        
      
    
    def gen_fun(self, res_dict=None,query=None):
        """函数代码生成提示生成器

        主要逻辑：
        1. 数据提取：从分析结果中提取用户问题和函数信息
        2. 格式定义：定义输出格式规范和函数信息模板
        3. 示例构建：创建完整的函数实现示例供AI参考
        4. 提示组装：构建结构化的代码生成提示模板

        Args:
            res_dict: 包含函数调用需求分析结果的字典
                     格式：{'query': 用户问题, 'thinking': 思考步骤, 'tools_num': 工具数量}

        Returns:
            str: 完整的函数代码生成提示，包含任务说明、格式要求和示例

        示例输入格式：
        
        res_dict = {'query': '当前文件的绝对路径是什么',
        'result': '要获取当前文件的绝对路径，需要调用函数 get_current_file_path。该函数无需参数，返回当前执行文件的绝对路径。',
        'thinking': [['理解用户的问题：用户想知道当前文件的绝对路径。', 0, ''],
        ['判断是否需要函数调用：作为AI，无法直接访问文件系统，因此需要函数调用来获取路径信息。', 0, ''],
        ['定义函数 get_current_file_path 来获取路径。',
        1,
        {'name': 'get_current_file_path',
            'description': '获取当前执行文件的绝对路径',
            'parameters': {}}]],
        'tools_num': 1}
        """
        # 1. 数据提取：从分析结果中提取用户问题
        if query is None:
            query = res_dict["query"]
        
        _func_doc = """
    函数功能描述

    Args:
        参数名称(参数类型): 参数描述，参数默认值或建议值，取值范围及功能说明; 比如，text (str): 包含日期信息的文本

    Returns:
        返回值说明

    Examples:
        举例说明
    """

        # 2. 格式定义：定义输出格式规范
        output_format = f"""
            输出格式：json格式，包含在```json ```标记中，
            1. query字段，string类型，其value为用户的问题
            2. result字段，string类型，其value为```python ...```结构中的Python代码,但不包含```python ```本身，即只取三重反引号中间的代码段
                2.1 再次检查该代码段去除了三重反引号标记
                2.2 再次检查该代码段否存在未终止的字符串错误或者缩进异常等语法错误，若存在则修正
                2.3 如果有多个函数，则逐次追加到文本尾部，合并为一个文本
                2.4 每个函数文件的首部，尾部都增加一个换行
                2.5 每个函数的尾部都增加一行代码: _register_function(函数名称)
            3. thinking字段，list类型，
                3.1 列表元素为大模型的思考步骤，按思考顺序整理为list列表；
                3.2 若无思考步骤，则列表为空
            
            """

        # 定义函数信息模板格式
        func_info = {
            "name": "要调用函数的名称",
            "description": "函数功能描述",
            "parameters": {
                "param1": ("number","默认值或建议值", "param1的取值范围或取值各类，param1的说明"),
                "param2": ("str","默认值或建议值","param2的取值范围或取值各类，param2的说明" ),
                "paramn":  ("number","默认值或建议值", "paramn的取值范围或取值各类，paramn的说明"),
            },
        }
        
     
        # 3. 示例构建：创建完整的函数实现示例
        exampels = """
        ```json
        {
            "query": "当前文件的绝对路径是什么",
            "result": "import os\n\ndef get_current_file_path():\n    \n    # 获取当前执行文件的绝对路径\n    return os.path.abspath(__file__)\n\n\n _register_function(read_csv_from_path)\n",
            "thinking": [
                ["理解用户的问题：用户想知道当前文件的绝对路径。", 0, ""],
                ["判断是否需要函数调用：作为AI，无法直接访问文件系统，因此需要函数调用来获取路径信息。", 0, ""],
                ["定义函数 get_current_file_path 来获取路径。", 1, {"name": "get_current_file_path", "description": "获取当前执行文件的绝对路径", "parameters": {}}]
            ]
        }
        ```

        """

        # 4. 提示组装：构建结构化的代码生成提示模板
        if res_dict is not None:
            prompt2 = f"""
            你的任务是根据用户问题以及相关函数信息，实现函数信息中函数定义
            
            用户问题相关函数信息如下：
            {res_dict}
            
            请生成上文函数信息中提到的函数
            1. 使用python实现
            2. 函数注释的格式参考{_func_doc}
    
            
            输出格式:
            {output_format}
            
            
            examples:
            {exampels}
            
            
            用户问题：
            {query}
            
            """
        if query is not None:
            prompt2 = f"""
        你是任务是根据用户问题生成函数
        - 在内部生成2-5个类似的方法，推荐出最好的1-2个方法
        - 最终结果给出的只有1-2个方法
        - 考虑的要素依次为：可执行性(输出前进行一次语法检查，如有语法错误则进行修正，比如代码缩进是否正确),安全性，稳定性，健壮性，通用性
        
        
        请生成函数
        1. 使用python实现
        2. 函数注释的格式参考{_func_doc}
  
        
        输出格式:
        {output_format}
        
        
        examples:
        {exampels}
        
        
        用户问题：
        {query}
        
        """
            
        return prompt2 
        
      
        
    def gen_fun_one(self, query):
        """根据用户问题生成单个函数代码的完整提示模板

        主要逻辑：
        1. 函数模板定义：定义标准的函数文档字符串模板
        2. 输出格式规范：定义JSON格式的输出结构要求
        3. 示例构建：创建完整的函数实现示例供AI参考
        4. 提示组装：将所有组件组装成结构化的代码生成提示

        Args:
            query (str): 用户提出的问题字符串

        Returns:
            str: 完整的函数代码生成提示，包含任务说明、格式要求和示例

        """
        # 1. 函数模板定义：定义标准的函数文档字符串模板

        _func_doc = """
    函数功能描述

    Args:
        参数名称(参数类型): 参数描述，参数默认值或建议值，取值范围及功能说明; 比如，text (str): 包含日期信息的文本

    Returns:
        返回值说明

    Examples:
        举例说明
    """

        # 2. 格式定义：定义输出格式规范
        output_format = f"""
            输出格式：json格式，包含在```json ```标记中，
            1. query字段，string类型，其value为用户的问题
            2. result字段，string类型，其value为```python ...```结构中的Python代码,但不包含```python ```本身，即只取三重反引号中间的代码段
                2.1 再次检查该代码段去除了三重反引号标记
                2.2 再次检查该代码段否存在未终止的字符串错误或者缩进异常等语法错误，若存在则修正
                2.3 如果有多个函数，则逐次追加到文本尾部，合并为一个文本
                2.4 每个函数文件的首部，尾部都增加一个换行
                2.5 每个函数的尾部都增加一行代码: _register_function(函数名称)
            3. thinking字段，list类型，
                3.1 列表元素为大模型的思考步骤，按思考顺序整理为list列表；
                3.2 若无思考步骤，则列表为空
            
            """
        
     
        # 3. 示例构建：创建完整的函数实现示例
        exampels = """
        ```json
        {
            "query": "当前文件的绝对路径是什么",
            "result": "import os\n\ndef get_current_file_path():\n    \n    # 获取当前执行文件的绝对路径\n    return os.path.abspath(__file__)\n\n\n _register_function(read_csv_from_path)\n",
            "thinking": [
                ["理解用户的问题：用户想知道当前文件的绝对路径。", 0, ""],
                ["判断是否需要函数调用：作为AI，无法直接访问文件系统，因此需要函数调用来获取路径信息。", 0, ""],
                ["定义函数 get_current_file_path 来获取路径。", 1, {"name": "get_current_file_path", "description": "获取当前执行文件的绝对路径", "parameters": {}}]
            ]
        }
        ```

        """

        # 4. 提示组装：构建结构化的代码生成提示模板
        prompt2 = f"""
        你是任务是根据用户问题生成函数
        - 在内部生成2-5个类似的方法，推荐出最好的1-2个方法
        - 最终结果给出的只有1-2个方法
        - 考虑的要素依次为：可执行性(输出前进行一次语法检查，如有语法错误则进行修正，比如代码缩进是否正确),安全性，稳定性，健壮性，通用性
        
        
        请生成函数
        1. 使用python实现
        2. 函数注释的格式参考{_func_doc}
  
        
        输出格式:
        {output_format}
        
        
        examples:
        {exampels}
        
        
        用户问题：
        {query}
        
        """
        return prompt2 
        
        

