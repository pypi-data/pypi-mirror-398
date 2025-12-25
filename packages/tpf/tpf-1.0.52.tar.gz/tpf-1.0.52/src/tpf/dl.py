
"""
DL 通用功能 
"""
import os 

from tpf.box.fil import log as log2 
from tpf import pkl_load,pkl_save
from tpf.d2 import mean_by_count
import matplotlib.pyplot as plt 
from PIL import Image

# PyTorch 三组件
import torch
from torch import nn
from torch.nn import functional as F

# 数据打包工具
from torch.utils.data import Dataset
from torch.utils.data import DataLoader

# 图像处理工具
from matplotlib import pyplot as plt

# import cv2
from torchvision import transforms

# 通用科学计算器
import numpy as np

# 解决 OMP问题
import os,time 
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"


BASE_DIR=os.path.dirname(os.path.abspath(__file__))
log_file = "main.log"
log_file = os.path.join(BASE_DIR,log_file)


def log(msg, fil="./main.log", max_file_size=10*1024*1024):
    """最大日志，超10M重写日志文件 
    """
    if fil:
        log_file = fil
    else:
        log_file = "/tmp/train.log"
    
    if os.path.exists(log_file):
        fil_size = os.path.getsize(log_file)
        if fil_size > max_file_size:
            # 写入空文件
            with open(log_file,"w",encoding="utf-8") as f:
                tim = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
                f.write("[{}] {} \n".format(tim,msg))
        else:
            with open(log_file,"a+",encoding="utf-8") as f:
                tim = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
                f.write("[{}] {} \n".format(tim,msg))
    else:
        with open(log_file,"w",encoding="utf-8") as f:
            tim = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
            f.write("[{}] {} \n".format(tim,msg))


def loop_deal(data):
    """自定义逻辑实现简单循环批次处理
    """
    ll = len(data)
    per_once = 100
    if ll%per_once == 0:
        pre_epoch = ll//per_once
    else:
        pre_epoch = ll//per_once + 1
        
    start_index = 0 
    for i in range(pre_epoch):
        data1= data[start_index:(start_index+per_once)]
        y_pred_1 = 1+1
        if i == 0:
            y_pred = y_pred_1
        else:
            # y_pred = torch.cat((y_pred,y_pred_1),dim=0)
            pass 
        start_index = start_index+per_once
    return y_pred

class MyDataSet(Dataset):
    
    def __init__(self,X,y):
        """
        构建数据集
        """
        self.X = X
        self.y = y.reshape(-1,1)
        print(f"seq_len={len(X[0])}")
    
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        x = self.X[idx]
        y = self.y[idx]

        return torch.tensor(data=x).float(), torch.tensor(data=y).float()


import pandas as pd 


class DataSet11(Dataset):
    """等比数据集
    """
    def __init__(self,X, y, nums_per_label = 1280, n_class=2):
        """二分类问题等比数据集，有放回随机抽样
        - 针对样本不均衡数据集
        - nums_per_label:每个样本类别一次采样的行数，可放回抽样
        - n_class:类别个数
        - 标签y为整数 
        

        examples
        ------------------------------------
        #每次要重新生成一份DataSet11
        train_dataset = DataSet11(X=X_train, y=y_train)
        train_dataloader = DataLoader(dataset=train_dataset, shuffle=True, batch_size=128)

        test_dataset = DataSet11(X=X_test, y=y_test)
        test_dataloader = DataLoader(dataset=test_dataset, shuffle=False, batch_size=256)
        test_dataset[0]

        """
        label_name="label_tmp_175"  #中间名称，叫什么没关系，有个名字能访问对应的列即可
        df = self.get_data(X, y, nums_per_label = nums_per_label, n_class=n_class, lable_name=label_name)
        self.X = np.array(df.drop([label_name],axis=1))
        self.y = np.array(df[label_name]).reshape(-1)
        # self.y = y.reshape(-1,1)
        
    def get_data(self, X_train, y_train, nums_per_label = 1280, n_class=2, lable_name="label"):
        """随机抽取指定行数的数据
        - 按标签等比抽取后合并，形成1:1等比数据集
        - n_class:类别个数，2表示2分类问题,索引编码,0,1,...
        """
        pd_all = pd.DataFrame()
        
        for i in range(n_class):
            X_train_0=X_train[y_train==i]
            pd0 = pd.DataFrame(X_train_0)
            pd0=pd0.sample(n=nums_per_label,replace=True)
            pd0[lable_name] = i
            if i ==0:
                pd_all = pd0
            else:
                pd_all = pd.concat([pd_all,pd0],axis=0)
        return pd_all
    
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        x = self.X[idx]
        y = self.y[idx]

        return torch.tensor(data=x).float(), torch.tensor(data=y).long()



