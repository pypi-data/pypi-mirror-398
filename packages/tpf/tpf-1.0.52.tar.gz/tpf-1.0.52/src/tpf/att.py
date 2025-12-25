# coding=utf-8
"""文件功能描述
多头注意力计算 

"""
import random 
import math
import torch
from torch import nn
from torch.nn import functional as F



def attention(Q, K, V, mask=None, multihead=False):
    """序列数据注意力计算函数
    - [batch_size,seq_len,embedding_dim],embedding_dim是要变换的维度
    - 变换的是特征维度，特征维度放在最后的一个维度上 
    - 序列的维度放在倒数第2维上
    - embedding_dim:大于0表示使用多头注意力，其值是数据原来的维度，即embedding_dim，多头合并为embedding_dim

    params
    -----------------------------------
    - seq_len：序列特征个数,[B,L,C]中的L
        Q (_type_): _description_
        K (_type_): _description_
        V (_type_): _description_
        mask (_type_): _description_

    """
    
    # b句话,每句话50个词,每个词编码成32维向量,4个头,每个头分到8维向量
    # Q,K,V = [b, 4, 50, 8]
    n_shape = len(Q.shape)

    # [b, 4, 50, 8] * [b, 4, 8, 50] -> [b, 4, 50, 50]
    # Q,K矩阵相乘,求每个词相对其他所有词的注意力
    if n_shape == 4: #embedding被拆分，多头注意力
        seq_len = Q.shape[2]
        score = torch.matmul(Q, K.permute(0, 1, 3, 2))
    elif n_shape == 3:
        seq_len = Q.shape[1]
        score = torch.matmul(Q, K.permute(0, 2, 1))
    else:
        raise Exception(f"only 3 or 4 dim,now is {n_shape}")
        

    # 除以每个头维数的平方根,做数值缩放
    k = Q.shape[-1]
    score /= k ** 0.5

    # mask 遮盖,mask是true的地方都被替换成-inf,这样在计算softmax的时候,-inf会被压缩到0
    # mask = [b, 1, seq_len, seq_len]
    if mask is not None:
        score = score.masked_fill_(mask, -float('inf'))

    score = torch.softmax(score, dim=-1)

    # 以注意力分数乘以V,得到最终的注意力结果
    # [b, 4, 50, 50] * [b, 4, 50, 8] -> [b, 4, 50, 8]
    score = torch.matmul(score, V)

    # 每个头计算的结果合一
    # [b, 4, 50, 8] -> [b, 50, 32]
    if multihead :
        head_n = Q.shape[1]
        k = Q.shape[-1]
        embedding_dim = head_n*k
        score = score.permute(0, 2, 1, 3).reshape(-1, seq_len, embedding_dim)

    return score


