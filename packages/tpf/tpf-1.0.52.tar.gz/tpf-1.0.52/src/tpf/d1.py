"""数据处理方法
输入:各种各样的原始数据(绝对路径),cvs,pkl,...
处理:空值,字符串编码,特征过滤, ...
输出:numpy 数组 
"""
# import torch 
import re 
import joblib 
import hashlib
import pickle as pkl 
import pandas as pd
import numpy as np 
import os, json,zipfile
import numpy as np
# from numpy.core.fromnumeric import reshape


import pandas as pd 
from itertools import combinations  
from sklearn.preprocessing import MinMaxScaler
from sklearn.utils import resample
from scipy.stats import chi2_contingency  

from tpf.box.fil import fil_suffix 
from tpf.data.dtype import NumpyEncoder 
from tpf.data.make import random_str

import numpy as np
import pandas as pd

def to_numpy(x):
    """如果 x 还不是 numpy.ndarray，就转成 ndarray。"""
    if isinstance(x, np.ndarray):
        return x
    # pandas 对象（DataFrame / Series）或其他支持 to_numpy 的对象
    if hasattr(x, 'to_numpy'):
        return x.to_numpy()
    # 兜底：强制转 np.array
    return np.asarray(x)


def is_single_label(y_test, y_pred):
    """预测集与预测值是否同时为相同的一个值，此时无法计算AUC"""
    label_test = pd.DataFrame(y_test).value_counts()
    label_pred = np.unique(y_pred)
    if len(label_test) == len(label_pred):
        if label_test.index[0] == label_pred[0]:
            return True
    return False


def df_batch_generator(df, batch_size):
    """使用生成器批次读取pandas数表 
    
    examples
    --------------------------------------------------
    # 使用生成器
    for batch in df_batch_generator(df, 10000):
        print(batch.shape)
    """
    for i in range(0, len(df), batch_size):
        yield df.iloc[i:i+batch_size]

def read_file2pd(file_path, sep='~', is_chunk_read=True, chunksize=10000, max_rows=1000000, label_name='sample_type'):
    """分块读取文件，限于01两分类数据，正样本(1-异常)因为数据量少而全部读取，但总量不超过max_rows
    - max_rows: 最多读取多少行
    - label_name: 标签名称
    """
    # 初始化计数器
    total_rows = 0
    
    # 用于存储结果的数据框
    result_df = pd.DataFrame()

    if is_chunk_read:
        # 如果内存不足，需要分块读取并手动处理（这里假设直接读取失败，我们使用分块读取整个文件然后过滤）
        chunk_iterator = pd.read_csv(file_path, chunksize=chunksize, sep=sep)
        df_type_1_chunks = [chunk[chunk[label_name] == 1] for chunk in chunk_iterator if label_name in chunk.columns]
        df_type_1 = pd.concat(df_type_1_chunks, ignore_index=True)
        result_df = pd.concat([result_df, df_type_1], ignore_index=True)
        total_rows += len(df_type_1)
    else:
        # 读取 sample_type 为 1 的所有数据（如果内存允许，否则需用其他方法确保读取完整）
        # 尝试直接读取（如果内存足够）
        df_type_1 = pd.read_csv(file_path,sep=sep)
        df_type_1 = df_type_1[df_type_1[label_name] == 1]
        result_df = pd.concat([result_df, df_type_1], ignore_index=True)
        total_rows += len(df_type_1)

        
    # 计算还需要多少行 sample_type 为 0 的数据
    remaining_rows = max_rows - total_rows

    if remaining_rows > 0:
        # 再次使用分块读取来获取 sample_type 为 0 的数据
        chunk_iterator = pd.read_csv(file_path, chunksize=chunksize, sep=sep)
        for chunk in chunk_iterator:
            if 'sample_type' not in chunk.columns:
                continue
            
            df_type_0_chunk = chunk[chunk[label_name] == 0]
            
            if len(result_df) + len(df_type_0_chunk) > max_rows:
                # 如果加上当前 chunk 后会超过最大行数，则只取需要的部分
                result_df = pd.concat([result_df, df_type_0_chunk.iloc[:remaining_rows]], ignore_index=True)
                break
            else:
                result_df = pd.concat([result_df, df_type_0_chunk], ignore_index=True)
                remaining_rows -= len(df_type_0_chunk)
            
            if remaining_rows <= 0:
                break
    return result_df



