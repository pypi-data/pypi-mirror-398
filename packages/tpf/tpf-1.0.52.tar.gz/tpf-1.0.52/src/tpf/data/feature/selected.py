"""
通用特征评估与选择工具类
- 基于LightGBM的多轮训练特征频率评估
- 支持特征共线性分析
- 输出重要特征及其重要性分数和相关性分析
"""

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import logging

logger = logging.getLogger(__name__)

class FeatureSelected:
    """特征评估与选择通用类"""

    def __init__(self, X=None, y=None, label_name=None,
                 feature_eval_nums=10, num_boost_round=30,
                 max_feature_selected_num=200, corr_line=0.95,
                 normalize_features=True, random_state=42):
        """
        初始化特征评估器

        Parameters
        ----------
        X : pd.DataFrame, optional
            特征数据
        y : array-like, optional
            目标变量
        label_name : str, optional
            标签列名，当X包含标签时使用
        feature_eval_nums : int, default=10
            模型评估的频次，即取多少次训练的综合重要性排序列
        num_boost_round : int, default=30
            每次训练迭代提升的次数
        max_feature_selected_num : int, default=200
            最大保留列的个数
        corr_line : float, default=0.95
            相关性阈值，超过此阈值的特征会被去重
        normalize_features : bool, default=True
            是否对特征进行归一化处理
        random_state : int, default=42
            随机种子
        """
        self.feature_eval_nums = feature_eval_nums
        self.num_boost_round = num_boost_round
        self.max_feature_selected_num = max_feature_selected_num
        self.corr_line = corr_line
        self.normalize_features = normalize_features
        self.random_state = random_state

        if X is not None and y is not None:
            self.X = X.copy()
            self.y = y.copy()
        elif X is not None and label_name is not None:
            # 从X中分离标签
            self.X = X.drop(columns=label_name)
            self.y = X[label_name]
        else:
            self.X = None
            self.y = None

        self.original_columns = self.X.columns.tolist() if self.X is not None else None
        self.selected_features = None
        self.feature_importance_df = None
        self.correlation_pairs_df = None

    def _normalize_data(self, X, num_type=None):
        """数据归一化处理"""
        if not self.normalize_features:
            return X

        if num_type is None:
            num_type = X.select_dtypes(include=['number']).columns.tolist()

        if len(num_type) > 0:
            # 保存归一化参数，以便transform方法使用
            if not hasattr(self, 'normalization_params'):
                self.normalization_params = {}
                for col in num_type:
                    min_val = X[col].min()
                    max_val = X[col].max()
                    if max_val != min_val:
                        self.normalization_params[col] = (min_val, max_val)
                        X[col] = (X[col] - min_val) / (max_val - min_val)
                    else:
                        self.normalization_params[col] = (min_val, max_val)
                        X[col] = 0.0  # 如果所有值相同，设为0
            else:
                for col in num_type:
                    if col in self.normalization_params:
                        min_val, max_val = self.normalization_params[col]
                        if max_val != min_val:
                            X[col] = (X[col] - min_val) / (max_val - min_val)
                        else:
                            X[col] = 0.0

        return X

    def _frequency_feature_selection(self, X, y):
        """基于频率的特征选择"""
        feature_importance_sum = {}

        for epoch in range(self.feature_eval_nums):
            # 随机种子确保每次训练略有不同
            np.random.seed(self.random_state + epoch)

            # 划分训练集和测试集
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.3, random_state=self.random_state + epoch
            )

            # 创建LightGBM数据集
            train_data = lgb.Dataset(X_train, label=y_train, free_raw_data=False)
            test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

            # 设置参数
            params = {
                'objective': 'binary' if len(np.unique(y)) == 2 else 'multiclass',
                'metric': 'binary_logloss' if len(np.unique(y)) == 2 else 'multi_logloss',
                'boosting_type': 'gbdt',
                'force_col_wise': True,
                'verbose': -1,
                'seed': self.random_state + epoch
            }

            if len(np.unique(y)) > 2:
                params['num_class'] = len(np.unique(y))

            # 训练模型
            try:
                lgb_model = lgb.train(
                    params,
                    train_data,
                    num_boost_round=self.num_boost_round,
                    valid_sets=[test_data],
                    callbacks=[lgb.log_evaluation(0)]
                )

                # 获取特征重要性并累加
                feature_importance = lgb_model.feature_importance()
                feature_names = X.columns.tolist()

                for i, importance in enumerate(feature_importance):
                    feature_name = feature_names[i]
                    feature_importance_sum[feature_name] = feature_importance_sum.get(feature_name, 0) + importance

            except Exception as e:
                logger.warning(f"Round {epoch+1} training failed: {e}")
                continue

        # 按累加重要性排序，选择top特征
        if feature_importance_sum:
            sorted_features = sorted(feature_importance_sum.items(), key=lambda x: x[1], reverse=True)
            # 选择比目标多一倍的特征，为相关性分析留有余地
            num_to_select = min(self.max_feature_selected_num * 2, len(sorted_features))
            selected_features = [feat for feat, imp in sorted_features[:num_to_select]]
        else:
            selected_features = X.columns.tolist()

        return selected_features

    def _correlation_analysis(self, X):
        """特征相关性分析 - 基于特征重要性智能去重"""
        if not isinstance(X, pd.DataFrame):
            return X.columns.tolist(), pd.DataFrame()

        # 计算特征重要性（如果没有的话）
        if hasattr(self, 'temp_feature_importance'):
            feature_importance = self.temp_feature_importance
        else:
            # 快速计算特征重要性
            feature_importance = {}
            for col in X.columns:
                # 使用方差作为重要性的简单估计
                feature_importance[col] = X[col].var()

        # 计算相关性矩阵
        corr_matrix = X.corr().abs()

        # 找出高度相关的特征对
        high_corr_pairs = []
        features_to_remove = set()

        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if corr_val > self.corr_line:
                    col1 = corr_matrix.columns[i]
                    col2 = corr_matrix.columns[j]
                    high_corr_pairs.append({
                        'col1': col1,
                        'col2': col2,
                        'correlation': corr_val
                    })

                    # 保留重要性更高的特征，移除重要性较低的特征
                    imp1 = feature_importance.get(col1, 0)
                    imp2 = feature_importance.get(col2, 0)

                    if imp1 >= imp2:
                        features_to_remove.add(col2)
                    else:
                        features_to_remove.add(col1)

        # 保留不被移除的特征
        selected_features = [col for col in X.columns if col not in features_to_remove]

        correlation_df = pd.DataFrame(high_corr_pairs)

        return selected_features, correlation_df

    def _calculate_feature_importance(self, X, y):
        """计算最终特征重要性"""
        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=self.random_state
        )

        # 创建LightGBM数据集
        train_data = lgb.Dataset(X_train, label=y_train, free_raw_data=False)
        test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

        # 设置参数
        params = {
            'objective': 'binary' if len(np.unique(y)) == 2 else 'multiclass',
            'metric': 'binary_logloss' if len(np.unique(y)) == 2 else 'multi_logloss',
            'boosting_type': 'gbdt',
            'force_col_wise': True,
            'verbose': -1,
            'seed': self.random_state
        }

        if len(np.unique(y)) > 2:
            params['num_class'] = len(np.unique(y))

        # 训练模型
        lgb_model = lgb.train(
            params,
            train_data,
            num_boost_round=self.num_boost_round,
            valid_sets=[test_data],
            callbacks=[lgb.log_evaluation(0)]
        )

        # 获取特征重要性
        feature_importance = lgb_model.feature_importance()
        feature_names = X.columns.tolist()

        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': feature_importance
        })

        # 计算特征与标签的相关性
        corr_results = []
        for col in X.columns:
            try:
                corr_val = np.corrcoef(X[col], y)[0, 1]
                if np.isnan(corr_val):
                    corr_val = 0
            except:
                corr_val = 0
            corr_results.append(corr_val)

        importance_df['corr_label'] = corr_results

        return importance_df.sort_values('importance', ascending=False)

    def fit_transform(self, X=None, y=None, label_name=None, num_type=None):
        """
        执行特征评估与选择

        Parameters
        ----------
        X : pd.DataFrame, optional
            特征数据，如果为None则使用初始化时的数据
        y : array-like, optional
            目标变量，如果为None则使用初始化时的数据
        label_name : str, optional
            标签列名
        num_type : list, optional
            数值型列名列表，用于归一化

        Returns
        -------
        pd.DataFrame
            选择后的特征数据
        """
        # 使用提供的数据或初始化时的数据
        if X is not None:
            if y is not None:
                X_data = X.copy()
                y_data = y.copy()
            elif label_name is not None:
                X_data = X.drop(columns=label_name)
                y_data = X[label_name]
            else:
                raise ValueError("必须提供y或label_name")
        else:
            if self.X is None or self.y is None:
                raise ValueError("没有可用的数据")
            X_data = self.X.copy()
            y_data = self.y.copy()

        # 数据归一化
        X_data = self._normalize_data(X_data, num_type)

        logger.info(f"Starting feature selection, original feature count: {X_data.shape[1]}")

        # 第一步：基于频率的特征选择
        freq_selected_features = self._frequency_feature_selection(X_data, y_data)
        logger.info(f"Feature count after frequency selection: {len(freq_selected_features)}")

        # 如果选择的特征太少，直接返回所有特征
        if len(freq_selected_features) <= 2:
            logger.warning("Too few features selected, returning all features")
            self.selected_features = X_data.columns.tolist()
            self.feature_importance_df = pd.DataFrame({
                'feature': X_data.columns.tolist(),
                'importance': [1.0] * len(X_data.columns),
                'corr_label': [0.0] * len(X_data.columns)
            })
            self.correlation_pairs_df = pd.DataFrame()
            return X_data

        # 第二步：基于相关性的特征选择
        X_freq_selected = X_data[freq_selected_features]

        # 保存特征重要性信息用于相关性分析
        freq_importance = {}
        for i, feat in enumerate(freq_selected_features):
            freq_importance[feat] = len(freq_selected_features) - i  # 简单的重要性估计
        self.temp_feature_importance = freq_importance

        corr_selected_features, correlation_df = self._correlation_analysis(X_freq_selected)
        logger.info(f"Feature count after correlation selection: {len(corr_selected_features)}")

        # 如果相关性选择后特征太少，使用频率选择的结果
        if len(corr_selected_features) <= 2:
            X_final = X_freq_selected
        else:
            X_final = X_data[corr_selected_features]

        # 第三步：计算最终特征重要性
        importance_df = self._calculate_feature_importance(X_final, y_data)

        # 保存结果
        self.selected_features = X_final.columns.tolist()
        self.feature_importance_df = importance_df
        self.correlation_pairs_df = correlation_df

        logger.info(f"Final selected feature count: {len(self.selected_features)}")

        return X_final

    def transform(self, X):
        """
        对新数据应用特征选择

        Parameters
        ----------
        X : pd.DataFrame
            要转换的数据

        Returns
        -------
        pd.DataFrame
            选择后的特征数据
        """
        if self.selected_features is None:
            raise ValueError("请先调用fit_transform方法")

        # 应用特征选择
        X_transformed = X[self.selected_features].copy()

        # 如果有归一化参数，应用归一化
        if hasattr(self, 'normalization_params') and self.normalization_params:
            for col in X_transformed.columns:
                if col in self.normalization_params:
                    min_val, max_val = self.normalization_params[col]
                    if max_val != min_val:
                        X_transformed[col] = (X_transformed[col] - min_val) / (max_val - min_val)
                    else:
                        X_transformed[col] = 0.0

        return X_transformed

    def get_feature_importance(self):
        """
        获取特征重要性结果

        Returns
        -------
        pd.DataFrame
            包含feature, importance, corr_label列的数据框
        """
        return self.feature_importance_df.copy() if self.feature_importance_df is not None else pd.DataFrame()

    def get_correlation_pairs(self):
        """
        获取相关性分析结果

        Returns
        -------
        pd.DataFrame
            包含col1, col2, correlation列的数据框
        """
        return self.correlation_pairs_df.copy() if self.correlation_pairs_df is not None else pd.DataFrame()

    def get_selected_features(self):
        """
        获取选择的特征列表

        Returns
        -------
        list
            选择的特征名列表
        """
        return self.selected_features.copy() if self.selected_features is not None else []

    def summary(self):
        """
        Print feature selection summary information
        """
        if self.selected_features is None:
            print("Feature selection not yet performed")
            return

        print("=" * 50)
        print("Feature Selection Summary")
        print("=" * 50)
        print(f"Original feature count: {len(self.original_columns) if self.original_columns is not None else 'Unknown'}")
        print(f"Final selected feature count: {len(self.selected_features)}")
        if self.original_columns is not None:
            print(f"Feature retention rate: {len(self.selected_features)/len(self.original_columns)*100:.2f}%")
        print()

        if self.feature_importance_df is not None and len(self.feature_importance_df) > 0:
            print("Top 10 important features:")
            print(self.feature_importance_df.head(10)[['feature', 'importance', 'corr_label']].to_string(index=False))
            print()

        if self.correlation_pairs_df is not None and len(self.correlation_pairs_df) > 0:
            print(f"High correlation feature pairs (threshold > {self.corr_line}):")
            print(self.correlation_pairs_df.head(10).to_string(index=False))
            print()

        print("Selected feature list:")
        for i, feature in enumerate(self.selected_features, 1):
            print(f"{i:2d}. {feature}")
          

