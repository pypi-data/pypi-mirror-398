#-*- coding:utf-8 -*-
from logging import shutdown
import os,re,jieba,math,json
from tkinter.messagebox import NO 
from jpype import *
from nltk import tokenize
from nltk.tokenize.treebank import TreebankWordTokenizer

from tpf.box.fil import iswin
from tpf.lgg.stop_words import get_stwd_1
from tpf.d2 import lda_batch, sort_data


import jieba, pickle
from scipy.sparse import data
from sklearn.model_selection import train_test_split
import numpy as np 
jieba.setLogLevel(jieba.logging.INFO)

from tpf.d2 import LDA
from tpf.box.base import NumpyEncoder

import tpf.d1 as d1 
from tpf.tim import current_time 
from nltk.tokenize import RegexpTokenizer 


from sklearn.feature_extraction.text import CountVectorizer ,TfidfTransformer,TfidfVectorizer


from tpf.lgg.hlp import HLP 

from tpf.lgg.base import replace_c,replace_c2

MODEUL_PATH = "/mij/73_code/yij/module"
MODEUL_PATH = "/wks/models/HanLP/hanlp-1.8.2-release"


# 全局配置
global_config = {}
global_config["isjmv_running"] = False



def merge_two_list(a, b):
    """
    合并两个列表 
    """
    c=[]
    len_a, len_b = len(a), len(b)
    minlen = min(len_a, len_b)
    for i in range(minlen):
        c.append(a[i])
        c.append(b[i])

    if len_a > len_b:
        for i in range(minlen, len_a):
            c.append(a[i])
    else:
        for i in range(minlen, len_b):
            c.append(b[i])  
    return c


def regex_cut(source_file,target_file,regex_list=[],hanlp_cut=False,jieba_cut=True):
    """
    使用 正则匹配 结合jieba/hanlp 分词


    用法示例
    ------------------------------------------------

    source_file = os.path.join(BASE_DATA_DIR,"text.txt")
    target_file = os.path.join(BASE_DATA_DIR,"result_cut.txt")

    regex_list= [u'(?:[^\u4e00-\u9fa5（）*&……%￥$，,。.@! ！]){1,5}期',r'(?:[0-9]{1,3}[.]?[0-9]{1,3})%']
    regex_cut(source_file,target_file,regex_list)

    正则列表为空[]表示不使用正则 
    """
    fp=open(source_file,"r",encoding="utf8")
    fout=open(target_file,"a",encoding="utf8") 

    if hanlp_cut:
        hlp = HLP()

    for line in fp.readlines():
        
        # 在使用jieba等工具分词之前,先使用正则匹配,以防规则被工具破坏
        # reg_index = 0
        reg_find = []  # 正则匹配项 
        flag_split = " 1010101001 "
        for reg in regex_list:
            # reg_index = reg_index+1
            # flag_split = "FL_o_AG_" + str(reg_index)

            p1=re.compile(reg)
            result1=p1.findall(line)  # 所有匹配的列表 
            

            if result1:       # 如果存在匹配项,则以指定字符替代
                line=p1.sub(flag_split,line)  #这个指定的词不能被其他分词工具拆开 
                reg_find.extend(result1)
                
        if jieba_cut:
            words=jieba.cut(line)
            line = " ".join(words)
        elif hanlp_cut:
            line=hlp.to_string(line)

        if flag_split in line:
            result=line.split(flag_split)
            result=merge_two_list(result,reg_find)
            line = " ".join(result)
        
        line = re.sub(r' +',' ',line)
        fout.write(line.lstrip())
    if hanlp_cut:
        hlp.shutdown()
    fout.write("\n")
    fout.close()
    fp.close()     