# Luong attention layer
class Attn(nn.Module):
    def __init__(self, method, hidden_size):
        """ 求解码矩阵相对编码矩阵的注意力 
        描述
          - 计算一句话中各个单词对输入单词的重要程度；
        
        输入参数
          - method：['dot', 'general', 'concat']中的一个 
          - hidden_size：输出单词特征数，单个单词以及批次单词的维数都是这个 
            - 大前提：求A相对B的注意力，A与B中向量的维数必须一致，指的是同一类事物，所以hidden_size就是特征数
            - hidden：输出单词
            - hidden的shape皆为[1, batch_size, hidden_size]
            - encoder_outputs.shape=[seq_len, batch_size, hidden_size]
          
        返回结果
          - 一个单词hidden与encoder_outputs seq_len个单词的得分(做了softmax总和为1)
          - 返回结果shape=[batch_size,1,seq_len]
          - sum(dim=2)=1,编码一句话中各个单词对输入单词的重要程度
        """
        super(Attn, self).__init__()
        self.method = method
        if self.method not in ['dot', 'general', 'concat']:
            raise ValueError(self.method, "is not an appropriate attention method.")
        
        self.hidden_size = hidden_size
        
        if self.method == 'general':
            # 矩阵相乘就是一系列向量内积
            self.attn = nn.Linear(self.hidden_size, hidden_size)
        elif self.method == 'concat':
            self.attn = nn.Linear(self.hidden_size * 2, hidden_size)
            self.v = nn.Parameter(torch.FloatTensor(hidden_size))

    def dot_score(self, hidden, encoder_output):
        # hidden.shape=[1,64,500],encoder_output.shape=[10,64,500]
        # 1个单词，64个批次，500为hidden的大小,这是按批次 对一个单词 转换后的矩阵
        # MAX_LENGTH = 10,句子最大长度为10,最后一个字符为EOS
        # 单词维度　位乘(按位置相乘)，再相加,sum之后单词这个维度消失
        # [sel_len,batch_size]
        # [1,64,500][10,64,500]=> [10,64,500][10,64,500]=>[10,64]=[sel_len,batch_size]
        # 位乘再相加，实际就是向量点乘，通常的点乘指两个向量之间的位乘再相加
        # 一个单词长度为hidden_size的向量，这样的单词有seq_len*batch_size个
        # 将它们按[sel_len,batch_size,hidden_size]的方式存放
        # 真实计算的时候，仍然是两个单词(hidden_size维度)之间的点乘
        # 每两个单词之间向量点乘之后，得到一个数字，这个数字近似代表了两个单词之间的相似程度
        # 这个单词与[sel_len,batch_size]个单词进行了点乘，就得到了[sel_len,batch_size]个结果
        # 这就是序列到序列，注意力提取特征的关键
        # 这里为什么不使用矩阵相乘呢？
        # 如果是矩阵相乘，那么[64,500]@[64,500]shape对不上，
        # 就算将其中一个矩阵转置，得到的却是[64,64]或[500,500]这样的方阵 
        # 回顾初衷，要求的是输入序列每个单词相对hidden的一个得分,那么应该选[64,64]这样的shape
        # 然后再把[64,64]的shape或sum或mean转化为[64]这样的shape可以吗？
        # 可不可以，本人没试，就算可以，也没有点乘来得直接 
        # 这里也体现了点乘（向量内积）与矩阵乘法的区别：
        # 矩阵乘法是向量内积按一定格式/规律计算的过程，前一个矩阵的首与后一个矩阵的尾维度相等，首尾同
        # 而向量内积的使用，除了矩阵乘法的计算方法外，
        # 还可以按矩阵shape一致的方式计算，首与首同，尾与尾同，即同shape计算
        return torch.sum(hidden * encoder_output, dim=2)

    def general_score(self, hidden, encoder_output):
        # 相当于用ht向量与编码层的每个向量进行向量内积运算
        # 得到编码层每个单词输出的得分，或叫做百分比
        energy = self.attn(encoder_output)

        # 编码层的输出与得分点乘再相加
        return torch.sum(hidden * energy, dim=2)

    def concat_score(self, hidden, encoder_output):
        energy = self.attn(torch.cat((hidden.expand(encoder_output.size(0), -1, -1), encoder_output), 2)).tanh()
        return torch.sum(self.v * energy, dim=2)

    def forward(self, hidden, encoder_outputs):
        """
        描述
          - 计算一句话中各个单词对输入单词的重要程度；
        
        输入参数
          - hidden：输出单词
          - hidden的shape皆为[1, batch_size, hidden_size]
          - encoder_outputs.shape=[seq_len, batch_size, hidden_size]
          
        返回结果
          - 一个单词hidden与encoder_outputs seq_len个单词的得分(做了softmax总和为1)
          - 返回结果shape=[batch_size,1,seq_len]
          - sum(dim=2)=1,编码一句话中各个单词对输入单词的重要程度
        """
        # Calculate the attention weights (energies) based on the given method
        if self.method == 'general':
            attn_energies = self.general_score(hidden, encoder_outputs)
        elif self.method == 'concat':
            attn_energies = self.concat_score(hidden, encoder_outputs)
        elif self.method == 'dot':
            attn_energies = self.dot_score(hidden, encoder_outputs)

        # Transpose max_length and batch_size dimensions
        # [sel_len,batch_size] --> [batch_size,sel_len]
        attn_energies = attn_energies.t()

        # 按seq_len维度转为概率,[batch_size,seq_len]
        # [batch_size,seq_len] --> [batch_size, 1, seq_len] 添加这个１是为了后面进行bmm
        attn_weights = F.softmax(attn_energies, dim=1).unsqueeze(1)
        

        
        # Multiply attention weights to encoder outputs to get new "weighted sum" context vector
        # encoder_outputs.shape=[seq_len,batch_size,hidden_size]
        # encoder_outputs.transpose(0, 1).shape = [batch_size,seq_len,hidden_size]
        # attn_weights.shape = [batch_size, 1, seq_len]
        # bmm [1, seq_len]@[seq_len,hidden_size] = [batch_size,1,hidden_size]
        # context.shape = [batch_size,1,hidden_size]
        # decoder中每个单词对应一个encoder的上下文向量
        # 加权平均，[1, seq_len] sum(dim=1)=1，注意力的得分之和为1，将这个得分乘到原来解码器上
        context = attn_weights.bmm(encoder_outputs.transpose(0, 1))
        
        return context