def feature_selection_lgbm(X, y,
                          feature_eval_nums=10,
                          num_boost_round=30,
                          max_feature_selected_num=100,
                          corr_line=0.95,
                          normalize_features=True,
                          random_state=42,
                          show_summary=True,
                          show_importance=True,
                          show_correlation=False):
    """
    Use FeatureSelected class for feature selection with customizable parameters

    Parameters
    ----------
    X : pd.DataFrame
        Feature data
    y : array-like
        Target variable
    feature_eval_nums : int, default=10
        Number of training evaluation rounds
    num_boost_round : int, default=30
        Number of iterations per round
    max_feature_selected_num : int, default=10
        Maximum number of features to select
    corr_line : float, default=0.95
        Correlation threshold for removing highly correlated features
    normalize_features : bool, default=True
        Whether to normalize features
    random_state : int, default=42
        Random seed for reproducibility
    show_summary : bool, default=True
        Whether to display feature selection summary
    show_importance : bool, default=True
        Whether to display feature importance details
    show_correlation : bool, default=False
        Whether to display correlation analysis results

    Returns
    -------
    tuple
        (selected_features, importance_df, correlation_df, selector)
    """
    if show_summary:
        print("=" * 60)
        print("Step 1: Feature Selection using FeatureSelected")
        print("=" * 60)

    # Initialize feature selector with provided parameters
    selector = FeatureSelected(
        feature_eval_nums=feature_eval_nums,
        num_boost_round=num_boost_round,
        max_feature_selected_num=max_feature_selected_num,
        corr_line=corr_line,
        normalize_features=normalize_features,
        random_state=random_state
    )

    # Execute feature selection
    X_selected = selector.fit_transform(X, y)

    # Display feature selection results
    if show_summary:
        selector.summary()

    # Get detailed feature importance information
    importance_df = selector.get_feature_importance()
    correlation_df = selector.get_correlation_pairs()
    selected_features = selector.get_selected_features()

    if show_importance:
        print("\nSelected feature importance details:")
        print(importance_df.to_string(index=False))

    if show_correlation and len(correlation_df) > 0:
        print("\nHigh correlation feature pairs:")
        print(correlation_df.to_string(index=False))

    return selected_features, importance_df, correlation_df 
          
            
if __name__ == '__main__':
    pass 