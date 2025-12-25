'''
Description: 信息提取 
Author: 七三学徒
Date: 2022-01-08 11:40:40
FilePath: /73_code/aisty/lgg/search_word.py
'''


#encoding=utf8
import nltk.tree as tree
import nltk
from jpype import *
from nltk.util import pr

huanhang=set(['。','？','！','?'])
keep_pos="q,qg,qt,qv,s,t,tg,g,gb,gbc,gc,gg,gm,gp,mg,Mg,n,an,ude1,nr,ns,nt,nz,nb,nba,nbc,nbp,nf,ng,nh,nhd,o,nz,nx,ntu,nts,nto,nth,ntch,ntcf,ntcb,ntc,nt,nsf,ns,nrj,nrf,nr2,nr1,nr,nnt,nnd,nn,nmc,nm,nl,nit,nis,nic,ni,nhm,nhd"
keep_pos_nouns=set(keep_pos.split(","))
keep_pos_v="v,vd,vg,vf,vl,vshi,vyou,vx,vi,vn"
keep_pos_v=set(keep_pos_v.split(","))
keep_pos_p=set(['p','pbei','pba'])
merge_pos=keep_pos_p|keep_pos_v
keep_flag=set(['：','，','？','。','！','；','、','-','.','!',',',':',';','?','(',')','（','）','<','>','《','》'])
drop_pos_set=set(['xu','xx','y','yg','wh','wky','wkz','wp','ws','wyy','wyz','wb','u','ud','ude1','ude2','ude3','udeng','udh'])

from tpf.lgg.hlp import HLP
lp = HLP()

def getNodes(parent,model_tagged_file=None):
    """
    遍历树节点,并写入文件
    """
    text=''
    for node in parent:
        if type(node) is nltk.Tree:
            print(node)
            if node.label() == 'NP':   
                text+=''.join(node_child[0].strip() for node_child in node.leaves())+"/NP"+3*" "
            if node.label() == 'VP':
                text+=''.join(node_child[0].strip() for node_child in node.leaves())+"/VP"+3*" "
        else: # 如果不是树,就是没有分叉,那就是叶子节点了
            if node[1] in keep_pos_p:  # set(['p','pbei','pba'])
                text+=node[0].strip()+"/PP"+3*" "  
            if node[0] in huanhang : # 中文的换行结束
                text+=node[0].strip()+"/O"+3*" "                    
            if node[1] not in merge_pos:
                text+=node[0].strip()+"/O"+3*" "                             
            #print("hh")

    # 本方法是在for循环中调用的,文件在for循环结束后关闭
    model_tagged_file.write(text+"\n")     


