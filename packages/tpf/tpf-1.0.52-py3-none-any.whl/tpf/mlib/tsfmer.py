'''
Description: 模型（注意力，RNN），损失函数定义，训练过程
Author: 七三学徒
Date: 2022-01-23 15:30:27
'''

import random 
import torch
from torch import nn
from torch.nn import functional as F


USE_CUDA = torch.cuda.is_available()
"""检测是否有GPU
"""

device = torch.device("cuda" if USE_CUDA else "cpu")
"""设备
"""


""" 
---------------------------------------------------------------
transformer系列 开始 
"""

class EncoderRNN(nn.Module):
    """编码模型
      - 从批次数据中pack_pad出真实数据
      - 将真实数据输入模型
      - 将模型输出进行pad_pack得到批次数据
      
    输入数据
      - 要求输入的数据格式为[seq_len,batch_size]
      - 通常为单词索引列表
    """
    def __init__(self, hidden_size, embedding, n_layers=1, dropout=0):
        super(EncoderRNN, self).__init__()
        self.n_layers = n_layers
        self.hidden_size = hidden_size
        self.embedding = embedding

        # Initialize GRU; the input_size and hidden_size params are both set to 'hidden_size'
        # because our input size is a word embedding with number of features == hidden_size
        self.gru = nn.GRU(hidden_size, hidden_size, n_layers,
                          dropout=(0 if n_layers == 1 else dropout), bidirectional=True)

    def forward(self, input_seq, input_lengths, hidden=None):
        # Convert word indexes to embeddings
        embedded = self.embedding(input_seq)

        # Pack padded batch of sequences for RNN module
        packed = nn.utils.rnn.pack_padded_sequence(embedded, input_lengths)

        # Forward pass through GRU
        outputs, hidden = self.gru(packed, hidden)

        # Unpack padding
        outputs, _ = nn.utils.rnn.pad_packed_sequence(outputs)

        # Sum bidirectional GRU outputs
        outputs = outputs[:, :, :self.hidden_size] + outputs[:, :, self.hidden_size:]

        # Return output and final hidden state
        return outputs, hidden

# Luong attention layer
class Attn(nn.Module):
    def __init__(self, method, hidden_size):
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
        # 矩阵乘法是向量内积按一定格式/规律计算的过程，前一个矩阵的首与后一个矩阵的尾维度相等，首尾同
        # 而向量内积的使用，除了矩阵乘法的计算方法外，
        # 还可以按矩阵shape一致的方式计算，首与首同，尾与尾同，即同shape计算
        # 这里不影响，这里计算的是一个单词相对一个句子的注意力 
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
        # 因为计算的是一个单词相对一个句子的注意力，这个1也可以理解为1个单词，即这个维度的业务含义是seq_len
        # [batch_size, 1, seq_len]中的seq_len的业务含义则是重要百分比，一个单词相对句子的重要百分比
        return F.softmax(attn_energies, dim=1).unsqueeze(1)

