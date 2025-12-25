import subprocess, tempfile, os
import ast

def exec_shell_code(cmd_list=['ls', '-l']):
    # 调用本地shell命令
    result = subprocess.run(cmd_list, capture_output=True, text=True)

    # 输出结果
    print(result.stdout)

def exec_python_code(source):
    """执行python代码并返回结果 
    
    exampels
    --------------------------------------
    source = '''
    import pandas as pd
    df = pd.DataFrame({'a':[1,2], 'b':[3,4]})
    print(df.shape)
    '''
    exec_python_code(source)
    
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(source)
        f.flush()
        fname = f.name
    
    try:
        proc = subprocess.run(
            ['python', fname],
            capture_output=True,
            text=True,
            timeout=10          # 防止死循环
        )
        if proc.returncode == 0:
            res = proc.stdout
            s = res.rstrip('\n')
            res ={"status":"ok","result":s}
        else:
            res ={"status":"error","result":proc.stderr} 
    finally:
        os.remove(fname)
    return res
        

def test_exec_python_code():
    source = '''
    import pandas as pd
    df = pd.DataFrame({'a':[1,2], 'b':[3,4]})
    print(df.shape)
    '''
    exec_python_code(source)
    
    
def check_grammar_noexec(code):
    """仅语法检查不执行
    - 正常返回'ok' 
    - 异常返回具体的错误字符串
    
    exampels
    --------------------------------------
    code = '''
    def f(a, b):
        return a+b -
    '''
    check_grammar_noexec(code)
    
    """
    try:
        ast.parse(code)          # 只解析，不执行
        res ={"status":"ok"}
    except SyntaxError as e:
        res ={"status":"error","result":f"{e}"}
    return res
    
    
def test_check_grammar_noexec():
    code = '''
    def f(a, b):
        return a+b -
    '''
    check_grammar_noexec(code)


    
