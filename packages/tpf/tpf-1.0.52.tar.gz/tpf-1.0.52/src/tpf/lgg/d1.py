
"""
数据转矩阵常用处理方法 

"""

from functools import total_ordering
from pickle import TRUE
from nltk import tokenize

from numpy.lib.financial import rate
from torch.nn.modules.activation import LogSoftmax
from torch.utils.data import Dataset  
import os ,torch ,time 
import torch.nn as nn 
import scipy.io.wavfile as wav 
from scipy import signal 
import numpy as np 
from tpf.py1.fil import mkdir 
from tpf.box.d1 import pkl_load,pkl_save,write,read,json_load
import jieba 


"""
步骤概述:
DataLoader批次加载数据
model模型输出并求得与标签的差异,即损失函数计算
optim模型优化
"""



def id2word(word2id):
    id2word = {}
    for key in word2id:
        id2word[word2id[key]] = key 
    return id2word 

def word2id(dict_file=None):
    """
    从文件中读取单词字典
    """
    if dict_file: # 文件存在时,优先读取文件 
        tmp_dict_file = dict_file+".wid"
        if os.path.exists(tmp_dict_file):
            word2id = read(tmp_dict_file)
        else:
            if dict_file.endswith(".pkl"):
                word2id = pkl_load(dict_file)
            elif  dict_file.endswith(".speech"):
                with open(dict_file,"r",encoding="utf-8") as f:
                    word2id = eval(f.read())
            elif  dict_file.endswith(".json"):
                word2id = json_load(dict_file)
        return word2id 


def addict(kv_dict, key, val):
    """
    向字典中添加新的key/val,
    字库的个数是网络最后一层的标签个数,在整个训练过程不可变；因此,在训练之前,要完成字库的更新
    """
    res = key in list(kv_dict.keys()) 
    if not res:
        kv_dict[key] = val 


def dict_addkv(kv_dict=None, dict_file=None, key="-", val=0):
    """
    读取字典文件,并且添加一对<key,val>,原来的key的ID变更为字典长度

    返回两个字典
    -----------------------------
    word2id, id2word
    """
    if kv_dict:
        _word2id = kv_dict  
    elif dict_file:
        _word2id = word2id(dict_file)
    _id2word =  id2word(_word2id)

    _old_key = _id2word[val]
    # _old_val = word2id[_old_key]

    last_num = len(_word2id)

    _word2id[key] = val 
    _word2id[_old_key] = last_num

    _id2word[val] = key 
    _id2word[last_num] = _old_key 


    return _word2id ,_id2word 


def onehot_text(text, split_flag="\n"):
    """
    一个段落 或 一句话 的独热编码 

    目前的独热编码,如果句子有重复的字或词,则按一个字或词计算 

    示例
    ---------------------------------------
    ss = "啊哈舍不得璀璨俗世,啊哈躲不开痴恋的欣慰,啊哈找不到色相代替,啊哈参一生参不透这条难题"
        
    onehot_text(ss,split_flag=",")


    return
    -------------------------------
    段落的向量表示,分词列表,去重排序后的词条

    """
    
    # 原始词列表 
    ss = text 
    word_all = ""
    if split_flag == "":  # 按空白切词
        token_segments = ss.split()
    else:
        token_segments = ss.split(split_flag)  # 划分句子或段落
    # print(token_segments)
    for seg in token_segments:
        word_all = word_all + seg 
    words = jieba.lcut(word_all)           # 词汇列表 

    vocab = sorted(set(words))      # 去重后的词条 

    row_size = len(words)           # 某个词在整个段落或句子中的位置 
    col_size = len(vocab)           # 多少个不重复的词或特征 ,某个词条在向量中的位置 

    #初始化0矩阵
    import numpy as np 
    onehot_vector = np.zeros((row_size,col_size),dtype=int)

    for i,word in enumerate(words):
        onehot_vector[i,vocab.index(word)] = 1 

    return onehot_vector,words,vocab

def words_bag(text, split_flag="\n"):
    # 原始词列表 
    ss = text 
    word_all = ""
    if split_flag == "":  # 按空白切词
        token_segments = ss.split()
    else:
        token_segments = ss.split(split_flag)  # 划分句子或段落
    # print(token_segments)
    for seg in token_segments:
        word_all = word_all + seg 
    words = jieba.lcut(word_all)           # 词汇列表 
    sentence_bow = {}
    for token in words:
        if token in list(sentence_bow.keys()):
            sentence_bow[token] += 1
        else:
            sentence_bow[token] = 1
    wbg = sorted(sentence_bow.items()) 

    return list(wbg)






# # 统一的音频窗口大小  
# n_per_seg = 512

# class TextDataSet(Dataset):
#     def __init__(self, base_dir = None, filname_nosuffix=None,  
#                 suffix=".wav", suffix_label=".wav.trn", dict_file=None, 
#                 nperseg=n_per_seg, istrain=True, dict_split_word=False,tmp_dir=None) -> None:
#         """
#         读取目录下的音频以及对应的标签 

