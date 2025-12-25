import sys 
import torch 
from torch import nn 
from torch.nn import functional as F 
import numpy as np
from sklearn.metrics import accuracy_score,roc_auc_score, confusion_matrix, classification_report, roc_curve, auc,f1_score

from tpf.mlib.models import MLib
from tpf.d1 import is_single_label
from tpf.mlib.seq import SeqOne 

from torch.utils.data import Dataset
from torch.utils.data import DataLoader 

import pandas as pd 

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

# class ModelPre():
#     """模型预测
#     - 统计由predict_probs方法实现
#     - 无此方法的，通过添加方法转化为该方法，目前只有lightgbm出现了无此API的情况
#     """

#     @classmethod
#     def predict_proba(cls, data, model_path=None, model_type=None, model=None,batch_size=0):
#         """二分类模型，根据模型的路径加载模型，然后预测
#         - model_type: 可选参数有["lgbm","lightgbm", None]，即是lgbm or 不是
#         - model:具体的模型对象，此时仅返回
#         - batch_size:深度学习是否使用批次预测，若是则填写一次预测多少行数据
#         """
#         y_probs = []

#         if model is None and model_type is not None:    # 机器学习
#             if model_type.lower() in ["lgbm","lightgbm"]:
#                 y_probs = cls.lgbm_predict_proba(data, model_path=model_path)
#             elif model_type.lower() in ["seqone","seqonedl"]:
#                 model = SeqOne(seq_len=data.shape[1], out_features=2)
#                 y_probs = cls.cls2_dl_proba(data, model_path=model_path, model=model, batch_size=100000)
#             else:  # 二分类，概率返回
#                 y_probs = cls.cls2_predict_proba(data, model_path=model_path)

#             if len(y_probs) > 0 and isinstance(y_probs[0], np.int64):
#                 raise Exception(f"期望返回浮点型概率，但目前返回的是Int64类型的标签:{y_probs[0]}")
#             return y_probs
#         elif model is not None and model_type is None:  #深度学习
#             model = SeqOne(seq_len=data.shape[1], out_features=2)
#             y_probs = cls.cls2_dl_proba(data, model_path=model_path, model=model, batch_size=100000)
#             return y_probs
#         else:
#             if hasattr(model, 'predict_proba') and callable(getattr(model, 'predict_proba')):
#                 print("obj has a callable my_method")
#                 y_porbs = model.predict_proba(data)
#                 if isinstance(y_porbs, np.ndarray) and y_porbs.ndim == 1:
#                     return y_porbs
#                 return y_porbs[:, 1]
#             else:
#                 raise Exception("仅支持predict_proba方法调用")


#     @classmethod
#     def lgbm_predict_proba(cls, data, model_path=None):
#         """二分类问题
#         """
#         model_lgbm = MLib.model_load(model_path=model_path)
#         y_porbs = model_lgbm.predict(data)
#         return y_porbs

#     @classmethod
#     def cls2_predict_proba(cls, data, model_path=None):
#         """二分类问题
#         - 适用返回2列概率的场景，包括深度学习
#         """
#         model = MLib.model_load(model_path=model_path)
#         y_porbs = model.predict_proba(data)
#         if isinstance(y_porbs, np.ndarray) and y_porbs.ndim == 1:
#             return y_porbs
#         return y_porbs[:, 1]
#     @classmethod
#     def cls2_dl_proba(cls, data, model_path=None,model=None,batch_size=0):
#         """二分类问题,深度学习预测,为1的概率值
#         - 适用返回2列概率的场景，包括深度学习
#         """
#         if model_path is None:
#             print("the model_path should not be None")
#             sys.exit()
#         device = "cuda:0" if torch.cuda.is_available() else "cpu"
#         model = MLib.model_load(model_path=model_path, model=model)
#         model.to(device=device)
#         model.eval()
#         with torch.no_grad():
#             if batch_size > 0 :
#                 dataset = XDataset(X=data)
#                 dataloader = DataLoader(dataset=dataset,shuffle=False,batch_size=batch_size)
#                 i = 0 
#                 for X in dataloader:
#                     X=X.to(device=device)
#                     y_pred = model(X)
#                     if i ==0:
#                         y_porbs = y_pred.cpu()
#                     else:
#                         y_porbs = torch.cat((y_porbs,y_pred.cpu()),dim=0)
#                     i=i+1
#                 y_porbs = np.array(y_porbs)

#             else:
#                 X=data.to(device=device)
#                 y_pred = model(X)
#                 y_porbs = y_pred.cpu().detach().numpy()
                
#             y_pred = F.softmax(y_pred,dim=1)

#         if isinstance(y_porbs, np.ndarray) and y_porbs.ndim == 1:
#             return y_porbs
 
#         return y_porbs[:, 1]


# def model_evaluate(y_probs, y_test):
#     """模型评估
#     params
#     -------------------------------------------------------
#     - y_probs:模型概率输出,1维，每个元素为 标签1的概率，即正样本概率列表
#     - y_test:真实标签，1维

#     return
#     -------------------------
#     - acc,precision,recall,f1,auc ,依次为准确率，精确率，召回率，f1值，AUC
#     - 其中精确率，召回率只针对 正样本-1

