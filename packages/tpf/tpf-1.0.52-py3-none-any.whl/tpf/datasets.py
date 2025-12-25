
"""小型数据集，通常是模型自带的数据集
规范:
多个数据集,全部以列表形式返回,格式:
[数据,标签],[数据1,标签2,数据2,标签2,],...

load_hotel

X_train, y_train, X_test, y_test = ds.load_iris()
X_train, y_train = ds.load_iris(split=False)

X,y = load_boston(split=False)
X_train, y_train, X_test, y_test = load_boston(split=True,test_size=0.15) 

"""

import random
import os
import numpy as np 
import pandas as pd 
import torch 
import tpf.d1 as d1 
from tpf.box.base import stp
from tpf import pkl_save,pkl_load 
from tpf.params import TestEnvPath as ep
from tpf.params import dataset_path1 as dp
from tpf.params import TPF_DATADIR
from tpf.params import IMG_CIFAR

ds = d1.DataStat()

BASE_DATA_DIR = "/opt/aisty/data/deal"
BASE_DATA_DIR = "/opt/aisty/data/deal"
# mnist_path="/opt/aisty/data/deep/mnist.npz"



from sklearn.model_selection import train_test_split
from sklearn import datasets
from sklearn.preprocessing import MinMaxScaler


def pd_ruxianai(file_path):
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
    else:

        # 加载乳腺癌数据集
        data = load_breast_cancer()
        X = pd.DataFrame(data.data, columns=data.feature_names)
        y = pd.DataFrame(data.target,columns=['target'])

        columns = X.columns
        df = pd.concat([X,y],axis=1)
        df.to_csv(file_path,index=False)
    return df



def local_cifar10_train():
    """本地cifar10训练数据集dataset
    """
    c10 = os.path.join(IMG_CIFAR,"c10_train.pkl")
    train_dataset = pkl_load(file_path=c10)
    return train_dataset

def local_cifar10_test():
    """本地cifar10测试数据集dataset
    """
    c10_test = os.path.join(IMG_CIFAR,"c10_test.pkl")
    test_dataset = pkl_load(file_path=c10_test)
    return test_dataset


def load_hotel(return_dict=False, return_Xy=True, dataset_path=dp):
    """酒店评论索引数据集
    - return_dict: 返回 words_set,word2idx
    - return_Xy： 返回 X_train,y_train,X_test,y_test, np.ndarray类型
    """
    BASE_DIR = os.path.join(dataset_path,"hotel_reader")
    dict_file = os.path.join(BASE_DIR,"data_pkl/wordict.pkl")
    file_train = os.path.join(BASE_DIR,"data_pkl/train.pkl")
    file_test = os.path.join(BASE_DIR, "data_pkl/test.pkl")
    if return_dict:
        words_set,word2idx = pkl_load(file_path=dict_file)   # 字典
        return words_set,word2idx 
    if return_Xy:
        X_train,y_train = pkl_load(file_path=file_train)     # 训练集
        X_test,y_test = pkl_load(file_path=file_test)        # 测试集
        X_train = np.array(X_train)
        y_train = np.array(y_train)
        X_test = np.array(X_test)
        y_test = np.array(y_test)
        print("X_train:",X_train.shape)  # X_train: (4800, 85)
        print("y_train:",y_train.shape)  # y_train: (4800,)
        print("X_test:",X_test.shape)    # X_test: (1200, 85)
        print("y_test:",y_test.shape)    # y_test: (1200,)
        return X_train,y_train,X_test,y_test


def load_iris(split=True):
    """
    split:True,拆分数据集为训练集与测试集,False为不拆分
    data_list = ds.load_iris()

    或

    X_train, y_train, X_test, y_test = ds.load_iris()

    或

    X_train, y_train = ds.load_iris(split=False)
    """
    data = datasets.load_iris()
    if split:
        x_train, x_test, y_train, y_test = train_test_split(data.data, data.target, test_size=0.20, random_state=73)
        return x_train, y_train, x_test, y_test
    else:
        return data.data, data.target


