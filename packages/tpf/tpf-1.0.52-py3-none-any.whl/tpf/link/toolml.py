import numpy as np 
import pandas as pd 
import joblib 
import pickle as pkl 
import os
import random 

from sklearn.metrics import accuracy_score,roc_auc_score, confusion_matrix, classification_report, roc_curve, auc,f1_score

from sklearn import preprocessing
from sklearn.model_selection import train_test_split

from tpf.d1 import DataDeal as dt
from tpf.d1 import is_single_label



def pkl_save(data, file_path, use_joblib=False, compress=0):
    """
    data:保存一个列表时直接写列表,多个列表为tuple形式
    """
    if use_joblib:
        joblib.dump(data, filename=file_path, compress=compress)
    else:
        data_dict = {}
        if type(data).__name__ == 'tuple':
            index = 0
            for v in data:
                index = index+1
                key = "k"+str(index)
                data_dict[key]= v 
        else:
            data_dict["k1"] = data 

        # 在新文件完成写入之前，不要损坏旧文件
        tmp_path = file_path+".tmp"
        bak_path = file_path+".bak"

        with open(tmp_path, 'wb') as f:
            # 如果这一步失败，原文件还没有被修改，重新写入即可
            pkl.dump(data_dict, f)

            # 如果这一步失败，.tmp文件已经被成功写入，直接将.tmp去掉就是最新写入的文件
            # 这里并没有测试rename是否被修改文件的内容，从命名上看，rename是不会的，
            if os.path.exists(file_path):
                os.rename(src=file_path,dst=bak_path)
        if os.path.exists(tmp_path):
            # 如果是下面这一步被强制中止，直接将.tmp去掉就是最新写入的文件
            # 也可以通过.bak文件恢复到修改之前的文件
            # 重命后，不会删除备份文件，最坏的结果是丢失当前的写入，但也会保留一份之前的备份
            os.rename(src=tmp_path,dst=file_path)
        

def pkl_load(file_path, use_joblib=False):
    """ 
    与pkl_load配对使用
    """
    if use_joblib:
        data = joblib.load(file_path)
        return data

    try:
        with open(file_path, 'rb') as f:
            data_dict = pkl.load(f)
        data = tuple(list(data_dict.values()))
        if len(data) == 1:
            return data[0]
        return data 
    except Exception as e:
    #     print(repr(e))
        model = joblib.load(file_path)
        return model 


def str_pd(data,cname_date_type):
    """pandas数表列转字符类型"""
    # data[cname_date_type] = data[cname_date_type].astype(str)
    # data[cname_date_type] = data[cname_date_type].astype("string")
    data.loc[:,cname_date_type] = data[cname_date_type].astype(str)
    data.loc[:,cname_date_type] = data[cname_date_type].astype("string")
    
    return data


def null_deal_pandas(data,cname_num_type=[], cname_str_type=[], num_padding=0, str_padding = '<PAD>'):
    """
    params
    ----------------------------------
    - data:pandas数表
    - cname_num_type：数字类型列表
    - cname_str_type：字符类型列表
    - num_padding:数字类型空值填充
    - str_padding:字符类型空值填充
    
    example
    -----------------------------------
    #空值处理
    data = null_deal_pandas(data,cname_num_type=num_type,cname_str_type=str_classification,num_padding=0,str_padding = '<PAD>')

    """
    if len(cname_num_type)>0:
        # 数字置为0
        for col in cname_num_type:
            data.loc[data[col].isna(),col]=num_padding
    
    if len(cname_str_type)>0:
        #object转str，仅处理分类特征，身份认证类特征不参与训练
        data[cname_str_type] = data[cname_str_type].astype(str)
        data[cname_str_type] = data[cname_str_type].astype("string")
        
        for col in cname_str_type:
            data.loc[data[col].isna(),col]=str_padding

        # nan被转为了字符串，但在pandas中仍然是个特殊存在，转为特定字符串，以防Pandas自动处理
        # 创建一个替换映射字典  
        type_mapping = {  
            'nan': str_padding,   
            '': str_padding
        }  
            
        # 使用.replace()方法替换'列的类型'列中的值  
        data[cname_str_type] = data[cname_str_type].replace(type_mapping)  
            
        nu = data[cname_str_type].isnull().sum()
        for col_name,v in nu.items():
            if v > 0 :
                print("存在空值的列:\n")
                print(col_name,v)
        return data

