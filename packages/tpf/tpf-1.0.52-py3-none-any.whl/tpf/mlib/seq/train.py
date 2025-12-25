
import os 
import time 
import numpy as np 
import pandas as pd 
from tpf.box.fil import log as log2 
from tpf import pkl_load,pkl_save
from tpf.d2 import mean_by_count
import matplotlib.pyplot as plt 
from PIL import Image

# Check if torch is available
try:
    import torch
    from torch import nn
    from torch.nn import functional as F
    from torch.utils.data import Dataset
    from torch.utils.data import DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# 图像处理工具
from matplotlib import pyplot as plt


# Define DataSet11 only if torch is available
if TORCH_AVAILABLE:
    class DataSet11(Dataset):
        """等比数据集
        """
        def __init__(self,X, y, nums_per_label = 1280, n_class=2):
            """等比数据集
            - 针对样本不均衡数据集
            - nums_per_label:每个样本类别一次采样的行数，可放回抽样
            - n_class:类别个数


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
else:
    # Fallback placeholder class when torch is not available
    class DataSet11:
        def __init__(self, X, y, nums_per_label=1280, n_class=2):
            raise ImportError("PyTorch is not installed. Please install torch to use DataSet11 dataset class.")

        def get_data(self, X_train, y_train, nums_per_label=1280, n_class=2, lable_name="label"):
            raise ImportError("PyTorch is not installed. Please install torch to use DataSet11 dataset class.")

        def __len__(self):
            raise ImportError("PyTorch is not installed. Please install torch to use DataSet11 dataset class.")

        def __getitem__(self, idx):
            raise ImportError("PyTorch is not installed. Please install torch to use DataSet11 dataset class.")


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


# Define T11 only if torch is available
if TORCH_AVAILABLE:
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
            return DataSet11(X=T11.X_train, y=T11.y_train, nums_per_label = 1280, n_class=2)

        @staticmethod
        def test_data_set():
            return DataSet11(X=T11.X_test, y=T11.y_test, nums_per_label = 1280, n_class=2)

        @staticmethod
        def train_one_epoch(model,
                loss_fn,
                optimizer,
                train_dataloader=None):
            """
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
                per_epoch=20):
            """
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
            T11.X_train=X_train
            T11.y_train=y_train
            T11.X_test=X_test
            T11.y_test=y_test

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
else:
    # Fallback placeholder class when torch is not available
    class T11(TBase):
        def __init__(self):
            raise ImportError("PyTorch is not installed. Please install torch to use T11 training class.")

        @staticmethod
        def train_data_set():
            raise ImportError("PyTorch is not installed. Please install torch to use T11 training class.")

        @staticmethod
        def test_data_set():
            raise ImportError("PyTorch is not installed. Please install torch to use T11 training class.")

        @staticmethod
        def train_one_epoch(model, loss_fn, optimizer, train_dataloader=None):
            raise ImportError("PyTorch is not installed. Please install torch to use T11 training class.")

        @staticmethod
        def train(model, X_train, y_train, X_test=None, y_test=None, epochs=50000, batch_size=512, learning_rate=1e-3, model_param_path="model_params_12.pkl.dict", log_file="/tmp/train.log", per_epoch=20):
            raise ImportError("PyTorch is not installed. Please install torch to use T11 training class.")

        @staticmethod
        def get_acc(dataloader, model=None):
            raise ImportError("PyTorch is not installed. Please install torch to use T11 training class.")
        

