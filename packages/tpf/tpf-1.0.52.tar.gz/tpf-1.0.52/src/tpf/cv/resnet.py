
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F


class ResNet50(nn.Module):
    """
        自定义ResNet
    """
    def __init__(self,n_classes=10):
        super(ResNet50, self).__init__()
        self.n_classes = n_classes

        # 最初的输入
        in_channels = 64

        # 头部
        self.head = nn.Sequential(
            nn.Conv2d(in_channels=3, out_channels=in_channels, kernel_size=7, stride=2, padding=3),
            nn.BatchNorm2d(num_features=in_channels),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        )

        # 第１个大模块
        mid_channels = 64
        out_channels = mid_channels*4
        
        self.block1_small1 = self.small(in_channels=in_channels,mid_channels=mid_channels, out_channels=out_channels, stride=1)
        
        self.block1_short_cut = nn.Sequential(
            nn.Conv2d(in_channels=in_channels, 
                       out_channels=out_channels, 
                       kernel_size=1,
                       stride=1, 
                       padding=0),
            nn.BatchNorm2d(num_features=out_channels)
        )

        
        self.block1_small2 = self.small(in_channels=out_channels,mid_channels=mid_channels, out_channels=out_channels,stride=1)
        
        # 第2个大模块
        in_channels  = out_channels
        mid_channels = in_channels//2
        out_channels = mid_channels*4
        
        self.block2_small1 = self.small(in_channels=in_channels,mid_channels=mid_channels, out_channels=out_channels,stride=2)
        
        self.block2_short_cut = nn.Sequential(
            nn.Conv2d(in_channels=in_channels, 
                       out_channels=out_channels, 
                       kernel_size=1,
                       stride=2, 
                       padding=0),
            nn.BatchNorm2d(num_features=out_channels)
        )
        
        self.block2_small2 = self.small(in_channels=out_channels,mid_channels=mid_channels, out_channels=out_channels,stride=1)
        

        # 第3个大模块
        in_channels  = out_channels
        mid_channels = in_channels//2
        out_channels = mid_channels*4
        
        self.block3_small1 = self.small(in_channels=in_channels,mid_channels=mid_channels,out_channels=out_channels,stride=2)
        
        self.block3_short_cut = nn.Sequential(
            nn.Conv2d(in_channels=in_channels, 
                       out_channels=out_channels, 
                       kernel_size=1,
                       stride=2, 
                       padding=0),
            nn.BatchNorm2d(num_features=out_channels)
        )

        
        self.block3_small2 = self.small(in_channels=out_channels,mid_channels=mid_channels,out_channels=out_channels,stride=1)
        

        # 第4个大模块
        in_channels  = out_channels
        mid_channels = in_channels//2
        out_channels = mid_channels*4
        
        self.block4_small1 = self.small(in_channels=in_channels,mid_channels=mid_channels,out_channels=out_channels,stride=2)
        
        self.block4_short_cut = nn.Sequential(
            nn.Conv2d(in_channels=in_channels, 
                       out_channels=out_channels, 
                       kernel_size=1,
                       stride=2, 
                       padding=0),
            nn.BatchNorm2d(num_features=out_channels)
        )

        self.block4_small2 = self.small(in_channels=out_channels,mid_channels=mid_channels,out_channels=out_channels,stride=1)
        
    
        
        # 在某种程度，可以部分实现输入任意大小的图像
        self.avgpool = nn.AdaptiveAvgPool2d(output_size=(1, 1))
        
        # classifier
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(in_features=2048, out_features=self.n_classes)
        )

    def small(self, in_channels, mid_channels, out_channels=None, stride=1):
        if out_channels:
            pass 
        else:
            out_channels = mid_channels*4

        return nn.Sequential(
            # Conv1 
            nn.Conv2d(in_channels=in_channels, out_channels=mid_channels, kernel_size=1, stride=1, padding=0),
            nn.BatchNorm2d(num_features=mid_channels),
            nn.ReLU(),
            
            # Conv2 注意stride
            nn.Conv2d(in_channels=mid_channels, out_channels=mid_channels, kernel_size=3, stride=stride, padding=1),
            nn.BatchNorm2d(num_features=mid_channels),
            nn.ReLU(),
            
            # Conv1 注意stride
            nn.Conv2d(in_channels=mid_channels, out_channels=out_channels, kernel_size=1, stride=1, padding=0),
            nn.BatchNorm2d(num_features=out_channels)
        ) 

 
        
    def forward(self, x):
        # [B, 3, 224, 224] --> [B, 64, 56, 56]
        x = self.head(x)


        # 第１个模块　
        h1 = self.block1_small1(x)
        h2 = self.block1_short_cut(x)
        o1 = h1 + h2 

        for i in range(3-1):
            o2 = self.block1_small2(o1)
            o1 = o1 + o2   # [32, 256, 56, 56]


        # 第2个模块　
        h1 = self.block2_small1(o1)
        h2 = self.block2_short_cut(o1)
        o1 = h1 + h2 # [32, 512, 28, 28]

        for i in range(4-1):
            o2 = self.block2_small2(o1)
            o1 = o1 + o2   # [32, 512, 28, 28]

        # 第3个模块　
        h1 = self.block3_small1(o1)
        h2 = self.block3_short_cut(o1)
        o1 = h1 + h2 
        for i in range(6-1):
            o2 = self.block3_small2(o1)
            o1 = o1 + o2  # [32, 1024, 14, 14]

        # 第4个模块　
        h1 = self.block4_small1(o1)
        h2 = self.block4_short_cut(o1)
        o1 = h1 + h2 
        for i in range(3-1):
            o2 = self.block4_small2(o1)
            o1 = o1 + o2  # [32, 2048, 7, 7]


        # [B, 2048, 1, 1]
        x = self.avgpool(o1)

        # [B, 2048] --> [B, 100]
        x = self.classifier(x)  # [32, 100]
        return x


