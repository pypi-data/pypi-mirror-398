
from tpf.nlp.tsfm import  Transformer


"""
序列类问题通用方法
"""
import torch 
from torch import nn 

from tpf.nlp.tsfm import Transformer



##----------------------------------------------------
## 位置编码 - 开始
##----------------------------------------------------

import math


# 位置编码层
class PositionEmbedding(nn.Module):
    def __init__(self,seq_len=50,num_embeddings=39,embedding_dim=32):
        """附带位置信息，针对矩阵中每个元素的位置产生一个区别于其他位置的数值加到原矩阵对应元素上
        - 融合了元素在序列中的位置信息，以及每个元素向量元素的位置信息，
        - 相当于生成了一份[seq_len,embedding_dim]shape的矩阵，
        - 使得每个元素位置都产生一个不同于其他位置的数值 
        - seq_len:序列长度，单词/事物/元素的长度
        - embedding_dim：每个元素使用embedding_dim长度的向量表示 
        
        examples
        -----------------------------------------------------------------
        import torch
        from torch import nn
        from tpf.seq import PositionEmbedding

        batch_size = 3
        seq_len = 7 
        nums = 36
        embedding_dim = 32
        data = torch.randint(0,high=nums,size=(batch_size,seq_len))
        pos = PositionEmbedding(seq_len=seq_len,num_embeddings=nums,embedding_dim=embedding_dim)

        embed = pos(data)
        embed.shape

        """
        super().__init__()

        # pos是第几个词,i是第几个维度,d_model是维度总数
        def get_pe(pos, i, d_model):
            temp = 1e4 ** (i / d_model)
            pe = pos / temp

            if i % 2 == 0:
                return math.sin(pe)
            return math.cos(pe)

        # 初始化位置编码矩阵
        pe = torch.empty(seq_len, embedding_dim)
        for i in range(seq_len):#第几个词
            for j in range(embedding_dim):#第几个维度
                pe[i, j] = get_pe(i, j, embedding_dim)

        pe = pe.unsqueeze(0)  #增加一个批次维度

        # 定义为不更新的常量
        self.register_buffer('pe', pe)

        # 词编码层,39=26+10+3
        self.embed = torch.nn.Embedding(num_embeddings, embedding_dim)
        
        # 初始化参数
        self.embed.weight.data.normal_(0, 0.1)

    def forward(self, x):
        # [8, 50] -> [8, 50, 32]
        embed = self.embed(x)

        # 词编码和位置编码相加
        # [8, 50, 32] + [1, 50, 32] -> [8, 50, 32]
        embed = embed + self.pe
        return embed


# 线性位置编码层
class PositionLinear(nn.Module):
    def __init__(self, seq_len=50, in_features=39, out_features=32):
        """线性变换附带位置信息，针对矩阵中每个元素的位置产生一个区别于其他位置的数值加到原矩阵对应元素上
        - 融合了元素在序列中的位置信息，以及每个元素向量元素的位置信息，
        - 相当于生成了一份[seq_len,embedding_dim]shape的矩阵，
        - 使得每个元素位置都产生一个不同于其他位置的数值 
        - seq_len:序列长度，单词/事物/元素的长度
        - embedding_dim：每个元素使用embedding_dim长度的向量表示 
        
        examples
        -----------------------------------------------------------------
        import torch
        from torch import nn
        batch_size    = 128     # 批次
        seq_len       = 64         # 相邻交易个数   
        col_nums      = 13        # 1行数据13列
        embedding_dim = 128  # 特征变换维度
        data          = torch.randn(batch_size, seq_len, col_nums)

        from tpf.seq import PositionLinear
        pos = PositionLinear(seq_len=seq_len, in_features=col_nums, out_features=embedding_dim)
        embed = pos(data)
        embed.shape        #torch.Size([128, 64, 128])

        """
        super().__init__()

        # pos是第几个词,i是第几个维度,d_model是维度总数
        def get_pe(pos, i, d_model):
            temp = 1e4 ** (i / d_model)
            pe = pos / temp

            if i % 2 == 0:
                return math.sin(pe)
            return math.cos(pe)

        # 初始化位置编码矩阵
        pe = torch.empty(seq_len, out_features)
        for i in range(seq_len):#第几个词
            for j in range(out_features):#第几个维度
                pe[i, j] = get_pe(i, j, out_features)

        pe = pe.unsqueeze(0)  #增加一个批次维度

        # 定义为不更新的常量
        self.register_buffer('pe', pe)

        # 词编码层,39=26+10+3
        self.embed = nn.Linear(in_features=in_features, out_features=out_features)
        
        # 初始化参数
        self.embed.weight.data.normal_(0, 0.1)

    def forward(self, x):
        # [8, 50] -> [8, 50, 32]
        embed = self.embed(x)

        # 词编码和位置编码相加
        # [8, 50, 32] + [1, 50, 32] -> [8, 50, 32]
        embed = embed + self.pe
        return embed


# 位置编码层
class PositionLinear2(nn.Module):
    def __init__(self,seq_len=100, in_feature=200, embedding_dim=256):
        """线性位置编码，自定义线性函数
        
        examples
        --------------------------------------------
        import math
        import torch
        from torch import nn
        
        class pc:
            batch_size = 64
            max_seq_len=100
            col_nums = 13
            embedding_dim=128
            
        #[B,L,C],一个序列100条交易，一条交易13个特征/列  
        data = torch.randn(pc.batch_size,pc.max_seq_len,pc.col_nums)


        """
        super().__init__()
        self.w = nn.Parameter(torch.ones(in_feature, embedding_dim, dtype=torch.float32),requires_grad=True)
        self.b = nn.Parameter(torch.ones(embedding_dim, dtype=torch.float32), requires_grad=True)
        self.norm = torch.nn.LayerNorm(normalized_shape=embedding_dim,
                                        elementwise_affine=True)
        # pos是第几个词,i是第几个维度,d_model是维度总数
        def get_pe(pos, i, d_model):
            temp = 1e4 ** (i / d_model)
            pe = pos / temp

            if i % 2 == 0:
                return math.sin(pe)
            return math.cos(pe)

        # 初始化位置编码矩阵
        pe = torch.empty(seq_len, embedding_dim)
        for i in range(seq_len):#第几个序列
            for j in range(embedding_dim):#第几个维度
                pe[i, j] = get_pe(i, j, embedding_dim)

        pe = pe.unsqueeze(0)

        # 定义为不更新的常量
        self.register_buffer('pe', pe)
        
        # 初始化参数
        # self.w.weight.data.normal_(0, 0.1)

    def forward(self, x):
        # [B, seq_len, C] -> [B, seq_len, embedding_dim]
        embed = x@self.w + self.b 
        # 特征维度归一化
        x = self.norm(embed)
        
        # 词编码和位置编码相加
        # [B, C, embedding_dim] + [1, C, embedding_dim] -> [B, C, embedding_dim] 
        embed = x + self.pe
        return embed


##----------------------------------------------------
## 位置编码 - 结束
##----------------------------------------------------




