class LinearModel(nn.Module):
    def __init__(self, in_features=100, out_features=1):
        """线性模型定义，初始化网络参数"""
        super().__init__()
        self.linear = nn.Linear(in_features=in_features, out_features=out_features)

    def forward(self, X):
        """让数据流过参数网络"""
        x = self.linear(X) 
        return x



class DMEval():

    is_regression = False
    loss_count = 0
    loss_list = np.array([])

    #当前训练过的批次数，深度学习按批次训练，完成一个批次加1
    batch_count = 0 

    #当前已训练轮次，一个轮次遍历一次全体数据集
    epoch = 0

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    
    img_save_path = "ml_acc.jpg"
    acc_test_file  ="ml_acc_test.txt"
    acc_train_file ="ml_acc_train.txt"
    loss_item_file="ml_loss_item.txt"
    good_model_path="ml_good_model_acc.txt"
    good_num=0
    optim_save_path="ml_optim_params.pkl"
    epoch_num_path="ml_epoch_num.txt"
    log_input_pred="train_pre.log"
    log_input_eval="ml_input_eval.log"
    log_dataset = "train_data.log"
    
    
    def __init__(self):
        pass

    @classmethod
    def msg_record(cls, val, file_path="acc_test.txt",replace=False):
        """日志记录，记录每个批次的信息于文件中，一行一个记录
        """
        if isinstance(val, (int, float)):  # 检查val是否是整数或浮点数
            rounded_val = round(val, ndigits=3)
        elif isinstance(val, str):  # 如果val是字符串，尝试转换为浮点数
            try:
                rounded_val = round(float(val), ndigits=3)
            except ValueError:
                # 如果转换失败，可以记录错误或采取其他措施
                print(f"Warning: Cannot convert {val} to float for rounding.")
                return
        else:
            # 如果val是其他类型，可以记录错误或采取其他措施
            print(f"Warning: Unsupported type {type(val)} for rounding.")
            return

        if os.path.exists(file_path):
            with open(file_path, "a+", encoding="utf-8") as f:
                f.write(f"{rounded_val}\n")
        else:
            # print("cls.batch_count:",cls.batch_count,file_path)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"{rounded_val}\n")
                
    

    @staticmethod
    def acc_lianxu(pre=[],real=[],acc=0.999):
        """连续浮点型标签，精度计算
        - 定下一个区间，在区间内为真

        >>> 0.1914*(1-0.95)
            0.00957
        """
        # print("基准：",acc)
        pre = pre.flatten()
        a1 = real.flatten() 
        aa = pre - a1
        
        a2 = np.abs(aa.cpu())/(a1.cpu()+0.00001)  # 防分母为0
        acc_list =np.array([])
        for v in a2:
            if v.item() <= (1-acc):  # 误差线
                acc_list=np.append(acc_list,1)
            else:
                acc_list=np.append(acc_list,0)
        acc3 = acc_list.sum()*100/len(acc_list)
        acc3 = "%.2f"%(acc3) # 前面乘100，后又保留两位有效数据，共四位有效数字
        return acc3 

    @staticmethod
    def deviation_lianxu(pre=[],real=[]):
        """连续浮点型标签，偏差计算：|real - pred|/|real|

        >>> 0.1914*(1-0.95)
            0.00957
        """

        a1 = real.flatten() 

        index = 0 
        acc_list =np.array([])
        for v in a1:
            aa = np.abs(v-pre[index])
            if np.allclose(v,0):  # 如果真实为0,allclose可计算浮点数是否为0
                acc_list=np.append(acc_list,aa)
            else:
                a2 = aa/v 
                acc_list=np.append(acc_list,a2)
            index += 1 
        acc3 = acc_list.sum()*100/len(acc_list)
        acc3 = "%.6f"%(acc3) # 前面乘100，后又保留两位有效数据，共四位有效数字
        return acc3 


    @classmethod
    def val_list(cls, file_path):
        vals = []
        with open(file_path) as f:
            line = f.readline() 
            while line:
                line = line.strip()
                if len(line)>0:
                    vals.append(float(line))
                line = f.readline()
        return vals

    @classmethod
    def acc_test_list(cls):
        return cls.val_list(cls.acc_test_file)

    @classmethod
    def acc_train_list(cls):
        return cls.val_list(cls.acc_train_file)

    @classmethod
    def loss_item_list(cls):
        return cls.val_list(cls.loss_item_file)


    @classmethod
    def loss_item_compute(cls, loss,ncount=100):
        """循环计算最近100个批次损失值
        - ncount:取最近ncount次损失的平均值 
        """

        # 当前批次损失
        cls._loss_item = loss 

        cls.loss_count += 1

        if cls.loss_count <= ncount:
            cls.loss_list = np.append(cls.loss_list, loss)
        else:
            i = cls.loss_count%100
            cls.loss_list[i] = loss

        cls.msg_record(val=loss,file_path=cls.loss_item_file)

    

    @classmethod
    def show_img_test(cls):
        vals = cls.acc_test_list()
        plt.plot(vals,color='r',linewidth=0.8)
    
    @classmethod
    def show_img_train(cls):
        vals = cls.acc_train_list()
        plt.plot(vals,color='g',linewidth=0.8)

    @classmethod
    def show_img(cls, using_old=False, mean_num=1):

        if os.path.exists(cls.img_save_path) and using_old:
            
            img = Image.open(cls.img_save_path)
            return img
        else:
            axis_y1 = cls.acc_train_list()
            axis_y2 = cls.acc_test_list()

            axis_y1 = mean_by_count(axis_y1,mean_num=mean_num)
            axis_y2 = mean_by_count(axis_y2,mean_num=mean_num)


            axis_x = [i for i in range(len(axis_y2))]

            # 显示设置
            plt.rcParams['axes.unicode_minus'] = False   # 负号显示
            plt.rcParams['font.style'] = 'normal'  # 正体normal， 斜体italic
            plt.rcParams['font.size'] = 14  # 字号

            fig, ax = plt.subplots(figsize=(8, 6))
            ax.plot(axis_x, axis_y1, label="train", color='g',linewidth=0.8)
            ax.plot(axis_x, axis_y2, label="test", color='r',linewidth=0.8,alpha=0.6)

            ax.set_xlabel("epoch")  # x轴标签
            ax.set_ylabel("p")  # y轴标签
            ax.set_title("acc")     # 标题
            plt.grid(visible=True, linestyle="--", alpha=0.5)  # 显示栅格
            plt.legend()  # 显示图例
            plt.savefig(cls.img_save_path, bbox_inches='tight', pad_inches=0.2)  # 保存
            plt.show()
            plt.close()
            

    @classmethod
    def show_img_loss(cls,mean_num=1, s=4,  marker='o',alpha=0.9,linewidths=0.3):
        vals = cls.loss_item_list()
        vals = mean_by_count(vals,mean_num=mean_num)

        axis_x = np.array([i for i in range(len(vals))])
        axis_y = np.array(vals)
        #根据x,y生成一个数列，将对应的数据点映射到coclarmap中的颜色上
        C = np.arctan(axis_x/axis_y)

        #c=C,edgecolors='w'
        plt.scatter(axis_x, axis_y, s=s,  marker=marker,alpha=alpha,linewidths=linewidths)

    @classmethod
    def loss_item(cls):
        """当前批次损失"""
        return cls._loss_item

    @classmethod
    def loss_avg100(cls):
        """最近100次损失的平均值"""
        item = round(cls.loss_list.mean(), ndigits=4)
        return item

    @classmethod
    def diff_time(cls, t=None, return_min=False):
        """代码运行时间差判断
        """
        import time 
        b = time.time()
        if not t:
            return b
        
        if return_min:
            c = round((b-t)/60)
            print(f"time pass {c} min")
        else:
            c = round(b-t)
            print(f"time pass {c} sec")

        return b

    @classmethod
    def get_good_model_acc(cls):
        if os.path.exists(cls.good_model_path):
            return cls.read(cls.good_model_path)
        else:
            return 0
            

    @classmethod
    def set_good_model_acc(cls,acc):
        cls.write(acc, file_path=cls.good_model_path)


    @classmethod
    def get_epoch_num(cls):
        if os.path.exists(cls.epoch_num_path):
            return cls.read(cls.epoch_num_path)
        else:
            return 0
            
    @classmethod
    def set_epoch_num(cls):
        epoch_num = cls.get_epoch_num()+1
        cls.write(epoch_num, file_path=cls.epoch_num_path)

    @classmethod
    def write(cls,obj,file_path):
        """
        直接将对象转字符串写入文件,这样可以在文件打开时,看到原内容,还可以进行搜索
        """
        ss = str(obj)
        with open(file_path,"w",encoding="utf-8") as f:
            f.write(ss)

    @classmethod
    def read(cls,file_path):
        with open(file_path,'r',encoding="utf-8") as f:
            c = eval(f.read())
            return c 
        