class DataDeal():
    
    @staticmethod
    def encoding_onehot(data, str_cnames, padding_null='<PAD>'):
        """one hot编码
        - 字符串列编码，编码后删除原列
        
        params
        --------------------------------------
        - data:pd数表
        - str_cnames:需要编码的字符名称列表
        - padding_null:空值填充符

        处理逻辑
        -----------------------
        针对字符串列进行编码，如果没有空值时，也适用于数字类型编码

        """
        for cname in str_cnames:
            cdata = data[cname]
            if cdata.isnull().any().sum()>0:
                if cdata.dtype!="string":
                    cdata = cdata.astype("string")
                cdata.fillna(padding_null,inplace=True)
            
            c_new_1 = pd.get_dummies(cdata, prefix=cname)
            c_new_1 = c_new_1.astype(np.float32).round(2)
            data = pd.concat([data,c_new_1],axis=1)
            data.drop([cname],axis=1,inplace=True)
        return data
    
    @staticmethod
    def encoding_data(data, col_name="CHANNEL", key="2", encoding_type="onehot", lable_dict=None):
        """获取编码的业务类型对应的数据
        
        功能
        -------------------------------------------
        原列有多种类型，onehot编码后每种类型为一列；
        现根据原列中的某个类型的值，过滤数表
        
        params
        --------------------------------------------
        - data:pd数表
        - col_name:原始的列名，进行字符编码前的列名
        - key:col_name中的字符串,需要编码的对象
        - encoding_type:index,onehot
        - lable_dict: 为全体数据集所有字符串形成的字典

        example onehot
        -------------------------------------------
        data_wangyin = onehot_encoding_data(data, col_name="CHANNEL", key="2", encoding_type="onehot")

        example index
        -------------------------------------------
        data_wangyin = onehot_encoding_data(data,col_name="CHANNEL", key="2", encoding_type="index", lable_dict=lable_dict)
        
        """
        if encoding_type=="onehot":    # one hot编码
            new_col_name = col_name + "_" + key
            if new_col_name in data.columns:
                data_tmp = data[data[new_col_name].eq(1)] #从数表中取出编码对应的数据,onehot只有0与1
                return data_tmp
            else:
                msg = f"现有数表不包含{new_col_name}列,请考虑现有以{col_name}开头的列名："
                slist = []
                for col in data.columns:
                    if col.startswith(col_name):
                        slist.append(col)
                msg = msg +",".join(slist)
                raise Exception(msg) 
        elif encoding_type=="index":           #索引编码,
            index_str_encoding = lable_dict[key]  #根据字典取编码
            data_tmp = data[data[col_name].eq(index_str_encoding)] #从数表中取出编码对应的数据
            return data_tmp
        return None

    
    @staticmethod
    def feature_add23(df):
        """特征组合
        - 将pandas中的数表两两组合相加，三三组合相加
        """
        # 获取所有列的名称  
        columns = df.columns  

        # 生成所有可能的列对（不包括自身组合）  
        column_pair2 = list(combinations(columns, 2))  
        
        # 遍历列对，计算每对列的和，并将新列添加到DataFrame中  
        for pair in column_pair2:  
            new_col_name = f"{pair[0]}+{pair[1]}"  
            df[new_col_name] = df[pair[0]] + df[pair[1]]
    
        # 生成所有可能的列对（不包括自身组合）  
        column_pair3 = list(combinations(columns, 3))  
        
        # 遍历列对，计算每对列的和，并将新列添加到DataFrame中  
        for pair in column_pair3:  
            new_col_name = f"{pair[0]}+{pair[1]}+{pair[2]}"  
            df[new_col_name] = df[pair[0]] + df[pair[1]]+ df[pair[2]]  
        return df
    
    
    @staticmethod
    def feature_add_prod23(df, istd=False):
        """将pandas中的数表两两组合（相加相乘），三三组合（相加相乘）
        
        params
        -------------------------------
        - istd:未归一化时量纲不统一，相乘后的数据可能过大，所以要求先做归一化
        
        建议
        ------------------------
        计算前，要求数表df中各列做归一化/标准化处理，防止...
        
        """
        if not istd:
            raise Exception("请先做归一化处理，统一量纲")
        
        # 获取所有列的名称  
        columns = df.columns  

        # 生成所有可能的列对（不包括自身组合）  
        column_pair2 = list(combinations(columns, 2))  
        
        # 遍历列对，计算每对列的和，并将新列添加到DataFrame中  
        for pair in column_pair2:  
            new_col_name = f"{pair[0]}+{pair[1]}"  
            df[new_col_name] = df[pair[0]] + df[pair[1]]

        # 遍历列对，计算每对列的乘积，并将新列添加到DataFrame中  
        for (col1, col2) in column_pair2:  
            new_col_name = f"{col1}*{col2}"  
            df[new_col_name] = df[col1] * df[col2]
    
    
        # 生成所有可能的列对（不包括自身组合）  
        column_pair3 = list(combinations(columns, 3))  
        
        # 遍历列对，计算每对列的和，并将新列添加到DataFrame中  
        for pair in column_pair3:  
            new_col_name = f"{pair[0]}+{pair[1]}+{pair[2]}"  
            df[new_col_name] = df[pair[0]] + df[pair[1]]+ df[pair[2]]  


        # 遍历列对，计算每对列的乘积，并将新列添加到DataFrame中  
        for (col1, col2, col3) in column_pair3:  
            new_col_name = f"{col1}*{col2}*{col3}"  
            df[new_col_name] = df[col1] * df[col2]* df[col3]
        return df
    
    
    @staticmethod
    def feature_select_chi2(X,y,threshold=3.84):
        """卡方验证
        - 计算特征与标签之间的相关性，并选择相关性高于threshold的特征

        params
        --------------------------------------
        - X:数据集
        - y:标签
        - threshold:特征与标签相关性不到threshold的列舍弃

        注意
        ---------------------------------------
        只针对离散型变量，如果是连续型变量可以考虑分箱
        
        示例
        ---------------------------------------
        label = df['label']
        X = df.drop(columns=["label"])
        col_name,col_value=feature_select_chi2(X=X,y=label)

        """
        cols = X.columns
        
        col_name=[]
        col_value=[]
        for col in cols:
            observed=pd.crosstab(X[col],y)
            chi2,p,dof,expected=chi2_contingency(observed)
            if chi2>threshold:
                col_name.append(col)
                col_value.append(chi2)

        return col_name,col_value

    @staticmethod
    def feature_select_corr(X, y, threshold=None, method='pearson', return_pd=False):
        """相关性系数
        - 计算特征与标签之间的相关性，并选择相关性高于threshold的特征

        params
        --------------------------------------
        - X:数据集
        - y:标签
        - threshold:0.01-特征与标签相关性不到1%的列舍弃,None-表示全部保留不会因为相关性舍弃任何的特征列
        - method:默认pearson，即皮尔逊相关系数
        - return_pd:返回pandas数表

        注意
        ---------------------------------------
        只针对连续型变量，因此X输入时要过滤掉分类型数据


        示例
        ---------------------------------------
        label = df['label']
        X = df.drop(columns=["label"])
        col_name,col_value=feature_select_corr(X=X,y=label)

        """
        corr_index = X.corrwith(y, method=method)
        corr_index = corr_index.fillna(0)
        if threshold is not None:
            corr_index = corr_index[abs(corr_index) > threshold]

        col_name = []
        col_value = []
        for k, v in corr_index.items():
            col_name.append(k)
            col_value.append(v)
        if return_pd:
            df = pd.DataFrame(columns=["feature_name", "corr_label"])
            df["feature_name"] = col_name
            df["corr_label"] = col_value
            return df

        return col_name, col_value

    
    # 定义一个函数来计算IV值  
    @staticmethod
    def feature_select_iv_single(X, y,  is_discrete_var=False,is_equifrequency=True, bins=None,bin_counts=10, special_values=None):
        """单列IV值计算
        - 计算单个特征相对标签信息价值

        params
        --------------------------------------
        - X:单个特征/pandas的一列
        - y:标签/目标变量
        - special_values:将一个类型划为其他类
        - is_equifrequency:True-等频分箱，否则为等宽
        - bins：自定义分箱，此时is_equifrequency参数就失效了，因为箱子由外部传入
        
        名词解释
        ------------------------------------------------------
        - 以金融为例，Goods指正常的金融交易，Bads是异常的金融交易
        - 
        """
        feature=X
        target=y
        if is_discrete_var: #离散型变量的每个类型本身就是一个桶/箱子
            bins = X     
        else:               #非离散型，即连续型变量
            if bins is None:  
                if is_equifrequency:  # 使用等频分箱，但注意qcut需要数值型数据  
                    bins = pd.qcut(feature, q=bin_counts, duplicates='drop')  
                else:  #等宽分箱
                    bins = pd.cut(feature, bins=bin_counts, right=False)
            else:
                pass   #外部传入分好的箱子，注意箱子行数与数据行数保持一致
        
            # 处理特殊值（如果有的话）  
            if special_values is not None:  
                for val in special_values:  
                    feature = feature.replace({val: np.nan})  
                feature = feature.fillna(-1)  
                bins = pd.cut(feature, bins=bins.cat.add_categories([-1]), right=False)  
    
        # 创建包含分组和是否违约的DataFrame  
        grouped = pd.DataFrame({  
            'feature': feature,  
            'target': target  
        }).groupby(bins,observed=True)  
    
        # 计算每个组的总数、违约数和未违约数  
        result = grouped.agg(  
            Total=('target', 'size'),  
            Bads=('target', lambda x: (x == 1).sum()),  
            Goods=('target', lambda x: (x == 0).sum())  
        )  
        # print(result)

        if 0 in result['Goods'].values:  
            raise Exception('Goods存在0值，即一些箱子中没有样本，请减少箱子数量') 
        if 0 in result['Bads'].values:  
            raise Exception('Bads存在0值，即一些箱子中没有样本，请减少箱子数量')

        # 计算分布和WOE  
        result['Distribution Goods'] = result['Goods'] / result['Goods'].sum()  
        result['Distribution Bads'] = result['Bads'] / result['Bads'].sum()  
        result['WOE'] = np.log(result['Distribution Goods'] / result['Distribution Bads'])  
        result['IV'] = (result['Distribution Goods'] - result['Distribution Bads']) * result['WOE']  
    
        # 返回总的IV值  
        iv_value = round(result['IV'].sum(), 3)
        return iv_value
        
    @staticmethod
    def feature_select_iv(X, y, threshold=0.1,is_discrete_var=False,is_equifrequency=True, bins=None,bin_counts=10, special_values=None):
        """IV值
        - 计算特征相对标签信息价值，并选择价值高于threshold的特征
        - 受数据量影响较大，默认具有足够的数据量，最好万级以上

        params
        --------------------------------------
        - X:pandas数表/单列-Series，特征
        - y:标签/目标变量
        - threshold:选择>=threshold的特征，无用特征（threshold<0.02）、弱价值特征（0.02<threshold<0.1）、中价值特征（0.1<threshold<0.3）和强价值特征（0.3<threshold<0.5）。
        - is_discrete_var:是否为离散变量，通过将一个数表中的数据分为两类，一类是连续型变量，一类是离散型变量
        - is_equifrequency:是否等频分箱，True-等频，False-等宽
        - bins：自定义分箱，此时is_equifrequency参数就失效了，因为箱子由外部传入
        - bin_counts：箱子的个数，箱子减少，IV值就会上升，因为波动小了

        注意
        ---------------------------------------
        连续型变量分箱，离散型变量每个类型就是一个箱子

        return 
        ---------------------------------------
        若返回为空，则表示没有达到threshold的标准，被过滤了
        
        示例
        ---------------------------------------
        label = df['label']
        X = df.drop(columns=["label"])
        col_name,col_value=feature_select_iv(X=X,y=label)

        """
        col_name = []
        col_value = []
        if isinstance(X, pd.Series):  #单列输入
            iv_value = DataDeal.feature_select_iv_single(X, y,is_discrete_var=is_discrete_var,is_equifrequency=is_equifrequency,bins=bins,bin_counts=bin_counts,special_values=special_values)  
            if iv_value > threshold:
                col_name.append(X.name)
                col_value.append(iv_value)
            return col_name,col_value
        
        cols = X.columns
        for col in cols:
            iv_value = DataDeal.feature_select_iv_single(X[col], y,is_discrete_var=is_discrete_var,is_equifrequency=is_equifrequency,bins=bins,bin_counts=bin_counts,special_values=special_values)  
            if iv_value > threshold:
                col_name.append(col)
                col_value.append(iv_value)
        return col_name,col_value

    
    @staticmethod
    def null_deal_pandas(data,cname_num_type, cname_str_type, num_padding=0, str_padding = '<PAD>'):
        """pandas空值处理
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
    
    @staticmethod
    def non_numeric_colnames(data_pd):
        """获取pandas数表非数字列的列名"""
        # 获取所有数字类型的列名  
        numeric_cols = data_pd.select_dtypes(include=['int64', 'float64','int16','int32','float32']).columns  
        
        # 获取所有非数字列的列名  
        non_numeric_cols = data_pd.columns.difference(numeric_cols)  
        return non_numeric_cols.tolist()
    
    
    @staticmethod
    def onehot_torch(idx, n_classes=10):
        """one hot 编码,按索引取编码向量
        """
        import torch 
        matrix = torch.eye(n_classes)
        return matrix[idx]
    
    @staticmethod
    def onehot_value_counts(data, col_name):
        """onehot编码后的数表中统计原旧列不同值的数量
        
        params
        ------------------------------------
        - data:pandas数表
        
        example
        ------------------------------------
        dt.onehot_value_counts(data,col_name="CHANNEL")
        
        """
        slist = []
        for col in data.columns:
            if col.startswith(col_name):
                slist.append(col)
        col_dict = {}
        for col in slist:
            col_dict[col] = data[col].eq(1).sum()
        return col_dict


    @staticmethod
    def pd_data_split(X, y, test_split=0.2, random_state=42,):
        """按标签类别等比随机采样，确保测试集中每类标签的数据与训练集保持等比，不会出现测试集中某个标签无数据的情况 

        主要逻辑
        --------------------------------------------------
        针对每个标签选test_split比例的数据，
        1. 当一个类别标签的个数tmp_count为0或1时，直接contine，即跳过当前轮次的for循环，进入下一个循环
        2. 当一个类别标签的个数tmp_count>1 and tmp_count<=5时，只随机取1条数据作为测试集
        3. 当一个类别标签的个数tmp_count>5时,再走现在的逻辑，即按test_split比例取个数


        存在问题
        --------------------------

        params
        ------------------------------------
        - X:数据,pandas数表
        - y:标签,pandas数表
        - test_split:测试集占比,
        - random_state:随机因子

        examples
        ------------------------------------
        X_train,y_train,X_test,y_test = pd_data_split(X, y, test_split=0.2, random_state=42,)
        
        """
        # 保存原始数据类型
        X_original_type = type(X)
        y_original_type = type(y)

        # 检查并转换X为pandas DataFrame
        if not isinstance(X, pd.DataFrame):
            X2 = pd.DataFrame(X)
        else:
            X2 = X

        # 检查并转换y为pandas Series
        if not isinstance(y, (pd.Series, pd.DataFrame)):
            y2 = pd.Series(y)
        else:
            y2 = y

        # 保存原始索引的副本，用于后续获取训练集数据
        copied_index = X2.index.copy()

        print(X2.shape, X2.index)
        # 初始化空的测试集DataFrame
        X_test = pd.DataFrame(columns=X2.columns)
        y_test = pd.DataFrame()

        # 获取数据集中所有唯一的标签类别
        # 由于标签可能包含列表等不可哈希类型，需要特殊处理
        unique_labels = []
        seen_labels = []
        for label in y2:
            label_str = str(label)  # 将标签转换为字符串进行比较
            if label_str not in seen_labels:
                seen_labels.append(label_str)
                unique_labels.append(label)

        # 遍历每个标签类别，确保每个类别在测试集中都有代表性样本
        for label in unique_labels:
            # 获取当前标签对应的所有数据行索引（处理不可哈希类型）
            label_indices = []
            for idx, y_val in y2.items():
                if str(y_val) == str(label):
                    label_indices.append(idx)
            label_indices = pd.Index(label_indices)
            tmp_count = len(label_indices)  # 当前标签的样本数量

            # 根据样本数量决定测试集选择策略
            if tmp_count == 0 or tmp_count == 1:
                # 当样本数为0或1时，跳过当前类别，不分配测试样本
                continue
            elif tmp_count > 1 and tmp_count <= 5:
                # 当样本数为2-5时，只随机取1条数据作为测试集
                num_samples_to_select = 1
            else:
                # 当样本数>5时，按test_split比例计算测试样本数
                if test_split is None:
                    test_split = 0.2
                num_samples_to_select = int(len(label_indices) * test_split)

            # 使用分层采样：从当前类别中随机抽取指定数量的样本作为测试集
            # replace=False表示不放回采样，确保数据不重复
            resampled_indices = resample(label_indices, replace=False, n_samples=num_samples_to_select,
                                         random_state=random_state)
            # 从原始索引中移除已选为测试集的索引，剩余索引将作为训练集
            copied_index = copied_index.difference(resampled_indices)

            # 根据抽取的索引获取对应的特征数据和标签数据
            X_label_test = X2.loc[resampled_indices]
            y_label_test = y2.loc[resampled_indices]

            # 将当前类别的测试样本添加到总的测试集中
            if X_test.shape[0] == 0:
                # 如果测试集为空，直接赋值
                X_test = X_label_test
                y_test = y_label_test
            else:
                # 如果测试集已有数据，使用concat追加新数据
                if X_label_test.shape[0]>0:
                    X_test = pd.concat([X_test, X_label_test], ignore_index=True)
                    y_test = pd.concat([y_test, y_label_test], ignore_index=True)

        # 使用剩余的索引创建训练集，确保训练集和测试集没有重叠
        X_train = X2.loc[copied_index]
        y_train = y2.loc[copied_index]

        # 根据原始数据类型转换返回值
        if X_original_type == list:
            X_train = X_train.values.tolist()
            X_test = X_test.values.tolist()

        if y_original_type == list:
            y_train = y_train.tolist()
            y_test = y_test.tolist()

        return X_train, y_train, X_test, y_test

    @staticmethod
    def data_split(X, y, test_size=0.2, random_state=42,):
        """按标签类别等比随机采样，确保测试集中每类标签的数据与训练集保持等比，不会出现测试集中某个标签无数据的情况 

        主要逻辑
        --------------------------------------------------
        针对每个标签选test_split比例的数据，
        1. 当一个类别标签的个数tmp_count为0或1时，直接contine，即跳过当前轮次的for循环，进入下一个循环
        2. 当一个类别标签的个数tmp_count>1 and tmp_count<=5时，只随机取1条数据作为测试集
        3. 当一个类别标签的个数tmp_count>5时,再走现在的逻辑，即按test_split比例取个数


        存在问题
        --------------------------

        params
        ------------------------------------
        - X:数据,pandas数表
        - y:标签,pandas数表
        - test_split:测试集占比,
        - random_state:随机因子

        examples
        ------------------------------------
        labels = df['label']
        train,test = dtl.data_split(df,labels,test_size=0.2)

        y_train = train['label']
        y_test  = test['label']
        X_train = train['text']
        X_test  = test['text']  

        """
        # 保存原始数据类型
        X_original_type = type(X)
        y_original_type = type(y)

        # 检查并转换X为pandas DataFrame
        if not isinstance(X, pd.DataFrame):
            X2 = pd.DataFrame(X)
        else:
            X2 = X

        # 检查并转换y为pandas Series
        if not isinstance(y, (pd.Series, pd.DataFrame)):
            y2 = pd.Series(y)
        else:
            y2 = y

        # 保存原始索引的副本，用于后续获取训练集数据
        copied_index = X2.index.copy()

        # 初始化空的测试集DataFrame
        X_test = pd.DataFrame(columns=X2.columns)
        y_test = pd.DataFrame()

        # 获取数据集中所有唯一的标签类别
        unique_labels = y.unique()

        # 遍历每个标签类别，确保每个类别在测试集中都有代表性样本
        for label in unique_labels:
            # 获取当前标签对应的所有数据行索引（处理不可哈希类型）
            label_indices = []
            for idx, y_val in y2.items():
                if str(y_val) == str(label):
                    label_indices.append(idx)
            label_indices = pd.Index(label_indices)
            tmp_count = len(label_indices)  # 当前标签的样本数量

            # 根据样本数量决定测试集选择策略
            if tmp_count == 0 or tmp_count == 1:
                # 当样本数为0或1时，跳过当前类别，不分配测试样本
                continue
            elif tmp_count > 1 and tmp_count <= 5:
                # 当样本数为2-5时，只随机取1条数据作为测试集
                num_samples_to_select = 1
            else:
                # 当样本数>5时，按test_split比例计算测试样本数
                if test_size is None:
                    test_size = 0.2
                num_samples_to_select = int(len(label_indices) * test_size)

            # 使用分层采样：从当前类别中随机抽取指定数量的样本作为测试集
            # replace=False表示不放回采样，确保数据不重复
            resampled_indices = resample(label_indices, replace=False, n_samples=num_samples_to_select,
                                         random_state=random_state)
            # 从原始索引中移除已选为测试集的索引，剩余索引将作为训练集
            copied_index = copied_index.difference(resampled_indices)

            # 根据抽取的索引获取对应的特征数据和标签数据
            X_label_test = X2.loc[resampled_indices]
            y_label_test = y2.loc[resampled_indices]

            # 将当前类别的测试样本添加到总的测试集中
            if X_test.shape[0] == 0:
                # 如果测试集为空，直接赋值
                X_test = X_label_test
                y_test = y_label_test
            else:
                # 如果测试集已有数据，使用concat追加新数据
                if X_label_test.shape[0]>0:
                    X_test = pd.concat([X_test, X_label_test], ignore_index=True)
                    y_test = pd.concat([y_test, y_label_test], ignore_index=True)

        # 使用剩余的索引创建训练集，确保训练集和测试集没有重叠
        X_train = X2.loc[copied_index]
        y_train = y2.loc[copied_index]

        # 根据原始数据类型转换返回值
        if X_original_type == list:
            X_train = X_train.values.tolist()
            X_test = X_test.values.tolist()

        if y_original_type == list:
            y_train = y_train.tolist()
            y_test = y_test.tolist()

        return X_train,X_test

    
    @staticmethod
    def std7(df, cname_num, means=None, stds=None, set_7mean=True):
        """标准化处理

        params
        --------------------------------
        - cname_num:对于df数表中指定的列进行标准化处理
        - means：cname_num列对应的均值
        - stds: cname_num列对应的标准差
        - set_7mean: 将超过7倍均值的数值置为7倍均值

        example
        -------------------------------
        # 创建一个示例DataFrame  
        data = {  
            'A': [1, 2, 3, 4, 5000],  
            'B': [10, 20, 30, 40, 50],  
            'C': [100, 200, 300, 400, 5000]  
        }  
        
        df = pd.DataFrame(data)  
        cname_num=["A","B"]
        means = df[cname_num].mean()
        stds = df[cname_num].std()
        df = std7(df, cname_num, means, stds)

        """
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
    
    @staticmethod
    def str_pd(data,cname_date_type):
        """pandas数表列转字符类型"""
        data[cname_date_type] = data[cname_date_type].astype(str)
        data[cname_date_type] = data[cname_date_type].astype("string")
        return data
        
        
class Stat():
    print_level = 2
    
    def __init__(self, print_level=1) -> None:
        """
        日志输出级别:
        0-什么都不输出,1-输出少量信息,2-详细的输出,3-超级详细的代码调试信息 
        """
        self.print_level = print_level
        self.score_list = []

    def update_print_level(self,print_level):
        self.print_level = print_level


    def log(self,msg, print_level=1):
        if self.print_level >= print_level:
            print(msg)
    def stat():
        pass 


def list_md5(string_list,n=0,random=0,is_lower=False):
    """返回字符串列表的md5值
    - string_list:字符串列表
    - n:仅返回md5字符串的前n位字符，若n=0则全部返回
    - random:添加n位随机字符(仅限数字与字母)，若n=0则不增加随机字符
    """
    
    # 使用空字符串将列表中的字符串拼接起来
    concatenated_string = "".join(string_list)
    
    # 选择一个哈希算法，例如md5
    hash_object = hashlib.md5()
    
    # 对拼接后的字符串进行编码，然后更新哈希对象
    hash_object.update(concatenated_string.encode('utf-8'))
    
    # 获取16进制格式的哈希值
    hash_digest = hash_object.hexdigest()
    ss = str(hash_digest)
    if n==0:
        return ss
    else:
        ss = ss[:n]
    if random == 0:
        return ss 
    else:
        ss += random_str(random)
    if is_lower:
        return ss.lower()
    return ss

import numpy as np
import string

def pkl_save(data, file_path, use_joblib=True, compress=0, weights_only=None,file_bak=False):
    """
    - data:保存一个列表时直接写列表,多个列表为tuple形式
    - weights_only: 使用torch的save与load，False通常是加载整个模型，True只针对参数，需要自己手工将参数载入模型
    """
    if weights_only is not None:
        import torch 
        torch.save(data, file_path)
    elif weights_only is None and  use_joblib:
        joblib.dump(data, filename=file_path, compress=compress)
    else:
        data_dict = {}
        if type(data).__name__ == 'tuple':
            index = 0
            for v in data:
                index = index+1
                key = "k"+str(index)
                data_dict[key]= v 
        else:
            data_dict["k1"] = data 

        if file_bak:
            # 在新文件完成写入之前，不要损坏旧文件
            tmp_path = file_path+".tmp"
            bak_path = file_path+".bak"

            with open(tmp_path, 'wb') as f:
                # 如果这一步失败，原文件还没有被修改，重新写入即可
                pkl.dump(data_dict, f)

                # 如果这一步失败，.tmp文件已经被成功写入，直接将.tmp去掉就是最新写入的文件
                # 这里并没有测试rename是否被修改文件的内容，从命名上看，rename是不会的，
                if os.path.exists(file_path):
                    if os.path.exists(bak_path):
                        os.remove(bak_path)
                    os.rename(src=file_path,dst=bak_path)
            if os.path.exists(tmp_path):
                # 如果是下面这一步被强制中止，直接将.tmp去掉就是最新写入的文件
                # 也可以通过.bak文件恢复到修改之前的文件
                # 重命后，不会删除备份文件，最坏的结果是丢失当前的写入，但也会保留一份之前的备份
                os.rename(src=tmp_path,dst=file_path)
        else:
            with open(file_path, 'wb') as f:
                # 如果这一步失败，原文件还没有被修改，重新写入即可
                pkl.dump(data_dict, f)
            

def pkl_load(file_path, use_joblib=True, weights_only=None):
    """ 
    与pkl_load配对使用
    """
    if weights_only is not None:
        import torch 
        data = torch.load(file_path, weights_only=weights_only)
        return data 
    
    if use_joblib:
        data = joblib.load(file_path)
        return data

    try:
        with open(file_path, 'rb') as f:
            data_dict = pkl.load(f)
        data = tuple(list(data_dict.values()))
        if len(data) == 1:
            return data[0]
        return data 
    except Exception as e:
    #     print(repr(e))
        model = joblib.load(file_path)
        return model 

def write(obj,file_path):
    """
    直接将对象转字符串写入文件,这样可以在文件打开时,看到原内容,还可以进行搜索
    """
    ss = str(obj)
    with open(file_path,"w",encoding="utf-8") as f:
        f.write(ss)

def read(file_path):
    if os.path.exists(file_path) == False:
        return None
    with open(file_path,'r',encoding="utf-8") as f:
        c = eval(f.read())
        return c 

def write_json(obj,file_path):
    fout=open(file_path, "w", encoding='utf-8')
    fout.write(json.dumps(obj, ensure_ascii=False,cls=NumpyEncoder))               
    fout.close() 

def read_json(file_path):
    with open(file_path,'r',encoding="utf-8") as f:
        c = json.load(f)
        return c

def read_zip1(filename):
    """
    读取zip压缩文件中的第一个文件内容

    return
    ---------------------------
    二进制数据
    """
    with zipfile.ZipFile(filename) as f:
        # namelist是解压后的文件列表
        # read返回的是二进制数据
        data = f.read(f.namelist()[0])
    return data


def np_save(x,file_path):
    """
    代码内容实际与np_save_x一样，但这里的参数，特定使用元组，
    在使用np_load方法时，直接以元组的方式取，就可以直接拿到对应的变量
    """
    np.savez(file_path,x=x)

def np_load(file_path): 
    sfx = fil_suffix(file_path)
    if sfx != ".npz":
        file_path = file_path+".npz"
    if os.path.exists(file_path) and os.path.getsize(file_path)>0: 
        fil = np.load(file_path)
        x = fil["x"]
        return x 

def np_save_x(x,file_path):
    np.savez(file_path,x=x)

def np_load_x(file_path): 
    sfx = fil_suffix(file_path)
    if sfx != ".npz":
        file_path = file_path+".npz"
    if os.path.exists(file_path) and os.path.getsize(file_path)>0: 
        fil = np.load(file_path)
        x = fil["x"]
        return x 


def json_dump(obj,file_path):
    ss = json.dumps(obj)
    with open(file_path,'w') as file_obj:
        json.dump(ss,file_obj)

def json_load(file_path):
    with open(file_path,'r') as file_obj:
        names = json.load(file_obj)
    names = json.loads(names)
    return names


def list_diff(a,b):
    """a减b
    Args:
        a (_type_): python list
        b (_type_): python list

    示例:
        a = [1,2,3,3]

        b = [2,3,4,4]

        c = set(a).difference(set(b))

        print(c)

        {1}
    """
    ll = list(set(a).difference(set(b)))
    return ll 

def list_jiaoji(a,b):
    ll = list(set(a).intersection(set(b)))
    return ll 


def numpy2pd(mat):
    """
    numpy 转 pandas,列的名称默认为0,1,2,...
    """
    mat = pd.DataFrame(mat)
    return mat 

def pd2numpy(mat):
    mat = np.array(mat)
    return mat 


def csv_slice(csv_path, target_file, start_end_index=(0,1)):
    """大文件截取一个切片，便于开发测试使用
    """
    fil = pd.read_csv(csv_path)
    fil = fil.iloc[start_end_index[0]:start_end_index[1]]
    fil.to_csv(target_file,index=False)

def csv_slice_small(csv_path, target_dir, max_row_one_csv=100000):
    """
    将一个大的CSV文件拆分成一个个小的CSV文件
    """
    fil = pd.read_csv(csv_path)
    # print(fil.shape[0])
    (filepath, tempfilename) = os.path.split(csv_path)
    (filesname, extension) = os.path.splitext(tempfilename)
        
    
    all_row_counts = fil.shape[0]

    single_file_rows = max_row_one_csv 
    if all_row_counts > single_file_rows*3:  # 是批次的3倍才值得拆一下，1个多批次的数据合在一起计算就可以了
        start_index = 0
        while start_index < all_row_counts:
            end_index = start_index + single_file_rows

            if end_index > all_row_counts:
                end_index = all_row_counts

            one_batch_data = fil.iloc[start_index:end_index]
            one_csv_path = os.path.join(target_dir,"{}_{}_{}".format(filesname,start_index, end_index)+".csv")
            one_batch_data.to_csv(one_csv_path, index=False)
            start_index = end_index 
    else:
        start_index = 0
        end_index = all_row_counts
        one_csv_path = os.path.join(target_dir,"{}_{}_{}".format(filesname,start_index, end_index)+".csv")
        one_batch_data.to_csv(one_csv_path, index=False)
         
         
class OneHot(object):
    def __init__(self):
        pass 
     
    @staticmethod
    def get_one_hot(idx, n_classes=10):
        """one hot 编码
        """
        import torch 
        matrix = torch.eye(n_classes)
        return matrix[idx]

    @staticmethod
    def get_one_hot_test():
        oh = OneHot.get_one_hot(3,n_classes=5)
        print(oh)
        
    
class DataStat(Stat):
    def __init__(self, print_level=2) -> None:
        """
        数据处理常用方法 
        """
        super().__init__(print_level=print_level)

    def value_counts(self, data, print_level=2):
        """统计不重复值的个数,用于样本标签均衡判断,

        参数
        ----------------------------
        - data: 2维numpy数组


        return 
        --------------------------------
        字典{"值":个数}


        示例
        ----------------------------------
        import ai.box.d1 as d1 

        import numpy as np 

        a = np.array([
            [1,1,3,3,4,5,5,7],
            [1,1,3,3,4,5,5,7]])

        dss = d1.DataStat()

        dss.value_counts(a)


        {
            1:4
            3:4
            4:2
            5:4
            7:2
        }


        """
        data = np.reshape(data,(1,-1))
        data = data[0]
        count = {}
        key_list = []
        for v in data:
            if v in count.keys():
                count[v] = count[v] + 1
            else:
                count[v] = 1
                key_list.append(v)

        
        key_list = np.sort(key_list)
        ss = "{\n"
        if self.print_level >= print_level:
            for k in key_list:
                ss = ss + "  {}:{}\n".format(k,count[k])
        ss = ss + "}"
        self.log(ss,print_level)
        return count 

    def resample_count(self, x, y, count_dict, print_level=2):
        """
        按指定数量对样本进行重采样,用于样本均衡


        参数
        -----------------------------------
        count_dict:类别个数字典,{"0":10,"1":20}
        """
        # 按标签对数据集分类,每类标签一个数据集列表
        x_count_lable = self.sort_by_lable(x,y,print_level) 

        index = 0
        for key in x_count_lable.keys():
            x_tmp = np.array(x_count_lable[key])
            
            # 数据扩展
            x_tmp = self.__resample_1(x_tmp, n_samples=count_dict["{}".format(key)])

            # 标签扩展,由于数据已按标签分类,所有一类数据对应的标签是相同的
            # 只要个数对应上即可 
            if index ==0:
                x_new = x_tmp
                y_new = np.array([key for i in range(len(x_new))])
            else:
                x_new = np.concatenate((x_new,x_tmp),axis=0)
                y_tmp = np.array([key for i in range(len(x_tmp))])
                y_new = np.concatenate((y_new,y_tmp),axis=0)
            index = index + 1
        return x_new,y_new


    def __resample_1(self,data,n_samples):
        """
        重采样,对数据集进行扩展/收缩,使数据集的数量增加/减少

        固定replace=True,如此,样本数据不仅可以减少,而且还可以增加 
        """
        from sklearn.utils import resample
        data = resample(data, n_samples=n_samples, replace=True)
        return data 

    def sort_by_lable(self,x,y,print_level=2):
        """
        按标签对数据集分类,每类标签一个数据集列表,

        return 
        --------------------------------
        不重复字典,标签字典,每个标签对应该标签所有的数据集
        """
        y_lable = np.reshape(y,(1,-1)) 
        lable = y_lable[0] 

        index = 0 
        # 分类列表,每类标签对应一个列表
        sort_dict = {}
        for ss in set(y):
            sort_dict[ss] = []

        for v in lable:
            sort_dict[v].append(x[index])
            index = index + 1

        return sort_dict

    def get_data_by_lable(self, x, y, data_size_every_lable):
        """"分层抽样

        data_size_every_lable:每个类别的数据量,如果有10个类别,总数据量为10*data_size


        从原数据集中，抽取一部分数据出来,
        接每个标签类别获取指定行数的数据,
        防止出现数据集中只有一个类别的情况，
        单类别场景,模型无法处理，也没有处理的必要
        """
        x_new = []
        y_new = []

        data_count = {}
        max_len = data_size_every_lable 
        index = 0
        for v in y:
            
            if v in data_count:
                data_count[v] += 1
            else:
                data_count[v] = 1
            if data_count[v] < max_len:
                y_new.append(v)
                x_new.append(x[index])
            index += 1
        return x_new,y_new
    
    def lable_encoding(self, lable_y, print_level=2):
        """
        文本分类打标签
        1. 取不重复分类数据集set
        2. 建立元组(标签名称，该标签在set中的索引下标)
        3. 转换为字典{标签名称：索引下标}
        4. 获取原分类名称对应的索引下标列表

        return
        ----------------------------------
        lable encoding后的列表和对应的字典,
        
        其中的类别转换为0,1,2,3,...等索引下标 

        """
        st = set(lable_y)
        dt = dict(zip(st,range(len(st))))
   
        lable_dict = dt
        self.log(lable_dict, print_level=print_level)
        lable_index = np.array([dt[k] for k in lable_y])

        return lable_index,lable_dict

    # def onehot_keras(self,y):
    #     """
    #     使用keras to_categorical方法独热编码,类别数为不重复标签个数 

    #     目前的独热编码,如果句子有重复的字或词,则不考虑这种场景 
    #     """
    #     from keras.utils import to_categorical
    #     num_classes = len(set(y))
    #     y = to_categorical(y, num_classes=num_classes)
    #     return y 

    
    def onehot_pd(self, dataset, to_numpy=True):
        """
        对整个数据集进行独热编码,不准备进行独热编码的列提前过滤掉不要包含进来

        目前的独热编码,如果句子有重复的字或词,则不考虑这种场景 
        """
        if isinstance(data, pd.DataFrame):
            df = dataset
        else:
            data = np.array(dataset)
            df = numpy2pd(data)
            print("columns:",df.columns)

        dataset = pd.get_dummies(data = df, columns=df.columns)
        if to_numpy:
            data = pd2numpy(dataset)
            return data 
        return dataset
    
    def onehot_encoding(data,c_names):
        """列拆分后删除旧列
        """
        for cname in c_names:
            c_new_1 = pd.get_dummies(data[cname], prefix=cname)
            data = pd.concat([data,c_new_1],axis=1)
            data.drop([cname],axis=1,inplace=True)
        return data.astype(np.float32).round(2)

    def onehot_text(self, text, split_flag="\n"):
        """
        一个段落 或 一句话 的独热编码 

        目前的独热编码,如果句子有重复的字或词,则按一个字或词计算 

        示例
        ---------------------------------------
        ss = "啊哈舍不得璀璨俗世,啊哈躲不开痴恋的欣慰,啊哈找不到色相代替,啊哈参一生参不透这条难题"
            
        onehot_text(ss,split_flag=",")


        return
        -------------------------------
        段落的向量表示,分词列表,去重排序后的词条

        """
        import jieba 
        # 原始词列表 
        ss = text 
        word_all = ""
        if split_flag == "":  # 按空白切词
            token_segments = ss.split()
        else:
            token_segments = ss.split(split_flag)  # 划分句子或段落
        # print(token_segments)
        for seg in token_segments:
            word_all = word_all + seg 
        words = jieba.lcut(word_all)           # 词汇列表 

        vocab = sorted(set(words))      # 去重后的词条 

        row_size = len(words)           # 某个词在整个段落或句子中的位置 
        col_size = len(vocab)           # 多少个不重复的词或特征 ,某个词条在向量中的位置 

        #初始化0矩阵
        import numpy as np 
        onehot_vector = np.zeros((row_size,col_size),dtype=int)

        for i,word in enumerate(words):
            onehot_vector[i,vocab.index(word)] = 1 

        return onehot_vector,words,vocab



