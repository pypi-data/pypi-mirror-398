



import pandas as pd 
import numpy as np 
import joblib
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import PowerTransformer

class COPODModel():
    def __init__(self, contamination=0.05,scale_func=None):
        """
        params
        ----------------------------------------------------
        - contamination:预计的离群数据比例
        - scale_func归一化方法

        examples
        -----------------------------------------------------
        model = COPODModel(contamination=0.05)
        model.predict_proba(X = data_scaled)
        """
        self.contamination = contamination 
        self.scale_func = scale_func
        

    def predict_proba(self, X):
        from pyod.models.copod import COPOD
        model = COPOD(contamination=self.contamination)
        model.fit(np.array(X))
        scaler = MinMaxScaler()
        copod_scores_2d = model.decision_scores_.reshape(-1,1)
        
        # 分数进行box-cox转换，该方法只能对正数进行转换，经常报错
        # pt = PowerTransformer(method = 'box-cox')
        # copod_scores_i_boxcox = pt.fit_transform(copod_scores_2d)
        
        if self.scale_func is None:
            # 直接使用MinMaxScaler进行归一化
            copod_scores_nol = scaler.fit_transform(copod_scores_2d).flatten()
        else:
            copod_scores_nol = self.scale_func(copod_scores_2d)
            
        return copod_scores_nol
    


exampel = """

from sklearn.preprocessing import StandardScaler
def generate_data(n_normal=100, n_anomalies=10):
    normal_data = np.random.normal(loc=0, scale=1, size=(n_normal, 2))
    anomaly_data = np.random.normal(loc=5, scale=0.5, size=(n_anomalies, 2))
    return np.vstack((normal_data, anomaly_data))

data = generate_data()

# 数据预处理（标准化）
scaler = StandardScaler()
data_scaled = scaler.fit_transform(data)


model = COPODModel(contamination=0.05)
model.predict_proba(X = data_scaled)

"""