def regex_cut1(source_file,target_file,add_words=True):
    """
    功能:常用正则方法封装
    ---------------------
    添加自定义词典，然后进行分词；
    添加的正则有:年，月，日，温度，温度,类似下面的话是可以分词的；

    target_file为追加写入;


    ss = "灵光一点录第１期，2022年８月１日天气记录：温度71%,温度29.8°C"
    """
    if add_words: # 添加自定义的词典
        from tpf.lgg.word_dict import all_word 
        word_pos = all_word()
        # 将读取到的单词与词性补充到jieba
        for word,pos in word_pos.items():
            # 要保证word中没有空格，否则jieba会优先按空格拆分单词
            # 即使suggest_freq也没有用
            jieba.add_word(word=word,tag=pos)
            jieba.suggest_freq(word)
  

    regex_list= [
        u'(?:[^\u4e00-\u9fa5（）*&……%￥$，,。.@! ！]){1,5}期',  # u针对中文，表示unicode编码，避免乱码
        u'(?:[\uff10-\uff19|0-9]){2,4}年',
        u'(?:[\uff10-\uff19]{1,2}|[0-9]{1,2})月',
        u'(?:[\uff10-\uff19]{1,2}|[0-9]{1,2})日',
        u'(?:[\uff10-\uff19]{1,2}|[0-9]{1,2})时',
        u'(?:[\uff10-\uff19]{1,2}|[0-9]{1,2})点',
        u'(?:[\uff10-\uff19]{1,2}|[0-9]{1,2})分',
        u'(?:[\uff10-\uff19]{1,2}|[0-9]{1,2})秒',
        u'(?:[\uff10-\uff19]{1,2}|[0-9]{1,3})岁',
        u'(?:[\uff10-\uff19]{1,2}|[0-9]{0,2}0)多岁',
        r'(?:[0-9]{1,3}[.]?[0-9]{0,11})万多?美?元?',
        r'(?:[0-9]{1,3}[.]?[0-9]{0,11})千?元',
        r'(?:[0-9]{1,5})多?万',
        r'(?:[0-9]{1,3})多?盒',
        r'(?:[0-9]{1,3})多?条',
        r'(?:[0-9]{1,3})多?斤',
        r'(?:[0-9]{1,3})多?张',
        r'(?:[0-9]{1,3})杯酒',
        r'(?:[0-9]{1,5})人',
        r'(?:[0-9]{1,3}[.]?[0-9]{0,3})%',
        r'(?:[0-9]{1,3}[.]?[0-9]{0,3})％',
        r'(?:[0-9]{1,3}[.]?[0-9]{0,3})°C']

    regex_cut(source_file=source_file,target_file=target_file,regex_list=regex_list)







# 词性 ------------------------------------------------------------------------------------
keep_pos="q,qg,qt,qv,s,t,tg,g,gb,gbc,gc,gg,gm,gp,m,mg,Mg,mq,n,an,vn,ude1,nr,ns,nt,nz,nb,nba,nbc,nbp,nf,ng,nh,nhd,o,nz,nx,ntu,nts,nto,nth,ntch,ntcf,ntcb,ntc,nt,nsf,ns,nrj,nrf,nr2,nr1,nr,nnt,nnd,nn,nmc,nm,nl,nit,nis,nic,ni,nhm,nhd"
keep_pos_n="n,an,vn,ude1,nr,ns,nt,nz,nb,nba,nbc,nbp,nf,ng,nh,nhd,o,nz,nx,ntu,nts,nto,nth,ntch,ntcf,ntcb,ntc,nt,nsf,ns,nrj,nrf,nr2,nr1,nr,nnt,nnd,nn,nmc,nm,nl,nit,nis,nic,ni,nhm,nhd"
keep_pos_n=set(keep_pos_n.split(","))
keep_pos_nouns=set(keep_pos.split(","))

keep_pos_v="v,vd,vg,vf,vl,vshi,vyou,vx,vi"
keep_pos_v=set(keep_pos_v.split(","))

keep_pos_p=set(['p','pbei','pba'])
drop_pos_set=set(['xu','xx','y','yg','wh','wky','wkz','wp','ws','wyy','wyz','wb','u','ud','ude1','ude2','ude3','udeng','udh','p','rr'])

# 汉语分词时,过滤掉所有非数字,字母,汉字,即标点符号全过滤了
han_pattern=re.compile(r'[^\dA-Za-z\u3007\u4E00-\u9FCB\uE815-\uE864]+')

#------------------------------------------------------------------------------------


# HLP中进行了JVA的start,一个项目只能启动一次,如果放在类中,生成多个实例时,就会启动两次
# 这是一个全局的实例,有一个就够了 
hlp = HLP()

