

import numpy as np
import pandas as pd

from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss

import lightgbm as lgb
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression

from tpf.link.toolml import pkl_load,pkl_save
from tpf.datasets import pd_ruxianai
from tpf.mlib.copod import COPODModel

    
        
    
class Link():

    def __init__(self, *args, **kwargs):
        """训练步骤/流程
        
        """
        # super(CLASS_NAME, self).__init__(*args, **kwargs)
        pass
        
    @staticmethod
    def a_readdata(file_path, split_flag=None):
        """第一步：读取数据，返回pandas数表及三种字段类型
        
        params:
        ----------------------
        - file_path: 训练所需要的数据集文件
        - split_flag: 拆分文件中一行数据的字符
        
        return
        ----------------------
        - 数据集df
        - 三类字段字段，标识，数字，布尔
        
        examples
        -----------------------------------------
        
        """
        # 读取数据 
        # df = pd_ruxianai(file_path)
        df = pd.read_csv(file_path)

        return df

    
    


