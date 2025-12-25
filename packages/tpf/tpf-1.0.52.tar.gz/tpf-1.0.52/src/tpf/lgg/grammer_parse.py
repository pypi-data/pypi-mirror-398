'''
Description: 
Author: 七三学徒
Date: 2022-01-29 15:48:27
FilePath: /73_code/aisty/lgg/grammer_parse.py
'''
#-*- coding:utf-8 -*-

import nltk,json


from tpf.lgg.pos import keep_pos_p,keep_pos_v,keep_pos_nouns,stanford_ner1
from tpf.lgg.cut_word import CutWord 
cw = CutWord 
from tpf.lgg.slp import SLP
slp = SLP()




class GrammerParse():
    """
    语法分析，依存分析
    """
    def __init__(self) -> None:
        self.cw = cw 
        self.slp = slp 
        pass

    def get_nltk_ner_nodes(self,parent):
        """
        nltk中命名实体识别的树节点
        """
        date=''
        org=''
        loc=''

        for node in parent:
            if type(node) is nltk.Tree:
                if node.label() == 'DATE' :
                    date=date+" "+''.join([i[0]  for i in node])

                elif node.label() == 'ORGANIZATIONL' :
                    org=org+" "+''.join([i[0]  for i in node])
                elif node.label() == 'LOCATION':
                    loc=loc+" "+''.join([i[0]  for i in node])
        if len(date)>0 or len(org)>0  or len(loc)>0 :
            return {'date':date,'org':org,'loc':loc}
        else:
            return {}

    def stanford_ner1(self,raw_sentence=None):
        """
        stanford命名实体识别，调用standordNlp的命名实体识别方法
        """
        #assert grammer_type in set(['hanlp_keep','stanford_ner_drop','stanford_pos_drop'])
        if len(raw_sentence.strip())<1:
            return False
        grammer_dict=stanford_ner1
        """
        DATE:{<DATE>+<MISC>?<DATE>*}
        {<DATE>+<MISC>?<DATE>*}
        {<DATE>+}
        {<TIME>+}
        ORGANIZATIONL:{<ORGANIZATION>+}
        LOCATION:{<LOCATION|STATE_OR_PROVINCE|CITY|COUNTRY>+}
        """

        stanford_ner_drop_rp = nltk.RegexpParser(grammer_dict['stanford_ner_drop'])
        try :
            # ner处理好的结果： [('爱', 'O'), ('竞逐', 'O'), ('镜', 'O'), ('花', 'O'), ('那', 'O'), ('美丽', 'O')
            # 再传入parse方法进行处理
            stanford_ner_drop_result = stanford_ner_drop_rp.parse(self.slp.ner(raw_sentence) )

        except:
            print("the error sentence is {}".format(raw_sentence))
        else:

            stanford_keep_drop_dict=self.get_nltk_ner_nodes(stanford_ner_drop_result)
            return stanford_keep_drop_dict
            














