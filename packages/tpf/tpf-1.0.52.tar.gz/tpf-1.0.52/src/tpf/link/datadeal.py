import os
import random
import string
import pandas as pd
import numpy as np
import pandas as pd
import numpy as np
import json
import joblib 
from pathlib import Path

from sklearn import preprocessing
from sklearn.model_selection import train_test_split

from tpf.d1 import DataDeal as dt

from tpf import pkl_save,pkl_load
from tpf.d1 import DataDeal as dt
from tpf.d1 import read,write
from tpf.box.fil import  parentdir
from tpf.link.toolml import str_pd
from tpf.link.feature import FeatureEval
from tpf.link.toolml import null_deal_pandas
from tpf.link.toolml import std7


# Check if torch is available
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from tpf import pkl_load,pkl_save
from datetime import date, timedelta

## 已转移至data.deal 
def drop_cols(df_all, columns=["dt"]):
    """多余字段删除"""
    # 多了一个dt日期 这里做删除处理
    df_all.drop(columns=columns,inplace=True)

## 已转移至data.deal 
def file_counter(file_path, add_num=0.01, reset0=False,format_float=None,return_int=False,max_float_count=4):
    """临时文件计数器
    - file_path:文本文件路径
    - add_num: 每次读取增加的数值
    - reset0:为True会将文件的数字置为0
    - format_float:指定小数位格式，比如，".2f"，效果类似0.10，最后一位是0也会保留
    -return_int:返回整数
    - max_float_count:最大小数位，最多保留几位小数

    examples
    -------------------------
    file_path = '.tmp_model_count.txt'
    count = file_counter(file_path, add_num=0.01, reset0=False)

    count = file_counter(file_path, add_num=0.01, reset0=False, format_float=".2f")
    """
    if reset0:
        write(0, file_path)

    # 检查文件是否存在
    if not os.path.exists(file_path):
        # 如果文件不存在，则创建文件并写入0
        write(0, file_path)
        current_count = 0
    else:
        # 如果文件存在，则读取文件中的数字，然后+1
        current_count = read(file_path)
        current_count += add_num
        # 将+1后的数字写入文件
        current_count=round(current_count, max_float_count)
        write(current_count, file_path)
    if return_int:
        return round(current_count)
    elif format_float is not None:
        return  f"{current_count:.2f}"

    # 返回+1后的数字
    return  current_count

#已转移至data.deal
def min_max_scaler(X, num_type=[], model_path=f"min_max_scaler.pkl", reuse=False):
        """针对指定的数字数据类型做min max scaler，通常是float32，float64,int64类型的数据
        
        params
        ---------------------------
        - num_type:需要做归一化的数字列，如果为空，则取数据X的所有列
        - reuse:False就不需要复用，也不会保存文件，此时model_path参数不起作用，比如一些无监督，特征选择等场景
        
        """
        if len(num_type) == 0:
            num_type = X.columns
    
        if reuse:
            if os.path.exists(model_path):
                scaler_train = pkl_load(file_path=model_path,use_joblib=True)
            else:
                # 仅对数值型的特征做标准化处理
                scaler_train = preprocessing.MinMaxScaler().fit(X[num_type])
                pkl_save(scaler_train,file_path=model_path,use_joblib=True)
        else:
            scaler_train = preprocessing.MinMaxScaler().fit(X[num_type])
        X[num_type] = scaler_train.transform(X[num_type])


def read_data():
    file10000 = "data/feature_10000.csv"
    if os.path.exists(file10000):
        df_all = pd.read_csv(file10000)
    else:
        file_path="data/feature.csv"
        df = pd.read_csv(file_path)
        print(df.shape)
        df = df[:10000]
        df_all = df.rename(columns=lambda x: x.lower())
        df_all['is_black_sample'] = np.random.randint(low=0,high=2,size=(df_all.shape[0]))  #随机生成标签
        df_all.to_csv(file10000,index=False)
    return df_all


def make_data(df_all):
    """数据制造
    """
    col_type_int = ['is_team_ip', 'is_self_ml', 'is_ii_metal', 'is_outlier_sum_amt_up_atm',
           'is_lvt_mental', 'is_merch_diff_opp', 'is_empty_id',
           'is_diff_open_location', 'is_cash_then_tran_fore', 'is_fre_fore_cash',
           'is_trans_atm_opp_sus', 'is_outlier_cnt_txn_up_atm',
           'is_free_trade_zone', 'is_salary_fre', 'is_diff_open_state','id_ddl_day_count', 'id_ddl_day_count','trace_day_1','trace_day_3','trace_day_10','trace_day_30']
    
    for ci in col_type_int:
        df_all[ci] = random.choices(string.digits, k=df_all.shape[0])
    
    col_type_cat = ['id_type', 'country_residence', 'occupation', 'industry', 'cur_risk_level','nationality','count_country_trans']
    for cc in col_type_cat:
        df_all[cc] = random.choices(string.digits, k=df_all.shape[0])
    
    col_remove = ['prop_merch_sus_count', 'is_id_expire', 'is_ctoi_sus', 'is_same_corp_tel']
    for cc in col_remove:
        df_all[cc] = random.choices(string.digits, k=df_all.shape[0])
    
    cor_remove_corr = ['out_count', 'third_trans_count', 'count_e_trans', 'sum_of_total_amt_receive', 'sum_of_total_amt_pay', 'sum_e_trans', 'is_non_resident', 'is_fore_open', 'sum_country_trans', 'trans_directcity_count', 'count_of_trans_opp_pay', 'is_rep_is_share', 'prop_merch_special_amt']
    for cc in cor_remove_corr:
        df_all[cc] = random.choices(string.digits, k=df_all.shape[0])
    
    not_in_cols = ['count_multi_open', 'in_count', 'count_of_opp_region', 'trans_city_count', 'count_ii_iii_acct', 'trace_day_10.0', 'trans_directcountry_count', 'trace_day_3.0', 'trans_country_count', 'is_overage', 'trace_day_30.0', 'is_reg_open_intrenal', 'trace_day_1.0']
    for cc in not_in_cols:
        df_all[cc] = np.random.randint(low=0,high=2,size=(df_all.shape[0]))



