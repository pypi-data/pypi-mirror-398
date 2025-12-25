import torch
from torch import nn
from torch.utils.data import DataLoader
from tpf.cv.dataset import FaceDataset 
import os
from tqdm.autonotebook import tqdm


class PNet(nn.Module):
    def __init__(self):
        super(PNet, self).__init__()
        
        self.pre_layer = nn.Sequential(
            # 第1层卷积
            nn.Conv2d(in_channels=3,
                      out_channels=10,
                      kernel_size=3,
                      stride=1,
                      padding=0),
            nn.BatchNorm2d(num_features=10),
            nn.PReLU(num_parameters=10, init=0.25),

            # 最大池化
            nn.MaxPool2d(kernel_size=2, stride=2),

            # 第2层卷积
            nn.Conv2d(in_channels=10,
                      out_channels=16,
                      kernel_size=3,
                      stride=1,
                      padding=0),
            nn.BatchNorm2d(num_features=16),
            nn.PReLU(num_parameters=16, init=0.25),

            # 第3层卷积
            nn.Conv2d(in_channels=16,
                      out_channels=32,
                      kernel_size=3,
                      stride=1,
                      padding=0),
            nn.BatchNorm2d(num_features=32),
            nn.PReLU(num_parameters=32, init=0.25)
        )

        # 输出人脸的概率 bce
        self.conv4_1 = nn.Conv2d(in_channels=32,
                                 out_channels=1,
                                 kernel_size=1,
                                 stride=1,
                                 padding=0)

        # 输出人脸的定位框的偏移量（误差）
        self.conv4_2 = nn.Conv2d(in_channels=32,
                                 out_channels=4,
                                 kernel_size=1,
                                 stride=1,
                                 padding=0)

    def forward(self, x):
        x = self.pre_layer(x)
        cls = torch.sigmoid(self.conv4_1(x))
        offset = self.conv4_2(x)
        return cls, offset

class RNet(nn.Module):
    def __init__(self):
        super(RNet, self).__init__()
        self.pre_layer = nn.Sequential(

            nn.Conv2d(3, 28, 3, 1),
            nn.BatchNorm2d(28),
            nn.PReLU(28),

            nn.MaxPool2d(3, 2, padding=1),

            nn.Conv2d(28, 48, 3, 1),
            nn.BatchNorm2d(48),
            nn.PReLU(48),

            nn.MaxPool2d(3, 2),

            nn.Conv2d(48, 64, 2, 1),
            nn.BatchNorm2d(64),
            nn.PReLU(64),
        )

        self.linear4 = nn.Sequential(
            nn.Linear(64 * 3 * 3, 128),
            nn.PReLU(128)
        )

        self.linear5_1 = nn.Linear(128, 1)
        self.linear5_2 = nn.Linear(128, 4)

    def forward(self, x):
        x = self.pre_layer(x)
        x = x.view(x.size(0), -1)
        x = self.linear4(x)
        cls = torch.sigmoid(self.linear5_1(x))
        offset = self.linear5_2(x)
        return cls, offset


class ONet(nn.Module):
    def __init__(self):
        super(ONet, self).__init__()
        self.pre_layer = nn.Sequential(

            nn.Conv2d(3, 32, 3, 1),  # 46
            nn.BatchNorm2d(32),
            nn.PReLU(32),

            nn.MaxPool2d(3, 2, padding=1),  # 23

            nn.Conv2d(32, 64, 3, 1),  # 21
            nn.BatchNorm2d(64),
            nn.PReLU(64),

            nn.MaxPool2d(3, 2),  # 10

            nn.Conv2d(64, 64, 3, 1),  # 8
            nn.BatchNorm2d(64),
            nn.PReLU(64),

            nn.MaxPool2d(2, 2),  # 4

            nn.Conv2d(64, 128, 2, 1),  # 3
            nn.BatchNorm2d(128),
            nn.PReLU(128)
        )
        self.linear5 = nn.Sequential(
            nn.Linear(128 * 3 * 3, 256),
            nn.PReLU(256)
        )
        self.linear6_1 = nn.Linear(256, 1)
        self.linear6_2 = nn.Linear(256, 4)
        self.linear6_3 = nn.Linear(256, 10)

    def forward(self, x):
        x = self.pre_layer(x)
        x = x.view(-1, 128 * 3 * 3)
        x = self.linear5(x)
        cls = torch.sigmoid(self.linear6_1(x))
        offset = self.linear6_2(x)
        point = self.linear6_3(x)
        return cls, offset, point


