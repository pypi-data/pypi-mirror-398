import numpy as np 



class ColumnType:
    def __init__(self):
        self.identity= []           # 标识表
        self.num_type = []          # 数字类
        self.bool_type = []         # 布尔类
        self.date_type = []         # 日期类
        self.classify_type=[]       # 类别
        
        self.feature_names = []     # 特征组合列
        self.feature_names_num= []  # 特征组合列之数字特征
        self.feature_names_str=[]   # 特征组合列之类别特征
        self.feature_logical_types={}


class ParamConfig:
    """有监督参数配置：乳腺癌数据集
    - 主要是人工划分表字段的类型，现分数字，布尔，标识，字符串，日期等类型
    - 因为要将表的字段归类，因此 一张模型输入表对应一个配置
    """
    v_date                   = None #验证集划分日期，不是所有的数据集都有跨周期验证
    label_name               = None
    feature_num_boost_round  = 10   #特征评估选择特征时lgbm训练的轮次
    max_feature_selected_num = 200
    corr_line                = 0.95 #特征评估，共线性分析时，两个特征去重的相似标准
    
    model_id                 = 'lr'+str(11)   #AI中算法ID
    
    data_feature_selected_path = None

    flag_padding = '<PAD>'
    feature_flag = None
    scale_type = ['min_max_scale','std_scale']
    
    #为每个表定义一个列对象，有字符串，数字，日期，标识,布尔等类列表，便于处理过程中获取对应表的字段
    col_type = ColumnType()               #特征类型

    
    def __init__(self , identity, num_type, bool_type, date_type, classify_type):
        """字段分类：明确字段的类型，以便于算法处理
        - 标识类，比如ID，卡号，账户号
        - 布尔类，1与0
        - 时间类，日期类型字段
        - 数字类，数字类型字段
        - 其余全部默认为字符串类型
        
        - 手工在该方法中写上表的标识字段，日期字段，数字字段，剩下的由代码计算出字符串字段
        """

        #表所有身份标识类字段
        self.cname_str_identity = identity
        self.col_type.identity = identity
        self.col_type.num_type  = num_type
        self.col_type.classify_type = classify_type
        self.col_type.bool_type = bool_type
        self.col_type.date_type = date_type
        
        
        #特征选择保存路径
        self.feature_select_save_path = f"model/feature_select_{self.model_id}.pkl"
        
        #这里为了方便，每个模型算法与批次固定一个文件，不考虑特征选择的差异
        self.model_save_path = f"{self.model_id}.pkl"
        self.data_feature_selected_path = f"{self.model_save_path}.feature"
        
        