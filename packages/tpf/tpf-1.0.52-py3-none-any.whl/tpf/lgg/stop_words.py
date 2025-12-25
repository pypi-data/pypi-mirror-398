

def stop_word_list(stpwrdpath):
    #从文件导入停用词表
    stpwrd_dic = open(stpwrdpath, 'rb')
    stpwrd_content = stpwrd_dic.read()
    #将停用词表转换为list  
    stpwrdlst = stpwrd_content.splitlines()
    stpwrd_dic.close()
    return stpwrdlst 

def get_stwd_1():
    """
    中文停用词列表 1 
    """
    word1 = "/opt/aisty/73_code/data/text/stop_words/ChineseStopWords.txt"
    ll = stop_word_list(word1)
    return ll

if __name__=="__main__":
    ll = get_stwd_1()
    print(ll[:30])