# 多头注意力计算层
class MultiHead(nn.Module):
    """多头注意力计算
    - 这里将向量特征拆分为四个部分，四头
    - 输入:[batch_size,seq_len,embedding_dim]
    - 输出:[batch_size,seq_len,embedding_dim]
    - 因为使用了短接，所以输入与输出的特征维度不变 
    """
    def __init__(self, n_features=32, head_num=4):
        """多头注意力计算层
        - n_features:特征数，最后是4的整数倍，会拆分成4个头，也叫hidden_size/embedding_dim 
        - 拆分的是特征向量n的维度 
        
        - 主要逻辑，以一句为例，不考虑批次
          - [seq_len1,embedding_dim]*[embedding_dim,seq_len2] = [seq_len1,seq_len2] ，序列1中每个单词相对序列2中每个单词的信息
          - [seq_len1,seq_len2]*[seq_len2,embedding_dim] = [seq_len1,embedding_dim],求得序列1中每个单词相对序列2的上下文向量embedding_dim
          - seq_len1就是解码器，seq_len2就是编码器，其他的都是技巧,比如多头，除以维度的开平方，softmax，短接...
          - 
          
        examples
        -------------------------------------------------
        import torch
        from torch import nn
        class pc:
            batch_size=64
            seq_len= 32
            embedding_dim = 128
            head_num = 4

        x = torch.randn(pc.batch_size,pc.seq_len,pc.embedding_dim)

        from tpf.att import MultiHead
        mhead = MultiHead(n_features=pc.embedding_dim,head_num=pc.head_num)
        x = mhead(x,x,x,mask=None)
        x.shape   #torch.Size([64, 32, 128])
                
        """
        super().__init__()
        self.head_num = head_num
        self.norm = nn.LayerNorm(normalized_shape=n_features, elementwise_affine=True)

        # Q 矩阵
        self.fc_Q = nn.Linear(n_features, n_features)
        # K 矩阵
        self.fc_K = nn.Linear(n_features, n_features)
        # V 矩阵
        self.fc_V = nn.Linear(n_features, n_features)


        self.out_fc = nn.Linear(n_features, n_features)

        self.dropout = nn.Dropout(p=0.1)
        
        

    # 注意力计算函数
    def attention(self, Q, K, V, mask=None):
        """注意力计算函数
        - mask: 01布尔矩阵，1代表pad,会被替换为-float('inf')，做softmax时转换为0 

        return 
        --------------------------
        - 上下文向量，shape=[batch_size, seq_len, n_features]


        多头的官方说法
        ------------------------
        可并行运算，有提速作用 
        这样做效果更好一些，具体原因官方未说，个人在代码注释部分有猜测(仅个人观点...)
        
        多头的个人理解
        ------------------------
        如果是全量，就是一个向量32维对上32维，就是整体对整体
        如果是多头，一个区域对应一个区域，有点兵对兵，将对将的意思，
        相比整体，更精细化一些，
        让局部的数据特性呆在局部，不会扩展到全体,
        比如，这里是四分，某个局部数据异常，那么这个异常会被限定在这四分之一

        """
        # print("att.py 179 mask",mask)
        # b句话,每句话50个词,每个词编码成32维向量,4个头,每个头分到8维向量
        # Q, K, V = [b, 4, 50, 8]
        batch_size, head_n1, seq_len, head_n2 = K.shape
        n_features = head_n1*head_n2

        # [b, 4, 50, 8] * [b, 4, 8, 50] -> [b, 4, 50, 50]
        # Q,K矩阵相乘,求每个词相对其他所有词的注意力
        #socre 183: torch.Size([1, 4, 6, 8]) torch.Size([1, 4, 6, 8])
        score = torch.matmul(Q, K.permute(0, 1, 3, 2))


        # 除以每个头维数的平方根,做数值缩放
        score /= head_n2 ** 0.5

        # mask 遮盖,mask是true的地方都被替换成-inf,这样在计算softmax的时候,-inf会被压缩到0
        # mask = [b, 1, 50, 50],[50,50]第二个50指一句话有50个词，第一个50指这句话被复制了50份

        
        # score的[50,50]
        # 第二个50指编码序列一句话有50个词，对应解码序列中的某个词
        # 第一个50是解码序列或者Q 一句话的50个词，每个词有50个特征，每个特征来自编码序列的每个词
        # mask对解码序列有PAD的位置进行了标记，这些位置将来不计算，经softmax会转为0  
        if mask is not None:
            score = score.masked_fill_(mask, -float('inf'))
        score = torch.softmax(score, dim=-1)

        # 以注意力分数乘以V,得到最终的注意力结果
        # [b, 4, 50, 50] * [b, 4, 50, 8] -> [b, 4, 50, 8]
        # 这里是解码序列的每个词都从编码序列的50个词中得到了8个特征，
        # 由于有4个头，这个过程被计算了4份，有点类似多尺度的味道，
        # 即每个解码序列的单词都与 编码序列所有单词 计算了4次，然后再将4次结果合并到一个向量中
        # 确切的说是针对编码序列所有单词的某个部分...因为每个单词的32个特征被拆分成了8，8，8，8四部分
        # 比如夫妻搬家，虽然二人都装货也卸货了，参与了全过程，但男方主要负责重的物品，女方主要负责轻的物品
        # 又比如，大家虽然都在同一软件公司上班，有人从头到尾只负责开发，有人则从头到尾只负责测试
        # 这里面开发跟开发交流的多，测试跟测试交流的多，业务跟业务交流的，保洁跟保洁交流的多
        # 一个单词用32个特征被拆分成 8，8，8，8，从所有单词都用32维向量表示的角度看，
        # 相对应的特征层面有更多的相似性，比如水果[色泽，口感，大小，价格]，
        # 拿起一个水果，这个水果的色泽要与剩下一堆中所有同类水果的色泽对比才更合理一些
        # 这么看的话，又好像没有多尺度了，因为并没有拿色泽这个部分去跟剩下所有特征计算，还是各算各的
        # 那不用多头的话，是个什么情况？
        # 就是水果[一堆特征]与其他水果[一堆特征]进行的计算了，
        # 这么看的话，好像还是细分好点吧...
        # 以上纯属个人猜测，未进行实验验证，如有雷同，纯属巧合... 
        score = torch.matmul(score, V)

        # 每个头计算的结果合一
        # [b, 4, 50, 8] -> [b, 50, 32]
        # score = score.permute(0, 2, 1, 3).reshape(-1, 50, 32)
        score = score.permute(0, 2, 1, 3).reshape(-1, seq_len, n_features)

        return score


    def forward(self, Q, K, V, mask=None):
        """
        
        params
        -------------------------
        - K.shape=[batch_size,seq_len,embedding_dim],embedding_dim对应n_features,
        - mask, 是否为PAD,shap=[B,1,seq_len,seq_len],是true的地方都被替换成-inf,这样在计算softmax的时候,-inf会被压缩到0
        """
        # Q, K, V 指的是 embedding + pe 之后的结果
        # b句话,每句话50个词,每个词编码成32维向量
        # Q,K,V = [b, 50, 32]
        head_n1 = self.head_num
        # 批量
        b = K.shape[0]
        seq_len = K.shape[1]
        n_features = K.shape[2]
        head_n2 = int(n_features/head_n1) 
        if head_n2 != n_features/head_n1:
            raise Exception("请设置特征数为head_n1={}的倍数".format(head_n1))

        # 保留下原始的Q,后面要做短接用
        clone_Q = Q.clone()

        # 规范化
        Q = self.norm(Q)
        K = self.norm(K)
        V = self.norm(V)

        # 线性运算,维度不变
        # [b, 50, 32] -> [b, 50, 32]
        K = self.fc_K(K)
        V = self.fc_V(V)
        Q = self.fc_Q(Q)

        # 拆分成多个头
        # b句话,每句话50个词,每个词编码成32维向量,4个头,每个头分到8维向量
        # [b, 50, 32] -> [b, 4, 50, 8]
        

        Q = Q.reshape(b, seq_len, head_n1, head_n2).permute(0, 2, 1, 3)
        K = K.reshape(b, seq_len, head_n1, head_n2).permute(0, 2, 1, 3)
        V = V.reshape(b, seq_len, head_n1, head_n2).permute(0, 2, 1, 3)


        # 计算注意力
        # [b, 4, 50, 8] -> [b, 50, 32]
        score = self.attention(Q, K, V, mask)

        # 计算输出,维度不变
        # [b, 50, 32] -> [b, 50, 32]
        score = self.dropout(self.out_fc(score))

        # 短接
        score = clone_Q + score
        return score

if __name__ == "__main__":
    print("att.py ----------")
    class pc:
        batch_size=64
        seq_len= 32
        embedding_dim = 128
        head_num = 4

    x = torch.randn(pc.batch_size,pc.seq_len,pc.embedding_dim)

    from tpf.att import MultiHead
    mhead = MultiHead(n_features=pc.embedding_dim,head_num=pc.head_num)
    x = mhead(x,x,x,mask=None)
    x.shape   #torch.Size([64, 32, 128])


