"""dlt1 深度学习训练简易版 常用方法 

"""
import numpy as np 

# PyTorch 三组件
import torch
from torch import nn
from torch.nn import functional as F

# 数据打包工具
from torch.utils.data import Dataset
from torch.utils.data import DataLoader


class DsReg(Dataset):
    """回归问题最简数据集
    """
    def __init__(self, X, y):
        """超参
        """
        self.X = X
        self.y = y
    
    def __getitem__(self, idx):
        """根据索引返回一对数据 (x, y)
        """
        return torch.tensor(data=self.X[idx]).float(), torch.tensor(data=self.y[idx]).float()
    
    
    def __len__(self):
        """数据总数
        """
        return len(self.X)
    
    

class DatasetCls(Dataset):
    """回归问题最简数据集
    """
    def __init__(self, X, y):
        """超参
        """
        self.X = X
        self.y = y
    
    def __getitem__(self, idx):
        """根据索引返回一对数据 (x, y)
        """
        return torch.tensor(data=self.X[idx]).float(), torch.tensor(data=self.y[idx]).long()
    
    
    def __len__(self):
        """数据总数
        """
        return len(self.X)

class LinearRegression(nn.Module):
    """模型定义
    """
    
    def __init__(self, in_features, out_features):
        """参数网络设计
        - 总体来说，做的事件是将数据从一个维度转换到另外一个维度
        """
        super().__init__()
        
        self.linear = nn.Linear(in_features=in_features, out_features=out_features)
        
    def forward(self, X):
        """正向传播
        - 调用定义的参数网络
        - 让数据流过参数网络，常量数据流过不过的参数产生不同的值
        - 这个过程参数本身不会变
        - 让参数变化的是后面的优化器 
        """
        out = self.linear(X)
        
        return out


def loss_monitor(dataset, model, loss_fn, batch_size=128, retain_precision=4, device=None):
    """整个数据集的损失均值
    - 批次计算损失，再求均值，最终返回整个数据集损失的均值
    """
    if device is None:
        device = "cuda:0" if torch.cuda.is_available() else "cpu"

    # 不移动模型，使用模型当前的设备
    model_device = next(model.parameters()).device

    dataloader = DataLoader(dataset=dataset, batch_size=batch_size, shuffle=False)
    model.eval()
    with torch.no_grad():
        batch_loss = []
        for X, y in dataloader:
            X = X.to(model_device)
            y = y.to(model_device)
            y_out = model(X)
            loss = loss_fn(y_out, y)
            batch_loss.append(loss.item())
        mean_loss = np.array(batch_loss).mean()
        return mean_loss.round(retain_precision)
    
    