def load_iris_onehot(split=True):
    """
    返回已经对标签独热编码过的数据集

    split:True,拆分数据集为训练集与测试集,False为不拆分,

    data_list = ds.load_iris_onehot()

    或

    [x_train, y_train, x_test, y_test] = ds.load_iris_onehot()

    或

    [X_train, y_train] = ds.load_iris_onehot(split=False)
    """
    data = datasets.load_iris()
    if split:
        x_train, x_test, y_train, y_test = train_test_split(data.data, data.target, test_size=0.33, random_state=42)
        
        y_train  = ds.onehot_pd(y_train)
        y_test  = ds.onehot_pd(y_test)
        return [x_train, y_train, x_test, y_test]
    else:
        lable  = ds.onehot_pd(data.target)
        return [data.data, lable]



def load_boston(split=True, test_size=0.15, reload=False):
    """房价（回归问题）,后续默认加载首次生成的文件 
    X,y = load_boston(split=False)
    X_train, y_train, X_test, y_test = load_boston(split=True,test_size=0.15) 

    print(type(X))   # <class 'numpy.ndarray'>
    print(X.shape)   # (506, 13)
    print(y.shape)   # (506,)
    """
    if not os.path.exists(TPF_DATADIR):
        os.makedirs(TPF_DATADIR, exist_ok=True)
    if split and (not reload):
        tmp_path = os.path.join(TPF_DATADIR,"fangjia_boston_split.pkl")
    else:
        tmp_path = os.path.join(TPF_DATADIR,"fangjia_boston.pkl")
    print(tmp_path)
    if os.path.exists(tmp_path):
        return pkl_load(tmp_path)

    data_url = "http://lib.stat.cmu.edu/datasets/boston"
    raw_df = pd.read_csv(data_url, sep=r'\s+', skiprows=22, header=None)
    # print(raw_df.info())
    """
<class 'pandas.core.frame.DataFrame'>
RangeIndex: 1012 entries, 0 to 1011
Data columns (total 11 columns):
 #   Column  Non-Null Count  Dtype
---  ------  --------------  -----
 0   0       1012 non-null   float64
 1   1       1012 non-null   float64
 2   2       1012 non-null   float64
 3   3       506 non-null    float64
 4   4       506 non-null    float64
 5   5       506 non-null    float64
 6   6       506 non-null    float64
 7   7       506 non-null    float64
 8   8       506 non-null    float64
 9   9       506 non-null    float64
 10  10      506 non-null    float64
dtypes: float64(11)
memory usage: 87.1 KB
    """
    # print(raw_df.describe())
    """
                0            1            2           3           4   ...          6           7           8           9           10
count  1012.000000  1012.000000  1012.000000  506.000000  506.000000  ...  506.000000  506.000000  506.000000  506.000000  506.000000
mean    180.143778    12.008350    16.834792    0.069170    0.554695  ...   68.574901    3.795043    9.549407  408.237154   18.455534
std     188.132839    17.250728     9.912616    0.253994    0.115878  ...   28.148861    2.105710    8.707259  168.537116    2.164946
min       0.006320     0.000000     0.460000    0.000000    0.385000  ...    2.900000    1.129600    1.000000  187.000000   12.600000   
25%       0.257830     0.000000     8.375000    0.000000    0.449000  ...   45.025000    2.100175    4.000000  279.000000   17.400000   
50%      24.021000     7.240000    18.100000    0.000000    0.538000  ...   77.500000    3.207450    5.000000  330.000000   19.050000   
75%     391.435000    16.780000    21.890000    0.000000    0.624000  ...   94.075000    5.188425   24.000000  666.000000   20.200000   
max     396.900000   100.000000    50.000000    1.000000    0.871000  ...  100.000000   12.126500   24.000000  711.000000   22.000000   

[8 rows x 11 columns]
    """

    data = np.hstack([raw_df.values[::2, :], raw_df.values[1::2, :2]])
    target = raw_df.values[1::2, 2]
    if split:
        X_train, X_test, y_train, y_test = train_test_split(data, target, test_size=test_size, random_state=73)
        stp(X_train,"X_train")
        stp(y_train,"y_train")
        pkl_save((X_train,y_train, X_test, y_test),file_path=tmp_path)
        return X_train,y_train, X_test, y_test
    else:
        stp(data, "X")
        stp(target,"y")
        pkl_save((data,target),file_path=tmp_path)
        return data,target


from pprint import pprint as pp