class Trainer:
    def __init__(self, net, param_path, data_path):
        # 检测是否有GPU
        self.device = torch.device(device='cuda:0') if torch.cuda.is_available() else torch.device(device="cpu")
        
        # 把模型搬到device
        self.net = net.to(self.device)
        self.param_path = param_path

        # 打包数据
        self.datasets = FaceDataset(data_path)

        # 定义损失函数：类别判断（分类任务）
        self.cls_loss_func = torch.nn.BCELoss()

        # 定义损失函数：框的偏置回归
        self.offset_loss_func = torch.nn.MSELoss()

        # 定义损失函数：关键点的偏置回归
        self.point_loss_func = torch.nn.MSELoss()

        # 定义优化器
        self.optimizer = torch.optim.Adam(params=self.net.parameters(), lr=1e-3)

    def train(self, max_epochs=50, stop_value=0.001, landmark=False):
        """
            - 连接训练  
            - transfer learning 迁移学习
            - pretrained model 预训练

        :param stop_value:
        :param landmark:
        :return:
        """

        # 加载上次训练的参数
        if os.path.exists(self.param_path):
            self.net.load_state_dict(torch.load(self.param_path))
        else:
            print("NO Param")

        # 封装数据加载器
        dataloader = DataLoader(self.datasets, batch_size=512, shuffle=True)

        epochs = 0

        while epochs < max_epochs:
            # 训练一轮
            for i, (img_data, _cls, _offset, _point) in enumerate(dataloader):

                # 数据搬家
                img_data = img_data.to(self.device)
                _cls = _cls.to(self.device)
                _offset = _offset.to(self.device)
                _point = _point.to(self.device)

                # O-Net输出三个
                if landmark:
                    out_cls, out_offset, out_point = self.net(img_data)
                else:
                    out_cls, out_offset = self.net(img_data)

                # [B, 1, 1, 1] --> [B, 1]
                out_cls = out_cls.view(-1, 1)

                # [B, 4, 1, 1] --> [B, 4]
                out_offset = out_offset.view(-1, 4)

                # 选取置信度为0，1的正负样本求置信度损失
                # 0: 负样本 1：正样本 2：偏样本
                # 人脸分类时，只选了正负样本，没有要部分样本 
                cls_mask = torch.lt(_cls, 2)

                # 筛选复合条件的样本的：标签
                cls = torch.masked_select(_cls, cls_mask)

                # 筛选复合条件的样本的：预测值
                out_cls = torch.masked_select(out_cls, cls_mask)

                # 求解分类的loss
                cls_loss = self.cls_loss_func(out_cls, cls)

                # 选取正样本和部分样本求偏移率的损失

                # 选取正样本和偏样本
                # 偏移计算时，没有要负样本
                offset_mask = torch.gt(_cls, 0)

                # bbox的标签
                offset = torch.masked_select(_offset, offset_mask)

                # bbox的预测值，模型输出的值
                out_offset = torch.masked_select(out_offset, offset_mask)

                # bbox损失
                offset_loss = self.offset_loss_func(out_offset, offset)

                if landmark:
                    # 正和偏样本的landmark损失
                    point = torch.masked_select(_point, offset_mask)
                    out_point = torch.masked_select(out_point, offset_mask)
                    point_loss = self.point_loss_func(out_point, point)
                    # O-Net 的 最终损失！！！！！！！
                    loss = cls_loss + offset_loss + point_loss
                else:
                    # P-Net和R-Net 的 最终损失！！！！！！！
                    loss = cls_loss + offset_loss

                if landmark:
                    print("loss:{0:.4f}, cls_loss:{1:.4f}, offset_loss:{2:.4f}, point_loss:{3:.4f}".format(
                        loss.float(), cls_loss.float(), offset_loss.float(), point_loss.float()))
                else:
                    print("loss:{0:.4f}, cls_loss:{1:.4f}, offset_loss:{2:.4f}".format(
                        loss.float(), cls_loss.float(), offset_loss.float()))

                # 清空梯度
                self.optimizer.zero_grad()

                # 梯度回传
                loss.backward()

                # 优化
                self.optimizer.step()

            # 保存模型（参数）
            torch.save(self.net.state_dict(), self.param_path)

            # 轮次加1
            epochs += 1
            print("epochs:",epochs,"---------------------------------------")
            
            # 设定误差限制
            if loss < stop_value:
                break



if __name__ == '__main__':
    # pnet = PNet()
    # x = torch.rand(5, 3, 12, 12)
    # cls, offset = pnet(x)
    # # cls.shape=torch.Size([5, 1, 1, 1]),offset.shape=torch.Size([5, 4, 1, 1])
    # print(f"cls.shape={cls.shape},offset.shape={offset.shape}")


    # x = torch.rand(5, 3, 14, 14)
    # cls, offset = pnet(x)
    # # cls.shape=torch.Size([5, 1, 2, 2]),offset.shape=torch.Size([5, 4, 2, 2])
    # print(f"cls.shape={cls.shape},offset.shape={offset.shape}")


    # x = torch.rand(5, 3, 24, 24)
    # rnet = RNet()
    # cls, offset = rnet(x)
    # # cls.shape=torch.Size([5, 1]),offset.shape=torch.Size([5, 4])
    # print(f"cls.shape={cls.shape},offset.shape={offset.shape}")

    x = torch.rand(5, 3, 48, 48)
    onet = ONet()
    cls, offset, point = onet(x)
    # cls.shape=torch.Size([5, 1]),offset.shape=torch.Size([5, 4])
    print(f"cls.shape={cls.shape},offset.shape={offset.shape}")
