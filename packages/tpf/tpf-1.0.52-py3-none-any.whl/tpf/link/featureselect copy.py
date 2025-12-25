"""通用特征重要性评估与选择工具
- 基于LightGBM的多轮训练特征频率评估
- 支持特征共线性分析
- 输出重要特征及其重要性分数
"""

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("feature_selection.log", mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FeatureSelection")

class FeatureFrequencyEval:
    """基于频率的特征评估器"""
    
    def __init__(self, X, y, num_boost_round=30):
        """初始化特征评估器
        
        Parameters
        ----------
        X : array-like or DataFrame
            特征数据
        y : array-like
            目标变量
        num_boost_round : int, optional
            每轮训练的boosting轮数, by default 30
        """
        self.X = X
        self.y = y
        self.is_pd = isinstance(X, pd.DataFrame)
        self.num_boost_round = num_boost_round
        self.col_feature_importance = []
        self.model = None

    def train_model(self, X, y):
        """训练LightGBM模型并返回特征重要性
        
        Parameters
        ----------
        X : array-like
            特征数据
        y : array-like
            目标变量
            
        Returns
        -------
        array
            特征重要性数组
        """
        # 划分训练集和测试集  
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
        
        # 创建LightGBM数据集
        train_data = lgb.Dataset(X_train, label=y_train, free_raw_data=False)
        test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
        
        # 设置参数
        params = {
            'objective': 'binary' if len(np.unique(y)) == 2 else 'multiclass',
            'metric': 'binary_logloss' if len(np.unique(y)) == 2 else 'multi_logloss',
            'boosting_type': 'gbdt',
            'force_col_wise': True,
            'verbose': -1
        }
        
        if len(np.unique(y)) > 2:
            params['num_class'] = len(np.unique(y))
        
        # 训练模型
        lgb_model = lgb.train(
            params, 
            train_data, 
            num_boost_round=self.num_boost_round,  
            valid_sets=[test_data]
        )
        
        self.model = lgb_model
        return lgb_model.feature_importance()

    def add_feature_col(self, show_msg=False):
        """训练模型并累计特征重要性"""
        fti = self.train_model(self.X, self.y)
        
        # 初始化重要性累计数组
        if len(self.col_feature_importance) == 0:
            self.col_feature_importance = [0] * len(fti)
        
        # 将有贡献的特征计数加1
        feature_index_desc = np.argsort(fti)[::-1]
        
        for i in range(len(fti)):
            index_pos = feature_index_desc[i]
            if fti[index_pos] == 0:
                if show_msg:
                    logger.info(f"重要性0边界，第{i}列")
                break
            self.col_feature_importance[index_pos] += 1

    def get_used_cols(self, max_col_nums=200, arise_atleast=1):
        """获取使用频率高的特征列
        
        Parameters
        ----------
        max_col_nums : int, optional
            最大选择特征数, by default 200
        arise_atleast : int, optional
            最小出现次数, by default 1
            
        Returns
        -------
        array
            选择的特征索引
        """
        col_feature_desc = np.argsort(self.col_feature_importance)[::-1]
        
        selected_cols = []
        for i in range(len(col_feature_desc)):
            idx = col_feature_desc[i]
            if self.col_feature_importance[idx] >= arise_atleast:
                selected_cols.append(idx)
            if len(selected_cols) >= max_col_nums:
                break
        
        logger.info(f"选择了 {len(selected_cols)} 个特征，最高频率: {max(self.col_feature_importance)}")
        return np.array(selected_cols)

    def max_freq_cols(self, epoch=10, max_col_nums=200, arise_atleast=1, show_msg=False):
        """获取高频特征列
        
        Parameters
        ----------
        epoch : int, optional
            训练轮次, by default 10
        max_col_nums : int, optional
            最大选择特征数, by default 200
        arise_atleast : int, optional
            最小出现次数, by default 1
        show_msg : bool, optional
            是否显示详细信息, by default False
            
        Returns
        -------
        array
            选择的特征索引或列名
        """
        logger.info(f"开始特征选择，共{epoch}轮训练")
        
        for i in range(epoch):
            logger.info(f"第 {i+1}/{epoch} 轮训练")
            self.add_feature_col(show_msg)
        
        use_cols = self.get_used_cols(max_col_nums, arise_atleast)
        
        if self.is_pd:
            return self.X.columns[use_cols]
        return use_cols


class FeatureEval:
    """特征评估工具类"""
    
    def __init__(self, X, corr_line=0.95):
        self.X = X
        self.corr_line = corr_line
    
    def feature_select_corr(self, X, y, return_pd=True, threshold=None):
        """计算特征与目标变量的相关性"""
        if isinstance(X, pd.DataFrame):
            corr_results = []
            for col in X.columns:
                corr_val = np.corrcoef(X[col], y)[0, 1] if not np.isnan(np.corrcoef(X[col], y)[0, 1]) else 0
                corr_results.append({'feature_name': col, 'corr_label': corr_val})
            
            result_df = pd.DataFrame(corr_results)
            if threshold is not None:
                result_df = result_df[abs(result_df['corr_label']) >= threshold]
            return result_df
        
        return None
    
    def new_list(self):
        """基于相关性的特征选择（去除高度相关的特征）"""
        if not isinstance(self.X, pd.DataFrame):
            logger.warning("非DataFrame格式，跳过相关性分析")
            return list(range(self.X.shape[1]))
        
        # 计算特征相关性矩阵
        corr_matrix = self.X.corr().abs()
        
        # 选择上三角矩阵（不含对角线）
        upper_triangle = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )
        
        # 找出相关性高于阈值的特征对
        to_drop = set()
        for col in upper_triangle.columns:
            high_corr_cols = upper_triangle[col][upper_triangle[col] > self.corr_line].index
            to_drop.update(high_corr_cols)
        
        # 保留未被丢弃的特征
        selected_features = [col for col in self.X.columns if col not in to_drop]
        
        logger.info(f"共线性分析后保留 {len(selected_features)} 个特征，丢弃 {len(to_drop)} 个高度相关特征")
        return selected_features
    
    def pairs(self):
        """获取高度相关的特征对"""
        if not isinstance(self.X, pd.DataFrame):
            return pd.DataFrame(columns=['col1', 'col2', 'correlation'])
        
        corr_matrix = self.X.corr().abs()
        high_corr_pairs = []
        
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                col1, col2 = corr_matrix.columns[i], corr_matrix.columns[j]
                corr_val = corr_matrix.iloc[i, j]
                if corr_val > self.corr_line:
                    high_corr_pairs.append({
                        'col1': col1, 
                        'col2': col2, 
                        'correlation': corr_val
                    })
        
        return pd.DataFrame(high_corr_pairs)