def load_ruxianai(split=True, test_size=0.15, lable2vec=False, random_state=73, file_dir=None):
    """疾病分类(二分类问题)

    params
    ----------------------------------------
    - split:是否拆分为训练集，测试集
    - test_size:测试集占比
    - lable2vec:为True将标签转为列向量，y_train.reshape((-1,1)),标签成为2维数据


    示例
    ------------------------------------------------
    X_train, y_train, X_test, y_test = load_ruxianai()

    或

    X_train, y_train = ruxianai(split=False)


        mean radius  mean texture  mean perimeter  ...  worst concave points  worst symmetry  worst fractal dimension
    count   569.000000    569.000000      569.000000  ...            569.000000      569.000000               569.000000
    mean     14.127292     19.289649       91.969033  ...              0.114606        0.290076                 0.083946
    std       3.524049      4.301036       24.298981  ...              0.065732        0.061867                 0.018061
    min       6.981000      9.710000       43.790000  ...              0.000000        0.156500                 0.055040
    25%      11.700000     16.170000       75.170000  ...              0.064930        0.250400                 0.071460
    50%      13.370000     18.840000       86.240000  ...              0.099930        0.282200                 0.080040
    75%      15.780000     21.800000      104.100000  ...              0.161400        0.317900                 0.092080
    max      28.110000     39.280000      188.500000  ...              0.291000        0.663800                 0.207500

    [8 rows x 30 columns]
    <class 'pandas.core.frame.DataFrame'>
    RangeIndex: 569 entries, 0 to 568

    Data columns (total 30 columns):
    #   Column                   Non-Null Count  Dtype
    ---  ------                   --------------  -----
    0   mean radius              569 non-null    float64
    1   mean texture             569 non-null    float64
    2   mean perimeter           569 non-null    float64
    3   mean area                569 non-null    float64
    4   mean smoothness          569 non-null    float64
    5   mean compactness         569 non-null    float64
    6   mean concavity           569 non-null    float64
    7   mean concave points      569 non-null    float64
    8   mean symmetry            569 non-null    float64
    9   mean fractal dimension   569 non-null    float64
    10  radius error             569 non-null    float64
    11  texture error            569 non-null    float64
    12  perimeter error          569 non-null    float64
    13  area error               569 non-null    float64
    14  smoothness error         569 non-null    float64
    24  worst smoothness         569 non-null    float64
    25  worst compactness        569 non-null    float64
    26  worst concavity          569 non-null    float64
    27  worst concave points     569 non-null    float64
    28  worst symmetry           569 non-null    float64
    29  worst fractal dimension  569 non-null    float64
    dtypes: float64(30)
    memory usage: 133.5 KB
    """

    if split:
        if file_dir is not None:
            ep.DATA_BREAST_CANCER_PATH = file_dir
        save_path = os.path.join(ep.DATA_BREAST_CANCER_PATH,"train_test.pkl")

        if os.path.exists(save_path):
            X_train, y_train, X_test, y_test = pkl_load(file_path=save_path)
            return X_train, y_train, X_test, y_test 
        data = datasets.load_breast_cancer()
        X = data.data  # numpy 
        y = data.target
        X_train, X_test, y_train,  y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
        pkl_save(data=(X_train, y_train, X_test, y_test),file_path=save_path)
        
        if lable2vec:
            # 原始数据的标签，是1维数据，每个样本向量对应一个标量
            # 将标签变成列向量
            y_train = y_train.reshape((-1,1))
            y_test = y_test.reshape((-1,1))
        
        print(f"X_train.shape={X_train.shape}, y_train.shape={y_train.shape}")
        print(f"X_test.shape={X_test.shape}, y_test.shape={y_test.shape}")
        
        return X_train, y_train, X_test, y_test
    else:
        if file_dir is not None:
            ep.DATA_BREAST_CANCER_PATH = file_dir
            
        save_path = os.path.join(ep.DATA_BREAST_CANCER_PATH,"train.pkl")
        
        if os.path.exists(save_path):
            X,y = pkl_load(file_path=save_path)
            if lable2vec:
                y = y.reshape((-1,1))
            return X,y
        data = datasets.load_breast_cancer()
        X = data.data  # numpy 
        y = data.target
        X_train, X_test, y_train,  y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
        
        pkl_save(data=(X,y),file_path=save_path)
        if lable2vec:
            y = y.reshape((-1,1))
        return X,y