class ac():
    is_regression = False 
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    
    def __init__(self):
        """精度计算方法"""
        pass 
    
    @staticmethod
    def acc_cls10(y_out, y_label):
        """01二分类准确率预测
        """
        # 自然概率
        y_pred = y_out.argmax(dim=1)

        # 0表示一个也没预测正确，即模型开始时参数不具备预测能力
        print("acc:",(y_pred == y_label).float().mean().item())
        
    @staticmethod
    def acc_reg(pre=[], real=[], error_ratio=0.001):
        """连续型变量准确率计算
        - 预测pre与真实值real做差/real = error_ratio，误差比为0表示预测数据与真实值重合 
        - 定下一个threshold，大于为真-1，小于为假-0 
        - pre,real为torch.tensor类型 
        - 适合于模型输出非概率的情况，模型输出值与标签值直接比较 
        - 对于模型输出是概率的情况，该计算方式也是适用的 
        

        >>> 0.1914*0.05
            0.00957
        """
        with torch.no_grad():
            # print("基准：",threshold)
            pre = pre.flatten()
            a1 = real.flatten() 
            aa = pre - a1
            
            a2 = np.abs(aa.cpu())/(a1.cpu()+0.00001)  # 防分母为0
            acc_list =np.array([])
            for v in a2:
                if v.item() <= error_ratio:  # 误差线
                    acc_list=np.append(acc_list,1)
                else:
                    acc_list=np.append(acc_list,0)
            acc3 = acc_list.sum()/len(acc_list)
            # acc3 = "%.2f"%(acc3) # 前面乘100，后又保留两位有效数据，共四位有效数字
        return acc3 
    
    # 定义过程监控函数
    @classmethod
    def acc_reg_batch(cls, dataloader, model):
        """回归问题批次准确率计算
        """
        accs = []
        model = model.to(cls.device)
        model.eval()
        with torch.no_grad():
            for X4,y4 in dataloader:
                X4 = X4.to(cls.device)
                y4 = y4.to(cls.device)
                y_pred = model(X4)
     
                acc = cls.acc_reg(pre=y_pred,real=y4)
                accs.append(acc)
        return np.array(accs).mean()
    
    # 定义过程监控函数
    @classmethod
    def acc_cls(cls, dataloader, model, class_index=1):
        """分类问题准确率计算及单独某个类别的精确率，召回率 
        -类别划分：使用y_pred.argmax的方法，大者取其类；并没有划定具体的score 
        - class_index:计算某个索引，1-对应第2个类别，2-对应第3个类别，n-对应第n+1个类别 
        """
        accs = []
        model = model.to(cls.device)
        model.eval()
        pre1_list = []
        with torch.no_grad():
            for X4,y4 in dataloader:
                X4 = X4.to(cls.device)
                y4 = y4.to(cls.device)
                y_pred = model(X4)
             
                y_pred = y_pred.argmax(dim=1) # 这里依然使用了最大值的方式,可以考虑使用最大值+阈值的方式
                # msg = f"\n batch size:{y4[:3]},y_pred.shape:{y_pred.shape},\n{y_pred[:3]}"
                # print(msg)
        
                #标签为1且模型预测为1的概率，二分类召回率计算 
                single_class_mean = 0 
                if class_index == 1:
                    label1_mean = y_pred[y4.reshape(-1)==class_index].float().mean()
                    single_class_mean = label1_mean
                else:
                    lablen = y_pred[y4.reshape(-1)==class_index]   #对应某个真实类型
                    lablen_count = float(lablen.shape[0])   #真实个数
                    n_pre = float(lablen[lablen == class_index].shape[0])  #真实中模型预测为真实的个数
                    single_class_mean = n_pre/lablen_count
                    
                # msg = f"\n batch size:{y4.shape[0]},acc:{(y_pred == y4).float().mean()},pre1:{single_class_mean}"
                # print(msg)
                pre1_list.append(single_class_mean.cpu().item())

                acc = (y_pred == y4).float().mean().item()
                accs.append(acc)
            acc_all = np.array(accs).mean()
            pre1_class = np.array(pre1_list).mean()
            print(f"acc:{acc_all.round(4)},tpf on class index {class_index}:{pre1_class.round(4)}")
        return acc_all


    # 定义过程监控函数
    @classmethod
    def _get_acc(cls, dataloader, model):
        """回归问题或二分类问题精度计算
        """
        accs = []
        model = model.to(cls.device)
        model.eval()
        with torch.no_grad():
            for X4,y4 in dataloader:
                X4 = X4.to(cls.device)
                y4 = y4.to(cls.device)
                y_pred = model(X4)
                if cls.is_regression:
                    acc = cls.acc_reg(pre=y_pred,real=y4)
                    return acc
                else:
                    y_pred = y_pred.argmax(dim=1)
                    # msg = f"\n batch size:{y4[:3]},y_pred.shape:{y_pred.shape},\n{y_pred[:3]}"
                    # print(msg)
          
                    #标签为1且模型预测为1的概率，二分类召回率计算 
                    label1_mean = y_pred[y4.reshape(-1)==1].float().mean()
                    
                    msg = f"\n batch size:{y4.shape[0]},pre right:{(y_pred == y4).float().mean()},pre1:{label1_mean}"
                    print(msg)
  
                    acc = (y_pred == y4).float().mean().item()
                    accs.append(acc)
        return np.array(accs).mean()

    

def train(epoch,batch_size,
            train_dataset,test_dataset,
            model,loss_fn,optim,
            loss_monitor_fn = loss_monitor,
            device=None):
    
    """多轮训练 
    
    examples
    -----------------------------------------------------------
    import numpy as np 
    import torch 
    from torch import nn 
    from tpf.datasets import load_boston
    from tpf.dlt1 import DsReg
    from tpf.dlt1 import LinearRegression
    from tpf.dlt1 import train

    # 加载数据
    X_train, y_train, X_test,  y_test = load_boston()
    y_train = y_train.reshape(-1,1)
    y_test = y_test.reshape(-1,1)

    # 训练集
    train_dataset = DsReg(X=X_train, y=y_train)
    test_dataset = DsReg(X=X_test, y=y_test)

    model = LinearRegression(in_features=13, out_features=1)
    loss_fn = nn.MSELoss()
    optim = torch.optim.Adam(params=model.parameters(),lr=1e-3)

    train(epoch=2,batch_size=32,
            train_dataset=train_dataset,test_dataset=test_dataset,
            model=model,loss_fn=loss_fn,optim=optim)
    
    
    """
    if device is None:
        device = "cuda:0" if torch.cuda.is_available() else "cpu"

    # 将模型移动到指定设备
    model = model.to(device)
    model.train()

    train_dataloader = DataLoader(dataset=train_dataset, batch_size=batch_size, shuffle=True, drop_last=True)

    for i in range(1,epoch+1):
        print(f"...第{i}轮训练开始....\n")
        # 一轮训练
        count = 0
        for X,y in train_dataloader:
            # 将数据移动到指定设备
            X = X.to(device)
            y = y.to(device)

            count = count+1
            y_out = model(X)
            loss = loss_fn(y_out, y)
            
    

            # 求当前参数在当前数据处的梯度
            loss.backward()
            if count%100==1:
                print(f"epoch={i},count={count},loss_item={round(loss.item(),4)}")

            # 下降一次，就是朝着最优解的方向前进一步
            optim.step()
            optim.zero_grad()

        if test_dataset is not None:
            # 确保在评估时模型也在正确的设备上
            model.eval()
            with torch.no_grad():
                epoch_loss_train = loss_monitor_fn(dataset=train_dataset, model=model, loss_fn=loss_fn, batch_size=batch_size, device=device)
                epoch_loss_test = loss_monitor_fn(dataset=test_dataset, model=model, loss_fn=loss_fn, batch_size=batch_size, device=device)
            print(f"第{i}轮训练，模型输出与训练集loss：{epoch_loss_train},与测试集loss：{epoch_loss_test}")
            model.train()  # 确保回到训练模式
        print("-------------------------\n")
        
        

