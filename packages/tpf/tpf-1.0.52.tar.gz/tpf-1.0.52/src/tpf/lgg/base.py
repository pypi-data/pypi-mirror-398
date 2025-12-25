'''
Description: 基础方法,本文本不会引入外部自定义方法 
Author: 七三学徒
Date: 2022-01-14 12:54:34
FilePath: /73_code/aisty/lgg/base.py
'''


def replace_c(text):
    """
    文本过滤
    """
    # 将中文符号转化为英文符号
    intab = ",?!()"
    outtab = "，？！（）"    

    # 删除一些html的元素 
    deltab = " \n)(<li>< li>+_-.><li \U0010fc01 _"
    trantab=text.maketrans(intab, outtab,deltab)
    return text.translate(trantab)

def replace_c2(text):
    """
    文本过滤,没有删除空格与换行 
    """
    # 将中文的intab转化为英文的outtab 
    intab = ",?!()"
    outtab = "，？！（）"    

    # 删除一些html的元素 
    deltab = ")(<li><li>+_-.><li_\U0010fc01"
    trantab=text.maketrans(intab, outtab,deltab)
    return text.translate(trantab)

def replace_zh_flag(text):
    intab = ",?!"
    outtab = "，？！"    
    deltab = ")(+_-.>< "
    trantab=text.maketrans(intab, outtab,deltab)
    return text.translate(trantab)
