


"""

"""

import os,sys 
import torch 
from torch import nn 
import numpy as np 
import pandas as pd 
from tpf.data.deal import DataDeal 
from tpf.data.deal import DataDeal as dtl
from tpf.data.tu11 import GraphDataDeal

from tpf.link.db import OracleDb,reset_passwd
# from tpf.nlp.text import TextEmbedding as tte 
from tpf.data.deal import TextEmbedding as tte
# from tpf.link.feature import Corr
# from tpf.link.feature import FeatureEval
# from tpf.link.feature import FeatureFrequencyEval
# from tpf.link.feature import feature_selected

# from tpf.link.toolml import null_deal_pandas,std7,min_max_scaler
# from tpf.link.toolml import str_pd,get_logical_types
# from tpf.link.toolml import data_classify_deal
# from tpf.link.toolml import pkl_save,pkl_load


# from tpf.link.config import ColumnType,ParamConfig 
from tpf.conf.common import ParamConfig
from tpf.data.deal import TextDeal
from tpf import read,write

from tpf import log 

def lg(msg):
    log_file_path = "/tmp/tpf.log"
    # 超过max_file_size大小自动重写，即超过10M就自动清空一次
    log(msg,fil=log_file_path,max_file_size=10485760)

from abc import ABC, abstractmethod

class FeatureEngine(ABC):
    """特征工程总类"""
    
    cls_dict = {}
    
    def __init__(self):
        """特征工程总体步骤,
        1. 读取文件
        2. 数据分类:类别编码，日期处理，数字归一化 
        
        
        """
        
        pass
    
    # @abstractmethod
    def feature_cls(self, df, identity, date_type=[], num_type=[], classify_type=[], bool_type=[]):
        """特征分类，本方法只是一个例子，具体有哪些类别，如何分区数字的类型，要看具体的数据; 子类必须实现这个方法
        - 分区数字与类别特征，并对类别特征embedding
        - identity: 标识列
        - date_type     #本流程无日期特征列
        - num_type      #连续型变量
        - bool_type     #只有0与1，在本流程中看作分类数据，即二分类，不参与归一化处理
        - classify_type  #分类，类别 类型 
        
        return 
        --------------------------- 
        - feature_cols:特征列，除去identity剩下的列 
        """
        column_all = df.columns
        
        lg(f"df.info()1:\n{df.info()}")

        #除去标识列，剩下的是特征列
        feature_cols = list(set(column_all)-set(identity))

        pc = ParamConfig(identity, num_type, bool_type, date_type, classify_type)
        pc.feature_cols = feature_cols
        

        lg(f"df.info()2:\n{df.info()}")
        
        ### 日期处理
        dtl.date_deal(df,date_type=date_type)
        
        lg(f"df.info()3:\n{df.info()}")

        ### 数字处理
        dtl.num_deal(df,num_type=num_type)
        
        lg(f"df.info()4:\n{df.info()}")
    
        ### 字符处理,若classify_type为空则会使用排除法确定类别列 
        dtl.str_deal(df, pc, classify_type=classify_type)
        
        lg(f"df.info()5:\n{df.info()}")
        
        # 在SVM,LR中可将布尔看作数字，在lgbm中看作分类更好，作为参数传入模型调用，视情况而用
        pc.col_type.classify_type = pc.col_type.classify_type+pc.col_type.bool_type
        
        return df,pc 
    
    def data_type_change(self, data, num_type,classify_type,date_type):
        """针对数字，类型，日期列进行类型转换"""
        df = dtl.data_type_change(data,num_type,classify_type,date_type)
        return df 

    
    @staticmethod 
    def cls2index(df, classify_type=[],word2id=None):
        """类别转索引"""
        dtl.str_pd(df,classify_type)
        tt = TextDeal(data=df)
        df,cls_dict = tt.word2id(classify_type,word2id=word2id)
        FeatureEngine.cls_dict.update(cls_dict)
        return  df,cls_dict 
    
    @staticmethod 
    def cls2index_pre(df, classify_type, word2id):
        """类别转索引预测"""
        dtl.str_pd(df,classify_type)
        tt = TextDeal(data=df)
        tt.word2id_pre(classify_type,word2id=word2id)
    
    @classmethod
    def col2index(cls,df,classify_type,classify_type2=[],dict_file="dict_file.dict",is_pre=False,word2id=None):
        tte.col2index(df,classify_type=classify_type,
            classify_type2=classify_type2,
            dict_file=dict_file,
            is_pre=is_pre,
            word2id=word2id,) 
    
    
    @staticmethod 
    def min_max_scaler(df, num_type=[], model_path=f"min_max_scaler.pkl", reuse=False,
                       log=False,log2=False,log10=False):
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
        
        if log:
            df[num_type] = df[num_type].clip(lower=1)
            df.loc[:,num_type] = torch.log(torch.tensor(df[num_type].values, dtype=torch.float32)).numpy()
        if log2:
            df[num_type] = df[num_type].clip(lower=1)
            df.loc[:,num_type] = torch.log2(torch.tensor(df[num_type].values, dtype=torch.float32)).numpy()
        if log10:
            df[num_type] = df[num_type].clip(lower=1)
            df.loc[:,num_type] = torch.log10(torch.tensor(df[num_type].values, dtype=torch.float32)).numpy()
        
        dtl.min_max_scaler(df, num_type=num_type, model_path=model_path, reuse=reuse)

    @staticmethod
    def min_max_update(df, num_type=[],is_pre=False, num_scaler_file=None,
                       log=False,log2=False,log10=False):
        dtl.min_max_update(df,num_type=num_type, is_pre=is_pre, num_scaler_file=num_scaler_file,
                           log=log,log2=log2,log10=log10)

    @staticmethod
    def min_max_date(df, date_type=[], scaler_file=None, max_date=None, adjust=True):
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
        df = dtl.min_max_scaler_dt(df, date_type=date_type, 
                                        scaler_file=scaler_file,
                                        max_date=max_date, adjust=adjust)
        return df 
       

        