def min_max_scaler(df):  
    return (df - df.min()) / (df.max() - df.min())  

def std7(df, cname_num, means=None, stds=None, set_7mean=True):
    if set_7mean: #将超过7倍均值的数据置为7倍均值
        # 遍历DataFrame的每一列,
        for col in cname_num:  
            # 获取当前列的均值  
            mean_val = means[col]  
            # 创建一个布尔索引，用于标记哪些值超过了均值的7倍  
            mask = df[col] > (7 * mean_val)  
            # 将这些值重置为均值的7倍  
            df.loc[mask, col] = 7 * mean_val  

    df[cname_num] = (df[cname_num] - means)/stds  #标准化
    
    return df  

def get_logical_types(col_type):
    """featuretools逻辑类型处理
    - 主要处理日期与字符串两类，即将日期，字符串类型的字段转换为featuretools的类型
    - 数字不需要处理，因为featuretools会默认把数字形式的字符串当数字处理
    """
    logical_types={}
    for col in col_type.date_type:
        logical_types[col] = 'datetime'
    
    #类别本来不是数字，但onehot编码后，就只剩下0与1这两个数字了
    for col in col_type.str_classification:
        logical_types[col] = 'categorical'

    return logical_types



def data_classify_deal(data, col_type, pc,dealnull=False,dealstd=False,deallowdata=False,lowdata=10,deallog=False):
    """数据分类处理
    - 日期处理
    - object转string
    - 空值处理
    - 数字处理
        - 边界：极小-舍弃10￥以下交易，极大-重置超过7倍均值的金额
        - 分布：Log10后标准化
        - 最终的数据值不大，并且是以0为中心的正态分布

    - 处理后的数据类型：数字，日期，字符
    -
    
    params
    --------------------------------
    - dealnull:是否同时处理空值
    - dealstd:是否进行标准化处理
    - deallog:是否对数字列log10处理
    
    example
    ----------------------------------
    data_classify_deal(data,pc.col_type_nolable,pc)
    
    """
    column_all = data.columns
     
     
    ### 日期
    date_type = [col for col in col_type.date_type if col in column_all] 
    data = str_pd(data, date_type)
    for col in date_type:
        data[col] = pd.to_datetime(data[col], errors='coerce')  

    ### 数字
    num_type = [col for col in col_type.num_type if col in column_all] 
    data[num_type] = data[num_type].astype(np.float32)
    
    
    bool_type = [col for col in col_type.bool_type if col in column_all]
    data[bool_type] = (data[bool_type].astype(np.float32)).astype(int)  # 为了处理'0.00000000'

    ### 字符-身份标识类
    cname_str_identity = pc.cname_str_identity 
    str_identity = [col for col in column_all if col in cname_str_identity]
    col_type.str_identity = str_identity
    data = str_pd(data,str_identity)

    ### 字符-分类，用于分类的列，比如渠道，交易类型,商户，地区等
    str_classification = [col for col in data.columns if col not in str_identity and col not in num_type and col not in date_type and col not in bool_type]
    col_type.str_classification = str_classification
    data = str_pd(data,str_classification)

    #空值处理
    if dealnull:
        data = null_deal_pandas(data,cname_num_type=num_type,cname_str_type=str_classification,num_padding=0,str_padding = '<PAD>')

    if len(num_type)>0:
        if deallowdata:
            #数字特征-极小值处理
            #将小于10￥的金额全部置为0，即不考虑10￥以下的交易
            for col_name in num_type:
                data.loc[data[col_name]<lowdata,col_name] = lowdata
        
            #将lowdata以下交易剔除
            data.drop(data[data.CNY_AMT.eq(10)].index, inplace=True)
        if deallog:
            #防止后面特征组合时，两个本来就很大的数据相乘后变为inf
            data[num_type] = np.log10(data[num_type])
    
        if dealstd:
            # 数字特征-归一化及极大值处理
            #需要保存，预测时使用
            means = data[num_type].mean()
            stds = data[num_type].std()
            
            data = std7(data, num_type, means, stds)
    

    return data
    
    