def train_cls(epoch,batch_size,
            train_dataset,test_dataset,
            model,loss_fn,optim,
            loss_monitor_fn = loss_monitor,class_index=1,device=None):
    
    """多轮训练 
    
    examples
    -----------------------------------------------------------
    import numpy as np 
    import torch 
    from torch import nn 
    from tpf.datasets import load_boston
    from tpf.dlt1 import DsReg
    from tpf.dlt1 import LinearRegression
    from tpf.dlt1 import train

    # 加载数据
    X_train, y_train, X_test,  y_test = load_boston()
    y_train = y_train.reshape(-1,1)
    y_test = y_test.reshape(-1,1)

    # 训练集
    train_dataset = DsReg(X=X_train, y=y_train)
    test_dataset = DsReg(X=X_test, y=y_test)

    model = LinearRegression(in_features=13, out_features=1)
    loss_fn = nn.MSELoss()
    optim = torch.optim.Adam(params=model.parameters(),lr=1e-3)

    train(epoch=2,batch_size=32,
            train_dataset=train_dataset,test_dataset=test_dataset,
            model=model,loss_fn=loss_fn,optim=optim)
    
    
    """
    if device is None:
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
    total_loss = 0
    model = model.to(device)
    model.train()
    train_dataloader = DataLoader(dataset=train_dataset, batch_size=batch_size, shuffle=True, drop_last=True)

    for i in range(1,epoch+1):
        print(f"...第{i}轮训练开始....\n")

        # 确保模型在正确的设备上
        model = model.to(device)
        model.train()

        # 一轮训练
        count = 0
        for X,y in train_dataloader:
            X=X.to(device)
            y=y.to(device)
            count = count+1

            
            y_out = model(X)
            loss = loss_fn(y_out, y)
            total_loss += loss.item()
            
            # 交叉䊞损失函数允许标签与模型输出维度不一致 
            # if count ==1:
            #     if y_out.shape == y.shape:
            #         pass 
            #     else:
            #         raise Exception(f"模型输出shape={y_out.shape}与标签shape={y.shape}不一致")
                

            # 求当前参数在当前数据处的梯度
            loss.backward()
            if count%100==1:
                print(f"epoch={i},count={count},loss_item={round(loss.item(),4)}")

            # 下降一次，就是朝着最优解的方向前进一步
            optim.step()
            optim.zero_grad()

        if test_dataset is not None:
            # 确保在评估时模型也在正确的设备上
            model.eval()
            with torch.no_grad():
                epoch_loss_train = loss_monitor_fn(dataset=train_dataset, model=model, loss_fn=loss_fn, batch_size=batch_size, device=device)
                epoch_loss_test = loss_monitor_fn(dataset=test_dataset, model=model, loss_fn=loss_fn, batch_size=batch_size, device=device)
            print(f"第{i}轮训练，模型输出与训练集loss：{epoch_loss_train},与测试集loss：{epoch_loss_test}")

            # 使用模型当前设备进行评估，而不是强制移动模型
            test_dataloader = DataLoader(dataset=test_dataset,batch_size=batch_size,shuffle=False)
            model_device = next(model.parameters()).device

            # 临时修改acc_cls方法以使用模型当前设备
            original_acc_cls = ac.acc_cls
            def acc_cls_fixed(dataloader, model, class_index=1):
                accs = []
                # 不移动模型，使用模型当前设备
                model.eval()
                pre1_list = []
                with torch.no_grad():
                    for X4, y4 in dataloader:
                        X4 = X4.to(model_device)
                        y4 = y4.to(model_device)
                        y_pred = model(X4)
                        # 确保y_pred是2D的（分类问题）
                        if y_pred.dim() > 1:
                            y_pred = y_pred.argmax(dim=1)
                        else:
                            y_pred = y_pred

                        y_label = y4
                        # 如果y_label也是2D，取其argmax
                        if y_label.dim() > 1:
                            y_label = y_label.argmax(dim=1)

                        y_pred_class = y_pred[y_label == class_index]

                        if len(y_pred_class) > 0:
                            pre1 = y_pred_class.float().mean()
                            pre1_list.append(pre1.item())

                        # 整体准确率
                        acc = (y_pred == y_label).float().mean().item()
                        accs.append(acc)

                overall_acc = np.array(accs).mean()
                if len(pre1_list) > 0:
                    pre1_mean = np.array(pre1_list).mean()
                else:
                    pre1_mean = 0.0
                print(f"acc:{overall_acc},tpf on class index {class_index}:{pre1_mean}")

            acc_cls_fixed(test_dataloader, model, class_index=1)
            model.train()  # 确保回到训练模式
        loss_one_epoch = total_loss / len(train_dataloader)
        
        print("-------------------------\n")
        
        