class T(DMEval):
    """训练器
    """
 
    def __init__(self, os_type="linux") -> None:
        """训练模板类

        examples
        --------------------------------------------
        T.train(
            continuation=True,
            model=lenet,loss_fn=loss_fn,optimizer=optimizer,
            epochs=30,
            train_dataset=train_dataset,test_dataset=test_dataset,train_dataloader=train_dataloader)
        """
        # if os_type == "linux":
        # 设备
        # self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
    
        pass 

    # 定义过程监控函数
    @classmethod
    def _get_acc(cls, dataloader, model):
        """精度计算
        """
        accs = []
        model = model.to(cls.device)
        model.eval()
        with torch.no_grad():
            for X4,y4 in dataloader:
                X4 = X4.to(cls.device)
                y4 = y4.to(cls.device)
                y_pred = model(X4)
                log(msg=f"\n eval input x0:\n{X4},\ny0:\n{y4[0]},\nmodel pre:\n{y_pred[0]}",fil=cls.log_input_eval)
                if cls.is_regression:
                    acc = cls.acc_lianxu(pre=y_pred,real=y4)
                    return acc
                else:#如果是多分类，可以指定某个类别上的阈值，超过该阈值即为该类别
                    y_pred = y_pred.argmax(dim=1)
                    # msg = f"\n batch size:{y4[:3]},y_pred.shape:{y_pred.shape},\n{y_pred[:3]}"
                    # print(msg)
          
                    label1_mean = y_pred[y4.reshape(-1)==1].float().mean()
                    
                    msg = f"\n batch size:{y4.shape[0]},pre right:{(y_pred == y4).float().mean()},pre1:{label1_mean}"
                    # print(msg)
                    log(msg=msg, fil=cls.log_input_pred)

                    acc = (y_pred == y4).float().mean().item()
                    accs.append(acc)
        return np.array(accs).mean()


    @classmethod
    def show_acc(cls, model, train_dataset, test_dataset=None, batch_size=128):
        """过程监控,监控模型在训练集或测试集上的表现
        """
        train_dataloader = DataLoader(dataset=train_dataset, shuffle=False, batch_size=batch_size)
        if test_dataset:
            test_dataloader = DataLoader(dataset=test_dataset, shuffle=False, batch_size=batch_size)
            acc_train = cls._get_acc(model=model, dataloader=train_dataloader)
            acc_test = cls._get_acc(model=model, dataloader=test_dataloader)
            msg = f"train_acc: {acc_train}, test_acc: {acc_test}, loss:{cls.loss_avg100()}"
            if cls.epoch%cls.per_epoch==1:
                print(msg)
                log(msg=msg,fil=cls.log_file)
            cls.msg_record(val=acc_train,file_path=cls.acc_train_file)
            cls.msg_record(val=acc_test,file_path=cls.acc_test_file)
            return acc_train,acc_test
        else:
            acc_train = cls._get_acc(model=model, dataloader=train_dataloader)
            msg = f"train_acc: {acc_train}, loss:{cls.loss_avg100()}"
            if cls.epoch%cls.per_epoch==1:
                print(msg)
                log(msg=msg,fil=cls.log_file)
            cls.msg_record(val=acc_train,file_path=cls.acc_train_file)
            return acc_train,None
    
    @classmethod
    def predict_proba(cls, dataloader, model):
        """概率输出
        """
        model = model.to(cls.device)
        model.eval()
        i_count = 0 
        with torch.no_grad():
            for X4,y4 in dataloader:
                X4 = X4.to(cls.device)
                y4 = y4.to(cls.device)
                y_pred = model(X4)
                y_pred = F.softmax(y_pred,dim=1)
                if i_count == 0:
                    y_pred_all = y_pred
                else:
                    y_pred_all = torch.cat([y_pred_all,y_pred],dim=0)
                i_count = i_count+1
        return np.array(y_pred_all.cpu()) 

    @classmethod
    def train_one_epoch(cls,
            model,
            loss_fn, 
            optimizer, 
            train_dataloader=None):
        """
        T.train_one_epoch(model=model,
            loss_fn=loss_fn, 
            optimizer=optim, 
            train_dataloader=train_dataloader)
        """

        count = 0 
        # print(cls.device)

        model = model.to(device=cls.device)
        model.train()

        for X3,y3 in train_dataloader:
            X3=X3.to(device=cls.device)
            y3=y3.to(device=cls.device)
            # print(cls.device,X3.device,y3.device,model)

            count += 1
            cls.batch_count += 1
            
            # 前一段时间看看小的批次，后面开始训练后，就不看了
            if count %10 ==0 and cls.batch_count < 1000: 
                print(f"batch {count} start...")

            # 正向传播
            y_pred = model(X3)

            # 清空梯度
            optimizer.zero_grad()

            # 计算损失
            loss = loss_fn(y_pred, y3)

            # 梯度下降
            loss.backward()

            # 优化一步
            optimizer.step()

            with torch.no_grad():
                DMEval.loss_item_compute(loss.item())

                # 输出
                log(msg=f"\ntrain input x0:\n{X3},\ny0:\n{y3[0]},\nmodel pre:\n{y_pred[0]}",fil=cls.log_input_pred)
                
                if loss < 0.01 and cls.loss_count%100==99:
                    log(msg=f"y_pred[:3]:{y_pred[:3]}",fil=cls.log_file)
                    log(msg=f"y_real[:3]:{y3[:3]}",fil=cls.log_file)

                # 前一段时间看看小的批次，后面开始训练后，就不看了
                if count %30 ==0 : 
                    # if cls.continuation:
                    #     torch.save(model.state_dict(), cls.param_path)
                    msg = f"batch {count}, loss:{loss.item()}"
                    print(msg)
                    log(msg=msg, fil=cls.log_file)
                
            
        return loss


    @classmethod
    def load_model(cls,model, model_param_path="model_params_12.pkl"):
        """加载模型参数
        """
        model.load_state_dict(torch.load(model_param_path, map_location=cls.device, weights_only=True))
        return model 

    # 定义训练过程
    @classmethod
    def train(cls,
            model, 
            loss_fn=None,
            optimizer="adam", 
            train_dataset_func=None, test_dataset_func=None,
            train_dataset=None, test_dataset=None,
            train_dataloader=None,
            epochs=1, 
            batch_size=128,
            learning_rate=1e-3,
            model_param_path="ml_model1_params.h5",
            auto_save=True,
            continuation=True,  #是否在之前训练的基础上进行训练
            is_regression=False,
            log_file="/tmp/train.log",
            per_epoch=10):
        """梯度下降训练

        params
        --------------------------
        - optimizer:"adam","sgd", 
        - train_dataset_func:每个轮次会重新调用该方法，这意味着如何数据集每次是随机生成的，该方法可以体现这种随机
        - train_dataloader: 指定此值，全局使用这一个loader，否则每次开始，重新生成一个loader
        - auto_save:是否自动保存模型参数，
        - continuation:是否持续训练，是否在之前训练的基础上进行训练
        - model_param_path:模型参数保存路径
        - is_regression: True-回归问题，False-分类问题


        examples
        ----------------------------------------------

        from tpf.dl import T
        T.train(model, 
                epochs=50000, 
                batch_size=512,
                learning_rate=1e-3,
                model_param_path="model_params_12.pkl",        
                train_dataset_func=train_data_set, 
                test_dataset_func=test_data_set,
                log_file="/tmp/train.log",
                per_epoch=10)


        T.train(model=model, 
            loss_fn=loss_fn,
            optimizer="adam", 
            train_dataset=train_dataset, test_dataset=test_dataset,
            epochs=3, 
            batch_size=128,
            learning_rate=1e-3,
            model_param_path="ml_model1_params.h5",
            auto_save=True,
            continuation=True,  #是否在之前训练的基础上进行训练
            is_regression=True,
            log_file="/tmp/train.log")

        """
        param_path= model_param_path
        cls.param_path = param_path
        cls.is_regression= is_regression
        cls.log_file = log_file
        cls.continuation = continuation
        if loss_fn is None:
            loss_fn = nn.CrossEntropyLoss()

        # 加载上次训练的参数
        if continuation:
            if os.path.exists(param_path):
                print(f"load param:{param_path}")
                model.load_state_dict(torch.load(param_path, map_location=cls.device, weights_only=True))

                if os.path.exists(cls.optim_save_path):
                    optimizer = pkl_load(file_path=cls.optim_save_path, use_joblib=False)
                
            else:
                print("重新开始训练...")
                
        # 定义优化器,重新加载的优化器数据类型不会为str
        if isinstance(optimizer,str):
            if optimizer.lower() == "sgd":
                optimizer = torch.optim.SGD(params=model.parameters(), lr=learning_rate)
            elif optimizer.lower() == "adam":
                optimizer = torch.optim.Adam(params=model.parameters(), lr=learning_rate)

        

        t_start = cls.diff_time()
        t = t_start
        cls.per_epoch = per_epoch
        for epoch in range(1, epochs+1):
            cls.epoch = epoch
            if train_dataset_func:
                train_dataset = train_dataset_func()
                # print("load train data set ok")

            if test_dataset_func:
                test_dataset = test_dataset_func()
                # print("load test data set ok")

            msg = f"\ntrain_dataset[0]:\n {train_dataset[0]},\ntest_dataset[0]:{test_dataset[0]}\n"
            log(msg, fil=cls.log_dataset)
            
            if train_dataloader is None:
                # 在每轮训练开始时，重新启用一个loader，理论上这种才合理，实际上，这种方法精度比loader全局定义的方法，每一轮精度低一些
                train_dataloader = DataLoader(dataset=train_dataset, shuffle=True, batch_size=batch_size)
            
            all_batch_size = len(train_dataloader)
            
            msg = f"\n正在进行第 epoch= {epoch} 轮训练...每轮次批次个数 ={all_batch_size},batch_size={batch_size}"

            T.train_one_epoch(model=model, loss_fn=loss_fn,optimizer=optimizer,train_dataloader=train_dataloader)

            log(msg, fil=log_file)
            if epoch%per_epoch==1:
                print(msg)
            acc_train,acc_test = T.show_acc(model=model, train_dataset=train_dataset, test_dataset=test_dataset)
            # print(f"train_acc: {show_acc(dataloader=train_dataloader)}, test_acc: {show_acc(dataloader=test_dataloader)}")

            
            # 保存模型（参数）
            # 保留最好的三个模型以及当前的模型
            if continuation or auto_save:
                torch.save(model.state_dict(), cls.param_path)
                pkl_save(optimizer, file_path=cls.optim_save_path, use_joblib=False)
                # print(f"save param:{param_path}")
                if acc_test:
                    good_acc = cls.get_good_model_acc()
                    if epoch%per_epoch==1:
                        print(f"acc_test={acc_test},good_acc={good_acc}")
                    if float(acc_test) > float(good_acc) or cls.epoch == 1:
                        good_params_path = "ml_{}_{}.good".format(cls.param_path, cls.good_num%3)
                        torch.save(model.state_dict(), good_params_path)
                        cls.good_params_path = good_params_path
                        cls.set_good_model_acc(acc_test)

            if epoch%per_epoch==1:
                t = cls.diff_time(t)

