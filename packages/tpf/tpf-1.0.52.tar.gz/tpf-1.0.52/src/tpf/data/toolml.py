import numpy as np 
import pandas as pd 


def str_pd(data,cname_date_type):
    """pandas数表列转字符类型"""
    data[cname_date_type] = data[cname_date_type].astype(str)
    data[cname_date_type] = data[cname_date_type].astype("string")
    return data


def null_deal_pandas(data,cname_num_type, cname_str_type, num_padding=0, str_padding = '<PAD>'):
    """
    params
    ----------------------------------
    - data:pandas数表
    - cname_num_type：数字类型列表
    - cname_str_type：字符类型列表
    - num_padding:数字类型空值填充
    - str_padding:字符类型空值填充
    
    """
    if len(cname_num_type)>0:
        # 数字置为0
        for col in cname_num_type:
            data.loc[data[col].isna(),col]=num_padding
    
    if len(cname_str_type)>0:
        #object转str，仅处理分类特征，身份认证类特征不参与训练
        data[cname_str_type] = data[cname_str_type].astype(str)
        data[cname_str_type] = data[cname_str_type].astype("string")
        
        for col in cname_str_type:
            data.loc[data[col].isna(),col]=str_padding

        # nan被转为了字符串，但在pandas中仍然是个特殊存在，转为特定字符串，以防Pandas自动处理
        # 创建一个替换映射字典  
        type_mapping = {  
            'nan': str_padding,   
            '': str_padding
        }  
            
        # 使用.replace()方法替换'列的类型'列中的值  
        data[cname_str_type] = data[cname_str_type].replace(type_mapping)  
            
        nu = data[cname_str_type].isnull().sum()
        for col_name,v in nu.items():
            if v > 0 :
                print("存在空值的列:\n")
                print(col_name,v)
        return data

def min_max_scaler(df):  
    return (df - df.min()) / (df.max() - df.min())  

def std7(df, cname_num, means=None, stds=None, set_7mean=True):
    if set_7mean: #将超过7倍均值的数据置为7倍均值
        # 遍历DataFrame的每一列,
        for col in cname_num:  
            # 获取当前列的均值  
            mean_val = means[col]  
            # 创建一个布尔索引，用于标记哪些值超过了均值的7倍  
            mask = df[col] > (7 * mean_val)  
            # 将这些值重置为均值的7倍  
            df.loc[mask, col] = 7 * mean_val  

    df[cname_num] = (df[cname_num] - means)/stds  #标准化
    
    return df  

def get_logical_types(col_type):
    logical_types={}
    for col in col_type.date_type:
        logical_types[col] = 'datetime'
    
    #类别本来不是数字，但onehot编码后，就只剩下0与1这两个数字了
    for col in col_type.str_classification:
        logical_types[col] = 'categorical'

    return logical_types


class ColumnType:
    def __init__(self):
        self.num_type = []          # 数字类
        self.date_type = []         # 日期类
        self.str_identity= []       # 标识
        self.str_classification=[]  # 类别
        self.feature_names = []     # 特征组合列
        self.feature_names_num= []  # 特征组合列之数字特征
        self.feature_names_str=[]   # 特征组合列之类别特征
        self.feature_logical_types={}





from sklearn import tree
from sklearn.tree import _tree


def Get_Rules(clf,X):
    n_nodes = clf.tree_.node_count
    children_left = clf.tree_.children_left
    children_right = clf.tree_.children_right
    feature = clf.tree_.feature
    threshold = clf.tree_.threshold
    value = clf.tree_.value
    
    node_depth = np.zeros(shape=n_nodes, dtype=np.int64)
    is_leaves  = np.zeros(shape=n_nodes, dtype=bool)
    stack = [(0, 0)]
    
    while len(stack) > 0:
        
        node_id, depth = stack.pop()
        node_depth[node_id] = depth
    
        is_split_node = children_left[node_id] != children_right[node_id]
        
        if is_split_node:
            stack.append((children_left[node_id],  depth+1))
            stack.append((children_right[node_id], depth+1))
        else:
            is_leaves[node_id] = True  
    feature_name = [
            X.columns[i] if i != _tree.TREE_UNDEFINED else "undefined!"
            for i in clf.tree_.feature]
    
    ways  = []
    depth = []
    feat = []
    nodes = []
    rules = []
    for i in range(n_nodes):   
        if  is_leaves[i]: 
            while depth[-1] >= node_depth[i]:
                depth.pop()
                ways.pop()    
                feat.pop()
                nodes.pop()
            if children_left[i-1]==i:#当前节点是上一个节点的左节点，则是小于
                a='{f}<={th}'.format(f=feat[-1],th=round(threshold[nodes[-1]],4))
                ways[-1]=a              
                last =' & '.join(ways)+':'+str(value[i][0][0])+':'+str(value[i][0][1])
                rules.append(last)
            else:
                a='{f}>{th}'.format(f=feat[-1],th=round(threshold[nodes[-1]],4))
                ways[-1]=a
                last = ' & '.join(ways)+':'+str(value[i][0][0])+':'+str(value[i][0][1])
                rules.append(last)
               
        else: #不是叶子节点 入栈
            if i==0:
                ways.append(round(threshold[i],4))
                depth.append(node_depth[i])
                feat.append(feature_name[i])
                nodes.append(i)             
            else: 
                while depth[-1] >= node_depth[i]:
                    depth.pop()
                    ways.pop()
                    feat.pop()
                    nodes.pop()
                if i==children_left[nodes[-1]]:
                    w='{f}<={th}'.format(f=feat[-1],th=round(threshold[nodes[-1]],4))
                else:
                    w='{f}>{th}'.format(f=feat[-1],th=round(threshold[nodes[-1]],4))              
                ways[-1] = w  
                ways.append(round(threshold[i],4))
                depth.append(node_depth[i]) 
                feat.append(feature_name[i])
                nodes.append(i)
    return rules

