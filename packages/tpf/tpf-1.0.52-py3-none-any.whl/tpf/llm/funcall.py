from tpf.llm.tools import Tools
from tpf.llm.ollama import chat
from openai import OpenAI

import os,sys
import json
from typing import TypedDict
from openai import OpenAI

class FunctionCallingResult(TypedDict):
    name: str
    arguments: str
    

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv(filename="env.txt"))


def get_abs_path(file_path="."):
    """获取文件的绝对路径
    """
    import os
    abs_path = os.path.abspath(file_path) #获取当前文件的绝对路径
    return abs_path



# 给出工具定义，使用json格式详细描述函数的功能以及参数的个数与类型
tools_json = [
    # 每一个列表元素项，就是一个工具定义
    {
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
        },
        "function": get_abs_path
    }
]


class FuncCall(Tools):
    def __init__(self):
        """函数调用
        - 还差循环判断，可以反复调用函数，直到无函数可调用时结合循环，返回所有函数调用的结果列表
        """
        super().__init__()
        self._client = OpenAI()
        self._is_openai_funcalled = False
        
        self._function_infos = {}   #除了函数本身外的所有信息，名称，参数，描述等
        self._function_mappings = {}#函数本身，name:function 
        
        self._messages = []
        self.ollama_local_model_name = ['DeepSeek-14B-Q8:latest','DeepSeek-R1-14B-Q8:latest','DeepSeek-R1-14B-F16:latest']
        self._func_call_message = []
        self._json_parsing_feiled = False

        for func in tools_json:
            self.register_function(
                name=func["name"],
                function=func["function"],
                description=func["description"],
                parameters=func["parameters"])

    def register_function(self, *, name, description, parameters, function, **kwargs):
        #函数信息列表，最全的函数信息列表
        self._function_infos.update({
            name: {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                    **kwargs
                }
            }
        })
        
        #函数列表
        self._function_mappings.update({ name: function })

        # #函数名称及参数列表,简要信息
        # smp_func = { "name": name, "description": description,"arguments":parameters }
        # self.func_name_list.append(smp_func)

        return self
        
    def get_tool_list(self):
        """工具列表，合并自带工具以及注册工具
        
        """
        tools = []
        tools.extend(self._function_infos.values()) 
        tools.extend(self.tool_list) 
        return tools
        
    def reset_messages(self,messages=None):
        if messages is None:
            self._messages = []
        else:
            self._messages = messages
        return self

    def append_message(self, role, content, **kwargs):
        self._messages.append({ "role": role, "content": content, **kwargs })
        print("[Processing Messages]:", self._messages[-1])
        return self
        
    def _call(self, function_calling_result:FunctionCallingResult):
        """openai格式调用函数"""
        function = self._function_mappings[function_calling_result.name]
        arguments = json.loads(function_calling_result.arguments)
        return function(**arguments)


    def _request(self, *, model_name="gpt-4o",base_url=None,api_key=None):
        """openai格式http请求"""
        # if role and content:
        #     self._messages.append({ "role": role, "content": content })
        
        if base_url is None:
            client = self._client
        else:
            client = OpenAI(
                base_url=base_url,
                api_key=api_key,    #必需但可以随便填写
            )
        result = client.chat.completions.create(
            model=model_name,
            messages=self._messages,
            tools=self.get_tool_list(),
        )

        completion = result
        if completion.choices is None:
            print(completion.error["message"])
        else:
            message = completion.choices[0].message
            response = message.content
            # print("outer api:\n",response)

            self.append_message(**dict(message))
            if message.tool_calls:
                for tool_call in message.tool_calls:  #返回的是工具列表
                    call_result = self._call(tool_call.function)
                    self.append_message("tool", str(call_result), tool_call_id=tool_call.id)
                    self._is_openai_funcalled = True
                # return self._request(model_name=model_name)    #将所有函数调用的结果加入消息后，最后又执行了一次请求，这次是要整合所有内容做一个统一的答复
            else:
                self.append_message("assistant", result.choices[0].message.content)
                self._is_openai_funcalled = False
            return message.content

    
    def tools_call(self, txt):
        """函数调用
        - 由大模型判断是否需要函数后，若有需要，由该方法解析其中的函数，并进行调用，且返回调用的结果 
        - txt:LLM识别是否需要func call的返回文本
        
        """
        try:
            
            json_str = self.get_json_str(txt)

            # 将JSON字符串转换为Python字典
            # print("begin change this text to json:\n",json_str)
            json_dict = json.loads(json_str)
            # print("22:\n",json_dict)
        
        except Exception as e:
            print(e)
            print("response text:\n",txt)
            # print("json parsing:\n",json_dict)
            self._json_parsing_feiled = True
            print("以上文本解析失败")
            sys.exit()
            # return []
        
        
        for func in json_dict:  #返回的是工具列表
            # print("func :\n",func)
            func_name = func["name"]
            arguments = func["arguments"]
            print(func_name,arguments)
            f = self._function_mappings[func_name]
            
            call_result = f(**arguments)
            # print(f"函数描述description")
            if "description" in func.keys():
                description = func["description"]
                # 添加函数说明，汇总最终结果时，帮助大模型理解上下文含义
                elem = {"函数名称name":func_name, "函数描述description":description, "函数回调结果func_call_result":call_result}
            else:
                elem = {"函数名称name":func_name, "函数回调结果func_call_result":call_result}
            print("func res:\n",elem)
            
            self._func_call_message.append(elem)
            
        return self._func_call_message
        

        # if len(json_dict)>0:
            

        #     if json_dict["name"] == 'get_abs_path':
        #         params = json_dict["parameters"]
        #         if len(params) ==0:
        #             file_path = ""
        #         elif len(params) ==1:
        #             values = list(dict(params).values())
        #             file_path = values[0]
        #         elif isinstance(params,dict) and "file_path" in params.keys() :
        #             file_path = params["file_path"]
        #             if isinstance(file_path,dict) and len(file_path) == 0:
        #                 file_path = ""
        #         elif isinstance(params,list)  :
        #             file_path = params[0]
        #             if file_path == "relative_path":
        #                 file_path = ""
        #         else:
        #             print(json_dict)
        #             raise Exception(f"func get_abs_path, file_path not in {params}")
        #         path = get_abs_path(file_path)
        #         # print(path)
        #         return path
            
                
        # else:
        #     print("No custom functions called")
        #     return ""
            

    def set_ollama_local_model(self,model_name):
        """添加本地ollama模型名称"""
        self.ollama_local_model_name.append(model_name)
        
    def prompt_system(self):
        """系统任务/角色描述"""
        # 任务描述
        instruction = """
        你的任务是识别回答用户问题是否需要调用指定的函数，如果需要则返回一个函数列表，告诉用户需要调用的函数名称以及函数参数，列表中每个元素如下：
        1. 函数名称name,函数列表中name的值；如果要列举的函数名称在指定的函数列表中不存在，则不要显示该函数
        2. 函数参数arguments,对应函数列表中parameters
        3. 函数描述description，可以通过函数列表中字典元素description的值确定函数的用途，与当前用户问题的匹配程度


        """
        
        # 输出格式增加了各种定义、约束
        output_format = """
        输出为一个函数列表，包含在```json ```标记中，列表元素为需要回答用户问题涉及的函数信息，列表中每个元素是一个JSON Object，包含的字段有：
        1. name字段的取值为string类型，取值必须为函数列表中某个元素name的值或null
        (1)如果不需要函数调用，或者没有函数调用时，则JSON输出为空
        2. arguments字段
        (1) 字典类型，但其中的key与value皆是字符串类型
        (2) 如果确定使用函数，格式为函数元素parameters.properties字段的说明来初始化该字段 
        3.description字段，其值为函数列表中对应函数description的值
        JSON输出中包含"name","arguments","description"三个字段，
          3.1 如果没有arguments字段，则找到上下文内容确定arguments的取值 
          3.2 输出包含 description字段字段，若不存在该字段，则从函数列表找对应函数的描述description的值
        
        """
        func_list = self.get_tool_list()
        # prompt 模版。instruction 和 input_text 会被替换为上面的内容
        
        prompt_system = f"""
        # 主要任务
        {instruction}

        # 如果需要额外的函数调用才能回答该问题，则从下面给出的"函数列表"中选择出最合适的函数反馈回来
        # 函数列表如下:
        {func_list}

        # 输出格式:
        {output_format}
        # examples:
        [
        {{
            "name": "get_abs_path",
            "arguments": {{
                "file_path": "."
            }},
            "description": "获取文件的绝对路径"
        }}
        ]

        """
        return prompt_system
    
    def prompt_user(self, query, output_format=None, use_custom_func=True):
        """
        - output_format:函数回调输出格式，如果使用自定义函数则要考虑与自定义函数的格式匹配
        - use_custom_func:没有使用openai格式的tools，而是自定义了函数调用，这时，会使用符合自定义函数的output_format输出格式
        """
        func_name_list = self.get_tool_list()
        if output_format is None and use_custom_func:
            # 输出格式增加了各种定义、约束
            output_format = """
            输出为一个函数列表，包含在```json ```标记中，列表元素为需要回答用户问题涉及的函数信息，列表中每个元素是一个JSON Object，包含的字段有：
            1. name字段的取值为string类型，取值必须为函数列表中某个元素name的值或null
            (1)如果不需要函数调用，或者没有函数调用时，则JSON输出为空
            2. arguments字段
            (1) 字段类型为字典，但其中的key与value皆是字符串类型
            (2) 如果确定使用函数，请参考所使用函数元素parameters字段的说明来初始化该字段 
            3. description字段，其值为函数列表中对应函数description的值
            输出包含arguments字段字段，若不存在该字段，则重新思考以确定arguments字段的取值
            输出包含 description字段字段，若不存在该字段，则从"函数列表"找对应函数的描述description的值
            
            """

        
        # prompt 模版。instruction 和 input_text 会被替换为上面的内容
        prompt_user = f"""
        #输出格式
        {output_format}

        #输出前的思考：
        1. 重新确认本功能所能够使用的工具：{func_name_list}
        2. 不要自己指定工具，检查自己选择的工具是否在{func_name_list}中,只能选择这其中的工具
        3. 函数输出为json格式，json内容包含在```json ```标记中，
        4. 确保所调用函数的name与arguments存在，且再次确认arguments字段是否满足JSON格式输出的要求
        5. 最后，确保输出严格按照指定的格式编写，即用```json ```包裹，并且正确使用双引号和换行符。不需要额外添加其他内容，简洁明了即可。

        用户输入：
        {query}
        """
        return prompt_user
    
    def get_messages(self, query, output_format=None, use_custom_func=True):
        """
        - use_custom_func: 除了open ai func call相关函数，也有自定义func call
        
        """
        """带func calling的消息模板"""
        prompt_system = self.prompt_system() 
        prompt_user = self.prompt_user(query=query, output_format=output_format, use_custom_func=use_custom_func)
        message = [
            {
                "role": "system",
                "content": prompt_system  # 注入新知识
            },
            {
                "role": "user",
                "content": prompt_user  # 问问题
            },
        ]
        return message 

    def func_call(self, query, model_list=["gpt-4o-mini",'DeepSeek-14B-Q8:latest'], 
                  model_index=1, use_custom_func=True,output_format=None,base_url=None,api_key=None):
        """
        - query:用户提问
        - model_index为model_list的索引，若以deepseek开头，则走自定义func call 
        
        """
        func_call_res = ''
        model_name = model_list[model_index]
        # if model_name.lower().startswith("deepseek") or (model_name in self.ollama_local_model_name):
        if model_name in self.ollama_local_model_name:
            prompt_system = self.prompt_system() 
            prompt_user = self.prompt_user(query=query, output_format=output_format, use_custom_func=use_custom_func)
            response = chat(prompt_user=prompt_user,prompt_system=prompt_system,model=model_name, )
            print("before tools call,func list:\n",response)
            func_call_res = self.tools_call(response)
            print("func call res:",func_call_res)
        else:
            messages   = self.get_messages(query=query,use_custom_func=use_custom_func)
            self.reset_messages(messages)
            response = self._request(model_name=model_name,base_url=base_url,api_key=api_key)
            if self._is_openai_funcalled:
                return self._messages 
            if (not self._is_openai_funcalled) and use_custom_func:
                print("No openai function is called... start customizing function calls...")
                func_call_res = self.tools_call(response)  #Tools中的func_call
                # print(func_call_res)
        return func_call_res
        
    def chat(self, query, model_list=["gpt-4o-mini",'DeepSeek-14B-Q8:latest'], 
             func_index=1, answer_index=None, use_custom_func=True, 
             output_format=None,base_url=None,api_key=None):
        """
        - query:用户提问
        - func_index:函数调用所使用的model索引
        - answer_index:函数调用之后整合回答所使用的模型索引，仅限本地模型，输入外部API调用会报错;若为None则没有第2步的问题整合
        - model_index为model_list的索引，若以deepseek开头，则走自定义func call 
        
        
        examples
        ------------------------------------
        response = fc.chat(query=prompt, model_list=["gpt-4o-mini",'DeepSeek-14B-Q8:latest'], func_index=0,answer_index=1, use_custom_func=True, output_format=None, )
        print(response)
        
        """
        
        func_call_res = self.func_call(query=query, 
                                       model_list=model_list, model_index=func_index, 
                                       use_custom_func=use_custom_func,
                                       output_format=output_format,base_url=base_url,api_key=api_key)
        if self._json_parsing_feiled: #如果文本解析失败，则再尝试一次，但也仅尝试一次
            func_call_res = self.func_call(query=query, 
                                       model_list=model_list, model_index=func_index, 
                                       use_custom_func=use_custom_func,
                                       output_format=output_format,base_url=base_url,api_key=api_key)
            self._json_parsing_feiled = False

        if answer_index is None:
            return func_call_res
            # model_answer = model_list[func_index]
        else:
            model_answer = model_list[answer_index]
        if output_format is None:
                output_format = """
#最终回答格式为JSON，格式为{"query":,"result":""},请根据上下文内容填充这个JSON
以JSON格式输出且输出的json内容包含在```json ```标记中。包含的字段有：
1. query字段，取值为string类型，取值为用户的问题
2. result字段,string类型，取值为用户问题的答案"""

        prompt_answer = f"""
        #用户输入：
        {query}
        
        #内部函数调用返回的结果
        {func_call_res}
        
        请结合用户输入的问题以及内部函数调用返回结果回答,
        - 简洁风格，针对问题与返回结果做一个总结，不扩展思考新的解决方案，不思考，不推理
        
        #输出格式
        {output_format}
        """
        
        if self._is_openai_funcalled:
            prompt_system=None
        else:#  自定义流程中message无system角色，因此可以重定义一下
            prompt_system = f"""
你的任务是根据以下内容回答用户的问题
最终回答格式为JSON，格式为{{query:用户问题,result:答案}},请根据上下文内容填充这个JSON
依据提供的上下文内容，主要是函数调用的返回结果，不要猜测或推理任何未直接提及的字段或内容
但至少两个字段
1. query字段，string类型，代表用户问题
2. result字段,string类型，代表答案

examples:
{{
    "query": "用户的问题是什么？",
    "result": "返回的结果是什么。"
}}
因此，请按照上述格式输出。"""
        print("开始总结并给出最终结果...")
        response = chat(prompt_user=prompt_answer, prompt_system=prompt_system, 
                        model=model_answer,base_url=base_url,api_key=api_key)
        return response
                
            
            
    def chat_func_prompt(self, query, model_list=["gpt-4o-mini",'DeepSeek-14B-Q8:latest'], 
             func_index=1, use_custom_func=True, output_format=None,base_url=None,api_key=None):
        """
        - query:用户提问
        - func_index:函数调用所使用的model索引
        - answer_index:函数调用之后整合回答所使用的模型索引，仅限本地模型，输入外部API调用会报错;若为None则没有第2步的问题整合
        - model_index为model_list的索引，若以deepseek开头，则走自定义func call 
        
        
        examples
        ------------------------------------
        response = fc.chat(query=prompt, model_list=["gpt-4o-mini",'DeepSeek-14B-Q8:latest'], func_index=0,answer_index=1, use_custom_func=True, output_format=None, )
        print(response)
        
        """
        
        func_call_res = self.func_call(query=query, 
                                       model_list=model_list, model_index=func_index, 
                                       use_custom_func=use_custom_func,
                                       output_format=output_format,base_url=base_url,api_key=api_key)
        if self._json_parsing_feiled: #如果文本解析失败，则再尝试一次，但也仅尝试一次
            func_call_res = self.func_call(query=query, 
                                       model_list=model_list, model_index=func_index, 
                                       use_custom_func=use_custom_func,
                                       output_format=output_format)
            self._json_parsing_feiled = False

        if output_format is None:
                output_format = """
#最终回答格式为JSON，格式为{"query":,"result":""},请根据上下文内容填充这个JSON
以JSON格式输出且输出的json内容包含在```json ```标记中。包含的字段有：
1. query字段，取值为string类型，取值为用户的问题
2. result字段,string类型，取值为用户问题的答案"""

        prompt_answer = f"""
        #用户输入：
        {query}
        
        #内部函数调用返回的结果
        {func_call_res}
        
        请结合用户输入的问题以及内部函数调用返回结果回答,
        - 简洁风格，针对问题与返回结果做一个总结，不扩展思考新的解决方案，不思考，不推理
        
        #输出格式
        {output_format}
        """
        
        if self._is_openai_funcalled:
            prompt_system=None
        else:#  自定义流程中message无system角色，因此可以重定义一下
            prompt_system = f"""
你的任务是根据以下内容回答用户的问题
最终回答格式为JSON，格式为{{query:用户问题,result:答案}},请根据上下文内容填充这个JSON
依据提供的上下文内容，主要是函数调用的返回结果，不要猜测或推理任何未直接提及的字段或内容
但至少两个字段
1. query字段，string类型，代表用户问题
2. result字段,string类型，代表答案

examples:
{{
    "query": "用户的问题是什么？",
    "result": "返回的结果是什么。"
}}
因此，请按照上述格式输出。"""
        print("开始总结并给出最终结果...")
        return prompt_answer,prompt_system

                
           
