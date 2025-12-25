import numpy as np 
import pandas as pd 
import lightgbm as lgb
from sklearn.model_selection import train_test_split

from tpf import pkl_load,pkl_save
from tpf.d1 import DataDeal as dt

class Corr():
    def __init__(self,X,corr_line=0.95):
        """使用pandas中的corr方法计算特征相关性
        - X:pandas数表
        - corr_line:相关性阈值
        """
        # 计算特征之间的相关系数矩阵
        self.corr_matrix = X.corr()
        self.corr_line = corr_line
        self.columns = X.columns.tolist()

    def pairs(self):
        """展示任何两列之间的相关性
        - 'col1', 'col2', 'correlation'
        """
        # 创建一个空的DataFrame来存储两两特征之间的相关性
        corr_pairs = pd.DataFrame(columns=['col1', 'col2', 'correlation'])
        
        # 遍历相关系数矩阵的上三角（不包括对角线），记录特征对及其相关性
        col_num = len(self.corr_matrix.columns)
        for i in range(col_num):
            for j in range(i + 1, col_num):
                if corr_pairs.shape[0] == 0:
                    corr_pairs =  pd.DataFrame({
                    'col1': self.corr_matrix.columns[i],
                    'col2': self.corr_matrix.columns[j],
                    'correlation': self.corr_matrix.iloc[i, j]
                }, index=[0],columns=['col1', 'col2', 'correlation'])
                else:
                    corr_pairs_new = pd.DataFrame({
                        'col1': self.corr_matrix.columns[i],
                        'col2': self.corr_matrix.columns[j],
                        'correlation': self.corr_matrix.iloc[i, j]
                    }, index=[0], columns=['col1', 'col2', 'correlation'])
                    corr_pairs = pd.concat([corr_pairs, corr_pairs_new], ignore_index=True)
        return corr_pairs


    def high_mat(self):
        """高度相关列矩阵
        """
        # 找出相关性大于corr_line的特征对  
        high_correlation_pairs = self.corr_matrix[(self.corr_matrix > self.corr_line) & (self.corr_matrix.ne(1.0))]  
        high_correlation_pairs=high_correlation_pairs.fillna(0)
        return high_correlation_pairs

    def drop_list(self):
        """高度相关且可删除的特征名称
        - 两列相关，保留第一个特征
        """
        high_correlation_pairs = self.high_mat()
        # 遍历高相关性对，只保留其中一个特征  
        # 注意：这里假设我们总是保留第一个特征（可以根据实际情况调整）  
        features_to_drop = []  
        for index, row in high_correlation_pairs.iterrows():  
            for col in row.index[row > self.corr_line]:  
                if index < col:  # 确保我们不会重复删除（只考虑上三角或下三角）  
                    features_to_drop.append(col)  
        return list(set(features_to_drop))
    def new_list(self):
        """线性相关选择特征列
        - 去除相关性高的列之后剩下的特征列
        """
        _list = set(self.columns) - set(self.drop_list()) 
        return list(_list)
        

    def high_pairs(self,feature_name=None):
        """查看与feature_name高度相关的特征有哪些
        - feature_name：数据集中的特征名称，若不输入具体某个特征，则输出所有相关性高的特征对
        """
        corr_pairs = self.pairs()
        if feature_name is None:
            df1 = corr_pairs[corr_pairs["correlation"]>self.corr_line]
        else:
            #查询所要删除的列中的特征与哪些特征高度相关
            df1 = corr_pairs[corr_pairs["col1"].eq(feature_name)]
            df1 = df1[df1["correlation"]>self.corr_line]
        return df1.sort_values(by='correlation', ascending=False)


