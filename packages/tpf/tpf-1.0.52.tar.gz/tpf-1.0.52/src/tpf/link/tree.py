

import numpy as np 
import pandas as pd 
from sklearn import tree
from sklearn.tree import _tree

def is_dataframe(obj):  
    return isinstance(obj, pd.DataFrame) 


class Decision():
    def __init__(self):
        """从决策树中提取分支供以决策
        """
        pass
    
    def node_samples_tovalue(self,clf):
        """决策树叶子节点样本数，按类别划分的个数,shape=[node_samples,1,n_classes]"""
        value = clf.tree_.value 
        tmp0 = value[0][0][0]  #第1个数
        tmp1 = value[0][0][1]  #第2个数
        pf = False
        if tmp0 > 0 and tmp0 < 1:    #皆是小数
            pf = True 
        elif tmp0 == 0 and tmp1 <= 1: #0或1
            pf = True 
        if pf:
            node_samples = clf.tree_.n_node_samples
            a = node_samples[:,np.newaxis,np.newaxis]
            p_value = clf.tree_.value
            value = np.round(a*p_value).astype(np.int64)
        return value
                                      

    def _clf_base(self,clf,X):
        """决策树规则生成"""
        n_nodes = clf.tree_.node_count
        children_left = clf.tree_.children_left
        children_right = clf.tree_.children_right
        feature = clf.tree_.feature
        threshold = clf.tree_.threshold
        # value = clf.tree_.value
        value = self.node_samples_tovalue(clf)
        
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

    def rules(self, X,y,columns=None,max_depth=5, min_samples_leaf=30, model=None,top_n=None,):
        """二分类问题规则生成
        params 
        -----------------------------------------
        - X:数据
        - y:标签
        - columns:数据特征名称列表
        - max_depth:树的最大深度
        - min_samples_leaf:叶子节点最小样本数
        - model:自定义决策树模型，如果为None，则按max_depth，min_samples_leaf定义一棵树
        
        
        desc
        --------------------------------------------------
        - 按异常样本的含量排序，
        - 100%是异常样本，与0%是异常样本同样有用，它们都是纯净的数据，看实际需要提取哪个
        """
        if not is_dataframe(X):
            if columns is not None:
                X=pd.DataFrame(X,columns=columns)
                y=pd.DataFrame(y,columns=['label']).squeeze()
            else:
                return 'X与y非pandas数表时，请指定 columns'
            
        
        if is_dataframe(y):
            y = y.squeeze()
        else:
            y=pd.DataFrame(y).squeeze()
            
        if columns is None:
            columns = X.columns.tolist()

        #训练一个决策树，这里限制了最大深度和最小样本树
        if model is None:
            clf = tree.DecisionTreeClassifier(max_depth=max_depth,min_samples_leaf=min_samples_leaf)
        else:
            clf = model
        clf = clf.fit(X, y)
        rules = self._clf_base(clf,X)
        
        # 结果格式整理
        df = pd.DataFrame(rules)
        df.columns = ['allrules']
        df['rules']    = df['allrules'].str.split(':').str.get(0)
        df['good-0']     = df['allrules'].str.split(':').str.get(1).astype(float)
        df['bad-1']      = df['allrules'].str.split(':').str.get(2).astype(float)
        df['all']      = df['bad-1']+df['good-0']
        
        columns_to_convert = ['good-0','bad-1','all']
        for col in columns_to_convert:
            df[col] = df[col].astype(int)
        
        df['rate'] = df['bad-1']/df['all']
        # df.drop(columns=['good-0','bad-1','all'],inplace=True)
        df = df.sort_values(by='rate',ascending=False)
        del df['allrules']
        if top_n:
            return df[:top_n]
        else:
            return df