def grammer(sentence,model_tagged_file=None):   
    """
    输入的是切词的结果,tuple列表(单词,词性):[('工作', 'vn'), ('描述', 'v'), ('：', 'w'), ('我', 'rr'), ('曾', 'd'), ('在', 'p')]
    """
    grammar1 = r"""NP: 
        {<a|an|ag>+<u|ude1>?<v|vd|vg|vf|vl|vshi|vyou|vx|vi|vn>*<n|an|nr|ns|nt|nz|nb|nba|nbc|nbp|nf|ng|nh|nhd|nz|nx|ntu|nts|nto|nth|ntch|ntcf|ntcb|ntc|nt|nsf|ns|nrj|nrf|nr2|nr1|nr|nnt|nnd|nn|nmc|nm|nl|nit|nis|nic|ni|nhm|nhd>+}
        {<v|vd|vg|vf|vl|vshi|vyou|vx|vi|vn>+<n|an|nr|ns|nt|nz|nb|nba|nbc|nbp|nf|ng|nh|nhd|nz|nx|ntu|nts|nto|nth|ntch|ntcf|ntcb|ntc|nt|nsf|ns|nrj|nrf|nr2|nr1|nr|nnt|nnd|nn|nmc|nm|nl|nit|nis|nic|ni|nhm|nhd>+}
        {<m|mg|Mg|mq|q|qg|qt|qv|s|>*<a|an|ag>*<s|g|gb|gbc|gc|gg|gm|gp|n|an|nr|ns|nt|nz|nb|nba|nbc|nbp|nf|ng|nh|nhd|o|nz|nx|ntu|nts|nto|nth|ntch|ntcf|ntcb|ntc|nt|nsf|ns|nrj|nrf|nr2|nr1|nr|nnt|nnd|nn|nmc|nm|nl|nit|nis|nic|ni|nhm|nhd>+<f>?<ude1>?<g|gb|gbc|gc|gg|gm|gp|n|an|nr|ns|nt|nz|nb|nba|nbc|nbp|nf|ng|nh|nhd|o|nz|nx|ntu|nts|nto|nth|ntch|ntcf|ntcb|ntc|nt|nsf|ns|nrj|nrf|nr2|nr1|nr|nnt|nnd|nn|nmc|nm|nl|nit|nis|nic|ni|nhm|nhd>+}
        {<n|an|nr|ns|nt|nz|nb|nba|nbc|nbp|nf|ng|nh|nhd|nz|nx|ntu|nts|nto|nth|ntch|ntcf|ntcb|ntc|nt|nsf|ns|nrj|nrf|nr2|nr1|nr|nnt|nnd|nn|nmc|nm|nl|nit|nis|nic|ni|nhm|nhd>+<cc>+<n|an|nr|ns|nt|nz|nb|nba|nbc|nbp|nf|ng|nh|nhd|nz|nx|ntu|nts|nto|nth|ntch|ntcf|ntcb|ntc|nt|nsf|ns|nrj|nrf|nr2|nr1|nr|nnt|nnd|nn|nmc|nm|nl|nit|nis|nic|ni|nhm|nhd>+}
        {<m|mg|Mg|mq|q|qg|qt|qv|s|>*<q|qg|qt|qv>*<f|b>*<vi|v|vn|vg|vd>+<ude1>+<n|an|nr|ns|nt|nz|nb|nba|nbc|nbp|nf|ng|nh|nhd|nz|nx|ntu|nts|nto|nth|ntch|ntcf|ntcb|ntc|nt|nsf|ns|nrj|nrf|nr2|nr1|nr|nnt|nnd|nn|nmc|nm|nl|nit|nis|nic|ni|nhm|nhd>+}
        {<g|gb|gbc|gc|gg|gm|gp|n|an|nr|ns|nt|nz|nb|nba|nbc|nbp|nf|ng|nh|nhd|nz|nx|ntu|nts|nto|nth|ntch|ntcf|ntcb|ntc|nt|nsf|ns|nrj|nrf|nr2|nr1|nr|nnt|nnd|nn|nmc|nm|nl|nit|nis|nic|ni|nhm|nhd>+<vi>?}
        VP:{<v|vd|vg|vf|vl|vshi|vyou|vx|vi|vn>+}
        """
    cp = nltk.RegexpParser(grammar1)
    try :
        result = cp.parse(sentence) 
        print(result)
    except:
        pass
    else:
        getNodes(result,model_tagged_file=model_tagged_file)


def get_nvp(fil_in,fil_out):
    """
    抽取 动名词短语/名词短语块 并写入文件 
    """
    fout=open(fil_out, 'w', encoding='utf8') 
    
    for line in open(fil_in, 'r', encoding='utf8'):    
        line=line.strip() 
        grammer(lp.to_list_with_tuple(line),model_tagged_file=fout)
    fout.close()

def gram_reg_file(fil_in,fil_out):
    get_nvp(fil_in,fil_out)



def get_vn_pair():
    pass

def get_noun_chunk(tree):
    noun_chunk=[]
    if tree.label()=="NP":  # 名词短语
        nouns_phase=''.join(tree.leaves())
        noun_chunk.append(nouns_phase)   
    return noun_chunk

def get_ip_recursion_noun(tree):
    np_list=[]
    if len(tree)==1:
        tr=tree[0]
        get_ip_recursion_noun(tr)
    if len(tree)==2:
        tr=tree[0]
        get_ip_recursion_noun(tr)        
        tr=tree[1]
        get_ip_recursion_noun(tr)        
    if len(tree)==3:
        tr=tree[0]
        get_ip_recursion_noun(tr)        
        tr=tree[1]
        get_ip_recursion_noun(tr)       
        tr=tree[2]
        get_ip_recursion_noun(tr)    
    if tree.label()=='NP':
        np_list.append(get_noun_chunk(tree))
    return np_list
    
