import numpy as np 
import random 

def rmse_batch(theta_vec, x, y, batch_size=0):
    """
    定义计算RMSE的函数，随机批次计算损失函数
    theta_vec多项式系数列表，第1个元素为偏置，可设可不设，不设时自动设置为0
    x为样本数组，其元素为样本向量
    y为标签数组，其元素为标量 
    batch_size为随机抽取的批次大小，默认值0表示全批量
    """
    index_list = []
    squared_err = 0
    x_row_count = len(x)
    theta0 = theta_vec[0] 
    theta = np.array(theta_vec[1:])
    # print(theta)

    if len(x[0]) == len(theta_vec):
        print('多项式偏置没有设置，为计算方便，计算过程中将其设置为0') 
        theta0 = 0
        theta = theta_vec

    if batch_size == 1:
        #  单独输入一个样本，或者只含有一个样本的数组
        if type(x[0]) == type([]): 
            x = x[0]
            y = y[0]
        d = theta0 * 1 + np.sum(theta * x)
        squared_err += (d - y) ** 2
        return squared_err
    elif batch_size==0: #全样本损失计算,0为默认值，不输入即全批量
        batch_size = x_row_count
        index_list = np.arange(batch_size)
    else: # 随机指定批次计算
        if batch_size > x_row_count:
            batch_size = x_row_count
        #  随机取batch_size个不重复索引下标
        index_list =  random.sample(range(x_row_count), batch_size) 
    # print(index_list)

    for i in index_list:
        f_out = theta0 * 1 + np.sum(theta * x[i])
        squared_err += (f_out - y[i]) ** 2
    squared_err = squared_err/x_row_count

    res = np.sqrt(squared_err)
    return res


def model_gd_predict(theta_vec, X_test):
    '''
    梯度下降目标函数
    '''
    y_test = []
    for i in range(len(X_test)):
        f_out = theta_vec[0]
        for n in range(1, len(theta_vec)):
            f_out += theta_vec[n] * X_test[i][n-1]
        y_test.append(f_out)
    return np.array(y_test).astype(np.float32)


# 定义计算梯度的函数
def compute_grad(theta_vec, x, y):
    """
    梯度下降损失函数求导计算
    损失函数为函数输出与样本标签之差的平方的均值再除以2

    目标函数的定义使theta_vec系数向量元素个数比特征个数多1
    h(X1) = w0 + w1*x1 + w2*x2 + ...  
    J(w) = ((h(X1) - d)**2)  
    grad = [0, 0, 0]  
    grad[0] = (h(x1) - d)  
    grad[1] = (h(x1) - d)x1  
    grad[2] = (h(x2) - d)x2  
    """
    row_count = len(x)

    # 计算模型输出，并求梯度
    f_out = theta_vec[0] * 1
    grad_sum = [0 for x in range(len(theta_vec))]
    for i in range(row_count):  # 循环整个样本，求全样本变化率之和
        for n in range(1, len(theta_vec)):
            f_out += theta_vec[n] * x[i][n-1]
        offset = f_out - y[i]   # 模型输出 － 样本标签 得到的差，是一个标量 

        grad_sum[0] = offset    # 按列存储梯度并求和
        for n in range(1, len(theta_vec)):
            grad_sum[n] += offset * x[i][n-1]
    # 梯度计算，列方向上求均值
    grad_mean = [0 for x in range(len(theta_vec))]
    grad_mean[0] = grad_sum[0]
    for n in range(1, len(theta_vec)):
        grad_mean[n] = grad_sum[n] / row_count

    gradient = np.array(grad_mean).astype(np.float32)
    return gradient

