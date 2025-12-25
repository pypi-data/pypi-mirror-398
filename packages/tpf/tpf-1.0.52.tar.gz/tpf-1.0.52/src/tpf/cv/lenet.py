import torch
from torch import nn
from torch.nn import functional as F

class LeNet2(nn.Module):
    
    def __init__(self,n_classes=10):
        """LeNet优化版 
        - 输入:32*32固定大小图片,格式[B,C,32,32]
        - 输出:批次的类别，格式[B, n_classes]
        """
        super().__init__()
        self.n_classes = n_classes

        # 第 1 层, [B, 1, 32, 32] -- > [B, 16, 16, 16]
        self.layer1 = nn.Sequential(
            nn.Conv2d(in_channels=1, out_channels=6, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(num_features=6),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2, padding=0)
        )
        
        # 第 2 层, [B, 6, 16, 16] --> [B, 16, 8, 8], 层数多少会影响模型收敛速度
        self.layer2 = nn.Sequential(
            nn.Conv2d(in_channels=6, out_channels=16, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(num_features=16),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2, padding=0)
        )
        
        # 分类
        self.classifier = nn.Sequential(
            nn.Linear(in_features=16*8*8, out_features=1024),
            nn.Dropout(p=0.3),
            nn.Linear(in_features=1024, out_features=256),
            nn.Dropout(p=0.2),
            nn.Linear(in_features=256, out_features=self.n_classes)
        )
    
    
    def forward(self,x):
        
        # [B, 1, 32, 32] -- > [B, 6, 16, 16]
        h = self.layer1(x)
        
        # [B, 6, 16, 16] --> [B, 16, 8, 8]
        h = self.layer2(h)
        
        # 维度转换 [B, 16, 8, 8] --> [B, 16*8*8=1024]
        h = h.view(h.size(0), -1)
        
        # [B, 1024] --> [B, 10]
        o = self.classifier(h)
        
        return o

class LeNet3(nn.Module):
    """
        LeNet,简易版
    """
    
    def __init__(self,n_classes=10):
        super().__init__()
        
        # 第 1 层, [B, 1, 32, 32] -- > [B, 16, 16, 16]
        self.layer1 = nn.Sequential(
            nn.Conv2d(in_channels=1, out_channels=16, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(num_features=16),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2, padding=0)
        )
        
        # 分类
        self.classifier = nn.Sequential(
            nn.Linear(in_features=16*16*16, out_features=n_classes)
        )
    
    
    def forward(self,x):
        
        # [B, 1, 32, 32] -- > [B, 6, 16, 16]
        h = self.layer1(x)
        
        # 维度转换 [B, 16, 16, 16] --> [B, 4096=16*16*16]
        h = h.view(h.size(0), -1)
        
        # [B, 4096] --> [B, 10]
        o = self.classifier(h)
        
        return o

class LeNet1(nn.Module):
    
    def __init__(self,n_classes=10):
        """论文中的LeNet:
        ２次卷积，池化，三次全连接;

        输入：[B,1,H,W]
        输出：[B,n_classes]
        """
        super().__init__()

        self.n_classes = n_classes # 标签类别个数


        # 第１层网络，卷积，[B, 1, 32, 32] --> [B, 6, 30, 30]
        self.conv1 = nn.Conv2d(in_channels=1, out_channels=6, kernel_size=3, stride=1, padding=0)
        
        # [B, 6, 30, 30] --> [B, 6, 15, 15]
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2, padding=0)
        self.relu1 = nn.ReLU()
        
        # 第２层网络，卷积，[B, 6, 15, 15] --> [B, 16, 13, 13]
        self.conv2 = nn.Conv2d(in_channels=6, out_channels=16, kernel_size=3, stride=1, padding=0)
        # [B, 16, 13, 13] --> [B, 16, 6, 6]
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2, padding=0)
        self.relu2 = nn.ReLU()
        
        # 展平层，辅助功能，处理数据使之能适合后面的全连接,[B, 16, 6, 6] --> [B, 16*6*6], 16*6*6=567
        self.flatten = nn.Flatten()
        
        # 第3层网络，全连接分类
        self.fc1 = nn.Linear(in_features=576, out_features=256)
        
        # 第4层网络，全连接分类
        self.fc2 = nn.Linear(in_features=256, out_features=128)
        
        # 第5层网络，全连接分类
        self.fc3 = nn.Linear(in_features=128, out_features=self.n_classes)
        
    
    def forward(self,x):

        # [B, 1, 32, 32] --> [B, 6, 30, 30]
        x = self.conv1(x)
        
        # [B, 6, 30, 30] --> [B, 6, 15, 15]
        x = self.pool1(x)
        
        x = self.relu1(x)
        
        # [B, 6, 15, 15] --> [B, 16, 13, 13]
        x = self.conv2(x)
        
        # [B, 16, 13, 13] --> [B, 16, 6, 6]
        x = self.pool2(x)

        x = self.relu2(x)
        
        # [B, 16, 6, 6] --> [B, 576]
        x = self.flatten(x)
        
        # [B, 576] --> [B, 256]
        x = self.fc1(x)
        
        # [B, 256] --> [B, 128]
        x = self.fc2(x)
        
        # [B, 128] --> [B, 10]
        x = self.fc3(x)
        
        return x


def test_LeNet():
    # 构建模型
    lenet = LeNet1()
    x = torch.randn(32, 1, 32, 32)

    # 正向传播
    y = lenet(x)
    print(y.shape)  # torch.Size([32, 10])


def test_LeNet2():
    model = LeNet2()
    x = torch.randn(size=(32,1,32,32))
    y = model(x) 
    print(y.shape)  # torch.Size([32, 10])


if __name__ == "__main__":

    test_LeNet2()
    # test_LeNet()
    
