"""字母转换
- 0-9,1-8,2-7...
- 小写转大写
"""

import numpy as np
import torch
from tpf.datasets import ZiMu11

class pc:
    min_seq_len=40
    max_seq_len=50  
    embedding_dim=32
    flag_eos = '<EOS>'



def index2word(index):
    d = {pc.word_dict[key]:key for key in pc.word_dict.keys()}
    return d[index]
   

def index2seq(indexs):
    ll = [pc.index2word(i) for i in indexs]
    eos_index = ll.index(pc.flag_eos)
    res = ''.join(ll[1:eos_index])
    return res



from tpf.vec3 import mask_pad
from tpf.seq import PositionEmbedding
from tpf.layer import Encoder 

# 主模型
class Transformer11(torch.nn.Module):
    """文本类序列，Transformer主流程,仅编码器
    模型定义参数
    - in_features:输入元素向量特征数，比如单词的embedding_dim
    - out_features：输出向量特征数，比如标签的维度，词典单词个数
    """
    def __init__(self, pc=None):
        super().__init__()
        # in_features=pc.embedding_dim
        # out_features=pc.num_embeddings
        self.pc = pc 
        
        # 位置编码和词嵌入层
        self.embed_x = PositionEmbedding(seq_len=pc.max_seq_len,num_embeddings=len(pc.word_dict),embedding_dim=pc.embedding_dim)
        self.encoder = Encoder(features=pc.embedding_dim,head_num=4)
        self.fc_out = torch.nn.Linear(pc.embedding_dim, pc.num_embeddings)

    def forward(self, x, y=None):
        """
        # x = [8, 50]
        # y = [8, 51]
        """
        # [b, 1, 50, 50]
        mask_pad_x = mask_pad(x, padding_index=self.pc.padding_index)
        
        x = self.embed_x(x)  #索引转向量
        # 编码层计算
        # x: [b, 50, 32] -> [b, 50, 32]
        # mask_pad_x:[b,1,50,50]
        x = self.encoder(x, mask_pad_x)

        # 全连接输出,维度改变
        # [b, 50, 32] -> [b, 50, 39]
        y = self.fc_out(x)
        return y




# 预测函数
def predict11(model,x):
    # x = [1, 50]
    model.eval()

    # [1, 1, 50, 50]
    mask_pad_x = mask_pad(x)

    with torch.no_grad():
        # x编码,添加位置信息
        # [1, 50] -> [1, 50, 32]
        x = model.embed_x(x)
    
        # 编码层计算,维度不变
        # #[batch_size,seq_len,embedding_dim]
        x = model.encoder(x, mask_pad_x)
    
        y_out = model.fc_out(x)  #[batch_size,seq_len,num_embeddings]
        out = y_out.argmax(dim=2).detach()
    return out


def train(model,optim,loss_func,loader,pc):
    for epoch in range(3):
        for i, (X, y) in enumerate(loader):
            # print(X.shape,y.shape)  #torch.Size([8, 50]) torch.Size([8, 50])
            # print(X[0])
            # print(y[0])
            y_out = model(X)
            # print(y_out.shape,y_out[0][0][:3])
            pred = y_out.reshape(-1, pc.num_embeddings)
            # print(pred.shape)
            y = y.reshape(-1)
            # print(y.shape)
        
            # 忽略pad,忽略一个批次中所有的PAD
            select = y != pc.padding_index
            pred = pred[select]  #选出pred中所有单词位置的向量
            y    = y[select]        #选出y中所有单词的索引，形成一个新的全是单词索引的向量
        
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
                print(epoch, i, lr, loss.item(), accuracy)
            
            # break
    
  

if __name__ == '__main__':
    # 数据加载器
    datasets = ZiMu11(min_seq_len=pc.min_seq_len,max_seq_len = pc.max_seq_len) 
    pc.word_dict = datasets.word_dict
    pc.padding_index = pc.word_dict["<PAD>"]
    pc.num_embeddings = len(pc.word_dict)
    pc.index2word = index2word
    # print(index2word(0))  #<PAD>
    
    loader = torch.utils.data.DataLoader(dataset=datasets,
                                         batch_size=8,
                                         drop_last=True,
                                         shuffle=True,
                                         collate_fn=None)
    # for (X,y) in loader:
    #     print(X.shape,y.shape)  #torch.Size([8, 50]) torch.Size([8, 50])
    #     print(X[0])
    #     print(y[0])
    #     break

    # 构建模型
    model = Transformer11(pc)

    # 定义损失函数
    loss_func = torch.nn.CrossEntropyLoss()

    # 优化器
    optim = torch.optim.Adam(model.parameters(), lr=2e-3)
            
    train(model,optim,loss_func,loader,pc)
    
    for i, (X, y) in enumerate(loader):
        print(X.shape,y.shape)  #torch.Size([8, 50]) torch.Size([8, 50])
        print(index2seq(X[0].tolist()))
        print(index2seq(y[0].tolist()))
        pred = predict11(model,X)
        print(index2seq(pred[0].tolist()))
        break

