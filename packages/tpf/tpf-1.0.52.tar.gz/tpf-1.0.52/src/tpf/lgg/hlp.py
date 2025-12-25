#-*- coding:utf-8 -*-
from logging import shutdown
import os,jieba 
from jpype import *
from tpf.box.fil import iswin
import jieba, pickle
from scipy.sparse import data
import numpy as np 
jieba.setLogLevel(jieba.logging.INFO)
from tpf.d2 import LDA
import tpf.d1 as d1 
from tpf.tim import current_time 
from sklearn.feature_extraction.text import CountVectorizer ,TfidfTransformer,TfidfVectorizer



# 固定的路径后续通过配置文件加载
MODEUL_PATH = "/source/aisty/73_code/yij/module"
# 默认HanLP路径，可通过参数传入
DEFAULT_MODEUL_PATH = "/wks/models/HanLP/hanlp-1.8.2-release"

global_config = {}
global_config["isjmv_running"] = False



class HLP():
    def __init__(self, version="1.8", config=global_config, model_path=None) -> None:
        # 如果没有提供model_path，使用默认路径
        if model_path is None:
            model_path = DEFAULT_MODEUL_PATH

        self.model_path = model_path

        if version == "1.5":
            MODEUL_HANLP = os.path.join(model_path,"hanlp1.5")
            MODEUL_HANLP_JAR = os.path.join(MODEUL_HANLP,"hanlp-1.5.0.jar")
        elif version == "1.6":
            MODEUL_HANLP = os.path.join(model_path,"hanlp1.6")
            MODEUL_HANLP_JAR = os.path.join(MODEUL_HANLP,"hanlp-1.6.2.jar")
        elif version == "1.8":
            MODEUL_HANLP = os.path.join(model_path,"hanlp1.8")
            MODEUL_HANLP_JAR = os.path.join(MODEUL_HANLP,"hanlp-1.8.2.jar")

        if iswin():
            self._djclass_path="-Djava.class.path="+MODEUL_HANLP_JAR+";"+MODEUL_HANLP
        else:
            self._djclass_path="-Djava.class.path="+MODEUL_HANLP_JAR+":"+MODEUL_HANLP

        self.config = config
        self.version = version
        # 根据版本确定JAR文件名
        if version == "1.5":
            self.jar_name = "hanlp-1.5.0.jar"
            self.version_dir = "hanlp1.5"
        elif version == "1.6":
            self.jar_name = "hanlp-1.6.2.jar"
            self.version_dir = "hanlp1.6"
        elif version == "1.8":
            self.jar_name = "hanlp-1.8.2.jar"
            self.version_dir = "hanlp1.8"

        self.start()
        
        self._HanLP = JClass('com.hankcs.hanlp.HanLP')
        self._StandardTokenizer = JClass('com.hankcs.hanlp.tokenizer.StandardTokenizer')
        self._NLPTokenizer = JClass('com.hankcs.hanlp.tokenizer.NLPTokenizer')
        self._CustomDictionary = JClass('com.hankcs.hanlp.dictionary.CustomDictionary')

    def start(self, model_path=None):
        if not self.config["isjmv_running"]:
            # 如果没有传入model_path参数，使用实例的model_path
            if model_path is None:
                model_path = self.model_path

            # 构建JAR文件和目录路径
            jar_path = os.path.join(model_path, self.version_dir, self.jar_name)
            hanlp_path = os.path.join(model_path, self.version_dir)

            # 构建classpath
            if iswin():
                classpath = f"{jar_path};{hanlp_path}"
            else:
                classpath = f"{jar_path}:{hanlp_path}"

            # 启动JVM
            startJVM(getDefaultJVMPath(),
                     f"-Djava.class.path={classpath}",
                     "-Xms1g",
                     "-Xmx1g")

            self.config["isjmv_running"] = True 


    def shutdown(self):
        if self.config["isjmv_running"]:
            shutdownJVM()
            self.config["isjmv_running"] = False

    def segment(self, sentence):
        """
        单词/词性, 有了词性的分区,可以近似地达到命名实体识别的效果,
        但同是名词,就无法分区哪些是人名,日期,地名

        [吞/v, 风吻/nr, 雨/n, 葬/vg, 落日/n, ...
        """
        return self._HanLP.segment(sentence)

    def summary(self, document,top=5):
        return self._HanLP.extractSummary(document, top)

    def segment_std(self, sentence):
        return self._StandardTokenizer.segment(sentence)

    def segment_NLP(self, sentence):
        return self._NLPTokenizer.segment(sentence) 

    def customDictionary(self, words=[]):
        """
        lp.customDictionary(["吞风吻雨",'葬落日','欺山赶海','践雪径'])


        print(lp.segment(ss))
        """
        for word in words:
            self._CustomDictionary.add(word)

    def to_string(self, sentence, tokenize="nlp"):
        """
        仅返回单词,不包括词性,以空格分隔
        """
        if tokenize == "std":
            return " ".join([str(word_pos_item).split('/')[0] for word_pos_item in self.segment_std(sentence)]   )
        elif tokenize == "nlp":
            return " ".join([str(word_pos_item).split('/')[0] for word_pos_item in self.segment_NLP(sentence)]   )


            
    def to_list(self, sentence, tokenize="nlp"):
        """
        仅返回单词,不包括词性,

        ['吞风', '吻', '雨葬', '落日', '未曾', '彷徨', ',', '欺山', '赶海', '践', '雪径', '也', '未', '绝望']

        """
        if tokenize == "std":
            return [str(word_pos_item).split('/')[0] for word_pos_item in self.segment_std(sentence)] 
        
        elif tokenize == "nlp":
            return [str(word_pos_item).split('/')[0] for word_pos_item in self.segment_NLP(sentence)]   

    def to_list_with_tuple(self, sentence, tokenize="nlp"):
        """
        列表中是一个tuple(单词,词性),

        [('吞风', 'n'), ('吻', 'v'), ('雨葬', 'n'), ('落日', 'n'), ('未曾', 'd'), ('彷徨', 'v'), (',', 'w'), ('欺山', 'ns'), ('赶海', 'v'), ('践', 'Vg'), ('雪径', 'n'), ('也', 'd'), ('未', 'd'), ('绝望', 'a')]

        """
        if tokenize == "std":
            return [(str(word_pos_item).split('/')[0],str(word_pos_item).split('/')[1]) for word_pos_item in self.segment_std(sentence) if len(str(word_pos_item).split('/'))==2] 
        
        elif tokenize == "nlp":
            return [(str(word_pos_item).split('/')[0],str(word_pos_item).split('/')[1]) for word_pos_item in self.segment_NLP(sentence) if len(str(word_pos_item).split('/'))==2]   



    def to_generator(self, sentence, tokenize="nlp"):
        """
        迭代器返回内容包括词性,第一个为词,第二个为词性 


        ['吞风吻雨', 'nz'] 
        ['葬落日', 'nz'] 
        ['未曾', 'd'] 
        ['彷徨', 'vi'] 
        [',', 'w'] 
        ['欺山赶海', 'nz'] 
        ['践雪径', 'nz'] 
        ['也', 'd'] 
        ['未', 'd'] 
        ['绝望', 'a'] 
        """
        if tokenize == "std":
            return (str(word_pos_item).split('/') for word_pos_item in self.segment_std(sentence))
        elif tokenize == "nlp":
            return (str(word_pos_item).split('/') for word_pos_item in self.segment_NLP(sentence))

    def extractKeyword(self,document,count=256):
        """
        关键字提取 
        """
        java_LinkedList = self._HanLP.extractKeyword(document, count)
        pl = []
        for v in java_LinkedList:
            pl.append(str(v))

        return pl 

    def extractSummary(self,document,count=8):
        """
        自动摘要
        """
        java_LinkedList = self._HanLP.extractSummary(document, count)
        pl = []
        for v in java_LinkedList:
            pl.append(str(v))

        return pl 

    def shortWord(self,document,count=256):
        """
        短语提取
        """
        java_LinkedList = self._HanLP.extractPhrase(document,count)
        pl = []
        for v in java_LinkedList:
            pl.append(str(v))

        return pl 

    def mean(self,document,count=256, only_keyword=False):
        """
        提取段落含义
        """
        word_mean = []

        # 段落的摘要固定为5个 
        _summary = self.extractSummary(document,5)
        word_mean.extend(_summary)

        keyword = self.extractKeyword(document,count)
        word_mean.extend(keyword)

        if not only_keyword:
            shortword = self.shortWord(document,count)
            word_mean.extend(shortword)

        return word_mean

