"""主要内容
- Encoder
- Decoder
- FullyConnectedOutput 
  - 全连接输出层
  - 带激活函数，层归一化
"""

import torch 
from torch import nn 
from tpf.att import MultiHead


# 全连接输出层
class FullyConnectedOutput(torch.nn.Module):
    """先放大4倍后收缩至原维度的全连接输出层,使用短接进行微调
    - 特征数先变大再变小
    - 并且是变回原来的大小，这样才能使用短接相加 
    """
    def __init__(self,features=32):
        super().__init__()
        self.fc = torch.nn.Sequential(
            torch.nn.Linear(in_features=features, out_features=features*4),
            torch.nn.ReLU(),
            torch.nn.Linear(in_features=features*4, out_features=features),
            torch.nn.Dropout(p=0.1)
        )

        self.norm = torch.nn.LayerNorm(normalized_shape=features,
                                       elementwise_affine=True)

    def forward(self, x):
        # 保留下原始的x,后面要做短接用
        clone_x = x.clone()

        # 单词维度归一化
        x = self.norm(x)

        # 线性全连接运算
        # [b, seq_len, feature_nums] -> [b, seq_len, feature_nums]
        out = self.fc(x)

        # 做短接
        out = clone_x + out

        return out


# 编码器层
class EncoderLayer(nn.Module):
    """编码器层,带补码,使用多头注意力 
    - features:数据的特征维数
    - 编码层是求自注意力
    """
    def __init__(self,features=32,head_num=4):
        """
        - features:特征向量维度，单维，比如单词向量的维度，
        - head_num：多头个数
        """
        super().__init__()
        # 多头注意力
        self.mh = MultiHead(n_features=features,head_num=head_num)

        # 全连接输出
        self.fc = FullyConnectedOutput(features=features)

    def forward(self, x, mask):
        """单层的编码器层
        - x : [batch_size, seq_len, feature_nums]格式的数据
        - mask: [batch_size, seq_len]格式的01矩阵，1为补，不参与得分计算
        """
        # 计算自注意力,维数不变
        # [b, seq_len, feature_nums] -> [b, seq_len, feature_nums]
        score = self.mh(x, x, x, mask)

        # 全连接输出,维数不变
        # [b, seq_len, feature_nums] -> [b, seq_len, feature_nums]
        out = self.fc(score)

        return out



# 解码器层
class DecoderLayer(torch.nn.Module):
    """求y相对x的注意力，带补码，使用多头注意力
    模型对象参数
    - x.shape默认为[B,C,L]
    - x.shape默认为[B,C,L]
    """
    def __init__(self,features=32):
        super().__init__()

        # 自注意力提取输入的特征
        self.mh1 = MultiHead(features=features)
        
        # 融合自己的输入和encoder的输出
        self.mh2 = MultiHead(features=features)
        
        # 全连接输出
        self.fc = FullyConnectedOutput(features=features)

    def forward(self, x, y, mask_pad_x, mask_tril_y):
        # 先计算y的自注意力,维度不变
        # [b, 50, 32] -> [b, 50, 32]
        y = self.mh1(y, y, y, mask_tril_y)

        # 结合x和y的注意力计算,维度不变
        # [b, 50, 32],[b, 50, 32] -> [b, 50, 32]
        y = self.mh2(y, x, x, mask_pad_x)

        # 全连接输出,维度不变
        # [b, 50, 32] -> [b, 50, 32]
        y = self.fc(y)

        return y



class Encoder(torch.nn.Module):
    def __init__(self, features=32, head_num=4):
        """编码器
        - features:序列元素特征维度个数，编码器不变换序列元素的位置，只变换元素特征的维度
        - head_num:多头的个数
        
        examples
        ----------------------------------------------
        import torch
        from torch import nn
        from tpf.seq import PositionEmbedding

        batch_size = 3
        seq_len = 7 
        elem_nums = 36
        embedding_dim = 32
        data = torch.randint(0,high=elem_nums,size=(batch_size,seq_len))
        pos = PositionEmbedding(seq_len=seq_len,num_embeddings=elem_nums,embedding_dim=embedding_dim)
        x = pos(data)
        x.shape  #torch.Size([3, 7, 32])
        
        from tpf.layer import Encoder
        encoder = Encoder(features=embedding_dim, head_num=4)
        x = encoder(x,None)
        x.shape   #torch.Size([3, 7, 32])
        
        from tpf.vec3 import mask_pad
        #data.shape=[batch_size,seq_len]=[3,7]
        mask_x = mask_pad(data,padding_index=0)  #假定0为补码索引
        mask_x.shape  #torch.Size([3, 1, 7, 7])
        x = encoder(x,mask_x)
        x.shape   #torch.Size([3, 7, 32])
        
        
        example 2 
        -------------------------------------------------
        from tpf.nlp.ts11 import Transformer11
        Transformer11是一个完整的Encoder使用的示例 

        """
        super().__init__()
        self.layer_1 = EncoderLayer(features=features,head_num=head_num)
        self.layer_2 = EncoderLayer(features=features,head_num=head_num)
        self.layer_3 = EncoderLayer(features=features,head_num=head_num)

    def forward(self, x, mask):
        """ 
        - x:[batch_size,seq_len,embedding_dim]格式的数据
        - mask:None-表示序列位置上皆是单词元素，无补
        
        
        

        """
        x = self.layer_1(x, mask)
        x = self.layer_2(x, mask)
        x = self.layer_3(x, mask)
        return x



class Decoder(torch.nn.Module):
    """解码器
    模型对象参数
    - x:[B,L,C]
    - y:[B,L,C]
    - mask_pad_x:[B,1,L,L],01布尔矩阵
    - mask_tril_y:[B,1,L,L],01布尔矩阵
    """
    def __init__(self,features=32):
        super().__init__()

        self.layer_1 = DecoderLayer(features=features)
        self.layer_2 = DecoderLayer(features=features)
        self.layer_3 = DecoderLayer(features=features)

    def forward(self, x, y, mask_pad_x, mask_tril_y):
        """多层解码器变换，每次输入都是编码器x，即x不变 
        """
        y = self.layer_1(x, y, mask_pad_x, mask_tril_y)
        y = self.layer_2(x, y, mask_pad_x, mask_tril_y)
        y = self.layer_3(x, y, mask_pad_x, mask_tril_y)
        return y
