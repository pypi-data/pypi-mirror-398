
from tpf.llm import MyChat
chat = MyChat(env_file="env.txt")

prompt = """
生成一个可以将一段python代码(文本格式)追加到一个python文件尾部的python方法
- 在内部生成2-3个类似的方法，推荐出最好的1-2个方法
- 最终结果给出的只有1-2个方法
"""
res = chat.tongyi(prompt_user=prompt)



def append_code_to_file(file_path, code_content):
    """
    将Python代码追加到文件尾部
    
    Args:
        file_path (str): 目标Python文件路径
        code_content (str): 要追加的Python代码内容
    
    Returns:
        bool: 操作成功返回True，失败返回False
    """
    try:
        with open(file_path, 'a', encoding='utf-8') as file:
            # 确保代码内容以换行符结尾
            if not code_content.endswith('\n'):
                code_content += '\n'
            file.write(code_content)
        return True
    except Exception as e:
        print(f"追加代码到文件时出错: {e}")
        return False

def append_code_to_file_with_backup(file_path, code_content, create_backup=True):
    """
    将Python代码追加到文件尾部，可选择创建备份
    
    Args:
        file_path (str): 目标Python文件路径
        code_content (str): 要追加的Python代码内容
        create_backup (bool): 是否创建备份文件
    
    Returns:
        bool: 操作成功返回True，失败返回False
    """
    import shutil
    import os
    
    try:
        # 创建备份
        if create_backup and os.path.exists(file_path):
            backup_path = file_path + '.bak'
            shutil.copy2(file_path, backup_path)
        
        # 追加代码
        with open(file_path, 'a', encoding='utf-8') as file:
            if not code_content.endswith('\n'):
                code_content += '\n'
            file.write(code_content)
        return True
    except Exception as e:
        print(f"追加代码到文件时出错: {e}")
        return False

code_txt = res['result']
print(code_txt)
append_code_to_file_with_backup("/ai/wks/aitpf/src/tpf/cn/funcs_bak.py", res['result'])