def feature_selection(X, y, feature_eval_nums=10, num_boost_round=30, 
                     max_feature_selected_num=200, corr_line=0.95, debug=False):
    """通用特征选择函数
    
    Parameters
    ----------
    X : array-like or DataFrame
        特征数据
    y : array-like
        目标变量
    feature_eval_nums : int, optional
        训练轮次, by default 10
    num_boost_round : int, optional
        每轮训练的boosting轮数, by default 30
    max_feature_selected_num : int, optional
        最大选择特征数, by default 200
    corr_line : float, optional
        相关性阈值, by default 0.95
    debug : bool, optional
        调试模式, by default False
        
    Returns
    -------
    tuple
        (重要特征DataFrame, 相关性对DataFrame)
    """
    logger.info("开始特征选择流程")
    logger.info(f"输入数据形状: X={X.shape}, y={y.shape}")
    
    # 保存原始列名（如果是DataFrame）
    if isinstance(X, pd.DataFrame):
        old_cols = X.columns.tolist()
    else:
        old_cols = list(range(X.shape[1]))
    
    # 第一步：基于频率的特征选择
    ffe = FeatureFrequencyEval(X, y, num_boost_round)
    use_cols = ffe.max_freq_cols(
        epoch=feature_eval_nums, 
        max_col_nums=max_feature_selected_num * 2,  # 先选择2倍数量的特征
        arise_atleast=1, 
        show_msg=debug
    )
    
    logger.info(f"频率选择后特征数: {len(use_cols)}")
    
    # 如果选择的特征太少，返回所有特征
    if len(use_cols) <= 2:
        logger.warning("选择的特征过少，返回所有特征")
        important_features = pd.DataFrame({
            'feature': old_cols,
            'importance': [1] * len(old_cols)
        })
        return important_features, pd.DataFrame()
    
    # 筛选特征
    if isinstance(X, pd.DataFrame):
        X_selected = X[use_cols]
    else:
        X_selected = X[:, use_cols]
        use_cols = [f'feature_{i}' for i in use_cols]  # 为特征生成名称
    
    # 第二步：共线性分析
    fe = FeatureEval(X_selected, corr_line=corr_line)
    feature_corr_selected = fe.new_list()
    
    if len(feature_corr_selected) <= 2:
        logger.warning("共线性分析后特征过少，返回频率选择结果")
        important_features = pd.DataFrame({
            'feature': use_cols,
            'importance': [ffe.col_feature_importance[i] for i in range(len(use_cols))]
        })
        return important_features, fe.pairs()
    
    # 最终特征重要性评估
    if isinstance(X_selected, pd.DataFrame):
        X_final = X_selected[feature_corr_selected]
    else:
        # 对于数组，需要重新映射索引
        col_indices = [use_cols.index(col) for col in feature_corr_selected]
        X_final = X_selected[:, col_indices]
    
    # 训练最终模型获取精确的重要性分数
    X_train, X_test, y_train, y_test = train_test_split(X_final, y, test_size=0.3, random_state=42)
    
    train_data = lgb.Dataset(X_train, label=y_train)
    test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
    
    params = {
        'objective': 'binary' if len(np.unique(y)) == 2 else 'multiclass',
        'metric': 'binary_logloss' if len(np.unique(y)) == 2 else 'multi_logloss',
        'boosting_type': 'gbdt',
        'force_col_wise': True,
        'verbose': -1
    }
    
    if len(np.unique(y)) > 2:
        params['num_class'] = len(np.unique(y))
    
    final_model = lgb.train(
        params, 
        train_data, 
        num_boost_round=num_boost_round,
        valid_sets=[test_data]
    )
    
    # 创建结果DataFrame
    feature_importance = final_model.feature_importance()
    important_features = pd.DataFrame({
        'feature': feature_corr_selected,
        'importance': feature_importance
    }).sort_values('importance', ascending=False)
    
    logger.info("特征选择完成")
    return important_features, fe.pairs()


# 使用示例
if __name__ == "__main__":
    from sklearn.datasets import make_classification
    
    # 生成示例数据
    X, y = make_classification(
        n_samples=1000, 
        n_features=50, 
        n_informative=10, 
        n_redundant=5,
        random_state=42
    )
    
    # 转换为DataFrame（可选）
    X_df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(X.shape[1])])
    
    # 使用特征选择
    important_features, corr_pairs = feature_selection(
        X_df, 
        y, 
        feature_eval_nums=5,
        num_boost_round=20,
        max_feature_selected_num=15,
        corr_line=0.9,
        debug=True
    )
    
    print("重要特征:")
    print(important_features.head(10))
    
    print("\n高度相关的特征对:")
    print(corr_pairs.head())