#     examples
#     --------------------------------------------------------
#     acc,precision,recall,f1,auc  = model_evaluate(y_probs,y_test)
#     """
#     if y_probs.ndim != 1:
#         raise Exception(f"y_probs必须为1维，实际为{y_probs.ndim}维")
#     # 定义预测结果：概率>0.5则预测结果为 1 即可疑；概率<=0.5则预测结果为0 即不可疑
#     y_pred = np.where(y_probs > 0.5, 1, 0)
#     is_single_value = is_single_label(y_test, y_pred)
#     if is_single_value:
#         roc_auc = 1
#     else:
#         # auc = roc_auc_score(y_test, y_pred)
#         # 计算ROC曲线和AUC值
#         fpr, tpr, thresholds = roc_curve(y_test, y_probs)
#         roc_auc = auc(fpr, tpr)

#     conf_matrix = confusion_matrix(y_test, y_pred)
#     acc = (conf_matrix[0, 0] + conf_matrix[1, 1]) / (
#                 conf_matrix[0, 0] + conf_matrix[1, 0] + conf_matrix[0, 1] + conf_matrix[1, 1])

#     # 对正样本的预测精度
#     pre_1 = conf_matrix[0, 1] + conf_matrix[1, 1]
#     true_1 = conf_matrix[1, 0] + conf_matrix[1, 1]
#     if pre_1 == 0 and true_1 > 0:  # 真实1个数不为0，但预测为1的个数为0，则精确率为0
#         precision = 0
#     elif pre_1 == 0:  # 预测可疑样本数为0 这个很可能会出现  比如一批样本中真的就没有可疑的 模型本身预测正样本的能力也差
#         precision = 1
#     else:
#         precision = float(conf_matrix[1, 1]) / pre_1

#     # Recall 召回率
#     real_1_num = conf_matrix[1, 0] + conf_matrix[1, 1]
#     if real_1_num == 0:  # 即真实的可疑样本个数为0，即一批样本中的数据都是正常的
#         recall = 1
#     else:
#         recall = float(conf_matrix[1, 1]) / real_1_num

#     f1 = 2 / (1 / (precision + 1e-6) + 1 / (recall + 1e-6))

#     # 保留2位有效数字
#     acc = np.around(acc, decimals=4)
#     precision = np.around(precision, decimals=4)
#     recall = np.around(recall, decimals=4)
#     f1 = np.around(f1, decimals=4)
#     roc_auc = np.around(roc_auc, decimals=4)

#     # 默认AI预测达不到1 即达不到100%准确,最多99%
#     if acc >= 1:
#         acc = 0.9999
#     if precision >= 1:
#         precision = 0.9999
#     if recall >= 1:
#         recall = 0.9999
#     if f1 >= 1:
#         f1 = 0.9999
#     if roc_auc >= 1:
#         roc_auc = 0.9999
#     return acc, precision, recall, f1, roc_auc


# class ModelEval():
#     def __init__(self):
#         pass

#     @staticmethod
#     def evaluate(y_probs, y_test):
#         """模型评估
#         params
#         -------------------------------------------------------
#         - y_probs:模型概率输出,1维，每个元素为 标签1的概率，即正样本概率列表
#         - y_test:真实标签，1维

#         return
#         -------------------------
#         - acc,precision,recall,f1,auc ,依次为准确率，精确率，召回率，f1值，AUC
#         - 其中精确率，召回率只针对 正样本-1

#         examples
#         --------------------------------------------------------
#         acc,precision,recall,f1,auc  = me.evaluate(y_probs,y_test)

#         """
#         return model_evaluate(y_probs, y_test)

#     @staticmethod
#     def confusion_matrix(y_probs, y_test):
#         """

#         examples
#         ------------------------------------
#         ## 混淆矩阵
#         confusion_matrix = me.confusion_matrix(y_probs,y_test)
#         print("\nconfusion_matrix:\n",confusion_matrix)


#                     pre
#                     0  1
#         real    0
#                 1
#         """
#         if y_probs.ndim != 1:
#             raise Exception(f"y_probs必须为1维，实际为{y_probs.ndim}维")
#         # 定义预测结果：概率>0.5则预测结果为 1 即可疑；概率<=0.5则预测结果为0 即不可疑
#         y_pred = np.where(y_probs > 0.5, 1, 0)
#         is_single_value = is_single_label(y_test, y_pred)
#         if is_single_value:
#             roc_auc = 1
#         else:
#             # auc = roc_auc_score(y_test, y_pred)
#             # 计算ROC曲线和AUC值
#             fpr, tpr, thresholds = roc_curve(y_test, y_probs)
#             roc_auc = auc(fpr, tpr)
#         if isinstance(y_test, pd.DataFrame):
#             print("label value count:\n", y_test.value_counts())
#         else: 
#             y_label = pd.DataFrame(y_test, dtype=np.int32)
#             print("label value count:\n", y_label.value_counts())
            
#         conf_matrix = confusion_matrix(y_test, y_pred)
#         return conf_matrix

#     @staticmethod
#     def classification_report(y_probs, y_test):
#         """分类报告

#         examples
#         ----------------------------------------------------
#         ## 分类报告
#         print("\nclassification_report:\n",me.classification_report(y_probs,y_test))

#         """
#         y_pred = np.where(y_probs > 0.5, 1, 0)
#         report = classification_report(y_test, y_pred)
#         return report

