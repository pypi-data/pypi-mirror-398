
# Check if torch is available
try:
    import torch
    from torch import nn
    from torch.nn import functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# Define SeqOne only if torch is available
if TORCH_AVAILABLE:
    class SeqOne(nn.Module):
        def __init__(self, seq_len, in_features=1, out_features=2):
            super().__init__()
            hidden_size = 256
            self.gram_2 = nn.Sequential(
                nn.Conv1d(in_channels=in_features, out_channels=hidden_size, kernel_size=2,stride=1,padding=1),
                nn.BatchNorm1d(num_features=hidden_size),
                nn.ReLU(),
                nn.MaxPool1d(kernel_size=2)  # [N, C, 1],
            )

            self.gram_3 = nn.Sequential(
                nn.Conv1d(in_channels=in_features, out_channels=hidden_size, kernel_size=3,stride=1,padding=1),
                nn.BatchNorm1d(num_features=hidden_size),
                nn.ReLU(),
                nn.MaxPool1d(kernel_size=2) # [N, C, 1]
            )

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
            self.ft = nn.Flatten()
            ll = ((seq_len+2*1)-2+1)//2+((seq_len+2*1)-3+1)//2+((seq_len+2*1)-4+1)//2 +seq_len
            ll=(ll//4)*256
            print(ll)
            self.fc1 = nn.Linear(in_features=ll, out_features=hidden_size)
            self.dropout2 = nn.Dropout(p=0.5)
            self.fc2 = nn.Linear(in_features=hidden_size, out_features=out_features)


        def attention(self, Q, K, V, mask=None, multihead=False):
            n_shape = len(Q.shape)
            if n_shape == 4:
                seq_len = Q.shape[2]
                score = torch.matmul(Q, K.permute(0, 1, 3, 2))
            elif n_shape == 3:
                seq_len = Q.shape[1]
                score = torch.matmul(Q, K.permute(0, 2, 1))
            else:
                raise Exception(f"only 3 or 4 dim,now is {n_shape}")

            k = Q.shape[-1]
            score /= k ** 0.5

            if mask is not None:
                score = score.masked_fill_(mask, -float('inf'))

            score = torch.softmax(score, dim=-1)
            score = torch.matmul(score, V)

            if multihead :
                head_n = Q.shape[1]
                k = Q.shape[-1]
                embedding_dim = head_n*k
                score = score.permute(0, 2, 1, 3).reshape(-1, seq_len, embedding_dim)

            return score


        def forward(self,X):
            # seq_len = X.shape[1]
            x=X.unsqueeze(dim=1)
            x1 = self.gram_2(x)
            x2 = self.gram_3(x)
            x3 = self.gram_4(x)
            x4 = self.attention(x,x,x)
            x4 = self.conv3(x4)
            x = torch.concat(tensors=(x1,x2,x3,x4),dim=2)
            x = self.conv1(x)
            x = self.conv2(x)
            x = self.dropout1(x)
            x = self.ft(x)
            x = self.fc1(x)
            x = self.dropout2(x)
            x = self.fc2(x)
            return x
else:
    # Fallback placeholder class when torch is not available
    class SeqOne:
        def __init__(self, seq_len, in_features=1, out_features=2):
            raise ImportError("PyTorch is not installed. Please install torch to use SeqOne deep learning model.")

        def forward(self, X):
            raise ImportError("PyTorch is not installed. Please install torch to use SeqOne deep learning model.") 



