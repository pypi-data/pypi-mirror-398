#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
乳腺癌数据集特征选择示例
演示如何使用 liushui.py 中的 feature_selection_and_reduction 方法
"""

import pandas as pd
import numpy as np
from sklearn.datasets import load_breast_cancer
import sys
import os

# 添加项目路径
sys.path.append('/ai/wks/aitpf/src')
from tpf.data.feature.liushui import FeatureEngineeringPipeline, FeatureConfig

# 直接导入模块
# import importlib.util
# spec = importlib.util.spec_from_file_location("liushui", "/ai/wks/aitpf/src/tpf/data/feature/liushui.py")
# liushui = importlib.util.module_from_spec(spec)
# spec.loader.exec_module(liushui)

FeatureEngineeringPipeline = FeatureEngineeringPipeline
FeatureConfig = FeatureConfig

def load_breast_cancer_data():
    """加载乳腺癌数据集"""
    # 加载sklearn内置的乳腺癌数据集
    cancer = load_breast_cancer()

    # 创建DataFrame
    df = pd.DataFrame(cancer.data, columns=cancer.feature_names)

    # 添加目标变量（用作price_col的替代）
    df['target'] = cancer.target

    # 添加时间列（必需参数）
    df['DT_TIME'] = pd.date_range(start='2020-01-01', periods=len(df), freq='D')

    # 添加标识列
    df['ID'] = range(len(df))

    print(f"乳腺癌数据集加载完成:")
    print(f"样本数量: {len(df)}")
    print(f"特征数量: {len(cancer.feature_names)}")
    print(f"特征名称: {list(cancer.feature_names)}")
    print(f"目标变量分布: {df['target'].value_counts().to_dict()}")
    print(f"0: 恶性肿瘤, 1: 良性肿瘤")

    return df

def demonstrate_feature_selection():
    """演示特征选择过程"""
    print("="*60)
    print("乳腺癌数据集特征选择示例")
    print("="*60)

    # 1. 加载数据
    df = load_breast_cancer_data()
    print(f"\n原始数据概览:")
    print(df.head())
    print(f"\n数据统计信息:")
    print(df.describe())

    # 2. 创建特征配置
    config = FeatureConfig()

    # 3. 执行特征选择和降维
    print(f"\n开始特征选择和降维...")

    # 使用目标变量作为price_col的替代，ID作为identity_cols
    df_processed, selected_features = FeatureEngineeringPipeline.feature_selection_and_reduction(
        df=df,
        config=config,
        identity_cols=['ID', 'DT_TIME'],
        price_col='target',  # 使用目标变量替代价格列
        time_col='DT_TIME'
    )

    # 4. 分析结果
    print(f"\n特征选择结果:")
    print(f"原始特征数量: {len([col for col in df.columns if col not in ['ID', 'DT_TIME', 'target']])}")
    print(f"选择的特征数量: {len(selected_features)}")
    print(f"选择的特征: {selected_features}")

    # 5. 检查是否生成了PCA成分
    pca_features = [col for col in df_processed.columns if col.startswith('pca_component_')]
    if pca_features:
        print(f"\n生成的PCA成分: {pca_features}")
        print(f"PCA成分统计信息:")
        print(df_processed[pca_features].describe())

    # 6. 显示处理后的数据
    print(f"\n处理后的数据维度: {df_processed.shape}")
    print(f"包含的列: {list(df_processed.columns)}")

    # 7. 特征选择效果分析
    if len(selected_features) > 0:
        print(f"\n选择的特征与目标变量的相关性:")
        # 移除target本身，避免自相关
        features_for_corr = [f for f in selected_features if f != 'target']
        if features_for_corr:
            correlations = df_processed[features_for_corr + ['target']].corr()['target'].drop('target')
            correlations = correlations.sort_values(key=abs, ascending=False)
            print(correlations.head(10))

    return df_processed, selected_features

def analyze_feature_importance(df, selected_features):
    """分析特征重要性"""
    print(f"\n特征重要性分析:")

    if len(selected_features) == 0:
        print("没有选择到特征")
        return

    # 计算每个特征与目标变量的相关性
    correlations = {}
    for feature in selected_features:
        corr = df[feature].corr(df['target'])
        correlations[feature] = abs(corr)

    # 按相关性排序
    sorted_features = sorted(correlations.items(), key=lambda x: x[1], reverse=True)

    print("特征重要性排序（按与目标变量的绝对相关性）:")
    for i, (feature, corr) in enumerate(sorted_features[:10], 1):
        print(f"{i:2d}. {feature:25s}: {corr:.4f}")

    # 特征统计信息
    print(f"\n选择的特征的统计信息:")
    print(df[selected_features].describe())

if __name__ == "__main__":
    # 执行特征选择演示
    df_processed, selected_features = demonstrate_feature_selection()

    # 分析特征重要性
    analyze_feature_importance(df_processed, selected_features)

    print(f"\n特征选择完成！")
    print(f"这个示例展示了如何使用 feature_selection_and_reduction 方法对乳腺癌数据集进行特征选择。")
    print(f"该方法包含了以下步骤:")
    print(f"1. 方差阈值过滤 - 移除方差过低的特征")
    print(f"2. 相关性过滤 - 移除高度相关的特征")
    print(f"3. 统计特征选择 - 使用F回归选择与目标变量最相关的特征")
    print(f"4. PCA降维 - 当特征数量过多时进行主成分分析")