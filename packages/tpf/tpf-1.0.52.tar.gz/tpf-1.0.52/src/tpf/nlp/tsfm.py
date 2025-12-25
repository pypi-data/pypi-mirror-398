

##----------------------------------------------------
## Transformer：补码，注意力，短接  - 开始
##----------------------------------------------------
import torch 

from tpf.nlp.vec3 import mask_pad,build_pad_mask
from tpf.nlp.vec3 import mask_tril
from tpf.nlp.layer import Decoder,Encoder 
from tpf.nlp.seq import PositionEmbedding 

# 主模型
class Transformer(torch.nn.Module):
    """Transformer：补码，注意力，短接 
    模型定义参数
    - in_features:输入元素向量特征数，比如单词的embedding_dim
    - out_features：输出向量特征数，比如标签的维度，词典单词个数

    模型对象参数
    - x:[B,seq1_len],批次索引矩阵，进入模型后先计算补码后编码
    - y:[B,seq2_len],批次索引矩阵，进入模型后先计算补码后编码
    - padding_index:补码索引 

    返回
    - 标签向量，特征数为单词个数 
    """
    def __init__(self,seq1_len=50,seq2_len=50,in_features=32,
                 dict_x=None, dict_y=None,
                 sos = '<SOS>',eos = '<EOS>', pad = '<PAD>', unk='<UNK>',
                 padding_index_x=None,padding_index_y=None,head_num=4,layer_num_encoder=3,layer_num_decoder=3):
        super().__init__()
        self.sos = sos
        self.eos = eos
        self.pad = pad
        self.dict_x = dict_x
        self.dict_y = dict_y
        self.head_num = head_num
        self.layer_num_encoder=layer_num_encoder
        self.layer_num_decoder=layer_num_decoder
        out_features = len(dict_y)

        if padding_index_x is None :
            padding_index_x = dict_x[pad]
        self.padding_index_x = padding_index_x 
        
        if padding_index_y is None :
            padding_index_y = dict_y[pad]
        self.padding_index_y = padding_index_y
        
        self.seq1_len = seq1_len
        self.seq2_len = seq2_len
        self.in_features = in_features
        self.out_features = out_features

        # 位置编码和词嵌入层
        # out_features对应标签，单词个数/元素个数
        self.embed_x = PositionEmbedding(seq_len=seq1_len,num_embeddings=len(dict_x),embedding_dim=in_features)
        self.embed_y = PositionEmbedding(seq_len=seq2_len,num_embeddings=len(dict_y),embedding_dim=in_features)
        
        #单词维度/特征数，在神经网络的流转中保持了不变 
        self.encoder = Encoder(features=in_features,head_num=head_num,layer_num=layer_num_encoder)
        self.decoder = Decoder(features=in_features,head_num=head_num,layer_num=layer_num_decoder)

        #单词embedding_dim 映射到 标签维度
        self.fc_out = torch.nn.Linear(in_features, out_features)

    def forward(self, x, y):
        """
        - 输入:x,y为索引矩阵
        - 输出:字典索引 
        # x = [8, 50]
        # y = [8, 51]
        """
        # 补码，标记关键信息-单词，方法是记住不重要的补码再取反位置 
        # [b, 1, 50, 50]
        mask_pad_x = mask_pad(x, padding_index=self.padding_index_x)
        mask_tril_y = mask_tril(y, padding_index=self.padding_index_y)
        mask_x = build_pad_mask(x, padding_index=self.padding_index_x)          # [B,1,1,Lx]

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
        # 真正喂给 mh2 的 mask 要把 pad mask 广播成 [B,1,Ly,Lx]
        mask_cross_yx = mask_x.expand(-1, 1, y.size(1), x.size(1))  # [B,1,Ly,Lx]
        y = self.decoder(x, y, mask_cross_yx, mask_tril_y)

        # 全连接输出,维度改变
        # [b, 50, 32] -> [b, 50, 39]
        y = self.fc_out(y)

        return y



    def study(self, loader, loss_func, optim, epoch=3):
        for e in range(epoch):
            for i, (x, y) in enumerate(loader):
                # x = [8, 50]
                # y = [8, 51]

                # 在训练时,是拿y的每一个字符输入,预测下一个字符,所以不需要最后一个字
                # 主要还是因为y是51，x是50，二者要保持一致 
                # [8, 50, 39]
                pred = self(x, y)
        

                # [8, 50, 39] -> [400, 39]
                # 多少个单词，展平到单词维度，准备按批次计算偏差
                pred = pred.reshape(-1, self.out_features)

                # [8, 51] -> [400]
                # y[:,0]为SOS标记的索引
                # y = y[:, 1:].reshape(-1)
                y = y.reshape(-1)
             

                # 忽略pad,忽略一个批次中所有的PAD
                select = y != self.padding_index_y
                pred = pred[select]  #选出pred中所有单词位置的向量
                y = y[select]        #选出y中所有单词的索引，形成一个新的全是单词索引的向量

                #pred[-1,dict_count],y单词索引向量
                #比如，y[0]=2,one hot转标签向量为[0,0,1]，期望模型输出的向量为[0,0.2,0.8]，最好是[0,0.1,0.9]，
                #损失减少的方向就是index=2位置上的数据尽量接近1，其他位置尽量逼近0 
                loss = loss_func(pred, y)
                optim.zero_grad()
                loss.backward()
                optim.step()

                if i % 1000 == 0:
                    # [select, 39] -> [select]
                    pred = pred.argmax(1)
                    correct = (pred == y).sum().item()
                    accuracy = correct / len(pred)
                    lr = optim.param_groups[0]['lr']
                    msg = f"eposh={e}, batch={i}, lr={lr}, loss={loss.item()}, acc={accuracy:.2f}"
                    print(msg)
        pass 

    # 预测函数
    def predict(self, x):
        """根据序列x预测序列y 
        - y的第1个单词为SOS标记 
        """
        dict_y = self.dict_y
        # x = [1, 50]
        self.eval()


        # [1, 1, 50, 50]
        mask_pad_x = mask_pad(x, padding_index=self.padding_index_x)

        # x编码,添加位置信息
        # [1, 50] -> [1, 50, 32]
        x = self.embed_x(x)

        # 编码层计算,维度不变
        # [1, 50, 32] -> [1, 50, 32]
        x = self.encoder(x, mask_pad_x)

        #序列长度为seq2_len，第一个单词为SOS标记，余下seq2_len-1个需要预测
        ydeal_count = self.seq2_len-1

        # 初始化输出,这个是固定值
        # [1, 50]
        # [[1,0,0,0...]]
        # 每次输入的shape是[1, 50]但第i次处理只有前i个词有效，其余词为PAD
        target = [dict_y[self.sos]] + [dict_y[self.pad]] * ydeal_count
        target = torch.LongTensor(target).unsqueeze(0)
        print(target.shape) # 

        # 遍历生成第1个词到第49个词
        for i in range(ydeal_count):
            # [1, 50]
            y = target

            # [1, 1, 50, 50]
            mask_tril_y = mask_tril(y, padding_index=self.padding_index_y)

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
            # y向量第1个维度是批次，每2个维度是seq2_len，第3维是单词维度
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
## Transformer：补码，注意力，短接  - 结束
##----------------------------------------------------


