
# 科学计算工具
import numpy as np

# torch 三组件
import torch
from torch import nn
from torch.nn import functional as F


class TextCNN2D(nn.Module):
    """
        使用二维卷积来处理文本分类
    """
    def __init__(self, word2idx, num_embeddings, embedding_dim=256, seq_len=None,):
        super(TextCNN2D, self).__init__()

        # 嵌入层
        self.embed = nn.Embedding(num_embeddings=num_embeddings, 
                                  embedding_dim=embedding_dim,
                                  padding_idx=word2idx["<PAD>"])

        # # seq_len --> seq_len//2 
        self.step1 = nn.Sequential(
            nn.Conv2d(in_channels=256, 
                                out_channels=512,
                                kernel_size=(3, 1),
                                stride=(1, 1),
                                padding=(1, 0)
                              ),
            nn.BatchNorm2d(num_features=512),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1), padding=(0, 0))
        )

        # seq_len --> seq_len//4
        self.step2 = nn.Sequential(
            nn.Conv2d(in_channels=512, 
                                out_channels=512,
                                kernel_size=(3, 1),
                                stride=(1, 1),
                                padding=(1, 0)
                              ),
            nn.BatchNorm2d(num_features=512),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1), padding=(0, 0))
        )

        # seq_len//8
        self.step3 = nn.Sequential(
            nn.Conv2d(in_channels=512, 
                                out_channels=1024,
                                kernel_size=(3, 1),
                                stride=(1, 1),
                                padding=(1, 0)
                              ),
            nn.BatchNorm2d(num_features=1024),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1), padding=(0, 0))
        )
        
        # 全连接层, [B, features, seq_len//(2**maxpool_count)]
        maxpool_count = 3
        line_in_features = 1024*(seq_len//(2**maxpool_count))

        """
        # 在这个场景中，使用nn.Sequential封装分类这一步，会降低精度，仅个人测试结果...
        self.classify = nn.Sequential(
            nn.Linear(in_features=line_in_features, out_features=512),
            nn.Dropout(p=0.2),
            nn.Linear(in_features=512, out_features=2)
        )
        """
        
        self.fc1 = nn.Linear(in_features=line_in_features, out_features=512)
        self.dropout = nn.Dropout(p=0.2)
        self.fc2 = nn.Linear(in_features=512, out_features=2)
        
    def forward(self, x):
        x = self.embed(x)
        x = x.permute(0, 2, 1)
        # [B, 256, seq_len] --> [B, 256, seq_len, 1]
        x = torch.unsqueeze(input=x, dim=-1)
        
        # 卷积提取特征
        x = self.step1(x)

        x = self.step2(x)
        
        x = self.step3(x)
        
        # 展平层
        x = x.view(x.size(0), -1)
        
        x = self.fc1(x)
        x = self.dropout(x)
        x =self.fc2(x)
        
        return x


class TextCNN1(nn.Module):
    """
        TextCNN论文实现
    """
    def __init__(self,num_embeddings, embedding_dim,padding_idx,seq_len):
        super().__init__()
        
        self.embed = nn.Embedding(num_embeddings=num_embeddings,
                                 embedding_dim=embedding_dim,
                                 padding_idx=padding_idx)
        
        # [N, C, seq_len] --> [N, C, seq_len-1],[N, C, seq_len-kernel_size+1]
        self.gram_2 = nn.Sequential(
            nn.Conv1d(in_channels=embedding_dim, out_channels=2, kernel_size=2),
            nn.MaxPool1d(kernel_size=seq_len-1)  # [N, C, 1]
        )

        # [N, C, seq_len, 1] --> [N, C, seq_len-2, 1]
        self.gram_3 = nn.Sequential(
            nn.Conv1d(in_channels=embedding_dim, out_channels=2, kernel_size=3),
            nn.MaxPool1d(kernel_size=seq_len-2) # [N, C, 1]
        )
        
        # [N, C, seq_len, 1] --> [N, C, seq_len-3, 1]
        self.gram_4 = nn.Sequential(
            nn.Conv1d(in_channels=embedding_dim, out_channels=2, kernel_size=4),
            nn.MaxPool1d(kernel_size=seq_len-3) # [N, C, 1]
        )

        self.dropout1 = nn.Dropout(p=0.2)
        self.fc1 = nn.Linear(in_features=2*3, out_features=2)
        
    
    def forward(self,X):
        # [B,seq_len,embedding_dim]
        x = self.embed(X)

        # [B, seq_len, embedding_dim] --> [B, embedding_dim, seq_len] 
        x = torch.permute(input=x, dims=(0, 2, 1))
        print(x.shape)  # torch.Size([128, 256, 87])

        x1 = self.gram_2(x)
        print(f"x1.shape={x1.shape}")  #torch.Size([128, ２, 1])
        x2 = self.gram_3(x)
        x3 = self.gram_4(x)

        x = torch.concat(tensors=(x1,x2,x3),dim=1)
        print(x.shape)  # torch.Size([128, ６, 1])
        x = torch.squeeze(x)

        x = self.dropout1(x)
        x = self.fc1(x)

        return x 


class TextCNN2(nn.Module):
    """
        TextCNN优化
    """
    def __init__(self,num_embeddings, embedding_dim,padding_idx,seq_len):
        super().__init__()
        
        self.embed = nn.Embedding(num_embeddings=num_embeddings,
                                 embedding_dim=embedding_dim,
                                 padding_idx=padding_idx)
        
        # [N, C, seq_len] --> [N, C, seq_len-1],[N, C, seq_len-kernel_size+1]
        self.gram_2 = nn.Sequential(
            nn.Conv1d(in_channels=embedding_dim, out_channels=256, kernel_size=2),
            nn.MaxPool1d(kernel_size=seq_len-1)  # [N, C, 1]
        )

        # [N, C, seq_len, 1] --> [N, C, seq_len-2, 1]
        self.gram_3 = nn.Sequential(
            nn.Conv1d(in_channels=embedding_dim, out_channels=256, kernel_size=3),
            nn.MaxPool1d(kernel_size=seq_len-2) # [N, C, 1]
        )

        # [N, C, seq_len, 1] --> [N, C, seq_len-3, 1]
        self.gram_4 = nn.Sequential(
            nn.Conv1d(in_channels=embedding_dim, out_channels=256, kernel_size=4),
            nn.MaxPool1d(kernel_size=seq_len-3) # [N, C, 1]
        )

        self.dropout1 = nn.Dropout(p=0.2)
        self.fc1 = nn.Linear(in_features=256*3, out_features=2)
        
    
    def forward(self,X):
        # [B,seq_len,embedding_dim]
        x = self.embed(X)
        # [B, seq_len, embedding_dim] --> [B, embedding_dim, seq_len] 
        x = torch.permute(input=x, dims=(0, 2, 1))
        # print(x.shape)  # torch.Size([128, 256, 87])

        x1 = self.gram_2(x)
        # print(f"x1.shape={x1.shape}")  #torch.Size([128, 256, 1])
        x2 = self.gram_3(x)
        x3 = self.gram_4(x)

        x = torch.concat(tensors=(x1,x2,x3),dim=1)
        # print(x.shape)  # torch.Size([128, 768, 1])
        x = torch.squeeze(x)

        x = self.dropout1(x)
        x = self.fc1(x)

        return x 


class TextCNN3(nn.Module):
    """
        TextCNN优化，
    """
    def __init__(self,num_embeddings, embedding_dim,padding_idx,seq_len):
        super().__init__()
        
        self.embed = nn.Embedding(num_embeddings=num_embeddings,
                                 embedding_dim=embedding_dim,
                                 padding_idx=padding_idx)
        
        # [N, C, seq_len] --> [N, C, seq_len-1],[N, C, seq_len-kernel_size+1]
        self.gram_2 = nn.Sequential(
            nn.Conv1d(in_channels=embedding_dim, out_channels=256, kernel_size=2),
            nn.BatchNorm1d(num_features=256),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=seq_len-1)  # [N, C, 1]
        )

        # [N, C, seq_len, 1] --> [N, C, seq_len-2, 1]
        self.gram_3 = nn.Sequential(
            nn.Conv1d(in_channels=embedding_dim, out_channels=256, kernel_size=3),
            nn.BatchNorm1d(num_features=256),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=seq_len-2) # [N, C, 1]
        )
        # [N, C, seq_len, 1] --> [N, C, seq_len-3, 1]
        self.gram_4 = nn.Sequential(
            nn.Conv1d(in_channels=embedding_dim, out_channels=256, kernel_size=4),
            nn.BatchNorm1d(num_features=256),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=seq_len-3) # [N, C, 1]
        )

        self.dropout1 = nn.Dropout(p=0.2)
        self.fc1 = nn.Linear(in_features=256*3, out_features=2)
        
    
    def forward(self,X):
        # [B,seq_len,embedding_dim]
        x = self.embed(X)
        # [B, seq_len, embedding_dim] --> [B, embedding_dim, seq_len] 
        x = torch.permute(input=x, dims=(0, 2, 1))
        # print(x.shape)  # torch.Size([128, 256, 87])

        x1 = self.gram_2(x)
        # print(f"x1.shape={x1.shape}")  #torch.Size([128, 256, 1])
        x2 = self.gram_3(x)
        x3 = self.gram_4(x)

        x = torch.concat(tensors=(x1,x2,x3),dim=1)
        # print(x.shape)  # torch.Size([128, 768, 1])
        x = torch.squeeze(x)

        x = self.dropout1(x)
        x = self.fc1(x)

        return x 
