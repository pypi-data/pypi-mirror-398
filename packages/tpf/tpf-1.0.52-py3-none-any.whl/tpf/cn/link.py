
import os
import json
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv(filename="env.txt"))

from tpf.cn.prompt import Prompt 
from tpf.llm.tools import Tools 
from tpf.cn.funcs import append_code_to_file_safely

class Think:
    
    def __init__(self, env_file=".env"):
        """配置文件中环境变量命名
        f"{llm_name}_base_url",f"{}_api_key"
        比如,deepseek为deepseek_base_url,deepseek_api_key,
        
        """
        if not os.path.exists(env_file):
            env_file = "/wks/bigmodels/conf/env.txt"  
        load_dotenv(env_file)  # 加载".env"文件 
        self._deepseek_base_url = os.getenv("deepseek_base_url")  
        self._deepseek_api_key = os.getenv("deepseek_api_key")  
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  
        self.OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")  
        self._qianfan_base_url=os.getenv("qianfan_base_url")
        self._qianfan_api_key=os.getenv("qianfan_api_key")
        self._DASHSCOPE_API_KEY=os.getenv("DASHSCOPE_API_KEY")
        self._DASHSCOPE_BASE_URL=os.getenv("DASHSCOPE_BASE_URL")
        
        
        self.pmt = Prompt()
        self.tools = Tools()
        

    def thinking(self, prompt_user, prompt_system=None,
            response_format="text",
            models=['deepseek-reasoner', 'deepseek-chat'],
            temperature=0.1,
            base_url=None,api_key=None,return_json=True):
        """AI超级大脑 - 对话模型调用方法

        主要逻辑：
        1. 参数配置：设置API基础URL和密钥
        2. 客户端初始化：创建OpenAI客户端实例
        3. 消息构建：根据是否有系统提示构建消息格式
        4. 模型调用：发送请求到指定的AI模型
        5. 响应处理：解析返回结果并格式化输出

        Args:
            prompt_user: 用户提示内容
            prompt_system: 系统提示内容（可选）
            response_format: 响应格式，默认为"text"
            models: 可用模型列表，默认为deepseek模型
            temperature: 温度参数，控制输出的随机性
            base_url: API基础URL（可选）
            api_key: API密钥（可选）
            return_json: 是否返回JSON格式，默认为True

        Returns:
            模型生成的响应内容，根据return_json参数返回JSON或文本
        """
        # 1. 参数配置：设置默认的API连接参数
        if base_url is None:
            base_url = self._deepseek_base_url
        if api_key is None:
            api_key= self._deepseek_api_key

        # 2. 客户端初始化：创建OpenAI客户端实例用于API调用
        client = OpenAI(
            base_url=base_url,
            api_key=api_key,    # 必需参数，但可以填写任意值
        )

        # 3. 消息构建：根据是否有系统提示构建不同的消息格式
        if prompt_system is None:
            # 纯用户对话模式
            message = [{'role': 'user','content': prompt_user,}]
        else:
            # 系统+用户对话模式，用于注入特定知识或约束
            message = [
                {
                    "role": "system",
                    "content": prompt_system  # 注入新知识或设定角色
                },
                {
                    "role": "user",
                    "content": prompt_user  # 用户的具体问题
                },
            ]

        # 4. 模型调用：发送请求到指定的AI模型获取响应
        response = client.chat.completions.create(
            model=models[0],  # 使用模型列表中的第一个模型
            messages=message,
            temperature=temperature,   # 控制模型输出的随机性，0表示确定性输出
            # 设置返回消息的格式：text（纯文本）或 json_object（JSON格式）
            response_format={"type": response_format},
        )

        # 5. 错误处理：检查API响应是否有效
        if response.choices is None:
            err_msg = response.error["message"]
            raise Exception(f"API调用失败: {err_msg}")

        # 提取模型生成的内容
        content = response.choices[0].message.content

        # 调试输出（已注释）
        # print("----------------------")
        # print(content)
        # print("----------------------")

        # 6. 响应格式化：根据参数决定返回格式
        if return_json:
            # 尝试解析为JSON格式
            res = self.tools.parse_json(content=content)
            return res

        return content          # 返回原始文本内容


    def deepseek_func_needing(self,query):
        """函数调用需求分析方法

        主要逻辑：
        1. 提示生成：调用提示生成器创建函数调用分析提示
        2. AI分析：通过thinking方法让AI模型分析用户问题
        3. 结果返回：返回AI模型的分析结果

        Args:
            query: 用户提出的问题字符串

        Returns:
            dict: 包含函数调用需求分析的结果，包含thinking步骤和tools_num等信息
        """
        # 1. 提示生成：调用提示生成器创建函数调用分析提示
        func_call_prompt = self.pmt.is_need_func_call(query)
    

        # 2. AI分析：通过thinking方法让AI模型分析用户问题是否需要函数调用
        res = self.thinking(func_call_prompt)

        # 3. 结果返回：返回AI模型的分析结果（包含thinking步骤、函数定义、tools_num等）
        return res  
    
    def deepseek_func_gen(self,query,
                          append_file_path="/ai/wks/aitpf/src/tpf/cn/funcs.py"):
        """函数代码生成完整流程

        主要逻辑：
        1. 需求分析：分析用户问题是否需要函数调用
        2. 提示生成：根据分析结果生成函数代码生成提示
        3. 代码生成：通过AI模型生成完整的函数代码实现
        4. 结果返回：返回生成的函数代码和相关信息

        Args:
            query: 用户提出的问题字符串

        Returns:
            dict: 包含生成的函数代码、tools_info和tools_mapping的结果字典
        """
        # 1. 需求分析：分析用户问题是否需要函数调用
        # 使用deepseek_func_needing方法获取函数调用需求分析结果
        is_need_func_call_res = self.deepseek_func_needing(query)
        
        # 2. 提示生成：根据分析结果生成函数代码生成提示
        # 调用gen_fun方法生成包含函数定义要求的提示模板
        prompt_gen_fun = self.pmt.gen_fun(res_dict=is_need_func_call_res)

        # 3. 代码生成：通过AI模型生成完整的函数代码实现
        # 使用thinking方法让AI模型根据提示生成函数代码
        res = self.thinking(prompt_gen_fun,return_json=True)

        # 将生成的代码安全地追加到指定文件中
        append_code_to_file_safely(file_path=append_file_path,code_content=res['result'])
        

        # 4. 结果返回：返回生成的函数代码和相关信息
        # 返回结果包含：query、result（函数代码）、thinking等字段
        return res  

    def tongyi(self, prompt_user,
                prompt_system=None,
                models=['qwen3-coder-plus'],
                temperature=0,
                return_json=True):
        response = self.thinking(prompt_user=prompt_user, 
                                prompt_system=prompt_system,
                                response_format="text",
                                models=models,
                                temperature=temperature,
                                base_url=self._DASHSCOPE_BASE_URL,
                                api_key=self._DASHSCOPE_API_KEY,
                                return_json=return_json)
        return  response
    def tongyi_func_gen(self, query,models=['qwen3-coder-plus'],
                        append_file_path="/ai/wks/aitpf/src/tpf/cn/funcs.py"):
        """使用通义千问模型生成函数代码并保存到文件

        主要逻辑：
        1. 提示生成：根据用户问题生成函数代码生成提示
        2. 代码生成：调用通义千问模型生成函数代码
        3. 代码保存：将生成的代码安全地追加到指定文件中
        4. 结果返回：返回生成的函数代码和相关信息

        Args:
            query (str): 用户提出的问题字符串
            models (list, optional): 使用的通义千问模型列表，默认为['qwen3-coder-plus']
            append_file_path (str, optional): 代码保存路径，默认为"/ai/wks/aitpf/src/tpf/cn/funcs.py"

        Returns:
            dict: 包含生成的函数代码、tools_info和tools_mapping的结果字典

        """
        
        prompt = self.pmt.gen_fun(query=query)

        res = self.tongyi(prompt_user=prompt,models=models)

        # 将生成的代码安全地追加到指定文件中
        append_code_to_file_safely(file_path=append_file_path,code_content=res['result'])
        
        return res