class LuongAttnDecoderRNN(nn.Module):
    def __init__(self, attn_model, embedding, hidden_size, output_size, n_layers=1, dropout=0.1):
        """
        输入参数
          - 一个批次某个位置上的单词，单词维度是索引，格式为[1,batch_size]
          - 隐藏层，编码器最后一次的输出，或者上一个解码器的输出
          - 解码层
          
        输出参数
          - 单词向量
            - 被预测的单词，经过了注意力计算，shape为[batch_size,dict_len]
            - 这里用[dict_len]长度的向量表示一个单词，并且使用softmax转概率，其和为1
            - 如此，就可以使用交叉熵逼迫其与one-hot意义的单词标签接近
          - gru输出的隐藏层

        批次计算每个单词的概率，最终将单词维度映射到字典，确定它是哪一个单词，然后解码输出一个单词
        """
        super(LuongAttnDecoderRNN, self).__init__()

        # Keep for reference
        self.attn_model = attn_model  # dot
        self.hidden_size = hidden_size # 500
        self.output_size = output_size # voc.num_words 7826
        self.n_layers = n_layers       # 2
        self.dropout = dropout

        # Define layers
        self.embedding = embedding
        self.embedding_dropout = nn.Dropout(dropout)
        self.gru = nn.GRU(hidden_size, hidden_size, n_layers, dropout=(0 if n_layers == 1 else dropout))
        self.concat = nn.Linear(hidden_size * 2, hidden_size)
        self.out = nn.Linear(hidden_size, output_size)  # 500 --> voc.num_words

        self.attn = Attn(attn_model, hidden_size)

    def forward(self, input_step, last_hidden, encoder_outputs):
        """根据前一个单词预测后一个单词

        Args:
            input_step (_type_): 某个位置一个批次的单词索引，shape=[1, 64]
            last_hidden (_type_): 隐藏层，shape=[2, 64, 500]
            encoder_outputs (_type_): [10,64,500]

        Returns:
            output: 单词向量，[64, 7826]，转了概率,方便后续与标签求损失
            hidden: 隐藏层，中间结果，[2, 64, 500]
        """
        # Note: we run this one step (word) at a time
        # Get embedding of current input word
        embedded = self.embedding(input_step)      # [1, 64, 500]
        embedded = self.embedding_dropout(embedded)

        # Forward through unidirectional GRU
        # 每次只输入一个单词，
        # 因此rnn_output, hidden的shape皆为[1, batch_size, hidden_size]
        rnn_output, hidden = self.gru(embedded, last_hidden) 

        # Calculate attention weights from the current GRU output
        # [batch_size,seq_len] --> [batch_size, 1, seq_len]
        # 1个单词与一个句子求注意力
        attn_weights = self.attn(rnn_output, encoder_outputs)
        
        # Multiply attention weights to encoder outputs to get new "weighted sum" context vector
        # encoder_outputs.shape=[seq_len,batch_size,hidden_size]
        # encoder_outputs.transpose(0, 1).shape = [batch_size,seq_len,hidden_size]
        # attn_weights.shape = [batch_size, 1, seq_len]
        # bmm [1, seq_len]@[seq_len,hidden_size] = [batch_size,1,hidden_size]
        # context.shape = [batch_size,1,hidden_size]
        # decoder中每个单词对应一个encoder的上下文向量
        # 加权平均，[1, seq_len] sum(dim=1)=1，注意力的得分之和为1，将这个得分乘到原来解码器上
        context = attn_weights.bmm(encoder_outputs.transpose(0, 1))

        # Concatenate weighted context vector and GRU output using Luong eq. 5
        # rnn_output.shape = [1, batch_size, hidden_size]
        # rnn_output.squeeze(0).shape = [batch_size, hidden_size]
        # decoder中每个单词的输出
        rnn_output = rnn_output.squeeze(0)

        # context.shape = [batch_size,hidden_size]
        # decoder中每个单词对应encoder中的上下文向量
        context = context.squeeze(1)

        # 将从encoder中得到的上下文向量拼接到decoder中每个单词的输出维度上
        # concat_input.shape=[batch_size,hidden_size*2]
        concat_input = torch.cat((rnn_output, context), dim=1)

        # 全连接，线性变换，再tanh，[batch_size,hidden_size*2]--> [batch_size,hidden_size]
        concat_output = torch.tanh(self.concat(concat_input))

        # Predict next word using Luong eq. 6
        # [batch_size,hidden_size] --> [batch_size,output_size]
        # output_size为标签的个数
        output = self.out(concat_output)
        
        # 这里转了概率，单词维度之和为1
        output = F.softmax(output, dim=1) # 转概率,不改变维度,[64, 7826]
        # Return output and final hidden state
        # hidden：普通的gru，一个单词通过gru得到的输出,[2, 64, 500]
        # output：经过gru+attention，然后转标签概率
        return output, hidden