def load_taitan():
    """
    泰坦尼克求生数据
    """
    data_path = os.path.join(BASE_DATA_DIR,"taitan/train.pkl")
    x,y = d1.pkl_xy_load(data_path)

    # 经处理的测试数据
    data_path = os.path.join(BASE_DATA_DIR,"taitan/test.pkl")
    x2,y2 = d1.pkl_xy_load(data_path) 
    return [x,y,x2,y2]


def batch_loader(file_dir=None, presfx="batch_", return_torch = False):
    """
    所有数据全部以numpy格式存储;
    不管原来数据什么格式，统统以列表存放；
    读取文件时，再做数据类型转换；
    或者自行修改本方法，以适应特别数据结构与类型
    """
    if not os.listdir(file_dir):
        print(file_dir,'目录为空！')
    else:
        for i in os.listdir(file_dir):
            path_file = os.path.join(file_dir,i)  #取文件绝对路径
            data = d1.pkl_load(file_path=path_file)

            yield data 




def batch_save_set(datasets, batch_size=32, file_dir=None, presfx="batch_"):
    """
    将datasets按批次存储；
    所有数据全部以numpy格式存储;
    """
    data = []
    count = 0
    for v in datasets:
        count += 1
        data.append(v)

        if count % batch_size == 0:
            save_path = os.path.join(file_dir,"{}{}.pkl".format(presfx,count)) 
            pkl_save(data=data,file_path=save_path)
            data = []

def batch_save_Xy(X, y, batch_size=32, file_dir=None, presfx="batch_"):
    """
    每batch_size条(X,y)存储为一个文件；
    numpy格式存储;
    """
    data_X = []
    data_y = []
    max_len = len(y)
    count = 0
    for label in y:
        count += 1
        x = X[count-1]

        if isinstance(x,torch.Tensor):
            x = x.numpy().tolist()
            label = label.numpy().tolist()
        else: # 反之按numpy类型处理
            x = x.tolist()
            label = label.tolist()
        data_X.append(x)
        data_y.append(label)

        if count % batch_size == 0 or count == max_len:
            save_path = os.path.join(file_dir,"{}{}.pkl".format(presfx,count)) 
            data_X = np.array(data_X)
            data_y = np.array(data_y)
            pkl_save(data=(data_X,data_y),file_path=save_path)
            data_X = []
            data_y = []

def batch_loader_Xy(file_dir=None, presfx="batch_", return_torch = False, show_file=False,gray=False):
    """
    批次加载数据，默认一个文件记录一个批次的(X,y)数据

    return_torch：
    为True返回torch.Tensor格式数据，反之返回numpy.ndarray；

    """
    if not os.path.exists(file_dir):
        return 
    if not os.listdir(file_dir):
        print(file_dir,'目录为空！')
    else:
        for i in os.listdir(file_dir):
            path_file = os.path.join(file_dir,i)  #取文件绝对路径
            if show_file:
                print(path_file)
                
            data = d1.pkl_load(file_path=path_file)

            x = data[0]
            label = data[1]
            if gray:  # 模拟图像灰度处理
                x = np.mean(x,axis=1,keepdims=True)
            if return_torch:
                data = (torch.Tensor(x),torch.Tensor(label).long())
            else:
                data = (x,label)
            yield data

def sample_from_dataset(datasets, label_list_key, max_count_one_label = 300):
    """
    按指定的label_list_key从datasets中提取数据，每个label最多提取max_count_one_label条数据；
    原数据集中每个元素为一个(x,y)，现将之拆解为x,y两个列表，然后返回；
    """
    key_count = len(label_list_key)
    label_list_count = [0 for i in range(key_count)]
    sample_dict = dict(zip(label_list_key,label_list_count))  # {0: 300, 1: 300, 2: 300, 3: 300, 4: 300, 5: 300, 6: 300, 7: 300, 8: 300, 9: 300}

    label_key_full = 0
    img_list = []
    train_len = len(datasets)
    label_add = [key for key in sample_dict.keys()]
    labels = []

    for i in range(train_len):
        x,label = datasets[i]
        if label in label_add:
            if sample_dict[label] < max_count_one_label:
                img_list.append(x.numpy().tolist())
                labels.append(label)
                sample_dict[label] += 1

            else:
                label_add.remove(label)
                label_key_full += 1

        if label_key_full == key_count:
            break

        
    img_list = torch.Tensor(img_list)
    labels = torch.Tensor(labels)
    return img_list,labels



