"""二分类问题 
"""
import torch 
from torch import nn 

from tpf.layer import Encoder 
from tpf.seq import PositionLinear
  
class SeqTrans(torch.nn.Module):
    """时序序列,Transformer主流程,仅编码器
    """
    def __init__(self,seq_len, in_feature_dim, out_feature_dim, embedding_dim, head_num=4):
        """ 

        examples 回归问题
        --------------------------------------------
        import torch
        from torch import nn
        from tpf.nlp.ts13 import SeqTrans

        class pc:
            batch_size = 64
            seq_len=100  
            col_nums = 3
            embedding_dim=128
            class_nums = 1

        data = torch.randn(pc.batch_size,pc.seq_len,pc.col_nums)

        transformer = SeqTrans(seq_len=pc.seq_len,in_feature_dim=pc.col_nums,out_feature_dim=pc.class_nums,embedding_dim=pc.embedding_dim)
        y_out  = transformer(data)
        y_out.shape          
        
        
        examples 二分类问题
        ---------------------------------------------------
        import torch
        from torch import nn
        from tpf.nlp.ts13 import SeqTrans

        class pc:
            batch_size = 64
            seq_len=100  
            col_nums = 3
            embedding_dim=128
            class_nums = 2

        data = torch.randn(pc.batch_size,pc.seq_len,pc.col_nums)

        transformer = SeqTrans(seq_len=pc.seq_len,in_feature_dim=pc.col_nums,out_feature_dim=pc.class_nums,embedding_dim=pc.embedding_dim)
        y_out  = transformer(data)
        y_out.shape            # torch.Size([64, 100, 2])  

        """
        super().__init__()

        # 位置编码和词嵌入层
        self.embed_x = PositionLinear(seq_len=seq_len, in_features=in_feature_dim, out_features=embedding_dim)
        self.encoder = Encoder(features=embedding_dim, head_num=head_num)
        self.fc_out = torch.nn.Linear(embedding_dim, out_feature_dim)

    def forward(self, x):
        """
        - x: [batch_size, seq_len, in_feature_dim]
        
        """
        x = self.embed_x(x)      # 转换到编码维度(要变换的维度)
        
        # 编码层计算
        x = self.encoder(x, None)

        # 全连接输出,维度改变
        y = self.fc_out(x)
        
        return y

  