def maskNLLLoss(inp, target, mask):
    """
    功能描述
      - 计算模型预测单词与target标签单词之间距离
      
    输入参数
      - inp: 某个位置一个批次的单词，inp.shape=[64, 7826] = [batch_size,dict_len]
      - target: 对应答句相应位置单词的索引
      - mask: 该位置是单词还是pad 
    输出参数
      - 批次平均损失
      - 批次中单词个数
    
    --------------
    按位置计算，一次计算某个位置上一个批次的单词；
    不同的句子长度不一致，所有句子在批次处理时长度皆为MAX_LENGTH
    mask记录对应位置是否为单词，是单词为True,PAD为False
    比如某句子长度为8，那么这句话9这个位置上就是PAD，
    9这个位置对应的mask为False
    """
    # 某个位置一个批次有多少个单词
    nTotal = mask.sum() # 表示一个批次的某个位置上有多少个单词，1表示有单词，0表示无单词

    print(f"target.shape={target.shape}")  # target.shape=torch.Size([64])
    index = target.view(-1, 1)  # [64, 1]


    # 取与 标签对应索引位置 上的模型输出的 数据，其他的都不要了
    # 比如某个单词在原dict_len=7826这个字典的索引为100，那么其他位置上的值都不是该单词
    # output的最后一维与dict_len=7826这个字典索引对应
    # 所以，若标签这个位置应该被预测为索引100对应的单词时，
    # 那么output索引100对应的数值应该概率最大
    # 针对每个单词，先获取标签单词在字典中的索引下标，从one-hot的角度看，只有该位置为1，其他位置皆为0
    # 同样取出模型输出的单词维度对应索引下标上的数据，该数据将与1通过损失函数进行校正
    # 让模型输出的单词维度相同索引下标的数据不断接近1，让损失慢慢减少
    # inp[batch_size,dict_len]单词维度dict_len做了softmax，其和为1
    # 当某个索引位置上的数据接近1时，其他位置将趋于0
    y = torch.gather(inp, 1, index)  # [64,1]
    y = y.squeeze(1)  # [64] 

    # 交叉熵计算，计算一个批次的两个分布之间的距离，模型预测的单词与标签单词的距离
    # -(lable*log(y) + (1-lable)*log(1-y))
    # lable = 1 , -log(y)
    # crossEntropy = -torch.log(torch.gather(inp, 1, index).squeeze(1))
    # 分布的维度就是批次的维度，因此可以做交叉熵 
    crossEntropy = -torch.log(y)  # [64]

    # 所有单词位置上的损失的均值 
    # 取有单词的位置上的数据，不计算PAD
    loss = crossEntropy.masked_select(mask).mean()
    loss = loss.to(device)
    return loss, nTotal.item()