class Fe(FeatureEngine):
    def __init__(self):
        """自定义特征工程类示例"""
        self.cls_dict = FeatureEngine.cls_dict
        
    def feature_cls(self, df, identity, date_type=[], num_type=[], classify_type=[], bool_type=[]):
        """特征分类，本方法只是一个例子，具体有哪些类别，如何分区数字的类型，要看具体的数据; 子类必须实现这个方法
        - 分区数字与类别特征，并对类别特征embedding
        - identity: 标识列
        - date_type     #本流程无日期特征列
        - num_type      #连续型变量
        - bool_type     #只有0与1，在本流程中看作分类数据，即二分类，不参与归一化处理
        - classify_type  #分类，类别 类型 
        
        return 
        --------------------------- 
        - feature_cols:特征列，除去identity剩下的列 
        """
        
        column_all = df.columns

        #除去标识列，剩下的是特征列
        feature_cols = list(set(column_all)-set(identity))

        pc = ParamConfig(identity, num_type, bool_type, date_type, classify_type)
        pc.feature_cols = feature_cols

        ### 日期处理
        dtl.date_deal(df,date_type=date_type)
        

        ### 数字处理
        dtl.num_deal(df,num_type=num_type)
        
    
        ### 字符处理,若classify_type为空则会使用排除法确定类别列 
        dtl.str_deal(df, pc, classify_type=classify_type)
        
        
        # 在SVM,LR中可将布尔看作数字，在lgbm中看作分类更好，作为参数传入模型调用，视情况而用
        pc.col_type.classify_type = pc.col_type.classify_type+pc.col_type.bool_type

        return df,pc 
    

    


def data_pre_update(df, identity, date_type, num_type, classify_type, classify_type2=[], bool_type=[],
                  save_file=None,dict_file=None,is_num_std=True, 
                  is_pre=False,num_scaler_file="scaler_num.pkl",
                  date_scaler_file="scaler_date.pkl", max_date='2035-01-01'):
    """对于数字及类别编码，在训练阶段是会自动更新字典的;适用于数据集不全，不断收集批次数据的极值
    - 日期归一化，有文件会自动应用
    - 类型归一化，需要指定is_pre=False
    - classify_type2:多列共用一个字典时，其元素为共用同一个字典的列的列表
    - num_scaler_file:如果文件已存在且是训练阶段，则更新元素的极值 
    
    """
    if save_file and os.path.exists(save_file):
        df = pd.read_csv(save_file)
        return df 
    
    if dict_file is None:
        raise Exception("请输入字典文件dict_file的路径")

    fe = Fe()
    
    #字段分类
    print(f"classify_type={classify_type}")
    df = fe.data_type_change(df, num_type=num_type,classify_type=classify_type,date_type=date_type)
    print(df.info())
    

    #类型字段索引编码,如果是训练则保存字典
    fe.col2index(df,classify_type=classify_type,
                classify_type2=classify_type2,
                dict_file=dict_file,
                is_pre=is_pre,
                word2id=None)


    ## 数字归一化
    if is_num_std:
        # fe.min_max_scaler(df, num_type=pc.col_type.num_type, model_path=num_scaler_file, reuse=True,log10=True)
        fe.min_max_update(df, num_type=num_type,num_scaler_file=num_scaler_file, is_pre=is_pre,log10=True)

    if date_scaler_file is not None or max_date is not None:
        ## 日期归一化
        df = fe.min_max_date(df,
            date_type=date_type,
            scaler_file=date_scaler_file,
            max_date=max_date,
            adjust=True)

    if save_file:
        df.to_csv(save_file,index=False)
    
    return df 

