'''
Description: 对生成好的数据集进一步处理 
Author: 七三学徒
Date: 2021-12-14 13:29:00
'''

"""
特征变换/处理:
降维
输出:numpy,指定数据维度；通常数据集二维,标签一维 
"""
import math 
import numpy as np 
# import torch
from tpf.ml import ModelLoad
import pandas as pd 
from sklearn.decomposition import LatentDirichletAllocation


def mean_by_count(a=[1,2,3,4,5,6,7], mean_num = 3):
    """按指定长度取均值，每mean_num个数取一次均值
    
    用法
    ----------------------------
    mean_by_count(a=[1,2,3,4,5,6,7], mean_num = 3)
    [2.0, 5.0]
    - 超出的长度舍弃
    
    
    """
    b = []
    ll = len(a)
    size = int(ll/mean_num)
    start_index=0
    for i in range(size):
        end_index=start_index+mean_num 
        if end_index>ll:
            end_index=ll
        b.append(np.array(a[start_index:end_index]).mean())
        start_index=end_index
        
    return b



def LDA(n_components, data, n_jobs=2):
    """
    n_components:想要降到的维度 

    LDA的数据输入格式
    [['轻便 紧凑型 长焦   富士 S2000HD 仅售 1870 元']]
    """
    from sklearn.decomposition import LatentDirichletAllocation
    model_lda = LatentDirichletAllocation(n_components= n_components, n_jobs=n_jobs)
    data_new = model_lda.fit_transform(data)
    # print("2",data_new[:1])
    return data_new


def lda_batch(x, n_components=128, batch_size=100, n_jobs=1,model_path=None):
    """
    LDA 降维,批次处理 
    """

    ll_x = len(x)
    print("row all:",ll_x)
    epoch = math.ceil(ll_x/batch_size)
    print("batch all:",epoch)

    start = 0 
    end = start + batch_size

    model_lda = LatentDirichletAllocation(n_components=n_components, n_jobs=n_jobs)
    

    data = ""
    index = 0
    while True:
        index = index + 1
        print("batch :",index)

        x_train = x[start:end]
        x_train = model_lda.fit_transform(x_train)

        if index==1:
            data = x_train
        else:
            data = np.concatenate((data,x_train),axis=0)
            print("已处理行数:",len(data),",本次处理行数:",len(x_train))
        
        start = end 
        end = start + batch_size
        if end >= ll_x:
            index = index + 1
            print("batch :",index)
            x_train = x[start:]
            x_train = model_lda.fit_transform(x_train)
            data = np.concatenate((data,x_train),axis=0)
            print("已处理行数:",len(data),",本次处理行数:",len(x_train))
            break 
    if model_path:
        ModelLoad.model_save_joblib(model_lda, model_path)
    return data 


def sort_data(data, sort_by, reverse=False,to_list=False):
    """级联排序
    比如输入data=(x,y),sort_by=y

    x,y 将按 y 排序,默认升序 ,排序后,x与y仍然是一一对应的
    reverse=True表示降序 

    to_list=True 
    不管原来的数据是list嵌套 numpy还是tensor,最终全部转为纯python list,这将通用于GUP-CPU
    要注意,list中的元素长度不需要一致,而numpy与tensor要求必须一致 


    examples
    ----------------------
        
    x = np.array([
        [1,0,0],
        [3,3,3],
        [2,2,0]])

    y = np.array([1,3,2])

    a,b = sort_data((x,y),sort_by=y,reverse=True)

    print(np.array(a))
    print(b)

    import torch

    x = torch.Tensor([
        [1,0,0],
        [3,3,3],
        [2,2,0]])


    y = torch.Tensor([1,3,2])
    print(11,y.shape)
    print(0-y)

    a,b = sort_data((x,y),sort_by=y,reverse=True)

    print(torch.Tensor(a))
    print(b)



    [[3 3 3]
    [2 2 0]
    [1 0 0]]

    [3 2 1]

    11 torch.Size([3])

    tensor([-1., -3., -2.])
    
    tensor([[3., 3., 3.],
            [2., 2., 0.],
            [1., 0., 0.]])

    tensor([3., 2., 1.])

    """
    import torch
    
    
    index = 0

    sort_index = np.argsort(sort_by)
    # print(11,sort_index)
    if reverse:
        sort_index2 = []
        max_index = len(sort_index)
        while max_index>0:
            max_index -= 1
            sort_index2.append(sort_index[max_index])
        sort_index = np.array(sort_index2) 

    sort_index = sort_index.tolist()
    # print(12,sort_index)
    

    res = []
    ll = len(data)
    while index<ll :
        d = data[index]
        is_list = isinstance(d,list)
        is_numpy = isinstance(d,np.ndarray)
        is_tensor = isinstance(d,torch.Tensor)

        if not is_list:
            d = data[index].tolist()

        
        lst1 = []
        for idx in sort_index :
            lst1.append(d[idx]) 
        if not to_list:  # 如果全部转为list,就保持原样输出
            if is_numpy:
                lst1 = np.array(lst1)
            if is_tensor:
                lst1 = torch.Tensor(lst1)
    
        res.append(lst1)

        index = index + 1

    return tuple(res)