class SmallBlock(nn.Module):
    """
        三层一模块
    """
    def __init__(self, in_channel, out_channel, stride, first=False):
        """
        params
        -----------------------
        - in_channel: 模块输入通道数
        - out_channel：模块输出通道数
        - stride：每个模块第二层步长，如果有短接层，也指短接层的步长
        - first：是否为resnet中每一个大模块中的第一个小模块；若是则有一个短接操作，反之直接与输入数据x短接
        """
        # 中间模块是输出模块通道数的四分之一 
        middle_channel = out_channel//4
        
        self.first = first
        
        super().__init__()
        self.main = nn.Sequential( 
            nn.Conv2d(in_channels=in_channel, out_channels=middle_channel, kernel_size=1, stride=1, padding=0),
            nn.BatchNorm2d(num_features=middle_channel),
            nn.ReLU(),
            
            nn.Conv2d(in_channels=middle_channel, out_channels=middle_channel, kernel_size=3, stride=stride, padding=1),
            
            nn.Conv2d(in_channels=middle_channel, out_channels=out_channel, kernel_size=1, stride=1, padding=0),
            nn.BatchNorm2d(num_features=out_channel)
            
        )
        
        self.short = nn.Sequential(
            nn.Conv2d(in_channels=in_channel, 
                       out_channels=out_channel, 
                       kernel_size=1,
                       stride=stride, 
                       padding=0),
            nn.BatchNorm2d(num_features=out_channel)
        )
    
    def forward(self, x):
        # 短接分支
        if self.first:  # 第一个模块与变换后的x短接
            h1 = self.short(x)
        else:
            h1 = x      # 后续模块与x本身短接
        # 主分支
        h2 = self.main(x)
        
        # 短接操作
        h = h1 + h2
        
        o = F.relu(h)
        
        return o