"""
T.train(
    continuation=True,
    model=lenet,loss_fn=loss_fn,optimizer=optimizer,
    epochs=30,
    train_dataset=train_dataset,test_dataset=test_dataset,train_dataloader=train_dataloader)


T.train(model=model, 
            loss_fn=loss_fn,
            optimizer="adam", 
            train_dataset=train_dataset, test_dataset=test_dataset,
            epochs=3, 
            batch_size=128,
            learning_rate=1e-3,
            model_param_path="ml_model1_params.h5",
            auto_save=True,
            continuation=True,  #是否在之前训练的基础上进行训练
            is_regression=True,
            log_file="/tmp/train.log")

"""

"""
基础训练类
"""
class TBase():
    
    
    @staticmethod
    def log(msg, fil="./train.log", max_file_size=10*1024*1024):
        """最大日志，超10M重写日志文件 
        """
        if fil:
            log_file = fil
        else:
            log_file = "/tmp/train.log"
        
        if os.path.exists(log_file):
            fil_size = os.path.getsize(log_file)
            if fil_size > max_file_size:
                # 写入空文件
                with open(log_file,"w",encoding="utf-8") as f:
                    tim = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
                    f.write("[{}] {} \n".format(tim,msg))
            else:
                with open(log_file,"a+",encoding="utf-8") as f:
                    tim = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
                    f.write("[{}] {} \n".format(tim,msg))
        else:
            with open(log_file,"w",encoding="utf-8") as f:
                tim = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
                f.write("[{}] {} \n".format(tim,msg))


