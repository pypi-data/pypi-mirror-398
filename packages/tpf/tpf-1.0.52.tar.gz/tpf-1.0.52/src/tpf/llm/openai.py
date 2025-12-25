from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv(filename="env.txt"))

import os
import json
from openai import OpenAI

from tpf.llm.prompt import return_json1 
from tpf.llm.tools import Tools 
from tpf.llm.funcall import FuncCall

tools = Tools()

def chat(prompt_user, prompt_system=None, 
         response_format="text", 
         model='deepseek-r1:1.5b', 
         temperature=1, 
         base_url='http://localhost:11434/v1/',api_key='key',
         return_json=False):
    """大模型对话问答

    params
    --------------------------------
    - prompt_user:用户prompt 
    - prompt_system:系统prompt，，默认None 
    = response_format:'json_object'或'text'
    - model:模型路径，如果是ollama，可通过ollama list查看模型名称
    - temperature: 温度系数，默认1 
    - base_url：LLM http地址
    
    example 1 local 
    -------------------------------
    from tpf.llm import chat
    prompt = "你好"
    response = chat(prompt_user=prompt, 
                    prompt_system=None, 
                    response_format="text", 
                    model='deepseek-r1:1.5b', 
                    temperature=1, 
                    base_url='http://localhost:11434/v1/')
    print(response)
    
    
    
    example 2 online  
    -------------------------------
    import os
    from dotenv import load_dotenv  
    load_dotenv("/home/llm/conf/env.txt")  # 加载".env"文件 
    deepseek_base_url = os.getenv("deepseek_base_url")  
    deepseek_api_key = os.getenv("deepseek_api_key")  
    
    from tpf.llm import chat
    prompt = "你好"
    response = chat(prompt_user=prompt, 
                    prompt_system=None, 
                    model='deepseek-chat', 
                    temperature=1, 
                    base_url=deepseek_base_url,
                    api_key=deepseek_api_key,
                    return_json=True)
    response

    
    
    """
    client = OpenAI(
        base_url=base_url,
        api_key=api_key,    #必需但可以随便填写
    )
    
    if return_json:
        output_format1 = return_json1()
        prompt_user = f"""
        {prompt_user}
        
        {output_format1}
        """
    
    if prompt_system is None:
        message = [{'role': 'user','content': prompt_user,}]
    else:
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

    response = client.chat.completions.create(
        model=model,
        messages=message,
        temperature=temperature,   # 模型输出的随机性，0 表示随机性最小
        # 返回消息的格式，text 或 json_object
        response_format={"type": response_format},
    )

    if response.choices is None:
        err_msg = response.error["message"]
        raise Exception(f"{err_msg}")
    
    content = response.choices[0].message.content
    if return_json:
        try:
            json_str = tools.get_json_str(content)
            json_dict = json.loads(json_str)
            is_parse_ok = True 
        except Exception as e:
            print(e)
            is_parse_ok = False 
            
        if is_parse_ok:
            return json_dict

    return content          # 返回模型生成的文本



