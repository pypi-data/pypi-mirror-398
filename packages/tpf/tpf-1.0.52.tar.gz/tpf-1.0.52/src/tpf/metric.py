
import numpy as np 
import pandas as pd 

##-------------------------异常值检测 开始 ------------------------------------

def std3(data, col_name="size"):
    """3sigma检测"""
    data_df = pd.DataFrame(data)  
      
    # 计算均值和标准差  
    mean = data_df[col_name].mean()  
    std = data_df[col_name].std()  
      
    # 确定阈值  
    lower_bound = mean - 3 * std  
    upper_bound = mean + 3 * std  
      
    # 识别异常值  
    outliers = data_df[(data_df[col_name] <= lower_bound) | (data_df[col_name] >= upper_bound)]  
    return outliers


##-------------------------异常值检测 开始 ------------------------------------

##-------------------------fsi计算 开始 ------------------------------------
# 上述代码使用了np.percentile来创建等宽的分数分档。这是基于整个分数分布（训练集和测试集合并）的，以确保分档的一致性。
# PSI的计算依赖于对数操作，因此当实际占比或预期占比为0时，需要跳过这些分档，以避免除以零的错误。
# PSI值越小，表示模型在不同数据集上的表现越稳定。然而，需要注意的是，PSI的阈值（如0.1和0.25）是根据具体情况和领域知识来设定的，可能需要根据实际情况进行调整。
# 在实际应用中，通常会将模型应用于更大的验证集或生产数据集，并与历史数据进行比较，以更准确地评估模型的稳定性。


# 计算两个数据集之间分桶的比率
def bin_rate(y_pred_raw,y_pred_raw_test,num_bins = 10,scale=100):
    """计算两个数据集之间分桶的比率
    - 验证集类似于开发自验，测试集是另外一个团队验证，测试集的数据理论上代表着未知的数据
    - 两个数据集在不同档次的分布比，前提是认为这两个数据集的分布基本一致
    """
    # 对训练集和测试集的分数进行分档  
    bins = np.percentile(np.concatenate([y_pred_raw, y_pred_raw_test]), np.linspace(0, scale, num_bins + 1))  
    train_counts, _ = np.histogram(y_pred_raw, bins=bins)  
    test_counts, _ = np.histogram(y_pred_raw_test, bins=bins) 

    # 计算每个分档的实际占比和预期占比  
    train_total = np.sum(train_counts)  
    test_total = np.sum(test_counts)  
    train_rate = train_counts / train_total  
    test_rate = test_counts / test_total  
    return train_rate,test_rate

# 计算PSI  
def calculate_psi(train_rate, test_rate):  
    """基于一个前提，训练集与测试集的数据分布一致，在此基础上才能显现出模型的稳定性
    """
    psi = 0.0  
    for base, comp in zip(train_rate, test_rate):  
        if base == 0 or comp == 0:  
            continue  # 避免除以零  
        psi += (base - comp) * np.log(base / comp)  
    return psi  


# 评估fsi的好坏
def show_psi(train_rate, test_rate):  
    """评估fsi的好坏
    PSI的阈值（如0.1和0.25）是根据具体情况和领域知识来设定的，可能需要根据实际情况进行调整
    """
    psi_value = calculate_psi(train_rate, test_rate)  
      
    print(f"PSI Value: {psi_value}")  
      
    # 根据PSI值评估模型稳定性  
    if psi_value < 0.1:  
        print("Model stability is good.")  
    elif psi_value >= 0.1 and psi_value < 0.25:  
        print("Model stability is moderate, may need monitoring.")  
    else:  
        print("Model stability is poor, requires investigation.")


# 划分为不同的档次对fsi的影响
def get_psi_bybins(y_pred_raw_train, y_pred_raw_test, scale=100):
    """划分为不同的档次对fsi的影响
    
    example 
    -----------------------------
    bin_count,fsi_value = get_psi_bybins(y_pred_raw_train, y_pred_raw_test, scale=100)
    
    """
    print(scale)
    x = []
    y = []
    for bin_count in range(10, scale, 1):
        train_rate,test_rate = bin_rate(y_pred_raw_train, y_pred_raw_test, num_bins = bin_count, scale=100)
        psi_value = calculate_psi(train_rate, test_rate)  
        # print(bin_count,round(psi_value,3))
        x.append(bin_count)
        y.append(round(psi_value,3))
    return x,y

##-------------------------fsi计算 结束 ------------------------------------