class T11(TBase):
    batch_count = 0
    device = "cuda:0" if torch.cuda.is_available() else "cpu"

    def __init__(self):
        """交易数据训练器
        - 正负样本极不均衡
        """
        pass

    @staticmethod
    def train_data_set():
        return DataSet11(X=T11.X_train, y=T11.y_train, nums_per_label = T11.nums_per_label, n_class=2)
    
    @staticmethod
    def test_data_set():
        return DataSet11(X=T11.X_test, y=T11.y_test, nums_per_label = T11.nums_per_label, n_class=2)

    @staticmethod
    def train_one_epoch(model,
            loss_fn, 
            optimizer, 
            train_dataloader=None):
        """单轮训练 
        T11.train_one_epoch(model=model,
            loss_fn=loss_fn, 
            optimizer=optim, 
            train_dataloader=train_dataloader)
        """

        count = 0 
        model = model.to(device=T11.device)
        model.train()

        for X3,y3 in train_dataloader:
            X3=X3.to(device=T11.device)
            y3=y3.to(device=T11.device)
            # print(cls.device,X3.device,y3.device,model)

            count += 1
            T11.batch_count += 1
            
            # 前一段时间看看小的批次，后面开始训练后，就不看了
            if count %10 ==0 and T11.batch_count < 1000: 
                print(f"batch {count} start...")

            # 正向传播
            y_pred = model(X3)

            # 清空梯度
            optimizer.zero_grad()

            # 计算损失
            loss = loss_fn(y_pred, y3)

            # 梯度下降
            loss.backward()

            # 优化一步
            optimizer.step()
            
        return loss.item()


    @staticmethod
    def train(model, X_train,  y_train, X_test=None, y_test=None,
            epochs=50000, 
            batch_size=512,
            learning_rate=1e-3,
            model_param_path="model_params_12.pkl.dict",        
            log_file="/tmp/train.log",
            per_epoch=20,
            nums_per_label=4096):
        """训练 
        
        params
        -----------------------------------
        - model_param_path:参数保存路径，建议以.dict结尾，表示存储的为参数字典

        return 
        ---------------------------------------
        train_accs,test_accs


        example
        -----------------------------------------
        from tpf.mlib.seq import SeqOne

        model = SeqOne(seq_len=X_test.shape[1], out_features=2)

        T11.train(model, X_train,  y_train, X_test, y_test,)

        
        return 
        ---------------------------------------
        train_accs,test_accs
        - train_accs:训练集上的精度 
        - test_accs：测试集上的精度，如果输入测试集的话

        """
        T11.X_train        = X_train 
        T11.y_train        = y_train
        T11.X_test         = X_test
        T11.y_test         = y_test
        T11.nums_per_label = nums_per_label
        
        device = T11.device
        if model_param_path.endswith(".dict"):
            model_param_path = model_param_path.removesuffix(".dict")
        good_params_path = "{}.dict".format(model_param_path)
        good_acc_path = "{}.acc".format(model_param_path)
        loss_fn = nn.CrossEntropyLoss()

        if os.path.exists(model_param_path):
            print(f"load param:{model_param_path}")
            model.load_state_dict(torch.load(model_param_path, map_location=device, weights_only=True))
        optimizer = torch.optim.SGD(params=model.parameters(), lr=learning_rate)

        train_accs = []
        test_accs  = []
        for epoch in range(1, epochs+1):
            train_dataset = T11.train_data_set()
            train_dataloader = DataLoader(dataset=train_dataset, shuffle=True, batch_size=batch_size)

            all_batch_size = len(train_dataloader)
            
            if epoch%per_epoch == 1:
                msg = f"\n正在进行第 epoch= {epoch} 轮训练...每轮次批次个数 ={all_batch_size},batch_size={batch_size}"
                T11.log(msg,fil=log_file)

            loss_item = T11.train_one_epoch(model=model, loss_fn=loss_fn,optimizer=optimizer,train_dataloader=train_dataloader)

            if X_test is not None:
                test_dataset = T11.test_data_set()
                test_dataloader = DataLoader(dataset=test_dataset, shuffle=False, batch_size=batch_size)
                test_acc = T11.get_acc(dataloader=test_dataloader,model=model)
                test_accs.append(test_acc)
                good_acc = T11.get_good_model_acc(good_acc_path)
                if float(test_acc) > float(good_acc):
                        torch.save(model.state_dict(), good_params_path)
                        T11.set_good_model_acc(test_acc,good_model_path=good_acc_path)

            train_acc = T11.get_acc(dataloader=train_dataloader,model=model)
            train_accs.append(train_acc)

            if epoch%per_epoch == 1:
                if X_test is not None:
                    msg = f"train_acc: {train_acc}, test_acc: {test_acc}, good_acc:{good_acc},loss_item:{loss_item}"
                else:
                    msg = f"train_acc: {train_acc}, test_acc: {test_acc},loss_item:{loss_item}"
                T11.log(msg,fil=log_file)
                torch.save(model.state_dict(), model_param_path)
        return train_accs,test_accs
        
    @staticmethod
    def read(file_path):
        with open(file_path,'r',encoding="utf-8") as f:
            c = eval(f.read())
            return c 
        
    @staticmethod
    def write(obj,file_path):
        """
        直接将对象转字符串写入文件,这样可以在文件打开时,看到原内容,还可以进行搜索
        """
        ss = str(obj)
        with open(file_path,"w",encoding="utf-8") as f:
            f.write(ss)
        
    @staticmethod
    def get_good_model_acc(good_model_path):
        if os.path.exists(good_model_path):
            return T11.read(good_model_path)
        else:
            return 0
        
    @staticmethod
    def set_good_model_acc(obj,good_model_path):
        T11.write(obj,file_path=good_model_path)
        
    # 定义过程监控函数
    @staticmethod
    def get_acc(dataloader, model=None):
        device = T11.device
        
        accs = []
        model.to(device=device)
        model.eval()
        with torch.no_grad():
            for X,y in dataloader:
                X=X.to(device=device)
                y=y.to(device=device)
                y_pred = model(X)
                y_pred = y_pred.argmax(dim=1)
                acc = (y_pred == y).float().mean().item()
                accs.append(acc)
        return np.array(accs).mean()
        

