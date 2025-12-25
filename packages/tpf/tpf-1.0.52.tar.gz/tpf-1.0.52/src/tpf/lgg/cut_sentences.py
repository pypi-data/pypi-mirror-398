'''
Description: 拆分段落为句子
Author: 七三学徒
Date: 2021-12-14 13:29:02
FilePath: /73_code/aisty/lgg/cut_sentences.py
'''
#-*- coding:utf-8 -*-

import re
from tpf.lgg.fn import replace_c 
from tpf.lgg.cut_word import CutWord 
cw = CutWord()

def __merge_symmetry(sentences, symmetry=('“','”')):
    '''合并对称符号，如双引号'''
    effective_ = []
    merged = True
    for index in range(len(sentences)):       
        if symmetry[0] in sentences[index] and symmetry[1] not in sentences[index]:
            merged = False
            effective_.append(sentences[index])
        elif symmetry[1] in sentences[index] and not merged:
            merged = True
            effective_[-1] += sentences[index]
        elif symmetry[0] not in sentences[index] and symmetry[1] not in sentences[index] and not merged :
            effective_[-1] += sentences[index]
        else:
            effective_.append(sentences[index])
        
    return [i.strip() for i in effective_ if len(i.strip()) > 0]

def to_sentences(paragraph):
    """段落拆分为句子，包含标签符号
    由段落切分成句子,中间还可以有其他标点符号,比如逗号,
    同时合并引号中的内容 
    
    """
    sentences = re.split(r"(？|。|！|\…\…)", replace_c(paragraph))
    sentences.append("")
    sentences = ["".join(i) for i in zip(sentences[0::2], sentences[1::2])]
    sentences = [i.strip() for i in sentences if len(i.strip()) > 0]
    
    for j in range(1, len(sentences)):
        if sentences[j][0] == '”':
            sentences[j-1] = sentences[j-1] + '”'
            sentences[j] = sentences[j][1:]
            
    return __merge_symmetry(sentences)


def text2words_raw(text):
    """段落拆分为句子，不包含标签符号
    由段落切分成句子,中间没有任何标点符号及空格的一句话 ；

    return
    ----------------------------
    针对的是段落,返回一个二维数据,第二维是是每句话的分词结果
    """
    split_sen=(i.strip() for i in re.split('。|,|，|：|:|？|！|\t|\n',replace_c(text)) if len(i.strip())>1)
    return [cw.with_filter(sentence) for sentence in split_sen]  


if __name__=="__main__":

    s1 = """我心里暗笑他的迂；他们只认得钱，托他们只是白托!而且我这样大年纪的人，难道还不能料理自己么？唉，我现在想想，那时真是太聪明了!
    我说道：“爸爸，你走吧。”他往车外看了看说：“我买几个橘子去。你就在此地，不要走动。”我看那边月台的栅栏外有几个卖东西的等着顾客。走到那边月台，须穿过铁道，须跳下去又爬上去。"""


    s1 = to_sentences(s1)
    print("\n".join(s1))
    """
    我心里暗笑他的迂；他们只认得钱，托他们只是白托!而且我这样大年纪的人，难道还不能料理自己么？
    唉，我现在想想，那时真是太聪明了!
    我说道：“爸爸，你走吧。”
    他往车外看了看说：“我买几个橘子去。你就在此地，不要走动。”
    我看那边月台的栅栏外有几个卖东西的等着顾客。
    走到那边月台，须穿过铁道，须跳下去又爬上去。
    """