class FeatureEval(Corr):
    def __init__(self, X=None, corr_line=None,):
        """
        - model:树模型，如果为None则使用方法内部的模板

        examples
        ---------------------------------------
        fe = FeatureEval(X, y, num_boost_round=3)
        fe.important_features()  #特征特征重要性
        
        fe = FeatureEval(X, corr_line=0.95)
        fe.high_pairs()          #高相关性特征对
        fe.high_pairs(feature_name="mean radius") #获取指定特征的高度相关的特征对
        fe.pairs()               # 所有特征的相关性关系对
        fe.new_list()    # 去除高度相关性之后的特征列表
        
        """
        if corr_line is not None and X is not None:
            super().__init__(X,corr_line=corr_line)
  
    def important_features(self, X, y, model=None, num_boost_round=100):
        if model is None:
            if y.dtype !="int64": #分类问题，标签为整数 
                y = y.astype(np.int64)
            # 创建LightGBM数据集
            train_data = lgb.Dataset(X, label=y)
            
            # 设置参数
            params = {
                'objective': 'binary',
                'metric': 'binary_logloss',
                'boosting_type': 'gbdt'
            }
            
            # 训练模型
            model = lgb.train(params, train_data, num_boost_round=num_boost_round)
        else:
            model = model 

        # 获取特征重要性
        importance = model.feature_importance()
        feature_names = X.columns
    
        # 创建特征重要性的DataFrame
        important_features = pd.DataFrame({'feature': feature_names, 'importance': importance})
        
        # 按重要性排序
        self._important_features = important_features.sort_values(by='importance', ascending=False)
        
        return self._important_features
        
    def n_important_features(self, X, y, model=None, num_boost_round=100, n=200, is_more_than_zero=True):
        """前n个重要特征
        
        params
        ---------------------------------------------
        - num_boost_round:训练的轮次
        - n:取前n个重要特征
        - is_more_than_zero:是否只保留重要生大于0的特征
        
        return
        ---------------------------------
        - 前n个重要特征列表
        """
        seature_by_importance = self.important_features(X,y,model=model, num_boost_round=num_boost_round)
        if is_more_than_zero:
            seature_by_importance=seature_by_importance[seature_by_importance['importance'] >0]
        i_list = seature_by_importance[:n]['feature'].tolist()
        return i_list
    
    def pd_important_features(self, X, y, model=None, num_boost_round=100, n=200, is_more_than_zero=True):
        """前n个重要特征
        - 返回pandas数表，包含两列，feature，importance
        
        params
        ---------------------------------------------
        - num_boost_round:训练的轮次
        - n:取前n个重要特征
        - is_more_than_zero:是否只保留重要生大于0的特征
        
        return
        ------------------------------
        - important_features:pandas数表，包含两列，feature，importance

        """
        seature_by_importance = self.important_features(X,y,model=model, num_boost_round=num_boost_round)
        if is_more_than_zero:
            seature_by_importance=seature_by_importance[seature_by_importance['importance'] >0]
        i_pd = seature_by_importance[:n]
        return i_pd

    @staticmethod
    def feature_select_corr(X, y, threshold=0.01, method='pearson', return_pd=False):
        """相关性系数
        - 计算特征与标签之间的相关性，并选择相关性高于threshold的特征

        params
        --------------------------------------
        - X:数据集
        - y:标签
        - threshold:特征与标签相关性不到1%的列舍弃
        - method:默认pearson，即皮尔逊相关系数
        - return_pd:返回pandas数表

        注意
        ---------------------------------------
        只针对连续型变量，因此X输入时要过滤掉分类型数据


        示例
        ---------------------------------------
        label = df['label']
        X = df.drop(columns=["label"])
        col_name,col_value=feature_select_corr(X=X,y=label,return_pd=True)

        """
        res = dt.feature_select_corr(X=X, y=y, threshold=threshold, method=method, return_pd=return_pd)
        return res
     


