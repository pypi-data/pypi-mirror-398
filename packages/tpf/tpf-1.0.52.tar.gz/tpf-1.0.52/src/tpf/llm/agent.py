
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv(filename="env.txt"))

import os
import json
from openai import OpenAI
import Agently

# 使用nest_asyncio确保异步稳定性
import nest_asyncio
nest_asyncio.apply()

class Agent:
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
        

    def openai(self, query, model_list=["gpt-4o-mini"]):
        """使用agent回答问题
        """
        agent = (
            Agently.create_agent(is_debug=True)
                .set_settings("current_model", "OpenAI")
                .set_settings("model.OpenAI.url", self.OPENAI_BASE_URL)
                .set_settings("model.OpenAI.auth", { "api_key": self.OPENAI_API_KEY  })
                .set_settings("model.OpenAI.options", { "model": model_list[0] })
        )

        agent.input(query).start()
        
        
    def _agent_openai(self, model_list=["gpt-4o-mini"]):
        """使用agent回答问题
        """
        agent = (
            Agently.create_agent(is_debug=True)
                .set_settings("current_model", "OpenAI")
                .set_settings("model.OpenAI.url", self.OPENAI_BASE_URL)
                .set_settings("model.OpenAI.auth", { "api_key": self.OPENAI_API_KEY  })
                .set_settings("model.OpenAI.options", { "model": model_list[0] })
        )
        return agent
    
    def _agent_deepseek(self, model_list=['deepseek-chat','deepseek-reasoner']):
        """使用agent回答问题
        """
        agent = (
            Agently.create_agent(is_debug=True)
                .set_settings("current_model", "OpenAI")
                .set_settings("model.OpenAI.url", self._deepseek_base_url)
                .set_settings("model.OpenAI.auth", { "api_key": self._deepseek_api_key  })
                .set_settings("model.OpenAI.options", { "model": model_list[0] })
        )
        return agent
    
    
    
    