class Activate(object):
    
    def __init__(self):
        pass 

    @staticmethod
    def relu(X):
        X = np.array(X)
        shape = X.shape
        X = X.reshape(-1)
        x = np.array([0 if x < 0 else x for x in X])
        x = x.reshape(shape)
        return x
    
    @staticmethod
    def relu2(X):
        X = torch.tensor(data=X,dtype=torch.float32)
        return X.relu()
    
    @staticmethod
    def relu3(X):
        X = torch.tensor(data=X,dtype=torch.float32)
        return F.relu(input=X,inplace=True)
    
    @staticmethod
    def rule_test():
        
        np.random.seed(73)
        A=np.random.randn(7,3)
        # print(A)
        """
        [[ 0.57681305  2.1311088   2.44021967]
        [ 0.26332687 -1.49612065 -0.03673531]
        [ 0.43069579 -1.52947433 -0.73025968]
        [ 1.05131524  1.61979267 -1.60501337]
        [ 0.33100953 -0.21095236  0.2981767 ]
        [-1.14607352  0.57536202 -0.36390663]
        [ 0.03639919 -0.52056399 -0.01576433]]
        """

        # B = Activate.relu(X=A)
        # print(B)
        """
        [[0.57681305 2.1311088  2.44021967]
        [0.26332687 0.         0.        ]
        [0.43069579 0.         0.        ]
        [1.05131524 1.61979267 0.        ]
        [0.33100953 0.         0.2981767 ]
        [0.         0.57536202 0.        ]
        [0.03639919 0.         0.        ]]
        """

        # B = Activate.relu2(X=A)
        # print(B)
        """可以看出torch.relu()只保留了四位有效数字
        tensor([[0.5768, 2.1311, 2.4402],
                [0.2633, 0.0000, 0.0000],
                [0.4307, 0.0000, 0.0000],
                [1.0513, 1.6198, 0.0000],
                [0.3310, 0.0000, 0.2982],
                [0.0000, 0.5754, 0.0000],
                [0.0364, 0.0000, 0.0000]], dtype=torch.float64)
        """

        B = Activate.relu3(X=A)
        print(B)
        """F.relu同样改变了数据的精度
        tensor([[0.5768, 2.1311, 2.4402],
                [0.2633, 0.0000, 0.0000],
                [0.4307, 0.0000, 0.0000],
                [1.0513, 1.6198, 0.0000],
                [0.3310, 0.0000, 0.2982],
                [0.0000, 0.5754, 0.0000],
                [0.0364, 0.0000, 0.0000]], dtype=torch.float64)
        """














