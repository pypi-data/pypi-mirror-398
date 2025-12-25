
import sys
import shap
import joblib
import torch 
from torch import nn 

import numpy as np
from tpf.mlib import COPODModel
from tpf.mlib import MLib as ml

from tpf.mlib.seq import SeqOne 
from tpf import pkl_load,pkl_save 

def dataset_pre(data_pd, cat_features):
    cat_features = list(set(cat_features))
    data_pd[cat_features] = data_pd[cat_features].astype("category") 
    return data_pd

class MyModel():
    def __init__(self, model_path, alg_type):
        self.model_path = model_path
        self.alg_type = alg_type

    def predict_proba(self, X):
        y_probs = MyModel.predict_proba(X, model_path=self.model_path, model_type=self.alg_type)
        return y_probs



import sys 
import shap
import joblib

import numpy as np 

from tpf.mlib import MLib as ml
from tpf import pkl_load,pkl_save
# from tpf.dl import T11
# from tpf.dl import DataSet11

import torch 
from torch import nn 
from torch.nn import functional as F 
from torch.utils.data import Dataset
from torch.utils.data import DataLoader 

from leadingtek.ai.algorithm.lightgbm import dataset_pre 
from leadingtek.ai.algorithm.lightgbm import lgbm_01 
from leadingtek.ai.algorithm.lightgbm import lgbmc_01 
from leadingtek.ai.algorithm.tree.xgbc import xgbc_01
from leadingtek.ai.algorithm.tree.catboost import catboostc_01
from leadingtek.ai.algorithm.svm import svc_01
from leadingtek.ai.algorithm.copod import COPODModel
from leadingtek.ai.algorithm.dl import SeqOne 
from leadingtek.ai.algorithm.dl.train import T11,DataSet11 
from leadingtek.ai.algorithm.common import ClsIndexEmbed

from leadingtek.ai.service.mydb import cls_dim,embed_file_pre

from leadingtek.conf.common import CommonConfig
cm = CommonConfig()

class MyModel():
    def __init__(self, model_path, alg_type):
        """统一算法模型处理
        - 因有多种算法模型，这里统一模型的预测方法为predict_proba
        - 仅输出0-1二分类问题中1-异常类别的概率
        """
        self.model_path = model_path
        self.alg_type   = alg_type
        
        
    def predict_proba(self, X):
        y_probs = AM.predict_proba(X, model_path = self.model_path, model_type=self.alg_type)
        return y_probs

class XDataset(Dataset):
    def __init__(self, X):
        super().__init__()
        self.X = X 
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        x = self.X[idx]
        if isinstance(x,torch.Tensor):
            return x.float()
        return torch.tensor(x).float()