from sklearn import tree
from sklearn.tree import _tree

def rules_clf_base(clf,X):
    n_nodes = clf.tree_.node_count
    children_left = clf.tree_.children_left
    children_right = clf.tree_.children_right
    feature = clf.tree_.feature
    threshold = clf.tree_.threshold
    value = clf.tree_.value
    
    node_depth = np.zeros(shape=n_nodes, dtype=np.int64)
    is_leaves  = np.zeros(shape=n_nodes, dtype=bool)
    stack = [(0, 0)]
    
    while len(stack) > 0:
        
        node_id, depth = stack.pop()
        node_depth[node_id] = depth
    
        is_split_node = children_left[node_id] != children_right[node_id]
        
        if is_split_node:
            stack.append((children_left[node_id],  depth+1))
            stack.append((children_right[node_id], depth+1))
        else:
            is_leaves[node_id] = True  
    feature_name = [
            X.columns[i] if i != _tree.TREE_UNDEFINED else "undefined!"
            for i in clf.tree_.feature]
    
    ways  = []
    depth = []
    feat = []
    nodes = []
    rules = []
    for i in range(n_nodes):   
        if  is_leaves[i]: 
            while depth[-1] >= node_depth[i]:
                depth.pop()
                ways.pop()    
                feat.pop()
                nodes.pop()
            if children_left[i-1]==i:#当前节点是上一个节点的左节点，则是小于
                a='{f}<={th}'.format(f=feat[-1],th=round(threshold[nodes[-1]],4))
                ways[-1]=a              
                last =' & '.join(ways)+':'+str(value[i][0][0])+':'+str(value[i][0][1])
                rules.append(last)
            else:
                a='{f}>{th}'.format(f=feat[-1],th=round(threshold[nodes[-1]],4))
                ways[-1]=a
                last = ' & '.join(ways)+':'+str(value[i][0][0])+':'+str(value[i][0][1])
                rules.append(last)
               
        else: #不是叶子节点 入栈
            if i==0:
                ways.append(round(threshold[i],4))
                depth.append(node_depth[i])
                feat.append(feature_name[i])
                nodes.append(i)             
            else: 
                while depth[-1] >= node_depth[i]:
                    depth.pop()
                    ways.pop()
                    feat.pop()
                    nodes.pop()
                if i==children_left[nodes[-1]]:
                    w='{f}<={th}'.format(f=feat[-1],th=round(threshold[nodes[-1]],4))
                else:
                    w='{f}>{th}'.format(f=feat[-1],th=round(threshold[nodes[-1]],4))              
                ways[-1] = w  
                ways.append(round(threshold[i],4))
                depth.append(node_depth[i]) 
                feat.append(feature_name[i])
                nodes.append(i)
    return rules

# 判断对象是否为 DataFrame 类型  

def is_dataframe(obj):  
    return isinstance(obj, pd.DataFrame) 

def rules_clf2(X,y,columns=None,max_depth=5,top_n=None,):
    """二分类问题规则生成
    - 按异常样本的含量排序，
    - 100%是异常样本，与0%是异常样本同样有用，它们都是纯净的数据，看实际需要提取哪个
    """
    if not is_dataframe(X):
        if columns is not None:
            X=pd.DataFrame(X,columns=columns)
            y=pd.DataFrame(y,columns=['label'])
        else:
            return 'X与y非pandas数表时，请指定 columns'

    #训练一个决策树，这里限制了最大深度和最小样本树
    clf = tree.DecisionTreeClassifier(max_depth=max_depth,min_samples_leaf=50)
    clf = clf.fit(X, y)
    rules = rules_clf_base(clf,X)
    
    # 结果格式整理
    df = pd.DataFrame(rules)
    df.columns = ['allrules']
    df['rules']    = df['allrules'].str.split(':').str.get(0)
    df['good']     = df['allrules'].str.split(':').str.get(1).astype(float)
    df['bad']      = df['allrules'].str.split(':').str.get(2).astype(float)
    df['all']      = df['bad']+df['good']
    df['rate'] = df['bad']/df['all']
    df.drop(columns=['good','bad','all'],inplace=True)
    df = df.sort_values(by='rate',ascending=False)
    del df['allrules']
    if top_n:
        return df[:top_n]
    else:
        return df