class FeatureFrequencyEval():

    #数据全部列的索引
    col_feature_importance =[]

    def __init__(self, X, y):
        """多轮训练取出现频次高的前n列特征
        - 主方法：max_freq_cols_pd
        
        
        example 
        -------------------------------------------------------
        X,y = make_classification(n_samples=1000,n_features=1000,n_classes=2,)
        ffe = FeatureFrequencyEval(X,y)
        use_cols = ffe.max_freq_cols_pd(epoch=10, max_col_nums=200, arise_atleast=1, show_msg=False)
        len(use_cols)
        
        """
        self.X = X
        self.y = y
        self.is_pd = isinstance(X, pd.DataFrame)

    def train_model(self,X,y):
        """训练模型并返回特征重要性列表
        - 添加一个树模型，要求模型有feature_importances_属性，比如决策树，或者lgbm 
        - 可以连续添加多个模型，每个模型训练一次得到的列都会累加到col_feature_importance一次
        
        """
        
        # 划分训练集和测试集  
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)
        
        # 创建LightGBM数据集，并指定分类特征
        # free_raw_data=False是因为在数据上设置部分列为category类型,此时lightgbm要求这个数据集不能被释放
        # train_data = lgb.Dataset(X_train, label=y_train, free_raw_data=False, categorical_feature=cat_features)
        train_data = lgb.Dataset(X_train, label=y_train, free_raw_data=False)
        test_data = lgb.Dataset(X_test, label=y_test,  reference=train_data)
        
        # 初始化LightGBM模型  
        # params = {  
        #     'objective': 'multiclass',  # 多分类问题  
        #     'num_class': 3,             # 类别数  
        #     'metric': 'multi_logloss'   # 评估指标  
        # }  
        
        # 设置参数并训练模型
        params = {
            'objective': 'binary', 
            'metric': 'binary_logloss', 
            'boosting_type': 'gbdt',
            # 'max_depth': 3,
            # 'num_leaves': 3,
            # 'max_bin':3,
            # 'min_gain_to_split':0,
            # 'min_data_in_leaf':10,
            'force_col_wise':True}
        lgb_model = lgb.train(params, train_data, num_boost_round=1,  valid_sets=[test_data],)
        self.model = lgb_model 
        
        feature_importance = lgb_model.feature_importance()
        return feature_importance
        

    def add_feature_col(self, show_msg=False):
        """训练累加
        - model:训练好的模型对象
        
        """
        
        # self.train_model(self.X, self.y)
        # fti = self.model.feature_importance()
        fti = self.train_model(self.X, self.y)
        
        fti_len = len(fti)
        if len(self.col_feature_importance)==0:
            for i in range(fti_len):
                self.col_feature_importance.append(0)
            
        #原列重要性列表 索引倒序排列
        feature_index_desc = np.argsort(fti)[::-1]
        
        
        #将有贡献的列加1，积计，每次有贡献，都+1
        for i in range(fti_len):
            index_pos =feature_index_desc[i] #原列索引 
            
            if fti[index_pos]==0: #直到一个列无任何贡献价值
                print(f"前{i+1}列有贡献")
                break
            else:
                #索引位置重要的话，其对应的值加1
                self.col_feature_importance[index_pos] = self.col_feature_importance[index_pos]+1
        
    
        #原列的索引
        index_0=0
        for i in range(fti_len):
            index_pos =feature_index_desc[i] 
            if fti[index_pos] == 0:
                if show_msg:
                    print(f"重要性0边界，第{i}列={fti[feature_index_desc[i-1]]},第{i+1}列={fti[index_pos]}\n")
                index_0=i
                break
        return index_0

    def get_used_cols(self, max_col_nums=200, arise_atleast=1):
        """取非0列，即有贡献的列,取累加后高频的列
        params
        - arise_atleast=2 至少出现过两次 
        - max_col_nums:最多取多少列
        
        """
        
        #取前N个重要列
        col_feature_desc = np.argsort(self.col_feature_importance)[::-1]
    
        # 非0重要性列
        col_feature_not0=[]
        
        #取非0重要列
        for i in range(len(col_feature_desc)):
            index_value_desc = col_feature_desc[i]
            importance_value = self.col_feature_importance[index_value_desc]
            if importance_value<arise_atleast:
                print("符合条件列的个数:",i)
                col_feature_not0=col_feature_desc[:i]
                break
        use_cols = col_feature_not0[:max_col_nums]
        return use_cols


    def max_freq_cols(self, epoch=10, max_col_nums=200, arise_atleast=1, show_msg=False):
        """累加训练
        
        params
        -----------------------------------------------------
        - epoch: 训练轮次
        - arise_atleast=2 至少出现过两次 
        - max_col_nums:最多取多少列
        - show_msg:展示更详细的日志信息
        
        return
        ----------------------------------------------------
        原数据列的索引
        
        X_train[:,use_cols][:3]  #numpy.ndarray
        

        example 
        -------------------------------------------------------
        X,y = make_classification(n_samples=1000,n_features=1000,n_classes=2,)
        ffe = FeatureFrequencyEval(X,y)
        ffe.set_model(model)
        use_cols = ffe.max_freq_cols(epoch=10, max_col_nums=200, arise_atleast=1, show_msg=False)
        len(use_cols)   #161
        
        ffe.add_model(model)  #这里假定再添加一个具有feature_importances_属性的模型
        use_cols = ffe.max_freq_cols(epoch=10, max_col_nums=200, arise_atleast=1, show_msg=False)
        len(use_cols)   #253,200
        
        """
        for i in range(epoch):
            self.add_feature_col(show_msg)  #出现次数累加
    
        #返回高频次出现的列
        use_cols = self.get_used_cols(max_col_nums=max_col_nums, arise_atleast=arise_atleast)
        return use_cols


    def max_freq_cols_pd(self,epoch=10, max_col_nums=200, arise_atleast=1, show_msg=False):
        """如果数据类型为pandas数表，则返回对应的列名，反之仍返回列的index

        params
        -----------------------------------------------------
        - epoch: 训练轮次
        - arise_atleast=2: 至少出现过两次 
        - max_col_nums: 最多取多少列
        - show_msg: 展示更详细的日志信息

        
        return
        ----------------------------------------------------
        如果输入的数据X是pandas数表，那么数据必定是有列名的，此时返回列名
        如果输入的数据X是numpy数组，那么返回的是原数据列的对应的索引
        不管如何，返回的都是一个列表，区别只是在于，是索引还是列名
        
        原数据列的索引
        X_train[:,use_cols][:3]  #numpy.ndarray
        

        example 
        -------------------------------------------------------
        X,y = make_classification(n_samples=1000,n_features=1000,n_classes=2,)
        ffe = FeatureFrequencyEval(X,y)
        use_cols = ffe.max_freq_cols_pd(epoch=10, max_col_nums=200, arise_atleast=1, show_msg=False)
        len(use_cols)
        
        """
        use_cols = self.max_freq_cols(epoch=epoch, max_col_nums=max_col_nums, arise_atleast=arise_atleast, show_msg=show_msg)
        if self.is_pd:
            all_cols = self.X.columns
            return all_cols[use_cols]
        else:
            return use_cols
        