class MyChat():
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
        
        
        
        self.fc = FuncCall() 
        
    def set_local_model(self,model_name_list):
        """添加本地ollama模型名称"""
        for model_name in model_name_list:
            self.fc.set_ollama_local_model(model_name)
        
    def get_local_model(self):
        return self.fc.ollama_local_model_name
        
    def func_call(self,query,
                  model_list=["gpt-4o-mini","gpt-4o",'DeepSeek-R1-14B-Q8:latest','DeepSeek-R1-14B-F16:latest'],
                   func_index=3, answer_index=2,base_url='http://localhost:11434/v1/',api_key='key'):
        res = self.fc.chat(query=query, 
                     model_list=model_list, func_index=func_index, answer_index=answer_index,base_url=base_url,api_key=api_key)

        return res 
    
    def tongyi(self, prompt_user,
                prompt_system=None,
                models=['qwen3-coder-plus'],
                temperature=0,
                return_json=True):
        response = chat(prompt_user=prompt_user,
                prompt_system=prompt_system,
                model=models[0],
                temperature=temperature,
                base_url=self._DASHSCOPE_BASE_URL,
                api_key=self._DASHSCOPE_API_KEY,
                return_json=return_json)
        return  response

    def tongyi_func_call(self, query, model_list=['qwen3-coder-plus','qwen-max','qwen-plus','DeepSeek-R1-14B-Q8:latest','DeepSeek-R1-14B-F16:latest'],
             func_index=0, answer_index=None, use_custom_func=True,
             output_format=None):
        if answer_index or answer_index is not None:
            ans_model = model_list[answer_index]
            if ans_model in self.get_local_model(): #使用本地模型整合
                response = self.fc.chat(query, model_list=model_list,
                            func_index=func_index, answer_index=answer_index,
                            use_custom_func=use_custom_func, output_format=output_format,
                            base_url=self._DASHSCOPE_BASE_URL,api_key=self._DASHSCOPE_API_KEY)
                return response
        ##使用在线模型整合
        prompt_answer,prompt_system = self.fc.chat_func_prompt(query, model_list=model_list,
                    func_index=func_index,
                    use_custom_func=use_custom_func, output_format=output_format,
                    base_url=self._DASHSCOPE_BASE_URL,api_key=self._DASHSCOPE_API_KEY)

        ans_model = model_list[func_index]
        response = self.tongyi(prompt_user=prompt_answer,
            prompt_system=prompt_system,
            models=[ans_model],
            temperature=0,
            return_json=True)

        return response
 

    
    def qianfan(self, prompt_user, 
                prompt_system=None, 
                models=['ernie-4.5-turbo-128k','ernie-4.5-turbo-vl','ernie-4.0-turbo-8k'], 
                temperature=0, 
                return_json=True):
        """
        - models:默认使用model[0]，使用时调整其顺序即可
        - temperature：[0,1]
        - return_json：
            输出格式：json格式，包含在```json ```标记中，
                1. query字段，string类型，其value为用户的问题
                2. result字段，string类型，其value为最终回复结果
                3. thinking字段，list类型，
                3.1 列表元素为大模型的思考步骤，按思考顺序整理为list列表；
                3.2 若无思考步骤，则列表为空
        """
        response = chat(prompt_user=prompt_user, 
                prompt_system=prompt_system, 
                model=models[0], 
                temperature=temperature, 
                base_url=self._qianfan_base_url,
                api_key=self._qianfan_api_key,
                return_json=return_json)
        return  response
    def qianfan_func_call(self, query, model_list=['ernie-4.5-turbo-128k','ernie-4.5-turbo-vl','ernie-4.0-turbo-8k','DeepSeek-R1-14B-Q8:latest','DeepSeek-R1-14B-F16:latest'], 
             func_index=0, answer_index=None, use_custom_func=True, 
             output_format=None):
        if answer_index or answer_index is not None:
            ans_model = model_list[answer_index]
            if ans_model in self.get_local_model(): #使用本地模型整合
                response = self.fc.chat(query, model_list=model_list, 
                            func_index=func_index, answer_index=answer_index, 
                            use_custom_func=use_custom_func, output_format=output_format,
                            base_url=self._qianfan_base_url,api_key=self._qianfan_api_key)
                return response 
        ##使用在线模型整合
        prompt_answer,prompt_system = self.fc.chat_func_prompt(query, model_list=model_list, 
                    func_index=func_index, 
                    use_custom_func=use_custom_func, output_format=output_format,
                    base_url=self._qianfan_base_url,api_key=self._qianfan_api_key)

        ans_model = model_list[func_index]
        response = self.qianfan(prompt_user=prompt_answer, 
            prompt_system=prompt_system, 
            models=[ans_model], 
            temperature=0, 
            return_json=True)

        return response 
    
    def deepseek(self, prompt_user, 
                prompt_system=None, 
                models=['deepseek-chat','deepseek-reasoner'], 
                temperature=0, 
                return_json=True):
        """
        - models:默认使用model[0]，使用时调整其顺序即可
        - temperature：[0,1]
        - return_json：
            输出格式：json格式，包含在```json ```标记中，
                1. query字段，string类型，其value为用户的问题
                2. result字段，string类型，其value为最终回复结果
                3. thinking字段，list类型，
                3.1 列表元素为大模型的思考步骤，按思考顺序整理为list列表；
                3.2 若无思考步骤，则列表为空
        """
        response = chat(prompt_user=prompt_user, 
                prompt_system=prompt_system, 
                model=models[0], 
                temperature=temperature, 
                base_url=self._deepseek_base_url,
                api_key=self._deepseek_api_key,
                return_json=return_json)
        return  response
    
    def deepseek_func_call(self, query, model_list=['deepseek-chat','deepseek-reasoner','DeepSeek-R1-14B-Q8:latest','DeepSeek-R1-14B-F16:latest'], 
             func_index=0, answer_index=None, use_custom_func=True, 
             output_format=None):
        if answer_index or answer_index is not None:
            ans_model = model_list[answer_index]
            if ans_model in self.get_local_model(): #使用本地模型整合
                response = self.fc.chat(query, model_list=model_list, 
                            func_index=func_index, answer_index=answer_index, 
                            use_custom_func=use_custom_func, output_format=output_format,
                            base_url=self._deepseek_base_url,api_key=self._deepseek_api_key)
                return response 
        ##使用在线模型整合
        prompt_answer,prompt_system = self.fc.chat_func_prompt(query, model_list=model_list, 
                    func_index=func_index, 
                    use_custom_func=use_custom_func, output_format=output_format,
                    base_url=self._deepseek_base_url,api_key=self._deepseek_api_key)

        ans_model = model_list[func_index]
        response = self.deepseek(prompt_user=prompt_answer, 
            prompt_system=prompt_system, 
            models=[ans_model], 
            temperature=0, 
            return_json=True)

        return response 
    
    
    
    def openai(self, prompt_user, 
                prompt_system=None, 
                models=["gpt-4o","o1-mini-2024-09-12"], 
                temperature=0, 
                return_json=True):
        """
        - models:默认使用model[0]，使用时调整其顺序即可
        - return_json：
            输出格式：json格式，包含在```json ```标记中，
                1. query字段，string类型，其value为用户的问题
                2. result字段，string类型，其value为最终回复结果
                3. thinking字段，list类型，
                3.1 列表元素为大模型的思考步骤，按思考顺序整理为list列表；
                3.2 若无思考步骤，则列表为空
        """
        response = chat(prompt_user=prompt_user, 
                prompt_system=prompt_system, 
                model=models[0], 
                temperature=temperature, 
                base_url=self.OPENAI_BASE_URL,
                api_key=self.OPENAI_API_KEY,
                return_json=return_json)
        return  response
    
    def openai_func_call(self, query, model_list=["gpt-4o-mini","gpt-4o",'DeepSeek-R1-14B-Q8:latest','DeepSeek-R1-14B-F16:latest'], 
             func_index=0, answer_index=0, use_custom_func=True, output_format=None,):
        if answer_index or answer_index is not None:
            ans_model = model_list[answer_index]
            if ans_model in self.get_local_model(): #使用本地模型整合
                response = self.fc.chat(query, model_list=model_list, 
                            func_index=func_index, answer_index=answer_index, 
                            use_custom_func=use_custom_func, output_format=output_format)
                return response 
        ##使用在线模型整合
        prompt_answer,prompt_system = self.fc.chat_func_prompt(query, model_list=model_list, 
                    func_index=func_index, 
                    use_custom_func=use_custom_func, output_format=output_format)

        ans_model = model_list[func_index]
        response = self.openai(prompt_user=prompt_answer, 
            prompt_system=prompt_system, 
            models=[ans_model], 
            temperature=0, 
            return_json=True)

        return response 
    
    def ollama(self,prompt_user, prompt_system=None, 
               model=["DeepSeek-R1-32B-Q8:latest","DeepSeek-R1-32B-Q6:latest","DeepSeek-R1-14B-F16:latest","DeepSeek-R1-14B-Q8:latest"], 
               temperature=0,base_url='http://localhost:11434/v1/',return_json=True):
        """
        - models:默认使用model[0]，使用时调整其顺序即可
        - return_json：
            输出格式：json格式，包含在```json ```标记中，
                1. query字段，string类型，其value为用户的问题
                2. result字段，string类型，其value为最终回复结果
                3. thinking字段，list类型，
                3.1 列表元素为大模型的思考步骤，按思考顺序整理为list列表；
                3.2 若无思考步骤，则列表为空
        """
        res = chat(prompt_user=prompt_user, prompt_system=prompt_system, temperature=temperature, 
           model=model[0],
           base_url=base_url,api_key='key',return_json=return_json)
        return res  
    
    
    def register_function(self, name, description, parameters, function, **kwargs):
        return self.fc.register_function(name=name, description=description, parameters=parameters, function=function, **kwargs)

    
    def prompt_system(self):
        return self.fc.prompt_system()
    
    def tool_list(self):
        return self.fc.get_tool_list()
    
    





