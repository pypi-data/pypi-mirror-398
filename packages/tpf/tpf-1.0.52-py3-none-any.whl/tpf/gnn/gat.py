import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv, Linear


class GAT(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels=128, out_channels=1, heads=8):
        super().__init__()
        self.conv1 = GATConv(in_channels, hidden_channels, heads, dropout=0.1)
        self.conv2 = GATConv(hidden_channels * heads, hidden_channels, heads=1, concat=False, dropout=0.1)
        self.conv3 = GATConv(hidden_channels, int(hidden_channels/4), heads=1, concat=False, dropout=0.1)
        self.lin = Linear(int(hidden_channels/4), out_channels)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x, edge_index, edge_attr):
        x = F.dropout(x, p=0.1, training=self.training)
        x = F.elu(self.conv1(x, edge_index, edge_attr))
        x = F.dropout(x, p=0.1, training=self.training)
        x = F.elu(self.conv2(x, edge_index, edge_attr))
        x = F.elu(self.conv3(x, edge_index, edge_attr))
        x = self.lin(x)
        x = self.sigmoid(x)
        
        return x