def data_split(df_all, v_date = '2015-08-01', split=0.8, col_lable="is_black_sample"):
    """
    return
    ---------------------
    - X_train,Y_train,X_test,Y_test,X_valid,Y_valid,df_train,df_test
    - df_train,df_test是正负样本客户分开的训练集与测试集，从中拆分出了X_train,Y_train,X_test,Y_test
    - 
    
    """
    # 本代码中将标签当作了数字而不是类型
    df_all[col_lable]  =df_all[col_lable].astype(int)
    
    # 将回溯日期大于2023-08-26的好样本划分为验证集
    df_validation = df_all[(df_all['target_dt']> v_date) & (df_all[col_lable] == 0) ]
    print("df_validation.shape",df_validation.shape)

    # 对于剩下的数据，按客户号的划分出好样本涉及的客户，与坏样本涉及的客户池
    white_pool = pd.unique(df_all[(df_all['target_dt']<= v_date) & (df_all[col_lable]== 0)]['index_id'])
    black_pool = pd.unique(df_all[df_all[col_lable]== 1]['index_id'])  #这里以全局的角度看客户 如果一个客户出现过坏样本 那它就是坏客户，这两个集合应该会有交集  应该做去重 但这里没有做


    # 从好样本池与坏样本池中分别抽取出80%的客户
    np.random.seed(1)
    white_train = np.random.choice(white_pool,round(len(white_pool)*split),replace = False) # white party_id used for train_set
    black_train = np.random.choice(black_pool,round(len(black_pool)*split),replace = False) # black party_id used for train_set
    

    # 上述客户分别将作为好坏样本加入训练集
    df_train = df_all[(df_all['target_dt'] <= v_date) & 
                      (
                      ((df_all[col_lable] == 0) & df_all['index_id'].isin(white_train)) | 
                      ((df_all[col_lable] == 1) & df_all['index_id'].isin(black_train)) 
                      )
                     ]


    # 将好样本池与坏样本池中余下的20%客户分别作为好坏样本加入测试集
    df_test = df_all[(df_all['target_dt'] <= v_date) & 
                      (
                      ((df_all[col_lable] == 0) & (~df_all['index_id'].isin(white_train))) | 
                      ((df_all[col_lable] == 1) & (~df_all['index_id'].isin(black_train))) 
                      )
                     ]

    # 剔除无关变量，定义训练集、测试集、验证集中的潜在入模特征“X”与目标变量“Y”
    Y_train = df_train[col_lable]
    Y_test = df_test[col_lable]
    df_valid = df_validation
    Y_valid = df_validation[col_lable]
    df_train.drop(columns=[col_lable],inplace=True)
    df_test.drop(columns=[col_lable],inplace=True)
    df_valid.drop(columns=[col_lable],inplace=True)
    return df_train,Y_train,df_test,Y_test,df_valid,Y_valid
        

def append_csv(new_data, file_path):
    """追加写csv文件，适合小数据量
    
    """
    if os.path.exists(file_path):
        # 读取现有的 CSV 文件
        existing_df = pd.read_csv(file_path)
    
        # 将新数据追加到现有的 DataFrame
        updated_df = pd.concat([existing_df, new_data], ignore_index=True)
    else:
        updated_df = new_data
    
    # 将更新后的 DataFrame 写回到 CSV 文件
    updated_df.to_csv(file_path, index=False)

def random_yyyymmdd():
    """随机生成日期,从2000年起
    - 格式：yyyy-mm-dd
    """
    from datetime import datetime, timedelta
    # 定义日期的起始和结束年份（如果需要）
    start_year = 2000
    end_year = datetime.now().year
    
    # 生成随机的年份
    year = random.randint(start_year, end_year)
    
    # 生成随机的月份
    month = random.randint(1, 12)
    
    # 生成随机的天数（注意每个月的天数不同）
    # 使用calendar模块可以帮助我们确定每个月的天数，但这里为了简单起见，我们使用datetime的date方法结合try-except来处理非法日期
    day = random.randint(1, 28)  # 先假设一个月最多28天
    
    while True:
        try:
            # 尝试创建日期对象
            random_date = datetime(year, month, day)
            # 如果成功，则跳出循环
            break
        except ValueError:
            # 如果日期非法（比如2月30日），则增加天数并重试
            day += 1
            if day > 28:  # 如果超过28天还未成功，则重置为1并从新月的天数开始检查（这里可以更加优化，比如根据月份确定最大天数）
                day = 1
                # 注意：这个简单的重置逻辑在跨月时可能不正确，因为它没有考虑到不同月份的天数差异。
                # 一个更准确的做法是使用calendar模块来确定每个月的最大天数。
                # 但为了简洁起见，这里我们假设用户不会频繁生成跨月的随机日期，或者接受偶尔的非法日期重试。
                # 在实际应用中，应该使用更精确的逻辑来确定每个月的最大天数。
                # 然而，为了这个示例的完整性，我们在这里保留这个简单的重置逻辑，并指出其潜在的不足。
    
    # 实际上，上面的while循环和重置逻辑是不完美的。下面是一个更准确的做法：
    from calendar import monthrange
    
    # 生成随机的天数（使用monthrange来确定每个月的最大天数）
    day = random.randint(1, monthrange(year, month)[1])
    random_date = datetime(year, month, day)
    
    # 格式化日期为"YYYY-MM-DD"
    formatted_date = random_date.strftime("%Y-%m-%d")
    return formatted_date