def test_batch_save_Xy():
    
    from torchvision import datasets
    from torchvision.transforms import Compose
    from torchvision.transforms import Resize
    from torchvision.transforms import ToTensor
    from torchvision.transforms import Normalize

    """
        打包数据
    """

    # 定义数据预处理
    transforms = Compose(transforms=[Resize(size=(224, 224)), 
                                        ToTensor(),
                                        Normalize(mean=[0.5, 0.5, 0.5], 
                                                    std=[0.5, 0.5, 0.5])])

    data_name = "cifar100"
    train_dataset = datasets.CIFAR100(root=data_name, train=True, transform=transforms, download=True)
    test_dataset = datasets.CIFAR100(root=data_name, train=False, transform=transforms, download=True)


    label_list_key   = [i for i in range(10)] # label列表
    max_count_one_label = 500  # 每个类别取多少条数据


    # imgs,labels = sample_from_dataset(datasets=train_dataset, label_list_key=label_list_key,max_count_one_label=max_count_one_label)
    # print("begin batch save-------")

    # # 这里更好的应该在加载的时候，加载完一批就存一批，而不加载完所有的，再批次保存
    # batch_save_Xy(X=imgs, y=labels, batch_size=32, file_dir="/source/data/tmp/ci100", presfx="batch_")


    imgs,labels = sample_from_dataset(datasets=test_dataset, label_list_key=label_list_key,max_count_one_label=100)
    print("begin batch save test-------")
    batch_save_Xy(X=imgs, y=labels, batch_size=32, file_dir="/source/data/tmp/ci100_test", presfx="batch_")


def test_batch_loader_Xy():

    file_dir="/source/data/tmp/ci100"
    data_loader = batch_loader_Xy(file_dir=file_dir, return_torch=True)

    count = 0
    for X,y in data_loader:
        count += 1
        print(f"count={count}, X.shape={X.shape}, y.shape={y.shape},y.dtype={type(y)}")



# import os
# 解决mac系统OMP: Error #15: Initializing libiomp5.dylib, but found libomp.dylib already initialized.
# os.environ['KMP_DUPLICATE_LIB_OK']='True'  

# 定义数据集
class ZiMu11(torch.utils.data.Dataset):
    def __init__(self,min_seq_len=30,max_seq_len = 50):
        """字母转换
        - 0-9,1-8,2-7...
        - 小写转大写
        
        examples
        -------------------------------------
        import numpy as np
        import torch
        from tpf.datasets import ZiMu11

        # 数据加载器
        loader = torch.utils.data.DataLoader(dataset=ZiMu11(min_seq_len=40,max_seq_len = 50),
                                            batch_size=8,
                                            drop_last=True,
                                            shuffle=True,
                                            collate_fn=None)
        for (X,y) in loader:
            print(X.shape,y.shape)  #torch.Size([8, 50]) torch.Size([8, 50])
            print(X[0])
            print(y[0])
            break
            
        
        """
        super(ZiMu11, self).__init__()

        str_x = '0,1,2,3,4,5,6,7,8,9,q,w,e,r,t,y,u,i,o,p,a,s,d,f,g,h,j,k,l,z,x,c,v,b,n,m'
        str_y = str_x.upper()
        ss = str_x+","+str_y
        
        # 定义字典,数据是0-9数字+小写字母，以及 三个标记 
        word_list = ['<PAD>','<SOS>','<EOS>']+list(set(ss.split(',')))
        
        word_dict = {word: i for i, word in enumerate(word_list)} 
    
        self.word_dict = word_dict
        self.min_seq_len = min_seq_len
        self.max_seq_len = max_seq_len
        
        
    def get_data(self):
        """获取一对x,y 
        """
        
        # 单词集合，没有标记
        words = [
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 
            'q', 'w', 'e', 'r',
            't', 'y', 'u', 'i', 'o', 'p', 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k',
            'l', 'z', 'x', 'c', 'v', 'b', 'n', 'm'
        ]
    
        # 每个词被选中的概率
        p = np.array([
            1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 
            1,   2,  3,  4,  5,  6,  7,  8,  9, 10, 
            11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26
        ])
        
        # 转概率，所有单词的概率之和为1
        p = p / p.sum()
    
        # 随机选n个词
        # Return random integer in range [a, b], including both end points.
        n = random.randint(self.min_seq_len, self.max_seq_len-2)  #有开始标记与结束标记
        x = np.random.choice(words, size=n, replace=True, p=p)
    
        # 采样的结果就是x
        x = x.tolist()
    
        # y是对x的变换得到的
        # 字母大写,数字取10以内的互补数
        def f(i):
            i = i.upper()
            if not i.isdigit():
                return i
            i = 9 - int(i)
            return str(i)
    
        y = [f(i) for i in x]
        
        # 每个标签结尾的字母重复2次，增加任务难度
        # y = y + [y[-1]]
        # # 逆序
        # y = y[::-1]
    
        # 加上首尾符号
        x = ['<SOS>'] + x + ['<EOS>']
        y = ['<SOS>'] + y + ['<EOS>']
    
        # 补pad到固定长度
        # 48+2，序列最大长度为50，不足50的补到50
        # y由于重复了一个字母，最大长度为51，不足51的补到51
        x = x + ['<PAD>'] * self.max_seq_len
        y = y + ['<PAD>'] * self.max_seq_len
        
        x = x[:self.max_seq_len]
        y = y[:self.max_seq_len]
    
        # 单词序列转 索引列表
        x = [self.word_dict[i] for i in x]
        y = [self.word_dict[i] for i in y]
    
        # 转tensor
        x = torch.LongTensor(x)
        y = torch.LongTensor(y)
        return x, y
    

    def __len__(self):
        return 100000

    def __getitem__(self, i):
        return self.get_data()