class ResNet50V2(nn.Module):
    """
        自定义ResNet
    """
    def __init__(self, in_channels=3, n_classes=1000):
        """ 
        - in_channels:输入图像通道数
        - n_classes:最后一层全连接的维度，也是标签类别个数 
        - 输入[32,3,224,224],输出[32,n_classes],
        - 损失计算：模型单个输出值在0-1之间，元素个数为n_classes的向量，求其最大值索引，与标签求损失
        """
        super().__init__()
    
        # 开始部分,升维，收缩特征图
        self.head = nn.Sequential(
            # (224 +2*3 - 7)/2 + 1 =  112.5 -> 112
            nn.Conv2d(in_channels=in_channels, out_channels=64, kernel_size=7, stride=2, padding=3),  #先将扩展通道的维度，扩展20倍
            nn.BatchNorm2d(num_features=64),
            nn.ReLU(),

            # (112 + 2*1 - 3)/2 + 1 = 56.5 -> 56
            nn.MaxPool2d(kernel_size=3, stride=2, padding=1)  #初步舍弃一部分不重要的/噪声信息，舍弃四分之三左右 
        )
        
        # 第一个大模块，三个小三层，输出256*56*56
        self.block1 = nn.Sequential(
            SmallBlock(in_channel=64, out_channel=256, stride=1, first=True),
            SmallBlock(in_channel=256, out_channel=256, stride=1),
            SmallBlock(in_channel=256, out_channel=256, stride=1),
        )
        
        # 第二个大模块，四个小三层, 输出512*28*28
        self.block2 = nn.Sequential(
            SmallBlock(in_channel=256, out_channel=512, stride=2, first=True),
            SmallBlock(in_channel=512, out_channel=512, stride=1),
            SmallBlock(in_channel=512, out_channel=512, stride=1),
            SmallBlock(in_channel=512, out_channel=512, stride=1)
        )
        
        # 第三个大模块,六个小三层，输出1024×14×14
        self.block3 = nn.Sequential(
            SmallBlock(in_channel=512, out_channel=1024, stride=2, first=True),
            SmallBlock(in_channel=1024, out_channel=1024, stride=1),
            SmallBlock(in_channel=1024, out_channel=1024, stride=1),
            SmallBlock(in_channel=1024, out_channel=1024, stride=1),
            SmallBlock(in_channel=1024, out_channel=1024, stride=1),
            SmallBlock(in_channel=1024, out_channel=1024, stride=1)
        )
        
        # 第四个大模块,六个小三层，输出2048×7×7 
        self.block4 = nn.Sequential(
            SmallBlock(in_channel=1024, out_channel=2048, stride=2, first=True),
            SmallBlock(in_channel=2048, out_channel=2048, stride=1),
            SmallBlock(in_channel=2048, out_channel=2048, stride=1),
        )
        
        # 2048×1×1
        self.avgpool = nn.AdaptiveAvgPool2d(output_size=(1, 1))
        
        # classifier
        if n_classes< 128:
            self.classifier = nn.Sequential(
                nn.Flatten(),
                nn.Linear(in_features=2048, out_features=512),
                nn.Dropout(p=0.2),
                nn.Linear(in_features=512, out_features=n_classes)
            ) 
        else:
            self.classifier = nn.Sequential(
                nn.Flatten(),
                nn.Linear(in_features=2048, out_features=n_classes)
            )
        
    def forward(self, X):
        x = self.head(X)    # [B, 3, 224, 224] -> [B, 64, 56, 56]
        print(x.shape)
        x = self.block1(x)  # [B,  64, 56, 56] -> [B, 256, 56, 56]
        x = self.block2(x)  # [B, 256, 56, 56] -> [B, 512, 28, 28]
        x = self.block3(x)  # [B, 512, 28, 28] -> [B, 1024,14, 14]
        x = self.block4(x)  # [B, 1024,14, 14] -> [B, 2048, 7,  7]
        
        x = self.avgpool(x) # [B, 2048, 7,  7] -> [B, 2048, 1,  1]

        x = self.classifier(x) # [B, 2048, 1,  1] --> [B, 1000]
        
        return x