#         filname_nosuffix:读取单个文件,用于预测,不需要有目录和后缀

#         use_word=True,在训练时遇到不存在的字或单词,会按空格分隔标签,以单词的方式更新字库 

#         """
        
#         super().__init__()

#         file_paths = []
#         if filname_nosuffix:
#             print(filname_nosuffix)
#             if filname_nosuffix.endswith(suffix):
#                 filname_nosuffix = filname_nosuffix.split(suffix)[0]
  
#             fil = os.path.join(base_dir, filname_nosuffix)
#             file_paths.append(fil)


#         else:
#             # 获取文件夹下所有的文件 
#             file_names = os.listdir(base_dir)
            
#             for name in file_names:
#                 if name.endswith(suffix):
#                     name = name.split(".")[0]   # 只取文件的名字 
#                     fil = os.path.join(base_dir,name)
#                     file_paths.append(fil)
#         self._file_paths = file_paths 
#         self._suffix = suffix
#         self._suffix_label = suffix_label


#         self._word2id = word2id(dict_file)
            
#         # 字典的更新是针对目录下所有音频标签的,不是单个音频标签 
#         if istrain: # 训练前更新字库,预测不更新 
#             print("before:---------",len(self._word2id))
#             self.updatedict(dict_split_word=dict_split_word)
#             print("after:----------", len(self._word2id))

#             if tmp_dir:
#                 dict_file = os.path.join(tmp_dir,"new_word2id.wid")
#             else:
#                 if not dict_file.endswith(".wid"):
#                     dict_file = dict_file+".wid"
#             write(self._word2id, dict_file)

#         self._nperseg = nperseg

#         # 总的字符的个数 
#         self._n_word = len(self._word2id)

#     def __len__(self):
#         """
#         添加该方法就可以对对象使用len()方法
#         """
#         return len(self._file_paths)

#     def __getitem__(self,index):
#         """
#         index:每几个文件 

#         将音频数据转为机器学习的数据

#         return
#         -------------------------------------
#         (x,y)

#         x[:,j]为一个字在一个时间片(也叫时间步)上的频率

#         y[i]一个字对应的id
        
#         """
#         name = self._file_paths[index]
#         wavpath = name + self._suffix 
#         labpath = name + self._suffix_label 
#         sample_rate,wave = wav.read(wavpath)

#         # print("sample_rate:",sample_rate,wave.shape)

#         with open(labpath,"r",encoding="utf-8") as f:
#             text = f.readline()
#             text = text.replace(" ","")
#             text = text.replace("\n","")

#         if not self._nperseg:  # 窗口应该随采样率缩放,仅个人猜测 
#             self._nperseg = int(sample_rate/32)


#         # stft
#         f,t,z = signal.stft(wave, fs=sample_rate, nperseg=self._nperseg)
#         # print("after stft:",z.shape)
        
#         z = np.abs(z)
        

#         # 转置,原来的行对应着同一时间片(也叫时间步)的不同频率,比如有200Hz,1000Hz等
#         # 原来的列,代表的一片片时间
#         # 转置后,不同的频率转为列,即成为机器学习中所讲的特征,代表着不同的频率
#         # 转置后,行方向上,代表时一片片时间,从小到大,是时间的递增 
#         z = z.T  
#         # print("T stft:",z.shape)
#         T,C = z.shape
#         x = torch.tensor(z, dtype=torch.float32)

#         # 标准化 
#         x -= x.mean() 
#         x /= (x.std() + 1e-6)

#         # 文本标签转换为ID
#         textid = [self._word2id.get(i,0) for i in text] 
#         label = torch.tensor(textid,dtype=torch.long)


#         # 代表一个音频文件中有多少个字符,一个字符对应多个时间步 
#         N = len(label)  

#         nx = T 
#         nd = N 

#         # print("每个文件shape",x.shape)

#         return (x, nx, label, nd)

#     def __addict(self,key):
#         """
#         字库的个数是网络最后一层的标签个数,在整个训练过程不可变；因此,在训练之前,要完成字库的更新
#         """
#         res = key in list(self._word2id.keys()) 
#         self._n_word = len(self._word2id)
#         if not res:
#             self._word2id[key] = self._n_word
#             self._n_word = len(self._word2id)

#     def updatedict(self, dict_split_word=False):
#         """
#         use_word表示使用单词,而非单个的字作为标签 
#         """
#         all_word = []
#         for lab in self._file_paths:
#             labpath = lab + self._suffix_label 
#             # print(labpath)
#             with open(labpath,"r",encoding="utf-8") as f:
#                 text = f.readline()
#                 if dict_split_word:
#                     text = text.split()  
#                 else:
#                     text = text.replace(" ","")
                
