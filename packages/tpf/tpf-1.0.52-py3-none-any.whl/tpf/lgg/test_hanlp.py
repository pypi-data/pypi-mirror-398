
#https://github.com/hankcs/HanLP
#pip install hanlp -i https://pypi.tuna.tsinghua.edu.cn/simple
#pip install jpype1  -i https://pypi.tuna.tsinghua.edu.cn/simple

import hanlp
HanLP = hanlp.load(hanlp.pretrained.mtl.CLOSE_TOK_POS_NER_SRL_DEP_SDP_CON_ELECTRA_SMALL_ZH) # 世界最大中文语料库

word_list = ['2021年HanLPv2.1为生产环境带来次世代最先进的多语种NLP技术。', '阿婆主来到北京立方庭参观自然语义科技公司。']

#Downloading https://file.hankcs.com/hanlp/mtl/close_tok_pos_ner_srl_dep_sdp_con_electra_small_20210111_124159.zip to /home/xt/.hanlp/mtl/close_tok_pos_ner_srl_dep_sdp_con_electra_small_20210111_124159.zip
res = HanLP(word_list)

print(res)