global client 
client = None





# 基于 prompt 生成文本
# gpt-3.5-turbo 
def get_completion(prompt, response_format="text", model="gpt-4o-mini"):
    
    global client 
    if not client:
        # 初始化 OpenAI 客户端
        client = OpenAI()  # 默认使用环境变量中的 OPENAI_API_KEY 和 OPENAI_BASE_URL

    messages = [{"role": "user", "content": prompt}]    # 将 prompt 作为用户输入
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,                                  # 模型输出的随机性，0 表示随机性最小
        # 返回消息的格式，text 或 json_object
        response_format={"type": response_format},
    )

    if response.choices is None:
        err_msg = response.error["message"]
        raise Exception(f"{err_msg}")

    return response.choices[0].message.content          # 返回模型生成的文本


def chat_openai(prompt, response_format="text", model="gpt-4o-mini"):
    """对话
    - prompt:输入文本
    - response_format:text,json_object
    
    """
    return get_completion(prompt, response_format, model)




def chat_stream(msg,model="gpt-4o-mini"):
    global client 
    if not client:
        # 初始化 OpenAI 客户端
        client = OpenAI()  # 默认使用环境变量中的 OPENAI_API_KEY 和 OPENAI_BASE_URL

    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": msg}],
        stream=True,
    )
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="")
            
            