def get_vv_loss_np(tree):
    if not isinstance(tree,nltk.tree.Tree):
        return False
    stack=[]
    np=[]
    stack.append(tree)
    current_tree=''
    while stack:
        current_tree=stack.pop()
        if isinstance(current_tree,nltk.tree.Tree) and current_tree.label()=='VP':
            continue        
        elif isinstance(current_tree,nltk.tree.Tree) and current_tree.label()!='NP':
            for i in range(len(current_tree)):                
                stack.append(current_tree[i])
        elif isinstance(current_tree,nltk.tree.Tree) and current_tree.label()=='NP':
            np.append(get_noun_chunk(tree))
    if np:
        return np
    else:
        return False
            
def searchVN(tree_in):
    """
    从一棵树中找到 动态+名词 的结构,
    依次读取树的节点,遇NP处理,否则压入栈
    """
    # 不是一棵树,就不遍历
    if not isinstance(tree_in,nltk.tree.Tree):
        return False    
    vp_pair=[]  
    stack=[]
    stack.append(tree_in)
    current_tree=''
    while stack:
        tree=stack.pop()
        if isinstance(tree,nltk.tree.Tree) and tree.label()=="ROOT":
            for i in range(len(tree)):
                stack.append(tree[i])	    
        if isinstance(tree,nltk.tree.Tree) and tree.label()=="IP":
            for i in range(len(tree)):
                stack.append(tree[i])	          
        if isinstance(tree,nltk.tree.Tree) and tree.label()=="VP":
            duplicate=[]
            if len(tree)>=2:
                for i in range(1,len(tree)):
                    # 如果一棵树是 动词+名称 的结构
                    if tree[0].label()=='VV' and tree[i].label()=="NP":
                        verb=''.join(tree[0].leaves())
                        noun=get_noun_chunk(tree[i])
                        if verb and noun:
                            vp_pair.append((verb,noun))
                            duplicate.append(noun)
                    elif tree[0].label()=='VV' and tree[i].label()!="NP":
                        noun=get_vv_loss_np(tree)
                        verb=''.join(tree[0].leaves())
                        if verb and noun and noun not in duplicate:
                            duplicate.append(noun)
                            vp_pair.append((verb,noun))
    if vp_pair:
        return vp_pair
    else:
        return False                        


    #if tree.label()=="NP":
        #nouns_phase=''.join(tree.leaves())
        #noun_chunk.append(nouns_phase)      