ds = d1.DataStat()


class CutWord():
    """
    分词相关处理方法  
    """
    def __init__(self) -> None:
        self.hanlp = hlp
        pass

    def tab_xy_jieba(self, data_file, save_file=None):
        """
        标签,tab 格式的文本,以jieba分词
        """
        word_x, word_y = self.tab_xy(data_file, save_file=save_file,fn_cut=jieba.cut)
        return word_x, word_y 

    def tab_xy(self, data_file, save_file=None,fn_cut=None,only_n=False):
        """
        标签,tab 格式的文本,以jieba分词
        """
        word_x = []
        word_y = []

        # 文件读取
        with open(data_file, "r", encoding='utf-8') as f:
            for line in f.readlines():
                conent = line.strip().split("\t")
                word_y.append(conent[0])   #文本 标签类别
                word_x.append(" ".join(fn_cut(conent[1])))   #文本 内容

        if save_file:
            with open(save_file, "wb") as f:
                pickle.dump([word_x,word_y], f)

        return word_x, word_y 

    def tab_xy_hanlp(self, data_file, save_file=None,only_n=False):
        word_x, word_y = self.tab_xy(data_file, save_file=save_file,only_n=only_n,fn_cut=self.sentence_hanlp_list)
        return word_x, word_y 

    def sentence_hanlp_list(self, sentence, with_filter=True, return_generator=False, only_n=False):
        """
        hanlp 对单个句子分词,并过滤掉特定词性的词,

        only_n=True: 只保留名词,优先级高于with_filter

        """
        segs=self.hanlp.to_generator(sentence=sentence)
        if only_n:
            g = [word_pos_pair[0] for word_pos_pair in segs if len(word_pos_pair)==2 and word_pos_pair[0]!=' ' and word_pos_pair[1] in keep_pos_n]
        
        elif with_filter:
            g = [word_pos_pair[0] for word_pos_pair in segs if len(word_pos_pair)==2 and word_pos_pair[0]!=' ' and word_pos_pair[1] not in drop_pos_set]
        else:
            g = [word_pos_pair[0] for word_pos_pair in segs if len(word_pos_pair)==2 and word_pos_pair[0]!=' ']
        return iter(g) if return_generator else g

    def with_filter(self, sentence, remove_flag=True, with_filter=True, return_tuple=False, only_n=False,keep_pos_set=set([]), return_generator=False):
        """
        中文分词,

        hanlp 对单个句子分词,并过滤掉特定词性的词,

        remove_flag 优先级最高,是否只保留数字,字母与汉字,删除空格,换行及所有标点符号 

        keep_pos_set 指定特定的词性,

        with_filter 滤过掉不想要词,否则会只保留 数字,字母与汉字,即去除所有标点符号 


        only_n=True: 只保留名词,优先级高于with_filter


        return
        -------------------------------------
        单词列表,不包括词性 
        

        """
        if only_n:
            keep_pos_set = keep_pos_n

        if remove_flag: 
            sentence = re.sub(han_pattern,"",sentence)
        else: # 不去除标点符号也要将之转换为英文的标点符号 
            sentence = replace_c(sentence)

        segs=self.hanlp.to_generator(sentence=sentence)

        if len(keep_pos_set)>0:
            if return_tuple:
                g = [(word_pos_pair[0],word_pos_pair[1]) for word_pos_pair in segs if len(word_pos_pair)==2 and word_pos_pair[0]!=' ' and word_pos_pair[1] in keep_pos_set]
            else:
                g = [word_pos_pair[0] for word_pos_pair in segs if len(word_pos_pair)==2 and word_pos_pair[0]!=' ' and word_pos_pair[1] in keep_pos_set]
            return iter(g) if return_generator else g

        if with_filter:
            if return_tuple:
                g = [(word_pos_pair[0],word_pos_pair[1]) for word_pos_pair in segs if len(word_pos_pair)==2 and word_pos_pair[0]!=' ' and word_pos_pair[1] not in drop_pos_set]
            else:
                g = [word_pos_pair[0] for word_pos_pair in segs if len(word_pos_pair)==2 and word_pos_pair[0]!=' ' and word_pos_pair[1] not in drop_pos_set]
        else:
            if return_tuple:
                g = [(word_pos_pair[0],word_pos_pair[1]) for word_pos_pair in segs if len(word_pos_pair)==2 and word_pos_pair[0]!=' ']
            else:
                g = [word_pos_pair[0] for word_pos_pair in segs if len(word_pos_pair)==2 and word_pos_pair[0]!=' ']
        return iter(g) if return_generator else g

    def nltk_reg(self, sentence):
        tokenize = RegexpTokenizer(r'\w+|[0-9.]+|\S+')
        words = tokenize.tokenize(sentence)
        return words 
    
    def nltk_tree(self, sentence):
        from nltk.tokenize import TreebankWordTokenizer 
        tokenize = TreebankWordTokenizer()
        return tokenize.tokenize(sentence)

    def nltk_casual(self, sentence):
        """
        过滤掉一些符号,减少重复的字母等
        """
        from nltk.tokenize.casual import casual_tokenize 
        return casual_tokenize(text=sentence,reduce_len=True,strip_handles=True)

    def nltk_ngrams(self,tokens,n,tolist=False):
        from nltk.util import ngrams 
        res = ngrams(tokens,n)
        if tolist:
            return list(res)

        return  res 

    ngram_dict_filter={}
    def ngram1(self,words,range_len=(2,3),filter_pattern=None,add_dict=True):
        """
        若输入的是一句话,则该句话中的字符进行ngram处理,

        sorry,让你失望了...,
        [('s', 'o'), ('o', 'r'), ('r', 'r'), ('r', 'y'), ('让', '你'), ('你', '失'), ('失', '望'), ('望', '了'), ('s', 'o', 'r'), ('o', 'r', 'r'), ('r', 'r', 'y'), ('让', '你', '失'), ('你', '失', '望'), ('失', '望', '了'), ('s', 'o', 'r', 'r'), ('o', 'r', 'r', 'y'), ('让', '你', '失', '望'), ('你', '失', '望', '了')]
        

        若输入的是一个列表,则对该列表中的元素进行ngram处理

        add_dict:每分析一句话,就会将单词放入字典

        """
        sentence = words
        if filter_pattern == None:
            filter_pattern = u'[^a-zA-Z\u4E00-\u9FA5]'
            pattern=re.compile(filter_pattern)
        m = range_len[0]
        n = range_len[1]
        if len(sentence) < n:
            n = len(sentence)
        temp=[tuple(sentence[i - k:i]) for k in range(m, n + 1) for i in range(k, len(sentence) + 1) ]
        
        nwords = [item for item in temp if len(''.join(item).strip())>1 and len(pattern.findall(''.join(item).strip()))==0]

        if add_dict:
            n_word=['_'.join(item) for item in nwords]
            for item in n_word:
                if item in self.ngram_dict_filter:
                    self.ngram_dict_filter[item]+=1
                else:
                    self.ngram_dict_filter[item]=1
        
        return nwords
    
    def get_ngram_dict(self):
        sort_dic=dict(sorted(self.ngram_dict_filter.items(),key=lambda val:val[1],reverse=True))#,reverse=False为降序排列,返回list
        return sort_dic

    def ngram_file(self,in_fil,out_fil,range_len=(2, 3), filter_pattern=None, add_dict=True):
        """
        分析文本的ngram将将其词频写入文件
        """
        [self.ngram1(self.with_filter(line.strip(),with_filter=True),range_len=range_len ,filter_pattern=filter_pattern,add_dict=add_dict) for line  in open(in_fil,'r',encoding='utf8') if len(line.strip())>0 and "RESUMEDOCSSTARTFLAG" not in line]  
        sort_dic= self.get_ngram_dict()

        fout=open(out_fil, "w", encoding='utf-8')
        fout.write(json.dumps(sort_dic, ensure_ascii=False,cls=NumpyEncoder))               
        fout.close() 
    
    def text2words_raw(self,text):
        """
        由段落切分成句子,中文一句话,中间没有任何标点符号的一句话；
        因为ngram不会跨越标点符号；
        每句话拆分为一组ngram,每句话之间的ngram是用空格分开的,


        return
        ----------------------------
        二维数组,第二维是是每句话的分词结果
        """
        split_sen=(i.strip() for i in re.split('。|,|，|：|:|？|！|\s',replace_c2(text)) if len(i.strip())>1)

        return [self.with_filter(sentence) for sentence in split_sen]  
        
    def fil2ngram(self, fil, range_len=(2,3),split_by=None, add_dict=True):
        """
        将多个文档的ngram合并到一个一维数组中,每个元素是一句话的ngram,得到语料库的ngram,
        将文件内容转为ngram,
        split_by:段落拆分标记；
        按此拆分文件中的内容为段落,若不指定,则认为,一行是一个完整的文本,

        每句话拆分为一组ngram,每句话之间的ngram是用空格分开的,每句话的ngram空格拼接后做为列表中的一个元素；


        return
        -------------------------------
        整个文档集合的ngram,
        同时生成ngram词频,可通过get_ngram_dict方法查看

        """
        # 按行读取,每行是一个段落,其中有多句话;实现上这里的一行,指的是一个完整的文本
        # text2words_raw针对的是段落,是一个二维数据,第二维是是每句话的分词结果
        # 因此,word3是一个三维数组 
        word3 = []
        if split_by:
            with open(fil,'r',encoding='utf8') as file_obj:
                contents = file_obj.read()
            # 改为生成器,省内存
            word3=(self.text2words_raw(line.strip()) for line in contents.split(split_by) if len(line.strip())>0)
            # word3=[self.text2words_raw(line.strip()) for line in contents.split(split_by) if len(line.strip())>0]

        else:
            word3=(self.text2words_raw(line.strip()) for line in open(fil,'r',encoding='utf8') if len(line.strip())>0)
            # word3=[self.text2words_raw(line.strip()) for line in open(fil,'r',encoding='utf8') if len(line.strip())>0]

        doc=[]  # 列表,一维数组 
        # if len(word3)>0: 
        for sentences in word3:
            for words in sentences:
                doc.extend([' '.join(['_'.join(i) for i in self.ngram1(words, range_len=range_len, add_dict=add_dict)])])
    
        # filter性能高,过滤空值
        # 将多个文档的ngram合并到一个一维数组中,每个元素是一句话的ngram,得到语料库的ngram
        doc=list(filter(None,doc))
        return doc 

    def word_tfidf(self,corpus):
        """
        计算一个文档的TF-IDF 
        

        return 
        --------------------------
        {单词:(TF-IDF,单词在整个文档中出现的次数)},按TF-IDF从大到小排序
        """
        vectorizer1=CountVectorizer()
        vec1=vectorizer1.fit_transform(corpus) 

        # 每列是一个单词,按列sum后就是单词在文档中的个数
        word_freq=[vec1.getcol(i).sum() for i in range(vec1.shape[1])]

        transformer=TfidfTransformer()#该类会统计每个词语的tf-idf权值  
        tfidf=transformer.fit_transform(vec1)
        tfidf_sum=[tfidf.getcol(i).sum() for i in range(tfidf.shape[1])]   
        tfidf_dic=vectorizer1.vocabulary_
        tfidf_dic=dict(zip(tfidf_dic.values(),tfidf_dic.keys()))

        # ngram词频及TF-IDF
        dic_filter={}
        for i,(word_freq_one,tfidf_one) in enumerate(zip(word_freq, tfidf_sum)):
            dic_filter[tfidf_dic[i]]=(tfidf_one,word_freq_one)

        # for a,b in dic_filter.items():
        #   print(a,b)  # 主要 (0.7071067811865475, 1)
        sort_dic=dict(sorted(dic_filter.items(),key=lambda val:val[1],reverse=True)) #,reverse=False为降序排列,返回list

        return sort_dic

    def regex_cut_file(self,source_file,target_file,regex_list=[],hanlp_cut=False,jieba_cut=False):
        """
        使用 正则匹配 结合jieba/hanlp 分词


        用法示例
        ------------------------------------------------

        source_file = os.path.join(BASE_DATA_DIR,"text.txt")
        target_file = os.path.join(BASE_DATA_DIR,"result_cut.txt")

        regex_list= [u'(?:[^\u4e00-\u9fa5（）*&……%￥$，,。.@! ！]){1,5}期',r'(?:[0-9]{1,3}[.]?[0-9]{1,3})%']
        regex_cut(source_file,target_file,regex_list,jieba_cut=False,hanlp_cut=True)

        正则列表为空[]表示不使用正则 
        """
        fp=open(source_file,"r",encoding="utf8")
        fout=open(target_file,"w",encoding="utf8") 

        for line in fp.readlines():
            line = self.regex_cut(line,regex_list=regex_list,jieba_cut=jieba_cut,hanlp_cut=hanlp_cut)
            fout.write(line)
        fout.close()
        fp.close()     

    def regex_cut(self,text,regex_list=[],hanlp_cut=False,jieba_cut=False):
        """
        使用 正则匹配 结合jieba/hanlp 分词


        用法示例
        ------------------------------------------------

        source_file = os.path.join(BASE_DATA_DIR,"text.txt")
        target_file = os.path.join(BASE_DATA_DIR,"result_cut.txt")

        regex_list= [u'(?:[^\u4e00-\u9fa5（）*&……%￥$，,。.@! ！]){1,5}期',r'(?:[0-9]{1,3}[.]?[0-9]{1,3})%']
        regex_cut(source_file,target_file,regex_list,jieba_cut=False,hanlp_cut=True)

        正则列表为空[]表示不使用正则 
        """
        line = text
        # 在使用jieba等工具分词之前,先使用正则匹配,以防规则被工具破坏
        # reg_index = 0
        reg_find = []  # 正则匹配项 
        flag_split = "1010101001"
        for reg in regex_list:
            # reg_index = reg_index+1
            # flag_split = "FL_o_AG_" + str(reg_index)

            p1=re.compile(reg)
            result1=p1.findall(line)  # 所有匹配的列表 
            

            if result1:       # 如果存在匹配项,则以指定字符替代
                line=p1.sub(flag_split,line)  #这个指定的词不能被其他分词工具拆开 
                reg_find.extend(result1)
                
        if jieba_cut:
            words=jieba.cut(line)
            line = " ".join(words)
        elif hanlp_cut:
            line=hlp.to_string(line)
            
        if flag_split in line:
            result=line.split(flag_split)
            result=merge_two_list(result,reg_find)
            line = " ".join(result)
            
        return line 


    def shutdown_hanlp(self):
        self.hanlp.shutdown()
