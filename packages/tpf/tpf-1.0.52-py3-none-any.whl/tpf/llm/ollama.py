from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv(filename="env.txt"))

from openai import OpenAI

def client_ollama(base_url='http://localhost:11434/v1/'):
    client = OpenAI(
        base_url=base_url,
        api_key='key',#必需但可以随便填写
    )
    return client


def chat_ollama(prompt, response_format="text", model='deepseek-r1:1.5b',temperature=0,base_url='http://localhost:11434/v1/'):
    client = OpenAI(
        base_url=base_url,
        api_key='key',#必需但可以随便填写
    )
    
    response = client.chat.completions.create(
        model=model,
        messages=[{'role': 'user','content': prompt,}],
        temperature=temperature,   # 模型输出的随机性，0 表示随机性最小
        # 返回消息的格式，text 或 json_object
        response_format={"type": response_format},
    )

    if response.choices is None:
        err_msg = response.error["message"]
        raise Exception(f"{err_msg}")

    return response.choices[0].message.content          # 返回模型生成的文本



def chat(prompt_user, prompt_system=None, 
         response_format="text", 
         model='deepseek-r1:1.5b', 
         temperature=0, 
         base_url='http://localhost:11434/v1/',api_key='key'):
    """大模型对话问答

    
    params
    --------------------------------
    - prompt_user:用户prompt 
    - prompt_system:系统prompt，，默认None 
    = response_format:'json_object'或'text'
    - model:模型路径，如果是ollama，可通过ollama list查看模型名称
    - temperature: 温度系数，默认1 
    - base_url：LLM http地址
    
    examples
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
    
    """
    client = OpenAI(
        base_url=base_url,
        api_key=api_key,    #必需但可以随便填写
    )
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

    return response.choices[0].message.content          # 返回模型生成的文本

