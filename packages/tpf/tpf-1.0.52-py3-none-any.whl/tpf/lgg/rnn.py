

import torch 
from torch import nn


seq_len       = 87
batch_size    = 32
embedding_dim = 256
output_size   = 512

class RNNDefine(nn.Module):
    def __init__(self,input_size=embedding_dim,hidden_size=output_size) -> None:
        super().__init__()
        self.cell_linear_x = nn.Linear(in_features=input_size,  out_features=hidden_size)
        self.cell_linear_h = nn.Linear(in_features=hidden_size, out_features=hidden_size)

    def forward(self,x,h0):

        seq_len, batch_size,embedding = x.shape

        # 从句子中取出每个单词，计算每个单词的输出
        output = []
        ht = h0[0] # [1,batch_size,embedding]
        for t in range(seq_len):

            # print(f"x[{t}].shape={x[t].shape}")  # x[86].shape=torch.Size([32, 256])

            # [batch_size,embedding] --> [batch_size,output_size]
            # 对于每一个时间步来说，不需要管seq_len的维度,因为一步一个单词
            each_word = self.cell_linear_x(x[t])
            # print(f"t={t},each_word.shape={each_word.shape}")
            # print(f"t={t},ht.shape={ht.shape}")         

            ht = self.cell_linear_h(ht)

            ht = torch.tanh(each_word + ht)
            # print(ht.shape)  # torch.Size([32, 512])

            output.append(ht.tolist())

        hn = torch.unsqueeze(input=ht,dim=0)
        # print(hn.shape)  # torch.Size([1, 32, 512])
        output = torch.Tensor(output)
        return output,hn



def seq_test():
    import jieba 
    sentences = ["我欠银行一百万","银行欠我一百万"]
    word_dict = dict()

    doc= []
    word_set = set()
    for sentence in sentences:
        sen = jieba.lcut(sentence)
        doc.append(sen)
        word_set =  word_set.union(set(sen))
    
    print(doc)      # [['我', '欠', '银行', '一百万'], ['银行', '欠', '我', '一百万']]
    print(word_set) # {'银行', '我', '欠', '一百万'}

    word_dict = {word:index for index,word in enumerate(word_set)}
    print(word_dict)  # {'欠': 0, '银行': 1, '一百万': 2, '我': 3}
    word_dict = {'我': 0, '欠': 1, '银行': 2, '一百万': 3}

    doc_index = []

    for sentence in doc:
        doc_index.append([ word_dict[word] for word in sentence ])

    print(doc_index)  # [[0, 1, 2, 3], [2, 1, 0, 3]]

    torch.manual_seed(73)

    batch_size    = 2 
    output_size   = 5 
    embedding_dim = 1

    # [batch_size,seq_len]
    x = torch.Tensor(doc_index) /10

    # [batch_size,seq_len]-->[seq_len,batch_size]
    x = x.permute(1,0)
    # [seq_len,batch_size] --> [seq_len,batch_size,1]
    x = torch.unsqueeze(input=x,dim=-1)
    h0= torch.zeros([1,batch_size,output_size])

    rnn = nn.RNN(input_size=embedding_dim,hidden_size=output_size)
    output,hn = rnn(x,h0)
    print(hn)
    """
    tensor([[[ 0.0815, -0.6230,  0.0100,  0.7387, -0.1968],
         [ 0.0382, -0.6100,  0.0052,  0.7299, -0.1448]]],
       grad_fn=<StackBackward0>)
    """
    






if __name__=="__main__":
    rnn = RNNDefine(input_size=embedding_dim,hidden_size=output_size) 

    x = torch.randn([87,batch_size,embedding_dim])

    # 每一个单元处理，都有一个隐藏层
    # 输出层output包含所有的隐藏层，[seq_len,batch_size,output_size]
    h0= torch.zeros([1,batch_size,output_size])

    # ht是每一个时间步t的输出，hn是最后一个时间步的输出
    output,hn = rnn(x,h0)
    # print(output.shape)  # torch.Size([87, 32, 512])

    seq_test()



