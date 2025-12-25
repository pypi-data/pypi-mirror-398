import os 
import pandas as pd 
import shutil

def file_move(source_file,destination_dir):
    """移动文件到另外一个目录
    - source_file:源文件路径
    - destination_dir:目标目录路径
    """

    # 确保目标目录存在，如果不存在则创建
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
    
    # 目标文件路径（包含文件名）
    destination_file = os.path.join(destination_dir, os.path.basename(source_file))
    
    # 移动文件
    try:
        shutil.move(source_file, destination_file)
        print(f"文件{source_file}已成功移动到 {destination_dir}")
    except Exception as e:
        print(f"移动文件时出错: {e}")
        
def csv_slice(csv_path, target_file, start_end_index=(0,1)):
    """大文件截取一个切片，便于开发测试使用
    """
    fil = pd.read_csv(csv_path)
    fil = fil.iloc[start_end_index[0]:start_end_index[1]]
    fil.to_csv(target_file,index=False)

def csv_slice_small(csv_path, target_dir, max_row_one_csv=100000):
    """
    将一个大的CSV文件拆分成一个个小的CSV文件
    """
    fil = pd.read_csv(csv_path)
    # print(fil.shape[0])
    (filepath, tempfilename) = os.path.split(csv_path)
    (filesname, extension) = os.path.splitext(tempfilename)
        
    
    all_row_counts = fil.shape[0]

    single_file_rows = max_row_one_csv 
    if all_row_counts > single_file_rows*3:  # 是批次的3倍才值得拆一下，1个多批次的数据合在一起计算就可以了
        start_index = 0
        while start_index < all_row_counts:
            end_index = start_index + single_file_rows

            if end_index > all_row_counts:
                end_index = all_row_counts

            one_batch_data = fil.iloc[start_index:end_index]
            one_csv_path = os.path.join(target_dir,"{}_{}_{}".format(filesname,start_index, end_index)+".csv")
            one_batch_data.to_csv(one_csv_path, index=False)
            start_index = end_index 
    else:
        start_index = 0
        end_index = all_row_counts
        one_csv_path = os.path.join(target_dir,"{}_{}_{}".format(filesname,start_index, end_index)+".csv")
        one_batch_data.to_csv(one_csv_path, index=False)
    


def mkdir(path):
	folder = os.path.exists(path)
	if not folder:                   #判断是否存在文件夹如果不存在则创建为文件夹
		os.makedirs(path)            #makedirs 创建文件时如果路径不存在会创建这个路径

def mkfil(fil):
    """
    创建文件
    """
    _file = open(fil,'w')
    _file.close()

def parentdir(fil):
    father_path=os.path.abspath(os.path.dirname(fil)+os.path.sep+".")
    return father_path


 
def load_file():
    # 获取当前文件路径
    current_path = os.path.abspath(__file__)
    # 获取当前文件的父目录
    father_path = os.path.abspath(os.path.dirname(current_path) + os.path.sep + ".")
    # config.ini文件路径,获取当前目录的父目录的父目录与congig.ini拼接
    config_file_path=os.path.join(os.path.abspath(os.path.dirname(current_path) + os.path.sep + ".."),'config.ini')
    print('当前目录:' + current_path)
    print('当前父目录:' + father_path)
    print('config.ini路径:' + config_file_path)

def filname_nosuffix(file_name):
    if os.path.exists(file_name):
       name_path = os.path.splitext(file_name)[0]  # 将文件名和扩展名(后缀)分开
       _name1 = os.path.split(name_path)[-1]
    return _name1  

def fil_suffix(file_name):
    """获取文件后缀
    """
    sfx = os.path.splitext(file_name)[1]  # 将文件名和扩展名(后缀)分开
    return sfx 

def rmfil(fil):
    if os.path.exists(r'{}'.format(fil)):
        shutil.rmtree(r'{}'.format(fil))


def write(text,file_name):              #定义函数名
    """
    写入少量内容到文件
    """
    # b = os.getcwd()[:-4] + 'new\\'
 
    if os.path.exists(file_name):     #判断当前路径是否存在，没有则创建new文件夹
        # os.makedirs(b)
 
        file = open(file_name,'w')
    
        file.write(text)        #写入内容信息
    
        file.close()

import time

# def log(msg, fil = "main.log"):
#     if fil:
#         log_file = fil
#     else:
#         log_file = "/tmp/main.log"
#     with open(log_file,"a+",encoding="utf-8") as f:
#         tim = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
#         f.write("[{}] {} \n".format(tim,msg))



def log(msg, fil, max_file_size=10*1024*1024):
    if fil:
        log_file = fil
    else:
        log_file = "./train.log"
    
    if os.path.exists(log_file):
        fil_size = os.path.getsize(log_file)
        if fil_size > max_file_size:
            # 写入空文件
            with open(log_file,"w",encoding="utf-8") as f:
                tim = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
                f.write("[{}] {} \n".format(tim,msg))
        else:
            with open(log_file,"a+",encoding="utf-8") as f:
                tim = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
                f.write("[{}] {} \n".format(tim,msg))
    else:
        with open(log_file,"w",encoding="utf-8") as f:
            tim = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
            f.write("[{}] {} \n".format(tim,msg))

# def lg(msg):
#     log_file_path = "../train.log"
#     # 超过max_file_size大小自动重写，即超过10M就自动清空一次
#     log(msg,fil=log_file_path,max_file_size=10485760)
    
    
# def lg2(smg, max_size=1024*1024, log_file = "./main.log"):
#     """指定文件大小的日志写
#     """
#     if os.path.exists(log_file):
#         siz = os.path.getsize(log_file)
#     else:
#         siz = 0
#     if siz>max_size:
#         with open(log_file,"w",encoding="utf-8") as f:
#             tim = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
#             f.write("[{}] {} \n".format(tim,smg))
#     else:
#         with open(log_file,"a+",encoding="utf-8") as f:
#             tim = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
#             f.write("[{}] {} \n".format(tim,smg))
            


def iswin():
    try:
        import platform
        if platform.system().lower() == 'windows':
            return True
        elif platform.system().lower() == 'linux':
            return False
    except:
        return True


from typing import Optional

def txt_contains(target: str,
                 file_path: str,
                 *,
                 is_line: bool = True,
                 encoding: str = 'utf-8') -> bool:
    """
    判断单列表格文件（仅一列）中是否存在目标字符串。

    参数
    ----
    target : str
        要查找的字符串
    file_path : str
        csv 文件路径
    is_line : bool, optional
        True  -> 整行精确匹配（默认）
        False -> 子串匹配（相当于 target in line）
    encoding : str, optional
        文件编码，默认 utf-8

    返回
    ----
    bool
        存在返回 True，否则 False
    """
    with open(file_path, 'r', encoding=encoding) as f:
        for line in f:
            line = line.rstrip('\n\r')   # 去掉换行符
            if is_line:
                if line == target:
                    return True
            else:
                if target in line:
                    return True
    return False




if __name__=="__main__":
    fil = "/opt/aisty/73_code/build/lib/aisty"
    rmfil(fil)
