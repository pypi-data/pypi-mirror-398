
import numpy as np 


def p_discrete_variable(data_list,x):
    """离散变量概率计算，python list计算
    - data_list: python list 
    - x: list中的某个元素

    exmaples
    ----------------------------------
    data_list = [1,1,2,3]
    p_discrete_variable(data_list,1)  #0.5

    """
    P = data_list.count(1) / len(data_list)
    return P

def p_discrete_variable_np(data_list):
    """离散型变量概率计算，numpy计算
    - data_list: numpy array
    - 返回列表对应元素的概率,ndarray
    """
    if not isinstance(data_list, np.ndarray):
        data_list = np.array(data_list)
    arr_len = len(data_list)
    unique,count=np.unique(data_list,return_counts=True)
    data_count=dict(zip(unique,count))
    p_list = [data_count[v]/arr_len for v in data_list]
    return np.array(p_list)

def p_normal(x, mu, sigma):
    """正态分布的概率密度函数
    - x：变量取值
    - mu：均值
    - sigma：标准差

    exmaples
    -----------------------------
    p_normal(x=0, mu=0, sigma=1)  # 0.3989422804014327

    p_normal(x=np.array([-1,0,1]), mu=0, sigma=1) # array([0.24197072, 0.39894228, 0.24197072])

    - 连续变量计算概率不需要像离散变量那样输入全体变量，因为连续变量的全体是无限的数量
    - 0.24+0.24+0.4 = 0.88，即正态分布标准化后，88%的数据落在标准差[-1,1]的范围内
    
    """
    return 1 / np.sqrt(2 * np.pi) / sigma * np.exp(- ((x - mu)/sigma) ** 2 / 2 )