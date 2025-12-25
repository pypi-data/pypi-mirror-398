"""二分类问题 
"""
import torch 
from torch import nn 

from tpf.layer import Encoder 
from tpf.seq import PositionLinear
  
class Transformer12(torch.nn.Module):
    """交易序列，Transformer主流程,仅编码器
    模型定义参数
    - in_features:输入元素向量特征数，比如单词的embedding_dim
    - out_features：输出向量特征数，比如标签的维度，词典单词个数,类别个数
    """
    def __init__(self, pc=None):
        """ 
        
        examples
        ---------------------------------------------
        import torch
        from torch import nn
        from tpf.nlp.ts12 import Transformer12

        class pc:
            batch_size = 64
            min_seq_len=40  #暂时没有使用,还没有完成开发 
            max_seq_len=50  
            col_nums = 13
            embedding_dim=128
            class_nums = 2 
            flag_eos = '<EOS>'
            padding_index = 0

        data = torch.randn(pc.batch_size,pc.max_seq_len,pc.col_nums)
        transformer = Transformer12(pc)
        y_out  = transformer(data)
        y_out.shape               #torch.Size([64, 50, 2])
        
        
        examples 回归问题
        --------------------------------------------
        import torch
        from torch import nn
        from tpf.nlp.ts12 import Transformer12

        class pc:
            batch_size = 64
            min_seq_len=40  #暂时没有使用,还没有完成开发 
            max_seq_len=100  
            col_nums = 3
            embedding_dim=128
            class_nums = 1
            padding_index = 0

        data = torch.randn(pc.batch_size,pc.max_seq_len,pc.col_nums)

        transformer = Transformer12(pc)
        y_out  = transformer(data)
        y_out.shape               #torch.Size([64, 50, 2])


        """
        super().__init__()
        # in_features=pc.embedding_dim
        # out_features=pc.num_embeddings
        self.pc = pc 
        
        # 位置编码和词嵌入层
        self.embed_x = PositionLinear(seq_len=pc.max_seq_len, in_features=pc.col_nums, out_features=pc.embedding_dim)
        self.encoder = Encoder(features=pc.embedding_dim,head_num=4)
        self.fc_out = torch.nn.Linear(pc.embedding_dim, pc.class_nums)

    def forward(self, x):
        """
        # x = [8, 50]
        # y = [8, 51]
        """
        # [b, 1, 50, 50],如果长度不足，计划全部置0 
        # mask_pad_x = mask_pad(x, padding_index=self.pc.padding_index)
        
        x = self.embed_x(x)  #索引转向量
        # 编码层计算
        # x: [b, 50, 32] -> [b, 50, 32]
        # mask_pad_x:[b,1,50,50]
        x = self.encoder(x, None)

        # 全连接输出,维度改变
        # [b, 50, 32] -> [b, 50, 39]
        y = self.fc_out(x)
        return y

  