class CsvStat():
    """
    csv文件数据处理
    """
    print_level = 2 
    
    def __init__(self,data=None, print_level=2) -> None:
        """
        日志输出级别:
        0-什么都不输出,1-输出少量信息,2-详细的输出,3-超级详细的代码调试信息
        
        - data: pandas数表 
         
        """
        self.print_level = print_level
        # self.score_list = []
        self.data = data 

    def update_print_level(self,print_level):
        self.print_level = print_level


    def log(self,msg, print_level=1):
        if self.print_level >= print_level:
            print(msg)
            

    def stat(self, csv_path=""):
        """
        使用pandas统计数据信息
        """
        if csv_path=="":
            print(type(self.data))
            print(self.data.info())
            print(self.data.describe())
        else:
            fil = pd.read_csv(csv_path)
            self.data = fil 
            info = fil.info()
            self.log(info)
            desc = fil.describe()
            self.log(desc)
            
    def update_data(self,data):
        self.data = data 

    def columns(self,print_level=3):
        cols = self.data.columns.tolist()
        self.log(cols,print_level)
        # cols = self.data.columns
        # for c in cols:
        #     print(c)
        #     print(self.data[c].isnull())
        #     print("---------------")
        return cols

    
    def head(self,num):
        return self.data.head(num)


    def col_filter(self,regex):
        """
        选择指定的列,不同的列以|分隔,"name|age",
        "一元.*" 匹配 "一元一次","一元二次"等所有以"一元"开头的字符串 
        """
        self.data = self.data.filter(regex=regex)
        self.log("数据过滤之后的列-------------------------:",2)
        self.log(self.data.info(),2)

    def empty_num(self,col_name):
        self.data.loc[(self.data[col_name].isnull()), col_name] = np.mean(self.data[col_name])

    def empty_str(self,col_name,char_null="N"):
        self.data.loc[(self.data[col_name].isnull()), col_name] = char_null

    def error_max_7mean(self,col_name):
        """
        超过均值7倍的数据转为均值7倍
        """
        col_mean = np.mean(self.data[col_name])
        self.data[col_name][self.data[col_name]>7*col_mean] = 7*col_mean

    def word2id(self,c_names,word2id=None):
        """
        return 
        -----------------------------
        每个列的编码字典,'<UNK>':0，即每一列的索引0代表未记录的词
        
        """
        cls_dict = {'<UNK>':0}
        ll_add = 1
        
        if word2id is not None :
            ll_add = len(word2id)+1
            
        for cname in c_names:
            _words_set = set(self.data[cname]) 
            if word2id is not None :
                _words_set = _words_set - set(word2id.keys())
            
            _word2id = dict(zip(_words_set, range(ll_add,ll_add+len(_words_set))))
            if word2id is not None :
                _word2id.update(word2id)
            cls_dict[cname] = _word2id
            idlist = [_word2id[val] for val in self.data[cname]]  # Using list comprehension
            self.data.loc[:, cname] = idlist
        return cls_dict



    def onehot_encoding(self,c_new_names):
        for cname in c_new_names:
            c_new_1 = pd.get_dummies(self.data[cname], prefix=cname)
            self.data = pd.concat([self.data,c_new_1],axis=1)
            self.data.drop([cname], axis=1, inplace=True)

    def col_drop(self,c_names):
        self.data.drop(c_names,axis=1,inplace=True)

    def replace_blank(self,to_float=True):
        """
        去除空格，并将NIL置0
        """
        for col in self.columns():
            index = 0
            for val in self.data[col]:
                # print("data type :",type(val))
                if isinstance(val,str):
                    matchObj = re.search( r'\s+', val)

                    if to_float:
                        # print("---col:{},val--{}==".format(col,val))
                        if val == "NIL":
                            val = "0"
                        if matchObj:
                            self.data[col].iloc[index] = float(val.replace('\s+','',regex=True,inplace=True))
                        else:
                            self.data[col].iloc[index] = float(val)
                    else:
                        if matchObj:
                            self.data[col].iloc[index] = val.replace('\s+','',regex=True,inplace=True)
                else:
                    continue
                index +=1





    def min_max_scaler(self,feature_range=(0, 1)):
        """
        return
        ---------------------
        <class 'numpy.ndarray'>,MinMaxScaler自动将pandas.core.frame.DataFrame转为了numpy.ndarray
        
        """
        self.scaler = MinMaxScaler(feature_range=feature_range)
        self.replace_blank()
        data = self.scaler.fit_transform(self.data)
        return data 

    def min_max_scaler_inverse(self, data):
        data = self.scaler.inverse_transform(data)
        return data 