def MissingValueThreshold(X_train_temp, X_test_temp, threshold = 0.9, fill_num = 0):
    """根据比例 删除缺失值比例较高的特征
    同时将其他缺失值统一填补为fill_num的值
    
    params
    --------------------------------
    - X_train_temp: 训练集特征
    - X_test_temp: 测试集特征
    - threshold: 缺失值比例阈值
    - fill_num: 其他缺失值填补数值
    
    return
    ---------------------------------
    剔除指定特征后的X_train_temp和X_test_temp

    参考
    ---------------------------------
    https://blog.csdn.net/weixin_44820355/article/details/125995946

    """
    for col in X_train_temp:
        if X_train_temp[col].isnull().sum() / X_train_temp.shape[0] >= threshold:
            del X_train_temp[col]
            del X_test_temp[col]
        else:
            X_train_temp[col] = X_train_temp[col].fillna(fill_num)
            X_test_temp[col] = X_test_temp[col].fillna(fill_num)
    return X_train_temp, X_test_temp


def label_cols(X_train, discrete_cols, y_train , P=0.05):
    """
    零假设：列与标签没有关系，
    求得p值低于某个值的列，即相关列
    """
    from sklearn.feature_selection import chi2
    chi2_p = chi2(X_train[discrete_cols], y_train)[1]  # chi2会输出卡方值和p值（就是显著性水平）
    cols = []

    for pValue, colname in zip(chi2_p, discrete_cols):
        print(colname,round(pValue,6))
        if pValue < P:  # 把显著性水平小于P，即是相互独立的可能性为小于P的筛选出来
            cols.append(colname)
    print(cols)

def label_cols_test():
    """
    定义一个分类，奇数为0,偶数为1,另外一个列随机
    """
    x_train = [
        [1,2],
        [2,3],
        [3,6],
        [4,2],
        [1,1],
        [1,3],
        [2,1],
    ]
    y_train = [
        0,
        1,
        0,
        1,
        0,
        0,
        1,
    ]

    x_train = pd.DataFrame(data=x_train,columns=["aa","bb"])
    y_train = pd.DataFrame(data=y_train)
    discrete_cols =["aa","bb"]
    label_cols(x_train, discrete_cols, y_train , P=0.05)
    """ 
    aa 0.28008721081149435
    bb 0.4142161782425252
    []
    aa明明与标签有强烈的相关性，但却没有统计学意义，我们将数据量加大


    """

def label_cols_test2():
    """
    定义一个分类，奇数为0,偶数为1,另外一个列随机
    """
    num = 1000
    aa = np.linspace(start=1,stop=num,num=num,dtype=np.int32)
    label = []
    for i in aa:
        if i%2 ==1:
            label.append(0)  # 奇数为0
        else:
            label.append(1)
    aa = pd.DataFrame(data=aa,columns=["aa"])
    bb = pd.DataFrame(data=np.random.randint(1,high=num,size=num),columns=["bb"])
    cc = pd.DataFrame(data=label,columns=["cc"])
    X_train = pd.concat([aa["aa"],bb["bb"],cc["cc"]],axis=1)
    discrete_cols=["aa","bb","cc"]
    y_train=pd.DataFrame(data=label)
    label_cols(X_train, discrete_cols, y_train , P=0.05)
    """ 
    aa 0.47972
    bb 0.0
    cc 0.0
    ['bb', 'cc']

    效果比较差，
    cc就是标签列，这一列它认为与标签不相关的概率是0,是基本的，因为就是标签自己，这要再算不出来要它何用 
    bb是个随机列，当数据量1000时，100%认为与标签强相关，这就是统计学... 
    aa就是个唯一有用的原始数据了，被寄于期望，却被认为没有统计学意义... 
    这说明统计学这种依据现象总结出来的规律，不包含求奇偶这种非线性的高级的计算，
    要不就直接叫非线性相关得了... 反而我以后就这么叫了... 
    """

if __name__ == "__main__":
    label_cols_test()