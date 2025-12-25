
import torch
from torch import nn
from torch.nn import functional as F

class SeqOne(nn.Module):
    """多尺度+注意力，
    - 单序数据，比如2维数表，时序数据等
    """
    def __init__(self, seq_len, out_features=2):
        """
        
        exampels
        -------------------------------
        import torch

        from torch import nn

        a = torch.randn(64,512)  #模拟2维数表

        model = SeqOne(seq_len=a.shape[1],  out_features=2)

        model(a)[:3]

        model = SeqOne(seq_len=X_test.shape[1], out_features=2)

        model(torch.tensor(X_test).float()[:3])[:3]

        tensor([[-0.5226,  0.2007],
                [-0.2852, -0.4373],
                [-0.2171,  0.6801]], grad_fn=<SliceBackward0>)
        """
        super().__init__()
        hidden_size = 256
        in_features=1

        # [N, C, seq_len] --> [N, C, seq_len-1],[N, C, seq_len-kernel_size+1]
        self.gram_2 = nn.Sequential(
            nn.Conv1d(in_channels=in_features, out_channels=hidden_size, kernel_size=2,stride=1,padding=1),
            nn.BatchNorm1d(num_features=hidden_size),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2)  # [N, C, 1],
        )


        # [N, C, seq_len, 1] --> [N, C, seq_len-2, 1]
        self.gram_3 = nn.Sequential(
            nn.Conv1d(in_channels=in_features, out_channels=hidden_size, kernel_size=3,stride=1,padding=1),
            nn.BatchNorm1d(num_features=hidden_size),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2) # [N, C, 1]
        )
        # [N, C, seq_len, 1] --> [N, C, seq_len-3, 1]
        self.gram_4 = nn.Sequential(
            nn.Conv1d(in_channels=in_features, out_channels=hidden_size, kernel_size=4,stride=1,padding=1),
            nn.BatchNorm1d(num_features=hidden_size),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2) # [N, C, 1]
        )

        self.conv1 = nn.Sequential(
            nn.Conv1d(in_channels=256, out_channels=hidden_size, kernel_size=3,stride=1,padding=1),
            nn.BatchNorm1d(num_features=hidden_size),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2)  
        )
        self.conv2 = nn.Sequential(
            nn.Conv1d(in_channels=hidden_size, out_channels=hidden_size, kernel_size=3,stride=1,padding=1),
            nn.BatchNorm1d(num_features=hidden_size),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2) 
        )
        self.conv3 = nn.Sequential(
            nn.Conv1d(in_channels=in_features, out_channels=hidden_size, kernel_size=3,stride=1,padding=1),
        )

        self.dropout1 = nn.Dropout(p=0.2)
        # 256×1×1
        self.ft = nn.Flatten()
        ll = ((seq_len+2*1)-2+1)//2+((seq_len+2*1)-3+1)//2+((seq_len+2*1)-4+1)//2 +seq_len
        ll=(ll//4)*256
        print(ll)
        self.fc1 = nn.Linear(in_features=ll, out_features=hidden_size)
        self.dropout2 = nn.Dropout(p=0.5)
        self.fc2 = nn.Linear(in_features=hidden_size, out_features=out_features)

        
    def attention(self, Q, K, V, mask=None, multihead=False):
        """序列数据注意力计算函数
        - 2维数表[batch_size,seq_len],embedding_dim是要变换的维度
          - 对于卷积来来说，[B,1,seq_len],卷积要变换的维度是1,特征维度embedding_dim=1，seq_len是特征shape
          - 对于注意力来说，[B,1,seq_len],要计算的维度是seq_len,特征维度embedding_dim=seq_len,注意力就是要计算哪些特征列重要，哪些不重要
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
    

    def forward(self,X):
        # [B, seq_len] --> [B, 1, seq_len] 
        seq_len = X.shape[1]
        x=X.unsqueeze(dim=1)
        x1 = self.gram_2(x)
        # print(f"x1.shape={x1.shape}")  #torch.Size([128, 256, 1])
        x2 = self.gram_3(x)
        x3 = self.gram_4(x)
        x4 = self.attention(x,x,x)
        x4 = self.conv3(x4)
        # print('x3',x3.shape,'x4',x4.shape)
        x = torch.concat(tensors=(x1,x2,x3,x4),dim=2)
        # print(x1.shape,x2.shape,x3.shape,x.shape)  # torch.Size([114, 256, 71])

        x = self.conv1(x)
        x = self.conv2(x)

        x = self.dropout1(x)
        # print(x.shape)
        x = self.ft(x)
        # print(x.shape)
        x = self.fc1(x)
        x = self.dropout2(x)
        x = self.fc2(x)

        return x 



class SmallBlock1d(nn.Module):
    """1维模型
    """
    def __init__(self, in_channel, hidden_size ):
        """简易1维模型
        """
        super().__init__()

        self.conv1 = nn.Sequential(
            nn.Conv1d(in_channels=in_channel, out_channels=hidden_size*4, kernel_size=3,stride=1,padding=1),
            nn.BatchNorm1d(num_features=hidden_size*4),
            nn.Conv1d(in_channels=hidden_size*4, out_channels=hidden_size*4, kernel_size=3,stride=1,padding=1),
            nn.Conv1d(in_channels=hidden_size*4, out_channels=hidden_size, kernel_size=3,stride=1,padding=1),
            nn.ReLU(),
        )

    
    def forward(self, x):
        h1 = x.clone()   
        x = self.conv1(x)
        o = h1 + x
        return o

class ShortBlock1d(nn.Module):
    """1维模型
    """
    def __init__(self, in_channel=256, hidden_size=256 ):
        """简易1维模型
        """
        super().__init__()

        self.s1 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s2 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s3 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s4 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s5 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s6 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s7 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s8 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s9 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s10 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s11 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s12 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s13 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s14 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s15 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s16 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s17 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s18 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s19 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s20 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s21 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s22 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s23 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s24 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s25 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s26 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s27 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s28 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s29 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s30 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s31 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s32 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s33 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s34 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s35 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s36 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s37 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s38 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s39 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s40 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s41 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s42 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s43 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s44 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s45 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s46 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s47 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s48 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s49 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s50 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s51 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s52 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s53 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s54 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s55 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s56 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s57 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s58 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s59 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)
        self.s60 = SmallBlock1d(in_channel=in_channel, hidden_size=hidden_size)

    
    def forward(self, x):
        x = self.s1(x)
        x = self.s2(x)
        x = self.s3(x)
        x = self.s4(x)
        x = self.s5(x)
        x = self.s6(x)
        x = self.s7(x)
        x = self.s8(x)
        x = self.s9(x)
        x = self.s10(x)
        x = self.s11(x)
        x = self.s12(x)
        x = self.s13(x)
        x = self.s14(x)
        x = self.s15(x)
        x = self.s16(x)
        x = self.s17(x)
        x = self.s18(x)
        x = self.s19(x)
        x = self.s20(x)
        x = self.s21(x)
        x = self.s22(x)
        x = self.s23(x)
        x = self.s24(x)
        x = self.s25(x)
        x = self.s26(x)
        x = self.s27(x)
        x = self.s28(x)
        x = self.s29(x)
        x = self.s30(x)
        x = self.s31(x)
        x = self.s32(x)
        x = self.s33(x)
        x = self.s34(x)
        x = self.s35(x)
        x = self.s36(x)
        x = self.s37(x)
        x = self.s38(x)
        x = self.s39(x)
        x = self.s40(x)
        x = self.s41(x)
        x = self.s42(x)
        x = self.s43(x)
        x = self.s44(x)
        x = self.s45(x)
        x = self.s46(x)
        x = self.s47(x)
        x = self.s48(x)
        x = self.s49(x)
        x = self.s50(x)
        x = self.s51(x)
        x = self.s52(x)
        x = self.s53(x)
        x = self.s54(x)
        x = self.s55(x)
        x = self.s56(x)
        x = self.s57(x)
        x = self.s58(x)
        x = self.s59(x)
        x = self.s60(x)
        return x