class SeqData():
    """序列数据"""
    def __init__(self):
        """时序数据
        examples
        --------------------------------------------
        X,y = sd.getXy31(seq_len=100)
        X.shape,y.shape  #(torch.Size([52551, 100, 3]), torch.Size([52551, 100, 1]))
        
                
        """
        pass

    # 生成模拟时序数据
    @staticmethod
    def generate_time_series11():
        """正弦时序数据
        - 主特征,value：三个特征+一个随机噪声
        - 两个随机特征,feature1,feature2 
        """
        time_index_1 = pd.date_range(
            start='2023-01-01 08:00', 
            end='2024-01-01 08:05', 
            freq='min'
        )
        num_steps = time_index_1.shape[0]
        trend = np.linspace(0, 5, num_steps)
        seasonality = 10 * np.sin(np.linspace(0, 10*np.pi, num_steps))
        noise = np.random.normal(0, 1, num_steps)
    
        #[low,high)
        #这里一个交易对应一个类别，一个序列中有seq_len条交易,这个类别也形成一个序列
        target = 3 * np.sin(np.linspace(0, 7*np.pi, num_steps))
        
    
        #将多个特征合并为一个时序
        value = trend + seasonality + noise + target
        return pd.DataFrame({
                'timestamp': time_index_1,
                'value': value.astype(np.float32),
                'feature1': np.random.uniform(0, 10, num_steps),  # 附加随机特征
                'feature2': np.random.randint(0, 5, num_steps)
            }).set_index('timestamp'),pd.DataFrame(target,columns=['target'])

    @staticmethod
    def mmscaler():
        """MinMaxScaler
        """
        # 生成数据
        df_X,df_y = sd.generate_time_series11()
        scaler = MinMaxScaler()
        scaled_data = scaler.fit_transform(df_X.values)
        return scaled_data,np.array(df_y)

    # 构建训练集
    @staticmethod
    def create_sequences11(data, label, seq_length, step=10, is_label_long=False):
        """滑动窗口取序列数据
        - data,数据 
        - label,标签
        - seq_length: 一个序列的数据个数，相当于一句话有多少个单词
        - step: 步长，一次跳过多少条数据，滑动窗口长度,一个窗口为一个序列的数据,然后跨越step个数据再取下一个窗口，类似于卷积的步长
        - is_label_long: 标签是否整数类型

        """
        sequences = []
        targets = []
        iv = seq_length//step
        for i in range(0,len(data)-seq_length,iv):
            sequences.append(data[i:i+seq_length])
            targets.append(label[i:i+seq_length])  # 预测主特征
        if is_label_long:
            return torch.FloatTensor(np.array(sequences)), torch.LongTensor(np.array(targets)) 
        return torch.FloatTensor(np.array(sequences)), torch.FloatTensor(np.array(targets))
        
    @staticmethod
    def getXy31(seq_len=100):
        """正弦时序数据
        - X:主特征value：三个特征+一个随机噪声;两个随机特征,feature1,feature2；做了归一化处理
        - y:主特征value中的一个正弦时序
        
        """
        # 参数配置
        SEQ_LENGTH = seq_len  # 滑动窗口长度 
        scaled_data,label_seq = sd.mmscaler()
        X, y = sd.create_sequences11(scaled_data, label_seq, SEQ_LENGTH)
        return X,y 
                