grammar1 = r"""VP:
        {<v|vd|vg|vf|vl|vshi|vyou|vx|vi|vn>+<n|an|nr|ns|nt|nz|nb|nba|nbc|nbp|nf|ng|nh|nhd|nz|nx|ntu|nts|nto|nth|ntch|ntcf|ntcb|ntc|nt|nsf|ns|nrj|nrf|nr2|nr1|nr|nnt|nnd|nn|nmc|nm|nl|nit|nis|nic|ni|nhm|nhd>+}
        {<v|vd|vg|vf|vl|vshi|vyou|vx|vi|vn>+}
        NP:{<a|an|ag>+<u|ude1>?<v|vd|vg|vf|vl|vshi|vyou|vx|vi|vn>*<n|an|nr|ns|nt|nz|nb|nba|nbc|nbp|nf|ng|nh|nhd|nz|nx|ntu|nts|nto|nth|ntch|ntcf|ntcb|ntc|nt|nsf|ns|nrj|nrf|nr2|nr1|nr|nnt|nnd|nn|nmc|nm|nl|nit|nis|nic|ni|nhm|nhd>+}
        {<m|mg|Mg|mq|q|qg|qt|qv|s|>*<a|an|ag>*<s|g|gb|gbc|gc|gg|gm|gp|n|an|nr|ns|nt|nz|nb|nba|nbc|nbp|nf|ng|nh|nhd|o|nz|nx|ntu|nts|nto|nth|ntch|ntcf|ntcb|ntc|nt|nsf|ns|nrj|nrf|nr2|nr1|nr|nnt|nnd|nn|nmc|nm|nl|nit|nis|nic|ni|nhm|nhd>+<f>?<ude1>?<g|gb|gbc|gc|gg|gm|gp|n|an|nr|ns|nt|nz|nb|nba|nbc|nbp|nf|ng|nh|nhd|o|nz|nx|ntu|nts|nto|nth|ntch|ntcf|ntcb|ntc|nt|nsf|ns|nrj|nrf|nr2|nr1|nr|nnt|nnd|nn|nmc|nm|nl|nit|nis|nic|ni|nhm|nhd>+}
        {<n|an|nr|ns|nt|nz|nb|nba|nbc|nbp|nf|ng|nh|nhd|nz|nx|ntu|nts|nto|nth|ntch|ntcf|ntcb|ntc|nt|nsf|ns|nrj|nrf|nr2|nr1|nr|nnt|nnd|nn|nmc|nm|nl|nit|nis|nic|ni|nhm|nhd>+<cc>+<n|an|nr|ns|nt|nz|nb|nba|nbc|nbp|nf|ng|nh|nhd|nz|nx|ntu|nts|nto|nth|ntch|ntcf|ntcb|ntc|nt|nsf|ns|nrj|nrf|nr2|nr1|nr|nnt|nnd|nn|nmc|nm|nl|nit|nis|nic|ni|nhm|nhd>+}
        {<m|mg|Mg|mq|q|qg|qt|qv|s|>*<q|qg|qt|qv>*<f|b>*<vi|v|vn|vg|vd>+<ude1>+<n|an|nr|ns|nt|nz|nb|nba|nbc|nbp|nf|ng|nh|nhd|nz|nx|ntu|nts|nto|nth|ntch|ntcf|ntcb|ntc|nt|nsf|ns|nrj|nrf|nr2|nr1|nr|nnt|nnd|nn|nmc|nm|nl|nit|nis|nic|ni|nhm|nhd>+}
        {<g|gb|gbc|gc|gg|gm|gp|n|an|nr|ns|nt|nz|nb|nba|nbc|nbp|nf|ng|nh|nhd|nz|nx|ntu|nts|nto|nth|ntch|ntcf|ntcb|ntc|nt|nsf|ns|nrj|nrf|nr2|nr1|nr|nnt|nnd|nn|nmc|nm|nl|nit|nis|nic|ni|nhm|nhd>+<vi>?}
        """


def parse_tree1(parent):
    """
    遍历树节点,返回节点列表
    """
    text=[]
    for node in parent:
        if type(node) is nltk.Tree:
            # print(node)
            if node.label() == 'NP':   
            
                text.append(''.join(node_child[0].strip() for node_child in node.leaves())+"/NP")
            if node.label() == 'VP':
                text.append(''.join(node_child[0].strip() for node_child in node.leaves())+"/VP")
        else: # 如果不是树,就是没有分叉,那就是叶子节点了
            if node[1] in keep_pos_p:  # set(['p','pbei','pba'])
                text.append(node[0].strip()+"/PP")
            if node[0] in huanhang : # 中文的换行结束
                text.append(node[0].strip()+"/O")                  
            if node[1] not in merge_pos:
                text.append(node[0].strip()+"/O")                           
            #print("hh")
    return text


def gram_reg(sentence):   
    """
    返回语法树列表,按指定的语法分隔短语列表
    """
    gram1 = grammar1
    cp = nltk.RegexpParser(gram1)
    try :
        # 输入的是切词的结果,tuple列表(单词,词性):[('工作', 'vn'), ('描述', 'v'), ('：', 'w'), ('我', 'rr'), ('曾', 'd'), ('在', 'p')]
        word_pos_list = lp.to_list_with_tuple(sentence)
        result = cp.parse(word_pos_list) 
        # print(result)
    except:
        return ""
    else:
        return parse_tree1(result)

from tpf.lgg.cfg import Cfg 
fg = Cfg()

def gram_cfg(sentence, str_gram_fmt, show_draw=False):   
    return fg.cfg(words=sentence, str_gram_fmt=str_gram_fmt, show_draw=show_draw)
