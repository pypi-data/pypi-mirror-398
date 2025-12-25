"""
vec3:多个向量，向量组的 计算

"""

#-------------------------------
# 矩阵基础运算 - 开始
#-------------------------------

def matrix_multiply(m1, m2):
    """numpy实现矩阵相乘
     [ˈmeɪtrɪks]   [ˈmʌltɪplaɪ]
    import numpy as np

    from ai.box.base import matrix_multiply

    a = np.arange(6).reshape(2,3)

    b = np.arange(6).reshape(3,2)

    c=matrix_multiply(a,b)
    
    print(c)
    
    """
    # 类型转换
    if not isinstance(m1,np.ndarray):
        m1 = np.array(m1)
    if not isinstance(m2,np.ndarray):
        m2 = np.array(m2)
    
    # 参数校验
    if m1.ndim !=2 or  m2.ndim != 2 or m1.shape[1] != m2.shape[0]:
        raise Exception("矩阵形状有误  ....")
    
    # 矩阵计算
    result = np.zeros(shape=(m1.shape[0], m2.shape[1]))
    
    for i in range(m1.shape[0]): # 第1个矩阵的行
        for j in range(m2.shape[1]): # 第2个矩阵的列
            result[i, j] = m1[i, :] @ m2[:, j]   
    return result


#-------------------------------
# 矩阵基础运算 - 结束
#-------------------------------



#-------------------------------
# 补码处理 - 开始 
#-------------------------------

import numpy as np
import torch

def mask_pad(data,padding_index=0):
    """补值掩码
    - 布尔矩阵，01矩阵，补码为1,为True
    - 句子中每个单词相对一个句子都有共同的补码向量，维数皆为seq_len
    - 对长度为seq_len的句子进行补码，形成[seq_len,seq_len]的布尔矩阵
    - 每个单词相对整个句子都有相同长度补码向量，向量维度为seq_len
    - 共有seq_len个单词 

    params
    -------------------------
    - data.shape = [batch_size,seq_len]
    - data的元素为索引，批次索引矩阵

    return 
    -------------------------
    - 补码矩阵， [batch_dize, 1, seq_len, seq_len]

    """
    # b句话,每句话50个词,这里是还没 embed 的，
    # 实指序列这个维度，就算embedding之后，序列的维度也还在
    # data = [b, 50]
    # 判断每个词是不是<PAD>
    mask = data == padding_index
    seq_len = data.shape[1]

    # [b, 50] -> [b, 1, 1, 50]
    mask = mask.reshape(-1, 1, 1, seq_len)

    # 在计算注意力时,是计算50个词和50个词相互之间的注意力,所以是个50*50的矩阵
    # 是pad的列是true,意味着任何词对pad的注意力都是0
    # 但是pad本身对其他词的注意力并不是0
    # 所以是pad的行不是true

    # 复制n次
    # [b, 1, 1, 50] -> [b, 1, 50, 50]
    # 第一个50指50句话，第二个50指每句话50个词
    mask = mask.expand(-1, 1, seq_len, seq_len)

    return mask


def mask_tril(data, padding_index=0):
    """布尔矩阵，01矩阵，补码为1,为True,
    - 在角阵规定的是上限，可能一句话的单词长度达不到int(seq_len/2)+1
    - mask_pad的基础增加每个索引只能看到自己及前面的索引
    - 0表示该位置是单词索引，1的位置表示PAD补的索引
    - 每个单词相对整个句子都有相同长度补码向量，向量维度为seq_len
    - 共有seq_len个单词 
    - data.shape = [batch_size,seq_len]
    - data的元素为索引，批次索引矩阵
    - 计算逻辑
      - 与PAD索引判断转化为布尔矩阵
      - 再与三角矩阵相加再次转化为01布尔矩阵
      - 最终输出矩阵为布尔矩阵，1对应PAD，0对象单词索引 
    """
    # b句话,每句话50个词,这里是还没embed的
    # data = [b, 50]
    seq_len = data.shape[1]

    # 50*50的矩阵表示每个词对其他词是否可见
    # 上三角矩阵,不包括对角线,意味着,对每个词而言,他只能看到他自己,和他之前的词,而看不到之后的词
    # [1, 50, 50]
    """tril,1代表的补，是1-PAD,将来通过softmax转化为0 
    每个向量至少有一个不是补码，即至少一个0,否则softmax无法计算
    这个三角限制了有效单词序列的最大长度，超出截断，按补码处理
    [[0, 1, 1, 1, 1],
     [0, 0, 1, 1, 1],
     [0, 0, 0, 1, 1],
     [0, 0, 0, 0, 1],
     [0, 0, 0, 0, 0]]"""
    tril = 1 - torch.tril(torch.ones(1, seq_len, seq_len, dtype=torch.long))

    # 判断y当中每个词是不是pad,如果是pad则不可见
    # [b, 50]
    mask = data == padding_index

    # 变形+转型,为了之后的计算
    # [b, 1, 50]
    mask = mask.unsqueeze(1).long()

    # mask和tril求并集
    # [b, 1, 50] + [1, 50, 50] -> [b, 50, 50]
    mask = mask + tril

    # 转布尔型
    mask = mask > 0

    # 转布尔型,增加一个维度,便于后续的计算
    # [b, 50, 50] -- [b, 1, 50, 50]
    mask = (mask == 1).unsqueeze(dim=1)

    return mask



#-------------------------------
# 补码处理 - 结束
#-------------------------------