class ModelPre():
    
    _lgbm_name_list = ["LightGBM".lower(),"lgbm"]
    _lgbmc_name_list = ["LGBMClassifier".lower(),"lgbmc"]

    @classmethod
    def model_load(cls,model_path, model=None, params=None):
        """深度学习参数文件以.dict保存 
        """
        if model_path.endswith(".dict"):
            if model is None:
                if "seqone" in model_path.lower():
                    seq_len    = params["seq_len"]
                    model = SeqOne(seq_len=seq_len, out_features=2)
            model.load_state_dict(torch.load(model_path,weights_only=False))
        else:
            model = pkl_load(file_path=model_path, use_joblib=True)
        return model

    @staticmethod
    def model_save(model, model_path):
        if model_path.endswith(".dict"):
            cm.lg(f"深度学习模型参数保存...{model_path}")
            torch.save(model.state_dict(), model_path)
        else:
            pkl_save(model, file_path=model_path, use_joblib=True)

    @staticmethod
    def cls_embedding(df,bsn_model_id):
        cm.lg(f"embed_file_pre={embed_file_pre}")
        
        #类别数据Embedding 
        cls_dim_dict = cls_dim(bsn_model_id)
        cm.lg(f"cls_dim_dict:{cls_dim_dict}")
        
        cie = ClsIndexEmbed(file_pre=embed_file_pre, log_func=cm.lg, nan_to_zero=True)
        df =cie(df,cls_dim_dict)
        
        # 按列名的升序重新排列
        df = df.sort_index(axis=1)

        return df,cie.category_list



    
    @classmethod
    def predict_proba(cls, data, model_path=None, model_type=None,model=None,cat_features=None):
        """二分类模型，根据模型的路径加载模型，然后预测
        - model_type: 可选参数有["lgbm","lightgbm", None]，即是lgbm or 不是
        - model:具体的模型对象，此时仅返回
        """
        y_probs = []

        # if model is None:
        #     if model_type is None:
        #         y_probs = cls.cls2_predict_proba(data, model_path=model_path)
        #     elif model_type.lower() in ["lgbm","lightgbm"]:
        #         y_probs = cls.lgbm_predict_proba(data, model_path=model_path,cat_features=cat_features)
        #     else:  # 二分类，概率返回
        #         y_probs = cls.cls2_predict_proba(data, model_path=model_path)

        #     if len(y_probs) > 0 and isinstance(y_probs[0], np.int64):
        #         raise Exception(f"期望返回浮点型概率，但目前返回的是Int64类型的标签:{y_probs[0]}")
        #     return y_probs

        if model is None and model_type is not None:    # 机器学习
            if model_type.lower() in ["lgbm","lightgbm"]:
                y_probs = cls.lgbm_predict_proba(data, model_path=model_path)
            elif model_type.lower() in ["seqone","seqonedl"]:
                model = SeqOne(seq_len=data.shape[1], out_features=2)
                y_probs = cls.cls2_dl_proba(data, model_path=model_path, model=model, batch_size=0)
            else:  # 二分类，概率返回
                y_probs = cls.cls2_predict_proba(data, model_path=model_path)

            if len(y_probs) > 0 and isinstance(y_probs[0], np.int64):
                raise Exception(f"期望返回浮点型概率，但目前返回的是Int64类型的标签:{y_probs[0]}")
            return y_probs
        elif model is not None and model_type is None:  #深度学习
            model = SeqOne(seq_len=data.shape[1], out_features=2)
            y_probs = cls.cls2_dl_proba(data, model_path=model_path, model=model, batch_size=100000)
            return y_probs

        else:
            if hasattr(model, 'predict_proba') and callable(getattr(model, 'predict_proba')):
                print("obj has a callable my_method")
                y_porbs = model.predict_proba(data)
                if isinstance(y_porbs, np.ndarray) and y_porbs.ndim == 1:
                    return y_porbs
                return y_porbs[:, 1]
            else:
                raise Exception("仅支持predict_proba方法调用")


    @classmethod
    def lgbm_predict_proba(cls, data, model_path,cat_features=None):
        """二分类问题
        """
        model_lgbm = joblib.load(model_path)
        if cat_features is None:
            y_porbs = model_lgbm.predict(data)
        else:
            data = dataset_pre(data_pd=data, cat_features=cat_features)
            y_porbs = model_lgbm.predict(data)
            
        return y_porbs

    @classmethod
    def cls2_predict_proba(cls, data, model_path):
        """二分类问题
        - 适用返回2列概率的场景，包括深度学习
        """
        model = joblib.load(model_path)
        y_porbs = model.predict_proba(data)
        if isinstance(y_porbs, np.ndarray) and y_porbs.ndim == 1:
            return y_porbs
        return y_porbs[:, 1]

    @classmethod
    def cls2_dl_proba(cls, data, model_path=None,model=None,batch_size=0,device=None):
        """二分类问题,深度学习预测,为1的概率值
        - 适用返回2列概率的场景，包括深度学习
        """
        if model_path is None:
            print("the model_path should not be None")
            sys.exit()
        if device is None:
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
        model = cls.model_load(model_path=model_path, model=model)
        model.to(device=device)
        model.eval()
        with torch.no_grad():
            if batch_size > 0 :
                dataset = XDataset(X=data)
                dataloader = DataLoader(dataset=dataset,shuffle=False,batch_size=batch_size)
                i = 0 
                for X in dataloader:
                    X=X.to(device=device)
                    y_pred = model(X)
                    if i ==0:
                        y_porbs = y_pred.cpu()
                    else:
                        y_porbs = torch.cat((y_porbs,y_pred.cpu()),dim=0)
                    i=i+1
                y_porbs = np.array(y_porbs)

            else:
                if isinstance(data,torch.Tensor):
                    X = data 
                else:
                    X = torch.tensor(np.array(data)).float()
                    
                X=X.to(device=device)
                y_pred = model(X)
                y_porbs = y_pred.cpu().detach().numpy()
                
            y_pred = F.softmax(y_pred,dim=1)

        if isinstance(y_porbs, np.ndarray) and y_porbs.ndim == 1:
            return y_porbs

        return y_porbs[:, 1]


    @staticmethod
    def shap_value(model_path, alg_type, data, cat_features):
        """模型shap value
        - 仅针对2分类问题，做的通用处理
        """
        if data.ndim != 2:
            raise Exception("数据输入必须为2维")
        params = {}
        params["seq_len"] = data.shape[1]
        # model = joblib.load(model_path)
        model = AM.model_load(model_path,params=params)
        cm.lg(f"模型加载成功,model_path:{model_path}\nalg_type:{alg_type}")
        
        if alg_type.lower() in  AM._lgbm_name_list:
            cat_features = list(set(cat_features))
            data[cat_features] = data[cat_features].astype("category")
            # 使用SHAP解释模型
            explainer = shap.TreeExplainer(model)
            print("LightGBM using TreeExplainer")
        elif alg_type.lower() in AM._lgbmc_name_list:
            # 使用SHAP解释模型
            explainer = shap.TreeExplainer(model)
            print("LGBMClassifier using TreeExplainer")
            
        else:
            model = MyModel(model_path=model_path, alg_type=alg_type)
            explainer = shap.KernelExplainer(model.predict_proba, data)
            print("using KernelExplainer")

        _shap_values = explainer.shap_values(data)
        if _shap_values.ndim == 3:
            shap_values = _shap_values[0,:,1]
        elif _shap_values.ndim == 2 :
            shap_values = _shap_values[0]
        elif _shap_values.ndim == 1 :
            shap_values = _shap_values
        else:
            print(f"shape 维度异常,{_shap_values},可以根据第3个参数explainer自行生成shap_values")
        
        print("explainer.expected_value type:",type(explainer.expected_value))
        expected_value = explainer.expected_value
        if isinstance(expected_value,np.ndarray) and len(expected_value)>1:
            expected_value = expected_value[1]
        return expected_value,shap_values,explainer

