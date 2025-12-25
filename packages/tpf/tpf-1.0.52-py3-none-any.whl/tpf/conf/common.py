
import os
from tpf import log 
from tpf import pkl_load,pkl_save,filname_nosuffix
from tpf.box.fil import parentdir 

class CommonConfig: 
    
    train_log_path = '/tmp/train.log'
    alg_model_dir  = '/ai/data/model'
    max_file_size  = 10485760
    
    def __init__(self, usedb=False):
        if usedb:
            pass  
        
    def set_log_path(self,log_path):
        self.train_log_path = log_path  
        
    def set_log_size(self,max_file_size):
        self.max_file_size = max_file_size
        
    def lg(self, msg):
        log(msg,fil=self.train_log_path,max_file_size=self.max_file_size)
        


class ColumnTu:
    nodeid     = 'Account'
    label_name = 'Label'
    feature_cols   = []
    from_col     = 'Account'
    to_col      = 'Account.1'
    time_col   = 'Timestamp'

class ColumnType:
    def __init__(self):
        self.identity= []           # 标识表
        self.num_type = []          # 数字类
        self.num_small = []         # 小数字类,大量低于1的数字
        self.bool_type = []         # 布尔类
        self.date_type = []         # 日期类
        self.classify_type=[]       # 类别
        
        self.classify_type2 = [[]]  #一组类别使用同一个字典
        self.classify_type_pre = []  #预测时的类别列

        
        self.feature_names = []     # 特征组合列
        self.feature_names_num= []  # 特征组合列之数字特征
        self.feature_names_str=[]   # 特征组合列之类别特征
        self.feature_logical_types={}
    
class ParamConfig(CommonConfig):
    
    #为每个表定义一个列对象，有字符串，数字，日期，标识,布尔等类列表，便于处理过程中获取对应表的字段
    col_type = ColumnType()               #特征类型
    tu       = ColumnTu()
    
    alg_type        = "lgbmc"
    model_save_dir  = "./"
    model_num       = 100
    label_name      = None
    
    max_date        = '2035-01-01'
    drop_cols       = []
    log10_transform =True
    
    is_train        = True
    file_num        = 1
    log10_transform =False
    is_merge_identity = False
    
    def __init__(self,usedb=False):
        super().__init__(usedb=usedb)

    
    def is_pre(self):
        return not self.is_train
    
    def data_deal_model_path(self):
        return os.path.join(self.model_save_dir,f"{self.alg_type}_dtmodel_{self.file_num}_{self.model_num}.pkl")

    def dict_file(self):
        return os.path.join(self.model_save_dir,f"{self.alg_type}_dictfile_{self.file_num}_{self.model_num}.dict")

    def num_scaler_file(self):
        return os.path.join(self.model_save_dir,f"{self.alg_type}_scaler_{self.file_num}_{self.model_num}.pkl")

    def date_scaler_file(self):
        return os.path.join(self.model_save_dir,f"{self.alg_type}_scaler_date_{self.file_num}_{self.model_num}.pkl")
    
    def model_param_path(self):
        return os.path.join(self.model_save_dir,f"{self.alg_type}_{self.model_num}.pkl")


    def pre_save_path(self,data_path):
        feature_file_name = filname_nosuffix(data_path)
        file_save_dir = parentdir(data_path)
        file_save_path = os.path.join(file_save_dir, feature_file_name+"_"+self.alg_type+"_"+f"{self.model_num}_pre.csv")
        return file_save_path

    def train_msg_path(self):
        file_path = os.path.join(self.model_save_dir,f"{self.alg_type}_{self.model_num}.msg")
        return file_path