
from torch.utils.data import DataLoader, Dataset
import torch
import numpy as np
import os
from PIL import Image


class FaceDataset(Dataset):
    def __init__(self, path):
        """
        人脸数据批量处理
        """
        super(FaceDataset, self).__init__()
        self.path = path
        self.datasets = []

        with open(os.path.join(path, "positive.txt")) as f:
            self.datasets.extend(f.readlines())

        with open(os.path.join(path, "negative.txt")) as f:
            self.datasets.extend(f.readlines())

        with open(os.path.join(path, "part.txt")) as f:
            self.datasets.extend(f.readlines())

    def __len__(self):
        return len(self.datasets)

    def __getitem__(self, item):
        """
        positive/0.jpg 
        1 

        # 4个box的偏移率
        0.15591397849462366 
        -0.01881720430107527 
        -0.08064516129032258 
        -0.002688172043010753 

        # 5个位置的偏移率
        0.34408602150537637 
        0.33602150537634407 
        0.6505376344086021 
        0.3736559139784946 
        0.5161290322580645 
        0.5403225806451613 
        0.3172043010752688 
        0.7123655913978495 
        0.5645161290322581 
        0.739247311827957
        """
        strs = self.datasets[item].strip().split()
        img_name = strs[0]  # 名称

        cls = torch.tensor([int(strs[1])], dtype=torch.float32) # 标签类别 

        strs[2:] = [float(x) for x in strs[2:]]
        offset = torch.tensor(strs[2:6], dtype=torch.float32) # 4个box的偏移率

        point = torch.tensor(strs[6:16], dtype=torch.float32) # 5个位置的偏移率

        img = Image.open(os.path.join(self.path, img_name))
        img_data = torch.tensor((np.array(img) / 255. - 0.5) / 0.5, dtype=torch.float32)
        img_data = img_data.permute(2, 0, 1)  # [h,w,c] --> [c,h,w]

        return img_data, cls, offset, point


def face_test():
    # data = FaceDataset(r"D:\DataSets\MTCNN\landmaks\48")
    data = FaceDataset(r"/data/tmp/MTCNN/48")
    img_data, cls, offset, point = data[0]
    print(f"img_data.shape={img_data.shape},cls={cls.item()}")
    print(f"box offset = {offset}")
    print(f"point offset = {point}")

    """
    img_data.shape=torch.Size([3, 48, 48]),cls=1.0
    box offset = tensor([ 0.0566, -0.1132, -0.1321, -0.0283])
    point offset = tensor([0.2547, 0.2642, 0.6321, 0.2642, 0.3868, 0.5000, 0.2830, 0.6651, 0.6604,
            0.6651])
    """

    print(f"数据个数：{len(data)}")  # 数据个数：102
    dataloder = DataLoader(data, batch_size=4, shuffle=True)
    print(f"总批次：{len(dataloder)}") # 总批次：26
    for img_data, cls, offset, point in dataloder:
        print(img_data.shape,cls)
        """
        batch_size=4 所以一次取出4条记录
        torch.Size([4, 3, 48, 48]) tensor([[0.],
        [0.],
        [0.],
        [0.]])
        """
        break


if __name__ == '__main__':
    face_test()
    