def feature_selected(X, y, num_boost_round=3, max_feature_selected_num=10, corr_line=0.95,debug=False):
    """特征选择与评估，默认为分类问题
    - 使用lightgbm算法训练多轮取出现频次最多的特征，然后相关性高的特征，最多保留200列
    - 之后再对特征进行一次重要性评估，此时的特征虽然有些列在本次被选中的特征组合中重要性被评估为0，但下次组合就可能不是0
    - 如此选择出来的特征更有弹性，在训练的时候才有更多的选择空间，有更多的可能，否则一些可能在特征评估时就被抹杀掉了
    
    return 
    ------------------------------
    important_features:pandas数表，包含两列，feature，importance
    
    内部处理逻辑，当需要定制化时，可重写该方法
    
    
    examples
    -------------------------------
    important_features_pd,corr_paris_pd = feature_selected(X, y,
    num_boost_round=3,
    max_feature_selected_num=10,
    corr_line=0.95,
    debug=False,)

    """
    if isinstance(X,np.ndarray):
        X = pd.DataFrame(X)
    
    old_cols = X.columns
    max_col_num = len(old_cols)
    if max_col_num > max_feature_selected_num:
        max_feature_selected_num = max_col_num
    
    ### 特征评估与特征
    impt = FeatureEval()

    
    ffe = FeatureFrequencyEval(X, y)
    print("多次训练选出出现频次多的特征列")
    use_cols = ffe.max_freq_cols_pd(epoch=10, max_col_nums=200, arise_atleast=1, show_msg=False)
    important_features = use_cols.tolist()
    
    ## 特征选择，初步选择，2倍于目标变量的选择
    if len(important_features)>2:   #如果重要性不足3个，就保存所有列，不选择了
        X = X[important_features]

    ### 线性评估，相似度超过95%只取一列
    fe = FeatureEval(X, corr_line=corr_line)
    feature_corr_selected = fe.new_list()  #最终选择特征
    corr_paris_pd = fe.pairs()
    
    print("feature_corr_selected:",len(feature_corr_selected))
    if len(feature_corr_selected)<=2:
        #此时，随机制造一些数据
        important_features_pd = pd.DataFrame(old_cols,columns=["feature"])
        important_features_pd["importance"] = 1
        return important_features_pd,corr_paris_pd
    
    X=X[feature_corr_selected]

    try:
        #前n个重要特征，最终选择，这里并没有再删除列，如果一个列本次组合没有被选中，那么其重要性为0
        #但若下次组合时被选中，其重要性可能就不是0了，所以这里并不是重要性为0就一定要删除这个列
        important_features = impt.pd_important_features(X,y,num_boost_round=num_boost_round,n=max_feature_selected_num,is_more_than_zero=False)  
 
    except Exception as e:
        
        print(e)
        print("X.shape:",X.shape)  #如果数据过于稀少，比如测试的时候

        #此时，随机制造一些数据
        important_features_pd = pd.DataFrame(old_cols,columns=["feature"])
        important_features_pd["importance"] = 1
        return important_features_pd,corr_paris_pd
        
    
    return important_features,corr_paris_pd



        
