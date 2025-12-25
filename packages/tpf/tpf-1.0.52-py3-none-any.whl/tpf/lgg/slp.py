'''
Description: 自然语言处理工具包,Java开发 
Author: 七三学徒
Date: 2021-12-14 13:29:02
FilePath: /73_code/aisty/lgg/slp.py
'''
#-*- coding:utf-8 -*-


import os,re 
from nltk import Tree, ProbabilisticTree
from nltk.util import pr
from stanfordcorenlp import StanfordCoreNLP # pip install stanfordcorenlp

nlp = StanfordCoreNLP(r'/home/qisan/73_code/yij/nlpsf/code/module/stanfordnlp', lang='zh')



root_path=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

drop_pos_set=set(['xu','xx','y','yg','wh','wky','wkz','wp','ws','wyy','wyz','wb','u','ud','ude1','ude2','ude3','udeng','udh'])
han_pattern=re.compile(r'[^\dA-Za-z\u3007\u4E00-\u9FCB\uE815-\uE864]+')


from tpf.lgg.fn import replace_c as _replace_c

class SLP():

    def __init__(self,module_path="/home/qisan/73_code/yij/module/stanfordnlp",lang='zh') -> None:
        """
        StanfordCoreNLP 常用方法 

        ner:    命令实体识别
        pos_tag:词性识别

        返回数列,每个元素是一个元组,
        元组第1个元素为单词,第二个元素为单词的属性

        """
        self.lp = StanfordCoreNLP(module_path,lang=lang)
        pass


    def ner(self,sentence):
        """
        命名实体识别 

        [('爱', 'O'), ('竞逐', 'O'), ('镜', 'O'), ('花', 'O'), ('那', 'O'), ('美丽', 'O')
        
        """
        res = self.lp.ner(sentence=sentence)
        return res 

    def pos_tag(self,sentence):
        """
        词性识别 

        (单词,词性), 有了词性的分区,可以近似地达到命名实体识别的效果,
        但同是名词,就无法分区哪些是人名,日期,地名

        [('天生', 'NN'), ('我', 'PN'), ('材必', 'AD'), ('有用', 'VA'), ('，', 'PU'), ('千', 'CD'), ('金', 'NN'), ('散尽', 'VV'), ('还', 'AD'), ('复来', 'VV')]
        
        """
        res = self.lp.pos_tag(sentence=sentence)
        return res
    
    def parse(self,sentence):
        return self.lp.parse(sentence)

    def parse_sentence(self,sentence):
        text=_replace_c(sentence)
        try:
            if len(text.strip())>5:
                return Tree.fromstring(self.lp.parse(sentence.strip()))
        except:
            pass
        

    def pos(self,sentence):
        text=_replace_c(sentence)
        if len(text.strip())>5:
            return self.lp.pos_tag(text)
        else:
            return False

    def denpency_parse(self,sentence):
        return self.lp.dependency_parse(sentence)


def deal_news():

    DATA_DIR = "/mij/aisty/73_code/test/lgg1/2-4-1"

    nlp = SLP()
    fin=open(os.path.join(DATA_DIR,'news.txt'),'r',encoding='utf8')
    fner=open(os.path.join(DATA_DIR,'res_ner.txt'),'w',encoding='utf8')
    ftag=open(os.path.join(DATA_DIR,'res_pos_tag.txt'),'w',encoding='utf8')

    for line in fin:
        line=line.strip()
        if len(line)<1:
            continue
    
        fner.write(" ".join([each[0]+"/"+each[1] for  each in nlp.ner(line) if len(each)==2 ])+"\n")
        ftag.write(" ".join([each[0]+"/"+each[1] for each in nlp.pos_tag(line) if len(each)==2 ])+"\n")

    fner.close()   
    ftag.close()
    

if __name__=="__main__":
    from tpf.lgg.slp import SLP 
    lp = SLP()

    ss = """
    爱竞逐镜花那美丽/马夫人
    怕幸运会转眼远逝/庄聚贤
    为贪嗔喜恶怒着迷/所有人
    """

    # print(lp.ner(sentence=ss))
    """
    [('爱', 'O'), ('竞逐', 'O'), ('镜', 'O'), ('花', 'O'), ('那', 'O'), ('美丽', 'O'), ('/', 'O'), ('马夫人', 'O'), ('怕', 'O'), ('幸运', 'O'), ('会', 'O'), ('转眼', 'O'), ('远逝', 'O'), ('/', 'O'), ('庄聚贤', 'PERSON'), ('为', 'O'), ('贪嗔', 'O'), ('喜恶', 'O'), ('怒', 'O'), ('着迷', 'O'), ('/', 'O'), ('所有人', 'O')]
    """
    # deal_news()
    # print(lp.parse_sentence(ss))
    """
    (ROOT
  (IP
    (IP
      (IP
        (VP
          (VP (VV 爱) (IP (VP (VV 竞逐) (NP (NN 镜)))))
          (VP
            (VV 花)
            (NP (DP (DT 那)) (ADJP (JJ 美丽)) (PU /) (NP (NN 马夫人))))))
      (VP
        (VV 怕)
        (IP
          (NP (NN 幸运))
          (VP (VV 会) (VP (ADVP (AD 转眼)) (VP (VV 远逝)))))))
    (PU /)
    (IP
      (NP (NR 庄聚贤))
      (VP
        (PP (P 为) (NP (NN 贪嗔)))
        (VP (VV 喜恶) (IP (VP (ADVP (AD 怒)) (VP (VV 着迷)))))))
    (PU /)
    (NP (NN 所有人))))
    """
    print(lp.denpency_parse(ss))
    """
    [('ROOT', 0, 1), ('ccomp', 1, 2), ('dobj', 2, 3), ('conj', 1, 4), ('dobj', 4, 5), ('dep', 9, 6), ('punct', 9, 7), ('nsubj', 9, 8), ('dep', 5, 9), ('nsubj', 13, 10), ('aux:modal', 13, 11), ('advmod', 13, 12), ('ccomp', 9, 13), ('punct', 9, 14), ('nsubj', 18, 15), ('case', 17, 16), ('nmod:prep', 18, 17), ('dep', 9, 18), ('advmod', 20, 19), ('ccomp', 18, 20), ('punct', 20, 21), ('dep', 20, 22)]
    """