class TextClassifier():
    def __init__(self) -> None:
        pass

    log_level = 1
    data_size = 0.1
    data_size_used = False

    def set_log_level(self, level):
        self.log_level = level

    def set_data_file(self, data_file,word_segment,word_vec,word_reduction):
        self.data_file = data_file
        self.word_segment = word_segment
        self.word_vec = word_vec
        self.word_reduction = word_reduction

    def data_pre(self):
        """
        数据预处理
        """
        pass

    def word_jieba(self):
        """
        分词
        """
        word_x = []
        word_y = []

        # 文件读取
        with open(self.data_file, "r", encoding='utf-8') as f:
            for line in f.readlines():
                conent = line.strip().split("\t")
                word_y.append(conent[0])   #标签类别
                word_x.append(" ".join(jieba.cut(conent[1])))   #新闻内容

        return word_x, word_y

    def log(self,step,msg="",level=2):
        if self.log_level == level:
            tm = current_time()
            print(tm, step,msg)

    def word_segment(self, func, data_file):
        """
        jieba分词
        返回：x,y
        """
        return func(data_file)
        

    def word_segment_save(self, func, data_file, word_seg_file):
        """
        jieba分词,然后保存分词后结果
        """
        x,y = func(data_file)
        with open(word_seg_file, "wb") as f:
            pickle.dump([x,y], f)

    def get_word_segment(self, word_seg_file):
        with open(word_seg_file, "rb") as f:
           x,y = pickle.load(f)
        return x,y 

    def lable_encoding(self, lable_y):
        """
        文本分类打标签
        1. 取不重复分类数据集set
        2. 建立元组(标签名称，该标签在set中的索引下标)
        3. 转换为字典{标签名称：索引下标}
        4. 获取原分类名称对应的索引下标列表
        """
        st = set(lable_y)
        dt = dict(zip(st,range(len(st))))
        if self.log_level == 2:
            print("dt:",dt) 
        lable_index = np.array([dt[k] for k in lable_y])

        return st,lable_index

    def index_inverse(self, lable_y):
        """
        将分类列表转换为对应的索引下标列表
        返回set是为了后处理时，方便将索引下标再转换为分类列表
        """
        lable_set,lable_index = np.unique(lable_y, return_inverse=True)
        return lable_set,lable_index

    def text_vec_batch(self, x, n_components=128, n_jobs=1, batch_size=100):
        """
        文本向量化及降维,批次处理 
        """

        ll_x = len(x)
        epoch = math.ceil(ll_x/batch_size)
        print("batch all:",epoch)

        start = 0 
        end = start + batch_size

        data = ""
        index = 0
        while True:
            index = index + 1
            x_train = x[start:end]
            print("batch :",index)
            # 是每个批次进行文本向量化再降维,还是一次向量化后批次降维还有待确认
            # <class 'scipy.sparse.csr.csr_matrix'>
            x_train = self.text_CountVectorizer(x_train)

            # 文本向量化与降维的数据要保存到一起，分开保存后，读取的数据LDA不认
            # ndarray
            x_train = LDA(n_components=n_components, data=x_train, n_jobs=1)
            if index==1:
                data = x_train
            else:
                data = np.concatenate((data,x_train),axis=0)
                print("已处理行数:",len(data),",本次处理行数:",len(x_train))
            
            
            start = end 
            end = start + batch_size
            if end >= ll_x:
                end = ll_x
                x_train = x[start:end]
                x_train = self.text_CountVectorizer(x_train)
                x_train = LDA(n_components=n_components, data=x_train, n_jobs=1)
                data = np.concatenate((data,x_train),axis=0)
                break 
        return data 


    def lda_batch(self, x, n_components=128, batch_size=100, n_jobs=1):
        """
        LDA 降维,批次处理 
        """
        data = lda_batch(x,n_components=n_components,n_jobs=n_jobs,batch_size=batch_size)
        return data 



    def text_CountVectorizer(self, train_data):

        """
        文本向量化
        """

        # if isinstance(train_data,list):
        #     train_data = np.array(train_data)

        stop_word_list = get_stwd_1()

        # 会对每一个样本进行向量化
        # 不是整个数据集所有的词合计到一起
        # 每个样本的词的个数与其他样本是不一样的
        # 所以，每行样本的向量长度也是不同的
        # vect_method = CountVectorizer(
        #                 stop_words={".","。"," ","(",")","[","]","{","}","（","）","！","?"},    #停用词
        #                 # stop_words=None,
        #                 token_pattern=r"(?u)\b\w+\b",
        #                 ngram_range=(2, 3),
        #                 max_df=0.95,                  #百分之百的词出现，无法根据此分类，可去掉； 1.0 ＝ 100％ 
        #                                             #min_df＝1只有一个文章出现
        #                 max_features= None            # 保存多少个重要特征
        #                 ) 
                
        vect_method = CountVectorizer(
                        stop_words=stop_word_list,    #停用词
                        # stop_words=None,
                        token_pattern=r"(?u)\b\w+\b",
                        ngram_range=(1, 3),
                        max_df=0.95,                  #百分之百的词出现，无法根据此分类，可去掉； 1.0 ＝ 100％ 
                                                    #min_df＝1只有一个文章出现
                        max_features= 20000            # 保存多少个重要特征
                        ) 

        text_sparse_matrix = vect_method.fit_transform(train_data) # 向量化 

        if self.log_level == 3:
            # print(type(text_sparse_matrix[0]))  # <class 'scipy.sparse.csr.csr_matrix'>
            # print(text_sparse_matrix.shape)     # (22, 30959)
            row_count = text_sparse_matrix.shape[0]
            print("row count:",row_count,len(train_data))
            for i in range(row_count):
                print("count_nonzero, row {} :".format(i), text_sparse_matrix[i].count_nonzero())

        return text_sparse_matrix
    

    def text_TfidfVectorizer(self, train_data):

        """
        文本向量化
        """

        # if isinstance(train_data,list):
        #     train_data = np.array(train_data)

        
        # 会对每一个样本进行向量化
        # 不是整个数据集所有的词合计到一起
        # 每个样本的词的个数与其他样本是不一样的
        # 所以，每行样本的向量长度也是不同的
        vect_method = TfidfVectorizer(
                        stop_words={".","。"," ","(",")","[","]","{","}","（","）","！","?"},    #停用词
                        # stop_words=None,
                        token_pattern=r"(?u)\b\w+\b",
                        ngram_range=(2, 3),
                        max_df=0.9,                  #百分之百的词出现，无法根据此分类，可去掉； 1.0 ＝ 100％ 
                                                    #min_df＝1只有一个文章出现
                        max_features= None            # 保存多少个重要特征
                        ) 

        text_sparse_matrix = vect_method.fit_transform(train_data) # 向量化 

        if self.log_level == 3:
            # print(type(text_sparse_matrix[0]))  # <class 'scipy.sparse.csr.csr_matrix'>
            # print(text_sparse_matrix.shape)     # (22, 30959)
            row_count = text_sparse_matrix.shape[0]
            print("row count:",row_count,len(train_data))
            for i in range(row_count):
                print("count_nonzero, row {} :".format(i), text_sparse_matrix[i].count_nonzero())

        return text_sparse_matrix
    


    def LDA(self, n_components, data):
        """
        文本降维之后会降低训练集得分，但不影响测试集得分
        """
        data = LDA(n_components=n_components,data=data)
        return data

    def get_lable_set(self):
        return self.lable_set

    def get_xy(self, func, data_file, down=True,n_components=128):
        """
        分词，文本向量化，降维
        """
        self.log("开始读取数据文件进行分词：",data_file)
        x,y = self.word_segment(func, data_file)
        
        data_len = len(y)
        self.log("分词完成，开始lable encoding,原始数据总长度：",data_len)

        if self.data_size_used:
            x,y = ds.get_data_by_lable(x, y, self.data_size)
            self.log("每个类别的采样处理数据最大长度：", self.data_size)
            self.log("采样数据总长度：", len(y))

        lable_set,lable_index = self.index_inverse(y)

        self.log("lable encoding完成，开始数据文本向量化,数据集类型:",type(x))
        x_train = self.text_CountVectorizer(x)
        self.log("文本向量化后的数据x[:1]","{}".format(x[:1]),3)
        if down:
            x_train = self.LDA(n_components=n_components, data=x_train)
            # print(x_train[:3])
        self.lable_set = lable_set
        # X_train, X_test, y_train, y_test = train_test_split(x_train,lable_index, test_size=0.33, random_state=42)
        return x_train,lable_index


    def data_format1(self, data_file):
        """
        读取数据文件并分词
        每行两列，第一列为分类名称，第二列为数据，以Tab分隔
        """
        word_x = []
        word_y = []
        # 文件读取
        with open(data_file, "r", encoding='utf-8') as f:
            for line in f.readlines():
                conent = line.strip().split("\t")
                word_y.append(conent[0])   #标签类别
                word_x.append(" ".join(jieba.lcut(conent[1])))   #新闻内容
        return word_x, word_y

    def set_data_size(self, data_size):
        """
        int，每个类别最多data_size大小
        防止出现整个数据集中只有一个类别的情况
        """
        self.data_size = data_size
        self.data_size_used = True 
        


    def get_xy_1(self, data_file,down=True,n_components=128):
        """
        分词，文本向量化，降维;
        按1:3拆分为训练集与测试集
        """
        x,y = self.get_xy(self.data_format1,data_file,down=down,n_components=n_components)
        X_train, X_test, y_train, y_test = train_test_split(x,y, test_size=0.33, random_state=42)
        return X_train, X_test, y_train, y_test


    def fit(self, model, x, y):
        model.fit(x, y)
        return model 



if __name__ == "__main__":
    lp = HLP()








    