if __name__=="__main__":
    # 示例1：使用默认路径
    hlp = HLP()

    # 示例2：使用自定义路径
    # hlp = HLP(model_path="/wks/models/HanLP")

    # 示例3：指定版本和路径
    # hlp = HLP(version="1.8", model_path="/wks/models/HanLP")
    sentence = "吞风吻雨葬落日未曾彷徨,欺山赶海践雪径也未绝望"
    print(hlp.segment(sentence=sentence))
    """
    [吞/v, 风吻/nr, 雨/n, 葬/vg, 落日/n, 未曾/d, 彷徨/vi, ,/w, 欺/vg, 山/n, 赶海/vi, 践/vg, 雪径/nr, 也/d, 未/d, 绝望/a]
    """
    
    """
    修改字典后
    [吞风/n, 吻雨/n, 葬/vg, 落日/n, 未曾/d, 彷徨/vi, ,/w, 欺/vg, 山/n, 赶海/vi, 践/vg, 雪径/nr, 也/d, 未/d, 绝望/a]
    """
    print(hlp.to_list_with_tuple(sentence=sentence))

    sentence = "保持良好的合作关系"
    # sentence = "良好的合作关系"
    print(hlp.to_list_with_tuple(sentence=sentence))
    sentence = "保持良好"
    print(hlp.to_list_with_tuple(sentence=sentence))