def test_model():
    """
    
    """
    model = ResNet50V2()
    x = torch.randn(size=(32,3,224,224))
    y = model(x) 
    print(y.shape)  # torch.Size([32, 1000])

    model = ResNet50V2(n_classes=100)
    x = torch.randn(size=(32,3,224,224))
    y = model(x) 
    print(y.shape)  # torch.Size([32, 100])


def train_once_demo(train_dataloader):
    """
    - 输入[32,3,224,224],输出[32,n_classes],
    - 损失计算：模型单个输出值在0-1之间，元素个数为n_classes的向量，求其最大值索引，与标签求损失

    运行示例：
    ------------------------------
    train_once_demo(train_dataloader)

    torch.Size([32, 3, 224, 224]) torch.Size([32])
    y_pred: tensor([26, 33, 22, 33, 33, 44, 26,  4, 44, 33, 22, 49,  4,  4,  4, 72, 22,  4,
            22,  4,  4, 33, 89, 33,  4, 70, 33, 33, 26,  4,  4, 26])
    label: tensor([39, 98, 36, 47, 78, 11,  4, 81, 25, 19, 79, 65, 56, 75, 77, 83, 95, 45,
            62, 66,  6, 33, 55, 26, 36, 43, 58,  8,  3, 16, 86, 81])
    自然概率： 0.03125


    损失函数
    -----------------------------
    loss_fn = nn.CrossEntropyLoss()
    两个参数：
    1. 模型的输出 0-1之间
    2. 标签，0,1,2,3, .... 

    """
    # 模型
    # -----------------------------------------

    # 检测GPU
    device = "cuda:0" if torch.cuda.is_available() else "cpu"

    # 构建模型
    resnet50 = ResNet50V2(n_classes=100)

    # 转到GPU
    resnet50.to(device=device)
    
    # 损失函数
    loss_fn = nn.CrossEntropyLoss()

    # 优化
    optimizer = torch.optim.SGD(params=resnet50.parameters(), lr=1e-3)


    resnet50.train()
    for X,y in train_dataloader:
        print(X.shape,y.shape)  # torch.Size([32, 3, 224, 224]) torch.Size([32])
        X.to(device=device)
        y.to(device=device)

        # 正向传播
        y_out = resnet50(X=X)
        print("y_out:",y_out)

        # 损失计算
        loss = loss_fn(y_out, y)

        # 梯度计算
        optimizer.zero_grad()
        loss.backward()

        # 参数优化
        optimizer.step()

        # 自然概率
        y_pred = y_out.argmax(dim=1)
        print("y_pred:",y_pred)
        print("label:",y)

        # 0表示一个也没预测正确，即模型开始时参数不具备预测能力
        print("自然概率：",(y_pred == y).float().mean().item())
        break 

if __name__=="__main__":
    # test_model()
    # 数据
    # -----------------------------------------
    from tpf.d1 import pkl_load
    from tpf.params import IMG_CIFAR 
    import os 
    data_base = "/wks/datasets/images"
    data_base = IMG_CIFAR 

    c100 = os.path.join(data_base,"c100_train.pkl")
    train_dataset = pkl_load(file_path=c100)
    c100_test = os.path.join(data_base,"c100_test.pkl")
    test_dataset = pkl_load(file_path=c100_test)

    # from torch.utils.data import DataLoader
    # train_dataloader = DataLoader(dataset=train_dataset, batch_size=32, shuffle=True)
    # train_once_demo(train_dataloader)
    
    from tpf.dl import T 
    # 检测GPU
    device = "cuda:0" if torch.cuda.is_available() else "cpu"

    # 构建模型
    resnet50 = ResNet50V2(n_classes=100)

    # 损失函数
    loss_fn = nn.CrossEntropyLoss()

    T.train(
            model=resnet50, 
            loss_fn=loss_fn,
            optimizer="adam", 
            train_dataset=train_dataset, test_dataset=test_dataset,
            epochs=30, 
            learning_rate=1e-3,
            model_param_path="/wks/datasets/images/c100_1.h5",
            auto_save=True,
            continuation=True,
            is_regression=False,
            log_file="/tmp/train.log")