class Train1:
        
    def train_once(self, model, loss_fn, optimizer,
                   train_dataset, batch_size, device=None, acc_cls_func=ac.acc_cls10):
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
        if device is None:
            device = "cuda:0" if torch.cuda.is_available() else "cpu"

        # 转到GPU
        model.to(device=device)
        
        total_loss = 0
        
        train_dataloader = DataLoader(dataset=train_dataset, batch_size=batch_size, shuffle=True, drop_last=True)

        icount = 0
        model.train()
        for X,y in train_dataloader:
            icount+=1
            # print(X.shape,y.shape)  # torch.Size([32, 3, 224, 224]) torch.Size([32])
            X=X.to(device=device)
            y=y.to(device=device)

            # 正向传播
            y_out = model(X=X)

            # 损失计算
            loss = loss_fn(y_out, y)
            total_loss += loss.item()

            # 梯度计算
            optimizer.zero_grad()
            loss.backward()

            # 参数优化
            optimizer.step()

            #精度计算
            if icount%10==1:
                acc_cls_func(y_out=y_out,y_label=y)
             
        loss_one_epoch = total_loss / len(train_dataloader)
        return loss_one_epoch
    
        
    def train(self, epoch,batch_size,
                train_dataset,test_dataset,
                model,loss_fn=None,optim=None,
                loss_monitor_fn = loss_monitor,class_index=1,device=None):
        
        """多轮训练 
        
        examples
        -----------------------------------------------------------
        import numpy as np 
        import torch 
        from torch import nn 
        from tpf.datasets import load_boston
        from tpf.dlt1 import DsReg
        from tpf.dlt1 import LinearRegression
        from tpf.dlt1 import train

        # 加载数据
        X_train, y_train, X_test,  y_test = load_boston()
        y_train = y_train.reshape(-1,1)
        y_test = y_test.reshape(-1,1)

        # 训练集
        train_dataset = DsReg(X=X_train, y=y_train)
        test_dataset = DsReg(X=X_test, y=y_test)

        model = LinearRegression(in_features=13, out_features=1)
        loss_fn = nn.MSELoss()
        optim = torch.optim.Adam(params=model.parameters(),lr=1e-3)

        train(epoch=2,batch_size=32,
                train_dataset=train_dataset,test_dataset=test_dataset,
                model=model,loss_fn=loss_fn,optim=optim)
        
        
        """
        if device is None:
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
        total_loss = 0
        model = model.to(device)
        model.train()
        
        # 损失函数
        if loss_fn is None:
            loss_fn = nn.CrossEntropyLoss()

        # 优化
        if optim is None:
            optim = torch.optim.SGD(params=model.parameters(), lr=1e-3)
            
        for i in range(1,epoch+1):
            print(f"...第{i}轮训练开始....\n")
            
            # 一轮训练
            count = 0 
            
            
            loss_one_epoch = self.train_once(model, loss_fn, optim,
                   train_dataset, batch_size, device=device)
                
            
            if test_dataset is not None:
                epoch_loss_train = loss_monitor_fn(dataset=train_dataset, model=model, loss_fn=loss_fn)
                epoch_loss_test = loss_monitor_fn(dataset=test_dataset, model=model, loss_fn=loss_fn)
                print(f"第{i}轮训练，模型输出与训练集loss：{epoch_loss_train},与测试集loss：{epoch_loss_test}")
                
                test_dataloader = DataLoader(dataset=test_dataset,batch_size=batch_size,shuffle=False)
                ac.acc_cls(test_dataloader,model,class_index=1)
            
            print("-------------------------\n")
            
            
        