def min_max(data,index_col=[]):
    """
    2维数据归一化处理
    """
    if not isinstance(data,np.ndarray):
        data = np.array(data)
    row_num,col_num = data.shape
    # print("len(index_list):",len(index_col))
    if len(index_col)==0:
        for i in range(col_num):
            _max,_min = data[:,i].max(),data[:,i].min()
            aa = _max 
            if _max>_min:
                aa = _max - _min 
            data[:,i] = (data[:,i]-_min )/aa 
    else:
        for i in index_col:
            _max,_min = data[:,i].max(),data[:,i].min()
            aa = _max 
            if _max>_min:
                aa = _max - _min 
            data[:,i] = (data[:,i]-_min )/aa  
    return data 



def pd_value_map(data,key_name="param_id", value_name="param_value", value_type_name=None, type_mapping = None ):
    """按'int', 'float', 'str', 'bool'等类型对数据进行转换
    """
    if value_type_name is None:
        result_dict = dict(zip(data['key_name'], data['value_name']))
        return result_dict

    if type_mapping is None:
        type_mapping = {
            'int': int,
            'float': float,
            'str': str,
            'bool': lambda x: eval(x)  
            }
    type_list = data[value_type_name].tolist()
    data['value_type'] = [type_mapping[t] for t in type_list]  # 这里使用了硬编码的列表来模拟转换过程
    
    df = pd.DataFrame(data)
    
    result_dict = {}
    for index, row in df.iterrows():
        param_id = row[key_name]
        param_value = row[value_name]
        value_type_func = row[value_type_name]
        print("value_type_func",value_type_func)

        if value_type_func == 'float':
            converted_value = float(param_value) if param_value != 'None' else None  # 处理可能的'None'字符串（如果需要）
        if value_type_func == 'int':
            converted_value = int(param_value) if param_value != 'None' else None  # 处理可能的'None'字符串（如果需要）
        if value_type_func == 'str':
            converted_value = str(param_value) if param_value != 'None' else None  # 处理可能的'None'字符串（如果需要）
        
        
        # 应用转换函数
        #converted_value = value_type_func(param_value) if param_value != 'None' else None  # 处理可能的'None'字符串（如果需要）
        
        # 将转换后的值添加到字典中
        result_dict[param_id] = converted_value
        
    return result_dict