# import pandas as pd

# 已弃用
def append_csv(new_data, file_path):
    """追加写csv文件，适合小数据量
    
    """
    if os.path.exists(file_path):
        # 读取现有的 CSV 文件
        existing_df = pd.read_csv(file_path)
    
        # 将新数据追加到现有的 DataFrame
        updated_df = pd.concat([existing_df, new_data], ignore_index=True)
    else:
        updated_df = new_data
    
    # 将更新后的 DataFrame 写回到 CSV 文件
    updated_df.to_csv(file_path, index=False)
    

from sklearn.base import BaseEstimator, TransformerMixin


# 已弃用
class MinMaxScalerCustom(BaseEstimator, TransformerMixin):
    """自定义 MinMaxScaler，支持动态更新 min/max"""
    def __init__(self):
        self.min_ = None
        self.max_ = None

    def fit(self, X):
        self.min_ = X.min()
        self.max_ = X.max()
        return self

    def transform(self, X):
        return (X - self.min_) / (self.max_ - self.min_)

    def partial_fit(self, X):
        """增量更新 min/max"""
        if self.min_ is None:
            self.min_ = X.min()
            self.max_ = X.max()
        else:
            self.min_ = min(self.min_, X.min())
            self.max_ = max(self.max_, X.max())

#已弃用
class DataDeal():
    def __init__(self):
        """ 
        1. s1_data_classify,字段分类，区分出标识，数字，字符，日期等分类的列 ，不同的列按不同的方式处理
        2. s2_pd_split,s2_data_split,训练集测试集按标签拆分 
        3. s3_min_max_scaler,数字类型归一化处理
        """
        pass
    
    #已弃用
    @staticmethod
    def rolling_windows(data_path=None, df=None,col_time='DT_TIME',
                    interval=7, win_len=10):
        """
        生成器：每次 yield (window_start, window_end, sub_df)
        从最早日期开始，每隔 interval 天取一个 win_len 天的窗口
        """
        if df is None:
            df = pd.read_csv(data_path, parse_dates=[col_time])
        date_col = df[col_time].dt.date

        min_date = date_col.min()
        max_date = date_col.max()

        # 当前窗口起点
        cur_start = min_date
        while cur_start + timedelta(days=win_len-1) <= max_date:
            cur_end = cur_start + timedelta(days=win_len-1)
            mask = date_col.between(cur_start, cur_end)
            yield cur_start, cur_end, df[mask]
            cur_start += timedelta(days=interval)
    
    @staticmethod
    def str_pd(data,cname_date_type):
        """pandas数表列转字符类型"""
        data[cname_date_type] = data[cname_date_type].astype(str)
        data[cname_date_type] = data[cname_date_type].astype("string")
        return data
    
    @staticmethod
    def num_deal(data, num_type=[]):
        column_all = data.columns
        ### 数字
        num_type = [col for col in num_type if col in column_all] 
        data[num_type] = data[num_type].astype(np.float64)
         
    
    @staticmethod
    def date_deal(data,date_type=[]):
        column_all = data.columns
        
        ### 日期
        date_type = [col for col in date_type if col in column_all] 
        data = str_pd(data, date_type)
        for col in date_type:
            data[col] = pd.to_datetime(data[col], errors='coerce')  
            
    #已弃用
    @staticmethod
    def str_deal(data, pc, classify_type=[]):
        """标识列及类别列处理
        - classify_type:指定值则类别列为指定的值，否则使用排除法，排除数字，布尔，标识列，剩下的列为类别列
        
        """
        column_all = data.columns
        identity = pc.col_type.identity
        ### 字符-身份标识类
        str_identity = [col for col in column_all if col in identity]
        data = DataDeal.str_pd(data,str_identity)

        ### 字符-分类，用于分类的列，比如渠道，交易类型,商户，地区等
        if len(classify_type)==0:
            str_classification = [col for col in data.columns if col not in str_identity and col not in pc.col_type.num_type and col not in pc.col_type.date_type and col not in pc.col_type.bool_type]
        else:
            str_classification = classify_type
        pc.col_type.classify_type = str_classification
        DataDeal.str_pd(data,str_classification)
        
        
    @staticmethod
    def s1_data_classify(data, col_type, pc, dealnull=False,dealstd=False,deallowdata=False,lowdata=10,deallog=False):
        """将pandas数表的类型转换为特定的类型
        - float64转换为float32
        - 布尔转为int64
        - 字符串日期转为pandas日期
        
        
        数据分类处理
        - 日期处理：字符串日期转为pandas 日期
        - object转string
        - 空值处理：数字空全部转为0，字符空全部转为'<PAD>'
        - 布尔处理：布尔0与1全部转为int64
        - 数字处理
            - 格式：全部转float32
            - 边界：极小-舍弃10￥以下交易，极大-重置超过7倍均值的金额
            - 分布：Log10后标准化
            - 最终的数据值不大，并且是以0为中心的正态分布

        - 处理后的数据类型：数字，日期，字符
        -
        
        params
        --------------------------------
        - data:pandas数表
        - col_type:pc参数配置中的col_type
        - pc:参数配置
        - dealnull:是否处理空值
        - dealstd:是否标准化处理
        - deallog:是否对数字列log10处理
        - deallowdata:金额低于10￥的数据全置为0
        
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
        col_type.classify_type = str_classification
        data = str_pd(data,str_classification)

        #空值处理
        if dealnull:
            data = null_deal_pandas(data,cname_num_type=num_type,cname_str_type=str_classification,num_padding=0, str_padding = '<PAD>')

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
        
    
    @staticmethod
    def s2_data_split(X, y,  test_size=0.2, random_state=42):
        """数据集拆分，不包含验证集，跨周期验证再额外处理
        - 或者在数据输入该方法之前，切一部分数据出现，单独作为验证集，本方法不再处理验证集
        
        return
        ---------------------
        -  X_train, X_test, y_train, y_test
        
        """
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)
        print("test label count:", y_test.value_counts())

        return  X_train, X_test, y_train, y_test
    
    # 已弃用
    @staticmethod
    def s2_data_split_valid(X, y,test_split=0.2):
        """验证集-跨周期验证
        - 如果数据没有数据无时间特征，即没有周期的概念，就没有必要加验证集
        - 要加也可以，可以随机取，可以切片取，比如取最后1000行数据
        """
        ss = """验证集-跨周期验证
        - 如果数据没有数据无时间特征，即没有周期的概念，就没有必要加验证集
        - 要加也可以，可以随机取，可以切片取，比如取最后1000行数据
        """
        return ss 
    
    
    # 已弃用
    @staticmethod
    def s2_pd_split(X, y, test_split=0.2, random_state=42,):
        """按标签类别等比随机采样，确保测试集中每类标签的数据与训练集保持等比，不会出现测试集中某个标签无数据的情况 

        params
        ------------------------------------
        - X:数据,pandas数表
        - y:标签,pandas数表 
        - lable_name:标签名称 
        - test_size:测试集占比,
        - random_state:随机因子

        examples
        ------------------------------------
        X_train,y_train,X_test,y_test = ddl.s2_pd_split(X, y, lable_name='target', test_size=0.2, random_state=42,)
        
        """
        X_train,y_train,X_test,y_test = DataDeal.pd_data_split(X=X, y=y, test_split=test_split, random_state=random_state,)
        return X_train,y_train,X_test,y_test
    
    ## 已弃用
    @staticmethod
    def s3_min_max_scaler(X, num_type=[], model_path=f"min_max_scaler.pkl", reuse=False):
        """针对指定的数字数据类型做min max scaler，通常是float32，float64,int64类型的数据
        
        params
        ---------------------------
        - num_type:需要做归一化的数字列，如果为空，则取数据X的所有列
        - reuse:False就不需要复用，也不会保存文件，此时model_path参数不起作用，比如一些无监督，特征选择等场景
        
        examples
        -------------------------------------------------
        # 训练集数字类型归一化, reuse=True时，首次执行因model_path不存在会保存preprocessing.MinMaxScaler().fit的结果
        ddl.s3_min_max_scaler(X, num_type=pc.col_type.num_type, model_path=pc.scale_path, reuse=True)

        #reuse=True且model_path存在时，直接加载文件，然后transform
        ddl.s3_min_max_scaler(X_test, num_type=pc.col_type.num_type,model_path=pc.scale_path, reuse=True)
        
        """
        # print(type(X),X.shape)
        if len(num_type) == 0:
            num_type = X.columns

        p_dir = parentdir(model_path)
        if not os.path.exists(p_dir):
            raise Exception(f"The file directory {p_dir} does not exist, unable to write files to it ")

        if reuse:
            if os.path.exists(model_path):
                scaler_train = pkl_load(file_path=model_path,use_joblib=True)
            else:
                # 仅对数值型的特征做标准化处理
                scaler_train = preprocessing.MinMaxScaler().fit(X[num_type])
                pkl_save(scaler_train,file_path=model_path,use_joblib=True)
        else:
            scaler_train = preprocessing.MinMaxScaler().fit(X[num_type])
        X[num_type] = scaler_train.transform(X[num_type])

    @staticmethod
    def pd_data_split(X, y, test_split=0.2, random_state=42,):
        """按标签类别等比随机采样，确保测试集中每类标签的数据与训练集保持等比，不会出现测试集中某个标签无数据的情况 

        params
        ------------------------------------
        - X:数据,pandas数表
        - y:标签,pandas数表
        - test_split:测试集占比,
        - random_state:随机因子

        examples
        ------------------------------------
        X_train,y_train,X_test,y_test = pd_data_split(X, y, test_split=0.2, random_state=42,)
        
        """
        # if isinstance(y, pd.Series):
        #     y = y.to_frame()
        # X = X.reset_index(drop=True)
        copied_index = X.index.copy()

        print(X.shape, X.index)
        # 初始化空的测试集
        X_test = pd.DataFrame(columns=X.columns)
        y_test = pd.DataFrame()

        # 获取唯一标签及其对应的索引,不同的标签
        unique_labels = y.unique()
        print(unique_labels, )

        # 遍历每个标签
        for label in unique_labels:
            # 获取该标签对应的索引
            label_indices = y[y == label].index
            print(len(label_indices), test_split)
            if test_split is None:
                test_split = 0.2

            # 计算该标签需要抽取的样本数（20%）
            num_samples_to_select = int(len(label_indices) * test_split)

            # 随机抽取指定数量的样本, replace=False表示不放回,这里是要拆分数据
            resampled_indices = resample(label_indices, replace=False, n_samples=num_samples_to_select,
                                            random_state=random_state)
            copied_index = copied_index.difference(resampled_indices)

            # 从X和y中选取这些样本
            X_label_test = X.loc[resampled_indices]
            y_label_test = y.loc[resampled_indices]

            if X_test.shape[0] == 0:
                # 添加到测试集中
                X_test = X_label_test
                y_test = y_label_test
            else:
                # 添加到测试集中
                X_test = pd.concat([X_test, X_label_test], ignore_index=True)
                y_test = pd.concat([y_test, y_label_test], ignore_index=True)

        # 剩下的作为训练集
        X_train = X.loc[copied_index]
        y_train = y.loc[copied_index]
        return X_train,y_train,X_test,y_test

    #已弃用
    @staticmethod
    def dt_min_max_scaler(X, date_type=[], scaler_file=None, max_date=None, adjust=True):
        """
        对pandas数据表中的日期列进行归一化处理
        
        参数:
        - X: pandas DataFrame, 需要处理的数据表
        - date_type: list, 需要归一化的日期列名列表
        - scaler_file: str, 用于保存或加载归一化参数的json文件路径
        - max_date: str, 指定归一化使用的最大日期（如'2099-01-01'）;因为预测时的日期是未来的，在训练时是没有，因此支持指定
        - adjust:将过于小的数，调整大一点，只有使用了max_date才会生效，这是缓冲max_date设置过大带来的归一化后数值过小的影响
        
        返回:
        - 处理后的DataFrame

        examples
        -----------------------------------------
        # 不使用max_date（使用数据实际最大值）
        df_normalized = dt_min_max_scaler(df, date_type=['date_column'])
        
        # 使用max_date指定最大日期
        df_normalized = dt_min_max_scaler(df, date_type=['date_column'], max_date='2099-01-01')
        
        # 同时使用scaler_file和max_date
        df_normalized = dt_min_max_scaler(df, 
                                        date_type=['date_column'], 
                                        scaler_file='scaler_params.json',
                                        max_date='2099-01-01')
                                    
        """
        
        # 如果date_type为空，直接返回原数据
        if not date_type:
            return X
        
        # 如果提供了scaler_file且文件存在，则加载归一化参数
        if scaler_file and Path(scaler_file).exists():
            # with open(scaler_file, 'r') as f:
                # scaler_params = json.load(f)
            scaler_params = read(scaler_file)
        else:
            scaler_params = {}
 
        # 复制数据避免修改原DataFrame
        df = X.copy()
        
        # 将max_date转换为时间戳数值（如果提供了）
        max_date_value = pd.to_datetime(max_date).value if max_date else None
        
        for col in date_type:
            # 确保列存在
            if col not in df.columns:
                continue
                
            # 转换为datetime类型
            df[col] = pd.to_datetime(df[col])
            
            # 转换为时间戳数值
            df[col] = df[col].apply(lambda x: x.value)
            
            # 如果scaler_file存在且包含当前列的参数，则使用保存的参数
            adjust_val = 1
            if scaler_params and (col in scaler_params):
                min_val = scaler_params[col]['min']
                max_val = scaler_params[col]['max']
            else:
                min_val = df[col].min()
                # 如果提供了max_date则使用它，否则使用数据的最大值
                max_val = max_date_value if max_date_value else df[col].max()
                scaler_params[col] = {'min': min_val, 'max': max_val}
            
            # 执行归一化
            range_val = max_val - min_val
            if range_val > 0:  # 避免除以0
                df[col] = (df[col] - min_val) / range_val
            else:
                df[col] = 0.0  # 如果所有值相同，归一化为0

            if max_date and adjust:
                if "adjust_val" in scaler_params[col].keys():
                    adjust_val = scaler_params[col]["adjust_val"]
                    df[col] = df[col]*adjust_val
                else:
                    df_col_max = df[col].max()
                    df_col_max = np.abs(df_col_max)
                    if df_col_max<0.00001:
                        adjust_val = 100000
                        df[col] = df[col]*adjust_val
                    elif df_col_max<0.0001:
                        adjust_val = 10000
                        df[col] = df[col]*adjust_val
                    elif df_col_max<0.001:
                        adjust_val = 1000
                        df[col] = df[col]*adjust_val
                    elif df_col_max<0.01:
                        adjust_val = 100
                        df[col] = df[col]*adjust_val
                    scaler_params[col]["adjust_val"] = float(adjust_val)
                
        # 如果指定了scaler_file，则保存归一化参数
        if scaler_file:
            write(scaler_params,file_path=scaler_file)
        return df


    # 已弃用
    @staticmethod
    def df_min_max_scaler(X, num_type=[],not_num_type=[], model_path=None, reuse=False):
        """针对指定的数字数据类型做min max scaler，通常是float32，float64,int64类型的数据
        
        params
        ---------------------------
        - num_type:需要做归一化的数字列，如果为空，则取数据X的所有列
        - not_num_type: X中所有非数字列，排除这些列，剩下的皆为数字列 
        - model_path:默认None不保存min,max值；指定具体路径时，保存到具体的文件;
        - reuse:False就不需要复用，也不会保存文件，此时model_path参数不起作用，比如一些无监督，特征选择等场景
        
        examples
        -------------------------------------------------
        # 训练集数字类型归一化, reuse=True时，首次执行因model_path不存在会保存preprocessing.MinMaxScaler().fit的结果
        ddl.s3_min_max_scaler(X, num_type=pc.col_type.num_type, model_path=pc.scale_path, reuse=True)

        #reuse=True且model_path存在时，直接加载文件，然后transform
        ddl.s3_min_max_scaler(X_test, num_type=pc.col_type.num_type,model_path=pc.scale_path, reuse=True)
        
        """
        # print(type(X),X.shape)
        if len(num_type) == 0:
            all_cols = X.columns
            if len(not_num_type)>0:
                num_type = list(set(all_cols) - set(not_num_type))  
            else:
                num_type = all_cols

        if model_path is not None:
            p_dir = parentdir(model_path)
            if not os.path.exists(p_dir):
                raise Exception(f"The file directory {p_dir} does not exist, unable to write files to it ")
            
            if reuse:
                if os.path.exists(model_path):
                    scaler_train = pkl_load(file_path=model_path,use_joblib=True)
                else:
                    # 仅对数值型的特征做标准化处理
                    scaler_train = preprocessing.MinMaxScaler().fit(X[num_type])
                    pkl_save(scaler_train,file_path=model_path,use_joblib=True)
        else:
            scaler_train = preprocessing.MinMaxScaler().fit(X[num_type])
        X[num_type] = scaler_train.transform(X[num_type])


    #已弃用
    @staticmethod
    def df_min_max_scale_sample(df, col, min_val, max_val):
        """Min-max scale a column"""
        return (df[col] - min_val) / (max_val - min_val)

    #已弃用
    @staticmethod
    def min_max_update(df, num_type=[],is_pre=False, num_scaler_file=None,
                       log=False,log2=False,log10=False):
        """
        Parameters:
        - df: DataFrame to process
        - dict_file: Not used in this implementation (kept for compatibility)
        - is_pre: Whether in preprocessing mode
        - num_scaler_file: File to store/load min-max scaler values (using joblib)
        
        Returns:
        - Processed DataFrame
        """
        
        
        if num_scaler_file is None:
            raise ValueError("num_scaler_file must be specified")
        
        if log:
            df[num_type] = df[num_type].clip(lower=1)
            if TORCH_AVAILABLE:
                df.loc[:,num_type] = torch.log(torch.tensor(df[num_type].values, dtype=torch.float32)).numpy()
            else:
                df.loc[:,num_type] = np.log(df[num_type].values)
        if log2:
            df[num_type] = df[num_type].clip(lower=1)
            if TORCH_AVAILABLE:
                df.loc[:,num_type] = torch.log2(torch.tensor(df[num_type].values, dtype=torch.float32)).numpy()
            else:
                df.loc[:,num_type] = np.log2(df[num_type].values)
        if log10:
            df[num_type] = df[num_type].clip(lower=1)
            if TORCH_AVAILABLE:
                df.loc[:,num_type] = torch.log10(torch.tensor(df[num_type].values, dtype=torch.float32)).numpy()
            else:
                df.loc[:,num_type] = np.log10(df[num_type].values)
        
        
        # Initialize scaler dictionary (column_name -> MinMaxScalerCustom)
        scaler_dict = {}
        
        # If not preprocessing mode, we need to update scaler values
        if not is_pre:
            # Load existing scaler values if file exists
            if os.path.exists(num_scaler_file):
                scaler_dict = joblib.load(num_scaler_file)
            
            # Update scaler values with new data
            if len(num_type) == 0:
                num_type = df.select_dtypes(include=['number']).columns
            for col in num_type:
                col_data = df[col].values
                
                if col in scaler_dict:
                    # Update min/max if current is lower/higher
                    scaler_dict[col].partial_fit(col_data)
                else:
                    # Initialize new column scaler
                    scaler = MinMaxScalerCustom()
                    scaler.fit(col_data)
                    scaler_dict[col] = scaler
            
            # Save updated scaler values
            joblib.dump(scaler_dict, num_scaler_file)
        
        else:
            # In preprocessing mode, just load the scaler values
            if not os.path.exists(num_scaler_file):
                raise FileNotFoundError(f"Scaler file {num_scaler_file} not found for preprocessing")
            
            scaler_dict = joblib.load(num_scaler_file)
        
        # Apply min-max scaling
        processed_df = df.copy()
        for col, scaler in scaler_dict.items():
            if col in processed_df.columns:
                if scaler.max_ != scaler.min_:  # Avoid division by zero
                    processed_df[col] = scaler.transform(processed_df[col].values)
                else:
                    processed_df[col] = 0.0  # Default value for constant columns
        
        return processed_df


class GraphDataDeal:
    def __init__(self, mp):
        """图数据处理"""
        self._mp = mp

    def preprocess(self, df):
        """
        - 将机构与账户合并为账户，对于df的处理只是账户合并了机构，其他未变，机构字段仍然保留
        - 提取账户节点属性：账户名称，金额，币种；若有新增类型，可以简化为多种分类的合并
        - 在这里将账户分为了两类，一类是付款账户，一类是收款账户；这两类账户有会有重复账户的，是有交叉的，即一个账户自转就即是收付双方
        """
        df[self._self._mp.id11] = df[self._self._mp.bank11].astype(int).astype(str) + '_' + df[self._self._mp.id11]
        df[self._self._mp.id12] = df[self._self._mp.bank12].astype(int).astype(str) + '_' + df[self._self._mp.id12]
        df = df.sort_values(by=[self._self._mp.id11])

        #付款收款账户的行数与df是一致的 
        receiving_df = df[[self._self._mp.id12, self._self._mp.amt2, self._self._mp.currency2]]
        paying_df = df[[self._self._mp.id11, self._self._mp.amt1, self._self._mp.currency1]]
        receiving_df = receiving_df.rename({self._self._mp.id12: self._self._mp.id11}, axis=1)

        #币种
        currency_ls = sorted(df[self._self._mp.currency2].unique())

        return df, receiving_df, paying_df, currency_ls


    def get_all_account(self, df):
        """所有不重复账户，一条交易为可疑，则对应的两个账户皆为可疑
        """
        ldf = df[[self._self._mp.id11, self._self._mp.bank11]]
        rdf = df[[self._self._mp.id12, self._self._mp.bank12]]
        
        suspicious = df[df[self._self._mp.label]==1]
        s1 = suspicious[[self._self._mp.id11, self._self._mp.label]]
        s2 = suspicious[[self._self._mp.id12, self._self._mp.label]]
        s2 = s2.rename({self._self._mp.id12: self._self._mp.id11}, axis=1)
        suspicious = pd.concat([s1, s2], join='outer')
        suspicious = suspicious.drop_duplicates()

        ldf = ldf.rename({self._self._mp.bank11: 'Bank'}, axis=1)
        rdf = rdf.rename({self._self._mp.id12: self._self._mp.id11, self._self._mp.bank12: 'Bank'}, axis=1)
        print(ldf.shape,rdf.shape)
        df = pd.concat([ldf, rdf], join='outer')
        print("df.shape:",df.shape)
        df = df.drop_duplicates()
        print("df.shape:",df.shape)
        print(df[:3])

        df[self._self._mp.label] = 0
        df.set_index(self._self._mp.id11, inplace=True)
        df.update(suspicious.set_index(self._self._mp.id11))
        df = df.reset_index()
        return df

    def paid_currency_aggregate(self, currency_ls, paying_df, accounts):
        """为付款账户增加付款特征
        - 
        """
        for i in currency_ls:
            temp = paying_df[paying_df[self._self._mp.currency1] == i]
            accounts['avg paid '+str(i)] = temp[self._self._mp.amt1].groupby(temp[self._self._mp.id11]).transform('mean')
            
            # # 按 id11 分组计算均值，得到 Series (索引为 id11 的值)
            # avg_by_account = paying_df[paying_df[self._self._mp.currency1] == i] \
            #                 .groupby(self._self._mp.id11)[self._self._mp.amt1].mean()
            # # 将均值映射到 accounts 表中
            # accounts['avg paid '+str(i)] = accounts[self._self._mp.id11].map(avg_by_account).fillna(0)
            
        return accounts

    def received_currency_aggregate(self, currency_ls, receiving_df, accounts):
        for i in currency_ls:
            temp = receiving_df[receiving_df[self._self._mp.currency2] == i]
            accounts['avg received '+str(i)] = temp[self._self._mp.amt2].groupby(temp[self._self._mp.id11]).transform('mean')
            
            # # 按 id11 分组计算均值，得到 Series (索引为 id11 的值)
            # avg_by_account = receiving_df[receiving_df[self._self._mp.currency2] == i] \
            #                 .groupby(self._self._mp.id11)[self._self._mp.amt2].mean()
            # # 将均值映射到 accounts 表中
            # accounts['avg received '+str(i)] = accounts[self._self._mp.id11].map(avg_by_account).fillna(0)
            
        accounts = accounts.fillna(0)
        return accounts

    def get_node_attr(self, currency_ls, paying_df,receiving_df, accounts):
        #账户的付款特征
        node_df = self.paid_currency_aggregate(currency_ls, paying_df, accounts)
        #账户的收款特征
        node_df = self.received_currency_aggregate(currency_ls, receiving_df, node_df)
        #账户的标签
        if TORCH_AVAILABLE:
            node_label = torch.from_numpy(node_df[self._self._mp.label].values).to(torch.float)
        else:
            node_label = node_df[self._self._mp.label].values.astype(np.float32)

        #形成数据与标签
        node_df = node_df.drop([self._self._mp.id11, self._self._mp.label], axis=1)
        node_df["Bank"] = node_df["Bank"].astype("float32") / 10000.0
        print(node_df[:3],node_df.shape)
        if TORCH_AVAILABLE:
            node_df = torch.from_numpy(node_df.values).to(torch.float)
        else:
            node_df = node_df.values.astype(np.float32)
        return node_df, node_label

    def get_edge_df(self, accounts, df):
        accounts = accounts.reset_index(drop=True)
        accounts['ID'] = accounts.index
        mapping_dict = dict(zip(accounts[self._self._mp.id11], accounts['ID']))
        df['From'] = df[self._self._mp.id11].map(mapping_dict)
        df['To'] = df[self._self._mp.id12].map(mapping_dict)
        df = df.drop([self._self._mp.id11, self._self._mp.id12, self._self._mp.bank11, self._self._mp.bank12], axis=1)

        if TORCH_AVAILABLE:
            edge_index = torch.stack([torch.from_numpy(df['From'].values), torch.from_numpy(df['To'].values)], dim=0)
        else:
            edge_index = np.stack([df['From'].values, df['To'].values], axis=0)

        df = df.drop([self._self._mp.label, 'From', 'To'], axis=1)
        print(df[:3])

        if TORCH_AVAILABLE:
            edge_attr = torch.from_numpy(df.values).to(torch.float)
        else:
            edge_attr = df.values.astype(np.float32)
        print("edge_attr:\n",edge_attr[:3])
        return edge_attr, edge_index
    

    def deal(self, df, save_path):
        df, receiving_df, paying_df, currency_ls = self.preprocess(df)
        accounts = self.get_all_account(df)
        print("accounts.shape:",accounts.shape)
        node_attr, node_label = self.get_node_attr(currency_ls, paying_df,receiving_df, accounts)
        edge_attr, edge_index = self.get_edge_df(accounts, df)
        pkl_save((node_attr, node_label,edge_attr, edge_index),file_path=save_path, weights_only=False)



class mp:
    time14    = "DT_TIME"
    id11      = "ACCT_NUM"
    id12      = "TCAC"
    bank11    = "ORGANKEY"
    bank12    = "CFIC"
    amt1      = "CRAT"  #原币交易金额,付
    amt2      = "CRAT"  #原币交易金额,收
    amt3      = "CNY_AMT"
    amt4      = "USD_AMT"
    currency1 = "CRTP"  #币种
    currency2 = "CRTP"
    channel   = "TSTP"
    label     = "VOUCHER_NO"
    
    drop_cols = ["TICD","CB_PK","TX_NO"]
    dict_file = "dict_file.txt"


class Tu:
    def __init__(self,mp=mp):
        self._mp = mp 

    def preprocess(self,df):
        """原始交易数据分类及类别统计
        - 交易：按账户排序
        - 付款账户：ID，金额，类别等特征，后续会单独进行特征处理
        - 收款账户：ID, 金额，类别等特征，后续会单独进行特征处理
        - 币种类别：后续会统计账户在该类别上的金额特征
        
        """
        # if len(self._mp.drop_cols)>0:
        #     df = df.drop(columns=self._mp.drop_cols)
        df[self._mp.id11] = df[self._mp.bank11].astype(str) + '_' + df[self._mp.id11]
        df[self._mp.id12] = df[self._mp.bank12].astype(str) + '_' + df[self._mp.id12]
        df = df.sort_values(by=[self._mp.id11])
        print(df[:3])
        receiving_df = df[[self._mp.id12, self._mp.amt2, self._mp.currency2]]
        paying_df = df[[self._mp.id11, self._mp.amt1, self._mp.currency1]]
        receiving_df = receiving_df.rename({self._mp.id12: self._mp.id11}, axis=1)
        currency_ls = sorted(df[self._mp.currency2].unique())

        return df, receiving_df, paying_df, currency_ls

    def get_all_account(self,df):
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

    def add_acc_label(self,df):
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

    def get_edge_df(self,accounts, df):
        accounts = accounts.reset_index(drop=True)
        accounts['ID'] = accounts.index
        mapping_dict = dict(zip(accounts[self._mp.id11], accounts['ID']))
        df['From'] = df[self._mp.id11].map(mapping_dict)
        df['To'] = df[self._mp.id12].map(mapping_dict)
        df = df.drop([self._mp.id11, self._mp.id12, self._mp.bank11, self._mp.bank12], axis=1)

        if TORCH_AVAILABLE:
            edge_index = torch.stack([torch.from_numpy(df['From'].values), torch.from_numpy(df['To'].values)], dim=0)
        else:
            edge_index = np.stack([df['From'].values, df['To'].values], axis=0)

        df = df.drop([self._mp.label, 'From', 'To'], axis=1)
        print(df.columns)
        if TORCH_AVAILABLE:
            edge_attr = torch.from_numpy(df.values).to(torch.float)
        else:
            edge_attr = df.values.astype(np.float32)
        return edge_attr, edge_index

    def paid_currency_aggregate(self,currency_ls, paying_df, accounts):
        for i in currency_ls:
            # temp = paying_df[paying_df[self._mp.currency1] == i]
            # accounts['avg paid '+str(i)] = temp[self._mp.amt1].groupby(temp[self._mp.id11]).transform('mean')

            # 按 id11 分组计算均值，得到 Series (索引为 id11 的值)
            avg_by_account = paying_df[paying_df[self._mp.currency1] == i] \
                            .groupby(self._mp.id11)[self._mp.amt1].mean()
            # 将均值映射到 accounts 表中
            accounts['avg paid '+str(i)] = accounts[self._mp.id11].map(avg_by_account).fillna(0)
            
        return accounts

    def received_currency_aggregate(self,currency_ls, receiving_df, accounts):
        for i in currency_ls:
            # temp = receiving_df[receiving_df[self._mp.currency2] == i]
            # accounts['avg received '+str(i)] = temp[self._mp.amt2].groupby(temp[self._mp.id11]).transform('mean')

            # 按 id11 分组计算均值，得到 Series (索引为 id11 的值)
            avg_by_account = receiving_df[receiving_df[self._mp.currency2] == i] \
                            .groupby(self._mp.id11)[self._mp.amt2].mean()
            # 将均值映射到 accounts 表中
            accounts['avg received '+str(i)] = accounts[self._mp.id11].map(avg_by_account).fillna(0)
            
        accounts = accounts.fillna(0)
        return accounts

    def get_node_attr(self, currency_ls, paying_df,receiving_df, accounts):
        node_df = self.paid_currency_aggregate(currency_ls, paying_df, accounts)
        node_df = self.received_currency_aggregate(currency_ls, receiving_df, node_df)
        if TORCH_AVAILABLE:
            node_label = torch.from_numpy(node_df[self._mp.label].values).to(torch.float)
        else:
            node_label = node_df[self._mp.label].values.astype(np.float32)
        node_df = node_df.drop([self._mp.id11, self._mp.label], axis=1)
        if TORCH_AVAILABLE:
            node_df = torch.from_numpy(node_df.values).to(torch.float)
        else:
            node_df = node_df.values.astype(np.float32)
        return node_df, node_label
    
