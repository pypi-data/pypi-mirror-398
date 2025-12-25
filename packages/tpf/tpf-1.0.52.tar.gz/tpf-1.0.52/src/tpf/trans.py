
##----------------------------------------------------
## Transformer：补码，注意力，短接  - 开始
##----------------------------------------------------
import torch 

from tpf.vec3 import mask_pad
from tpf.vec3 import mask_tril
from tpf.layer import Decoder,Encoder 
from tpf.seq import PositionEmbedding 

# 主模型
class Transformer(torch.nn.Module):
    """Transformer：补码，注意力，短接 
    模型定义参数
    - in_features:输入元素向量特征数，比如单词的embedding_dim
    - out_features：输出向量特征数，比如标签的维度，词典单词个数

    模型对象参数
    - x:[B,seq_len],批次索引矩阵，进入模型后先计算补码后编码
    - y:[B,seq_len],批次索引矩阵，进入模型后先计算补码后编码
    - padding_index:补码索引 

    返回
    - 标签向量，特征数为单词个数 
    """
    def __init__(self,seq_len=50,in_features=32,out_features=39):
        super().__init__()

        self.seq_len = seq_len

        # 位置编码和词嵌入层
        # out_features对应标签，单词个数/元素个数
        self.embed_x = PositionEmbedding(seq_len=seq_len,num_embeddings=out_features,embedding_dim=in_features)
        self.embed_y = PositionEmbedding(seq_len=seq_len,num_embeddings=out_features,embedding_dim=in_features)
        
        #单词维度/特征数，在神经网络的流转中保持了不变 
        self.encoder = Encoder(features=in_features)
        self.decoder = Decoder(features=in_features)

        #单词embedding_dim 映射到 标签维度
        self.fc_out = torch.nn.Linear(in_features, out_features)

    def forward(self, x, y, padding_index=2):
        """x,y为索引矩阵
        # x = [8, 50]
        # y = [8, 51]
        """
        # 补码，标记关键信息-单词，方法是记住不重要的补码再取反位置 
        # [b, 1, 50, 50]
        mask_pad_x = mask_pad(x, padding_index=padding_index)
        mask_tril_y = mask_tril(y, padding_index=padding_index)

        # 编码且添加位置信息
        # x = [b, 50] -> [b, 50, 32]
        # y = [b, 50] -> [b, 50, 32]
        x, y = self.embed_x(x), self.embed_y(y)
 

        # 编码层计算
        # x: [b, 50, 32] -> [b, 50, 32]
        # mask_pad_x:[b,1,50,50]
        x = self.encoder(x, mask_pad_x)

        # 解码层计算
        # [b, 50, 32],[b, 50, 32] -> [b, 50, 32]
        y = self.decoder(x, y, mask_pad_x, mask_tril_y)

        # 全连接输出,维度改变
        # [b, 50, 32] -> [b, 50, 39]
        y = self.fc_out(y)

        return y


    # 预测函数
    def predict(self, x, dict_y):
        """根据序列x预测序列y 
        - y的第1个单词为SOS标记 
        """
        # x = [1, 50]
        self.eval()


        # [1, 1, 50, 50]
        mask_pad_x = mask_pad(x, padding_index=2)

        # x编码,添加位置信息
        # [1, 50] -> [1, 50, 32]
        x = self.embed_x(x)

        # 编码层计算,维度不变
        # [1, 50, 32] -> [1, 50, 32]
        x = self.encoder(x, mask_pad_x)

        #序列长度为seq_len，第一个单词为SOS标记，余下seq_len-1个需要预测
        ydeal_count = self.seq_len-1

        # 初始化输出,这个是固定值
        # [1, 50]
        # [[1,0,0,0...]]
        # 每次输入的shape是[1, 50]但第i次处理只有前i个词有效，其余词为PAD
        target = [dict_y['<SOS>']] + [dict_y['<PAD>']] * ydeal_count
        target = torch.LongTensor(target).unsqueeze(0)

        # 遍历生成第1个词到第49个词
        for i in range(ydeal_count):
            # [1, 50]
            y = target

            # [1, 1, 50, 50]
            mask_tril_y = mask_tril(y, padding_index=2)

            # y编码,添加位置信息
            # [1, 50] -> [1, 50, 32]
            y = self.embed_y(y)

            # 解码层计算,维度不变
            # [1, 50, 32],[1, 50, 32] -> [1, 50, 32]
            # 虽然输入的是y向量，多个特征，但会结合mask，只计算mask位置上的单词，
            # 因此每次参与计算的，只有i个 
            y = self.decoder(x, y, mask_pad_x, mask_tril_y)

            # 全连接输出,39分类
            # [1, 50, 32] -> [1, 50, 39]
            # 每次输出的只有一个单词
            # y向量第1个维度是批次，每2个维度是seq_len，第3维是单词维度
            # 只要序列维度中第i个位置的输出，所以这个out还不是最终结果  
            out = self.fc_out(y)

            # 取出当前词的输出
            # [1, 50, 39] -> [1, 39]
            out = out[:, i, :]

            # 取出分类结果
            # [1, 39] -> [1]
            out = out.argmax(dim=1).detach()

            # 以当前词预测下一个词,填到结果中
            target[:, i + 1] = out

        return target


##----------------------------------------------------
## Transformer：补码，注意力，短接  - 开始
##----------------------------------------------------