#                 tmp = [i for i in text] 
#                 all_word.extend(tmp)
#         all_word_set = set(all_word)
#         for w in all_word_set:
#             self.__addict(w)
#     def feature_count(self):
#         x, nx, label, nd = self.__getitem__(0)
#         T,C = x.shape
#         return C 

# def dataset_test():
#     BASE_DATA_DIR = "/opt/aisty/73_code/data/yuyin/ai40"
#     WAV_DIR = os.path.join(BASE_DATA_DIR, "wav1/")
#     # WAV_DIR = os.path.join(BASE_DATA_DIR, "data_thchs30/")
#     # WAV_DIR = os.path.join(BASE_DATA_DIR, "data_example/")
#     DICT_FILE = os.path.join(BASE_DATA_DIR, "ckpt/word2id.speech")

#     # 指定目录,通常是训练集
#     dataset  = TextDataSet(istrain=True, dict_file=DICT_FILE, base_dir=WAV_DIR)
#     print(len(dataset))   # 文件个数 
#     print("特征个数:",dataset.feature_count())
#     for i in range(len(dataset)):
#         x, nx, label, nd = dataset[i]
#         print(x.shape,label.shape)

#     # 指定单个文件,通常是预测文件
#     dataset  = TextDataSet(istrain=False, dict_file=DICT_FILE, base_dir=WAV_DIR,filname_nosuffix="a0011")
#     print(len(dataset))   # 文件个数 
#     for i in range(len(dataset)):
#         x, nx, label, nd = dataset[i]
#         print(x.shape,label.shape)


# from torch.nn.utils.rnn import pad_sequence 
# from torch.utils.data import DataLoader 


# class TextDataLoader():
#     def __init__(self, base_dir = None, filname_nosuffix=None,  
#                 suffix=".wav", suffix_label=".wav.trn", dict_file=None, 
#                 nperseg=n_per_seg, istrain=True,tmp_dir=None) -> None:

#         # 初始化数据集 
#         self._dataset  = TextDataSet(base_dir = base_dir, 
#         filname_nosuffix=filname_nosuffix,
#         suffix=suffix,suffix_label=suffix_label,
#         dict_file=dict_file,
#         nperseg=nperseg,istrain=istrain,
#         tmp_dir=tmp_dir)
        
#         self._feature_count = self._dataset.feature_count()
#         self._word2id = self._dataset._word2id


#     def data_deal_last(self,batch):
#         """
#         补0操作

#         数据后处理,按批次进行,即每个批次的数据处理完毕后,会调用该方法,进行一次后处理 
#         """
#         # xs:输入的波形,ds输入的标签 
#         xs,ds = [],[] 
#         # xs,ds对应的数据长度 
#         nx,nd = [],[]

#         for x,lx,d,ld in batch:
#             xs.append(x)
#             ds.append(d)
#             nx.append(lx)
#             nd.append(ld)

#         xs = pad_sequence(xs).float()

#         # 这里是按批次处理的,所以有批次的维度 
#         ds = pad_sequence(ds,batch_first=True).long()

#         nx = torch.Tensor(nx).long()
#         nd = torch.Tensor(nd).long()

#         return xs, ds, nx, nd 

#     def data_loader(self, batch_size=32, num_workers=1, collate_fn=None):
#         """
#         通过DataSet获取多个样本,组成一个batch的数据  
#         num_workers,使用几个进行,windows系统只能用一个进程   
#         """
#         if collate_fn:
#             dataloader = DataLoader(dataset=self._dataset,batch_size=batch_size,shuffle=True,collate_fn=collate_fn, num_workers=num_workers)
#         else:
#             dataloader = DataLoader(dataset=self._dataset,batch_size=batch_size,shuffle=True,collate_fn=self.data_deal_last, num_workers=num_workers)
#         return dataloader


# def data_loader_test(batch_size=32):
#     BASE_DATA_DIR = "/opt/aisty/73_code/data/yuyin/ai40"
#     WAV_DIR = os.path.join(BASE_DATA_DIR, "wav1/")
#     # WAV_DIR = os.path.join(BASE_DATA_DIR, "data_thchs30/")
#     # WAV_DIR = os.path.join(BASE_DATA_DIR, "data_example/")
#     DICT_FILE = os.path.join(BASE_DATA_DIR, "ckpt/word2id.speech")

#     # 指定音频目录,音频与标签的后缀,字典文件,是否为训练 四个参数
#     dl = TextDataLoader(base_dir = WAV_DIR, suffix=".wav", suffix_label=".wav.trn", dict_file=DICT_FILE, istrain=True)
#     train_dataloader = dl.data_loader(batch_size=batch_size)

#     epoch = 1 

#     for i in range(epoch):
#         # dataloader自己实现了一个迭代器
#         # 经过dataloader处理的数据,每个数据都是一个batch的数据 
#         for x,d,nx,nd in  train_dataloader:
#             print(x.shape,d.shape)

# # data_loader_test()
# # dataset_test()

