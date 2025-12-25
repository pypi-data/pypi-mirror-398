
import sys
# import shap
import joblib
# import torch 
# from torch import nn 

import numpy as np
from tpf.mlib.copod import COPODModel
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
# import shap
import joblib

import numpy as np 

from tpf.mlib import MLib as ml
from tpf import pkl_load,pkl_save
# from tpf.dl import T11
# from tpf.dl import DataSet11

# Check if torch is available
try:
    import torch
    from torch.nn import functional as F
    from torch.utils.data import Dataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


from tpf.nlp import ClsIndexEmbed
from tpf.mlib.modelbase import ModelBase

class MyModel():
    def __init__(self, model_path, alg_type):
        """统一算法模型处理
        - 因有多种算法模型，这里统一模型的预测方法为predict_proba
        - 仅输出0-1二分类问题中1-异常类别的概率
        """
        self.model_path = model_path
        self.alg_type   = alg_type
        
        
    def predict_proba(self, X):
        y_probs = ModelPre.predict_proba(X, model_path = self.model_path, model_type=self.alg_type)
        return y_probs

# Define XDataset only if torch is available
if TORCH_AVAILABLE:
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
else:
    XDataset = None

class ModelPre(ModelBase):
    
    _lgbm_name_list = ["LightGBM".lower(),"lgbm"]
    _lgbmc_name_list = ["LGBMClassifier".lower(),"lgbmc"]
    _lr = ["lr","logisticregression"]

    # @classmethod
    # def model_load(cls,model_path, model=None, params=None):
    #     """深度学习参数文件以.dict保存 
    #     """
    #     if model_path.endswith(".dict"):
    #         if model is None:
    #             if "seqone" in model_path.lower():
    #                 seq_len    = params["seq_len"]
    #                 model = SeqOne(seq_len=seq_len, out_features=2)
    #         model.load_state_dict(torch.load(model_path,weights_only=False))
    #     else:
    #         model = pkl_load(file_path=model_path, use_joblib=True)
    #     return model

    # @staticmethod
    # def model_save(model, model_path):
    #     if model_path.endswith(".dict"):
    #         torch.save(model.state_dict(), model_path)
    #     else:
    #         pkl_save(model, file_path=model_path, use_joblib=True)

    @staticmethod
    def cls_embedding(df,embed_file_pre,cls_dim_dict = {
            'is_luobo': 3,
            'is_qiche': 2
        },log_func=None):
        """#类别数据Embedding
        """

        cie = ClsIndexEmbed(file_pre=embed_file_pre, log_func=log_func, nan_to_zero=True)
        df =cie(df,cls_dim_dict)
        
        # 按列名的升序重新排列
        df = df.sort_index(axis=1)

        return df,cie.category_list

    
    @classmethod
    def predict_proba(cls, data, model_path=None, 
                      model_type=None,model=None,cat_features=None):
        """二分类模型，根据模型的路径加载模型，然后预测

        该方法提供统一的二分类概率预测接口，支持多种机器学习和深度学习模型。
        对于二分类问题，始终返回类别1（异常类别）的概率值。

        Args:
            data: 输入数据，可以是numpy数组、pandas DataFrame或torch张量
            model_path: 模型文件路径，支持.pkl、.joblib、.dict等格式
            model_type: 模型类型，可选值包括：
                       - "lgbm"/"lightgbm": LightGBM模型
                       - "seqone"/"seqonedl": 深度学习序列模型
                       - None: 其他通用模型（如SVC、XGBoost、CatBoost等）
            model: 已加载的模型对象，如果提供则直接使用该对象进行预测
            cat_features: 类别特征列表，仅对LightGBM模型有效，用于指定哪些特征是类别型

        Returns:
            numpy.ndarray: 返回每个样本属于类别1（异常类别）的概率值，形状为(n_samples,)

        Raises:
            Exception: 当模型返回Int64类型标签而非概率时抛出异常
            Exception: 当模型不支持predict_proba方法时抛出异常

        Note:
            - 对于深度学习模型，自动检测并使用GPU（如果可用）
            - 对于LightGBM模型，会自动处理类别特征的类型转换
            - 批量预测时，对于大数据集会使用DataLoader进行内存优化
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
                y_probs = cls.lgbm_predict_proba(data, model_path=model_path,cat_features=cat_features)
            elif model_type.lower() in ["seqone","seqonedl"]:
                model = SeqOne(seq_len=data.shape[1], out_features=2)
                y_probs = cls.cls2_dl_proba(data, model_path=model_path, model=model, batch_size=0)
            else:  # 二分类，概率返回
                if model_type.lower() in cls._lr:
                    data = np.array(data)
                y_probs = cls.cls2_predict_proba(data, model_path=model_path)

            if len(y_probs) > 0 and isinstance(y_probs[0], np.int64):
                raise Exception(f"期望返回浮点型概率，但目前返回的是Int64类型的标签:{y_probs[0]}")
            return y_probs

        elif model_type and model_type.lower() == "seqone":  #深度学习
            model = SeqOne(seq_len=data.shape[1], out_features=2)
            y_probs = cls.cls2_dl_proba(data, model_path=model_path, model=model, batch_size=100000)
            return y_probs
        elif model_type and model_type.lower() in cls._dlbase:  #深度学习
            y_probs = cls.cls2_dl_proba(data, model_path=model_path, model=model, batch_size=100000)
            return y_probs

        else:
            if hasattr(model, 'predict_proba') and callable(getattr(model, 'predict_proba')):
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
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is not installed. Please install torch to use deep learning functionality.")

        import torch
        from torch.nn import functional as F
        from torch.utils.data import DataLoader

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
                if XDataset is None:
                    raise ImportError("XDataset class is not available. Please install torch to use batch processing.")
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
        import shap
        
        if data.ndim != 2:
            raise Exception("数据输入必须为2维")
        params = {}
        params["seq_len"] = data.shape[1]
        # model = joblib.load(model_path)
        model = ModelPre.model_load(model_path,params=params)
 
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