def value_map(data,key_name="param_id", value_name="param_value", value_type_name=None, type_mapping = None ):
    """按'int', 'float', 'str', 'bool'等类型对数据进行转换

    params
    ----------------------------
    -data: pandas数表 
    -type_mapping: None默认为{'int': int,'float': float,'str': str,'bool': lambda x: eval(x) }

    exmaples
    -----------------------------------
    result_dict = value_map(data,key_name='param_id',value_name="param_value",value_type_name="value_type")


    """
    if value_type_name is None:
        result_dict = dict(zip(data['key_name'], data['value_name']))
        return result_dict

    if type_mapping is None:
        type_mapping = {
            'int': int,
            'float': float,
            'str': str,
            'bool': lambda x: eval(x)  
            }

    type_list = data[value_type_name].tolist()
    data['value_type'] = [type_mapping[t] for t in type_list]  # 这里使用了硬编码的列表来模拟转换过程
    
    df = pd.DataFrame(data)
    
    result_dict = {}
    for index, row in df.iterrows():
        param_id = row[key_name]
        param_value = row[value_name]
        value_type_func = row[value_type_name]
        
        # 应用转换函数
        converted_value = value_type_func(param_value) if param_value != 'None' else None  # 处理可能的'None'字符串（如果需要）
        
        # 将转换后的值添加到字典中
        result_dict[param_id] = converted_value
        
    return result_dict


if __name__ == "__main__":
    OneHot.get_one_hot_test()  # tensor([0., 0., 0., 1., 0.])
    pass 