def train(input_variable, lengths, target_variable, mask, max_target_len, 
          encoder, decoder, embedding,
          encoder_optimizer, decoder_optimizer, batch_size, clip, 
          max_length=15, SOS_token=0,teacher_forcing_ratio=1):
    """训练
    [seq_len,batch_size,embedding_dim]说明：
    seq_len:
    """
    # Zero gradients
    encoder_optimizer.zero_grad()
    decoder_optimizer.zero_grad()

    # Set device options
    input_variable = input_variable.to(device)
    target_variable = target_variable.to(device)

    mask = mask.to(device)

    # Lengths for rnn packing should always be on the cpu
    lengths = lengths.to("cpu")

    # Initialize variables
    loss = 0
    print_losses = []
    n_totals = 0

    # Forward pass through encoder
    # encoder_hidden.shape=[4, 64, 500],双层双向
    # encoder_outputs.shape=[10, 64, 500]
    # 双层双向输出维度outputs本来应该是hidden_size*2，但这里的encoder不是把正反向拼接，而是相加
    # 保持了输出的维度仍然是hidden_size
    encoder_outputs, encoder_hidden = encoder(input_variable, lengths)

    # Create initial decoder input (start with SOS tokens for each sentence)
    # decoder_input.shape=[1,batch_size]
    # 这里的decoder_input的元素是单词，还没有embedding，embedding是在decoder中进行的
    # 64句话，每句话的开头都是SOS标记，每个批次中每个元素存放的只有一个单词
    # 即对于单个批次来讲，在某一时刻，一个输入一个单词数据，预测出一个单词，然后重复这个过程，直到结束
    decoder_input = torch.LongTensor([[SOS_token for _ in range(batch_size)]])  #第一个单词批次
    decoder_input = decoder_input.to(device)

    # Set initial decoder hidden state to the encoder's final hidden state
    # encoder_hidden.shape=[4,64,500]
    # decoder中的GRU是单向的
    # decoder_hidden.shape=[2, 64, 500]
    # 这里decoder初始化隐藏层取encoder的最终输出隐藏层
    # 编码器是双向的，解码器是单向的，只有从开始到结束的序列，因此相同层数下，解码器只有编码器的一半
    # 这里取编码器输出隐藏层的一半，来做为解码器的隐藏层输入
    decoder_hidden = encoder_hidden[:decoder.n_layers]

    # Determine if we are using teacher forcing this iteration
    # random.random()用于生成一个0到1的随机符点数: 0 <= n < 1.0
    use_teacher_forcing = True if random.random() < teacher_forcing_ratio else False

    # Forward batch of sequences through decoder one time step at a time
    if use_teacher_forcing:
        # 一个单词一个单词地计算，按序列循环，一个位置上的单词有一个批次的数据 
        for t in range(max_target_len): # 解码序列有多少个单词，就循环多少次
            # decoder_input每次从target_variable取出一个单词
            # decoder_input.shape=[1, 64]
            # decoder_hidden.shape=[2, 64, 500]
            # decoder_output=[64,dict_len]
            decoder_output, decoder_hidden = decoder(
                decoder_input, decoder_hidden, encoder_outputs
            )
            
            # Teacher forcing: next input is current target
            # 取当前序列需要输入的单词
            # decoder_input.shape=[1,64]
            # target_variable.shape=[10,64]
            # target_variable是答句的word2index列表，还没有embedding
            # 一次输入某个序列位置上一个批次的单词 
            # [64] --> [1,64]
            # 从第二次循环开始，输入的是单词[seq_len,batch_size]，其中seq_len=1
            decoder_input = target_variable[t].view(1, -1)

            # Calculate and accumulate loss
            # mask[t]表示t位置是单词还是PAD标记，为单词时为True
            # target_variable[t]是t位置一个批次单词的索引
            mask_loss, nTotal = maskNLLLoss(decoder_output, target_variable[t], mask[t])
            loss += mask_loss
            print_losses.append(mask_loss.item() * nTotal)
            n_totals += nTotal
    else:
        for t in range(max_target_len):
            decoder_output, decoder_hidden = decoder(
                decoder_input, decoder_hidden, encoder_outputs
            )
            # No teacher forcing: next input is decoder's own current output
            _, topi = decoder_output.topk(1)
            # 每个单词向量最大值所对应的索引,对应的是一个单词，解码器，输入的是一个单词，输出的还是单词 
            # 输入的是上一个输出的单词，而输出的单词要参与损失函数计算
            decoder_input = torch.LongTensor([[topi[i][0] for i in range(batch_size)]])
            decoder_input = decoder_input.to(device)
            # Calculate and accumulate loss
            mask_loss, nTotal = maskNLLLoss(decoder_output, target_variable[t], mask[t])
            loss += mask_loss
            print_losses.append(mask_loss.item() * nTotal)
            n_totals += nTotal

    # Perform backpropatation
    loss.backward()

    # Clip gradients: gradients are modified in place
    _ = nn.utils.clip_grad_norm_(encoder.parameters(), clip)
    _ = nn.utils.clip_grad_norm_(decoder.parameters(), clip)

    # Adjust model weights
    encoder_optimizer.step()
    decoder_optimizer.step()

    return sum(print_losses) / n_totals





""" 
transformer系列 结束
---------------------------------------------------------------
"""