class SeqXy31(torch.utils.data.Dataset):
    def __init__(self,seq_len=100):
        """时序数据，序列到序列
        - 使用了sd序列数据源 

        examples
        --------------------------------
        dataset = SeqXy31()
        X,y = dataset[0]
        X.shape,y.shape    # (torch.Size([100, 3]), torch.Size([100, 1]))

        """
        super().__init__()
        
        X,y = sd.getXy31(seq_len=seq_len)
        self.X = X 
        self.y = y 
        self.len = len(y)

    def __len__(self):
        return self.len

    def __getitem__(self, i):
        x = self.X[i]
        y = self.y[i]
        return x,y  



#-------------------IBM图数据集------------------

import os,datetime
import numpy as np
import pandas as pd
from sklearn import preprocessing
import torch
from typing import Callable, Optional
from torch_geometric.data import (
    Data,
    InMemoryDataset
)

class AMLtoGraph(InMemoryDataset):

    def __init__(self, root: str, edge_window_size: int = 10,
                 transform: Optional[Callable] = None,
                 pre_transform: Optional[Callable] = None,
                 raw_file_names=None,processed_file_names=None,mp=None):
        """
        
        """
        self.edge_window_size = edge_window_size
        self._raw_file_names = raw_file_names
        self._mp = mp
        self._processed_file_names=processed_file_names
        super().__init__(root, transform, pre_transform)
        self.data, self.slices = torch.load(self.processed_paths[0],weights_only=False)
        

    @property
    def raw_file_names(self) -> str:
        return self._raw_file_names 

    @property
    def processed_file_names(self) -> str:
        return self._processed_file_names

    @property
    def num_nodes(self) -> int:
        return self._data.edge_index.max().item() + 1

    def df_label_encoder(self, df, columns):
        le = preprocessing.LabelEncoder()
        for i in columns:
            df[i] = le.fit_transform(df[i].astype(str))
        return df


    def preprocess(self, df):
        """
        - 类别编码：索引编码
        - 时间处理：min max scaler
        - 将机构与账户合并为账户 
        - 提取账户节点属性：账户名称，金额，币种；若有新增类型，可以简化为多种分类的合并
        - 
        
        """
        df = self.df_label_encoder(df,[self._mp.channel, self._mp.currency1, self._mp.currency2])

        # 时间本可以
        df[self._mp.time14] = pd.to_datetime(df[self._mp.time14])
        df[self._mp.time14] = df[self._mp.time14].apply(lambda x: x.value)
        df[self._mp.time14] = (df[self._mp.time14]-df[self._mp.time14].min())/(df[self._mp.time14].max()-df[self._mp.time14].min())

        df[self._mp.id11] = df[self._mp.bank11].astype(str) + '_' + df[self._mp.id11]
        df[self._mp.id12] = df[self._mp.bank12].astype(str) + '_' + df[self._mp.id12]
        df = df.sort_values(by=[self._mp.id11])
        receiving_df = df[[self._mp.id12, self._mp.amt2, self._mp.currency2]]
        paying_df = df[[self._mp.id11, self._mp.amt1, self._mp.currency1]]
        receiving_df = receiving_df.rename({self._mp.id12: self._mp.id11}, axis=1)
        currency_ls = sorted(df[self._mp.currency2].unique())

        return df, receiving_df, paying_df, currency_ls

    def get_all_account(self, df):
        ldf = df[[self._mp.id11, self._mp.bank11]]
        rdf = df[[self._mp.id12, self._mp.bank12]]
        suspicious = df[df[self._mp.label]==1]
        s1 = suspicious[[self._mp.id11, self._mp.label]]
        s2 = suspicious[[self._mp.id12, self._mp.label]]
        s2 = s2.rename({self._mp.id12: self._mp.id11}, axis=1)
        suspicious = pd.concat([s1, s2], join='outer')
        suspicious = suspicious.drop_duplicates()

        ldf = ldf.rename({self._mp.bank11: 'Bank'}, axis=1)
        rdf = rdf.rename({self._mp.id12: self._mp.id11, self._mp.bank12: 'Bank'}, axis=1)
        df = pd.concat([ldf, rdf], join='outer')
        df = df.drop_duplicates()

        df[self._mp.label] = 0
        df.set_index(self._mp.id11, inplace=True)
        df.update(suspicious.set_index(self._mp.id11))
        df = df.reset_index()
        return df
    
    def paid_currency_aggregate(self, currency_ls, paying_df, accounts):
        for i in currency_ls:
            temp = paying_df[paying_df[self._mp.currency1] == i]
            accounts['avg paid '+str(i)] = temp[self._mp.amt1].groupby(temp[self._mp.id11]).transform('mean')
        return accounts

    def received_currency_aggregate(self, currency_ls, receiving_df, accounts):
        for i in currency_ls:
            temp = receiving_df[receiving_df[self._mp.currency2] == i]
            accounts['avg received '+str(i)] = temp[self._mp.amt2].groupby(temp[self._mp.id11]).transform('mean')
        accounts = accounts.fillna(0)
        return accounts

    def get_edge_df(self, accounts, df):
        accounts = accounts.reset_index(drop=True)
        accounts['ID'] = accounts.index
        mapping_dict = dict(zip(accounts[self._mp.id11], accounts['ID']))
        df['From'] = df[self._mp.id11].map(mapping_dict)
        df['To'] = df[self._mp.id12].map(mapping_dict)
        df = df.drop([self._mp.id11, self._mp.id12, self._mp.bank11, self._mp.bank12], axis=1)

        edge_index = torch.stack([torch.from_numpy(df['From'].values), torch.from_numpy(df['To'].values)], dim=0)

        df = df.drop([self._mp.label, 'From', 'To'], axis=1)

        edge_attr = torch.from_numpy(df.values).to(torch.float)
        return edge_attr, edge_index

    def get_node_attr(self, currency_ls, paying_df,receiving_df, accounts):
        node_df = self.paid_currency_aggregate(currency_ls, paying_df, accounts)
        node_df = self.received_currency_aggregate(currency_ls, receiving_df, node_df)
        node_label = torch.from_numpy(node_df[self._mp.label].values).to(torch.float)
        node_df = node_df.drop([self._mp.id11, self._mp.label], axis=1)
        node_df = self.df_label_encoder(node_df,['Bank'])
        node_df = torch.from_numpy(node_df.values).to(torch.float)
        return node_df, node_label

    def process(self):
        df = pd.read_csv(self.raw_paths[0])
        df, receiving_df, paying_df, currency_ls = self.preprocess(df)
        accounts = self.get_all_account(df)
        node_attr, node_label = self.get_node_attr(currency_ls, paying_df,receiving_df, accounts)
        edge_attr, edge_index = self.get_edge_df(accounts, df)

        data = Data(x=node_attr,
                    edge_index=edge_index,
                    y=node_label,
                    edge_attr=edge_attr
                    )
        
        data_list = [data] 
        if self.pre_filter is not None:
            data_list = [d for d in data_list if self.pre_filter(d)]

        if self.pre_transform is not None:
            data_list = [self.pre_transform(d) for d in data_list]

        data, slices = self.collate(data_list)
        torch.save((data, slices), self.processed_paths[0])
        # torch.save((data, slices), self.processed_paths[0],weights_only=False)

#-------------------IBM图数据集------------------






if __name__=="__main__":
    # test_batch_loader_Xy()
    # load_breast_cancer()
    # X_train, y_train, X_test, y_test = ruxianai()
    # print(X_train.shape,X_test.shape)

    X_train, y_train, X_test, y_test = load_iris()
    print(X_train.shape,X_test.shape)
