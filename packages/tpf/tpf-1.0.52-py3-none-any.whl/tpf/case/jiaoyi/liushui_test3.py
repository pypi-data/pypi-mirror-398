"""
乳腺癌数据集特征选择和降维示例
使用 feature_selection_and_reduction 方法进行特征的选择
"""

import pandas as pd
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.preprocessing import StandardScaler
import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'tpf'))

from tpf.data.feature.liushui import FeatureEngineeringPipeline, FeatureConfig, pc

def load_breast_cancer_data():
    """
    加载乳腺癌数据集

    Returns:
        tuple: (DataFrame, 特征列表, 目标变量)
    """
    # 加载sklearn内置的乳腺癌数据集
    cancer = load_breast_cancer()

    # 创建DataFrame
    df = pd.DataFrame(cancer.data, columns=cancer.feature_names)
    df['target'] = cancer.target

    print(f"乳腺癌数据集形状: {df.shape}")
    print(f"特征数量: {len(cancer.feature_names)}")
    print(f"目标变量分布: {np.bincount(cancer.target)}")
    print(f"类别名称: {cancer.target_names}")

    return df, cancer.feature_names.tolist(), 'target'

def prepare_breast_cancer_for_selection(df, cols=None):
    """
    准备用于特征选择的乳腺癌数据

    Args:
        df: 乳腺癌数据集DataFrame
        cols: 使用的特征列列表，如果为空则使用所有数值特征列

    Returns:
        DataFrame: 准备好的数据
    """
    if cols is None:
        # 使用所有特征列（排除目标变量）
        exclude_cols = ['target']
        cols = [col for col in df.columns if col not in exclude_cols]

    print(f"使用的特征列数量: {len(cols)}")
    print(f"使用的特征列: {cols[:5]}..." if len(cols) > 5 else f"使用的特征列: {cols}")

    # 选择数据
    df_selected = df[cols + ['target']].copy()

    # 标准化数据（特征选择前的预处理）
    feature_cols = [col for col in df_selected.columns if col != 'target']
    scaler = StandardScaler()
    df_selected[feature_cols] = scaler.fit_transform(df_selected[feature_cols])

    # 添加一些标识列以模拟交易数据的结构
    df_selected['sample_id'] = range(len(df_selected))
    df_selected['time_index'] = range(len(df_selected))

    print(f"预处理后数据形状: {df_selected.shape}")
    print(f"数值特征列数量: {len(feature_cols)}")

    return df_selected

def create_breast_cancer_feature_config():
    """
    为乳腺癌数据集创建特征配置

    Returns:
        FeatureConfig: 配置对象
    """
    config = FeatureConfig(
        # 基础特征（乳腺癌数据集没有价格变化概念，使用默认配置）
        basic_features=['mean_radius', 'mean_texture', 'mean_perimeter', 'mean_area', 'mean_smoothness'],

        # 移动窗口特征（为医学特征创建滑动窗口特征）
        moving_windows=[3, 5, 10],
        moving_indicators=['mean', 'std', 'min', 'max', 'median'],

        # 其他特征保持默认配置
        rsi_periods=[14],
        momentum_indicators=['momentum_3', 'momentum_5'],
        volatility_periods=[5, 10],
        volume_windows=[5, 10],
        technical_windows=[5, 10],
        time_features=['hour', 'day_of_week'],
        lag_periods=[1, 2, 3],
        high_order_windows=[3, 5],
        risk_windows=[5, 10]
    )

    return config

def demonstrate_feature_selection_and_reduction(df, cols=None):
    """
    演示特征选择和降维过程

    Args:
        df: 输入数据框
        cols: 使用的列列表，如果为空则使用所有数值特征

    Returns:
        tuple: (选择后的DataFrame, 选择的特征列表)
    """
    print("=" * 60)
    print("乳腺癌数据集特征选择和降维示例")
    print("=" * 60)

    # 1. 准备数据
    print("\n1. 准备数据...")
    df_prepared = prepare_breast_cancer_for_selection(df, cols)

    # 2. 创建特征配置
    print("\n2. 创建特征配置...")
    config = create_breast_cancer_feature_config()

    # 3. 进行特征选择和降维
    print("\n3. 开始特征选择和降维...")

    # 定义标识列
    identity_cols = ['sample_id', 'time_index']
    price_col = 'mean_radius'  # 使用第一个特征作为"价格"列的替代
    time_col = 'time_index'    # 使用时间索引作为时间列

    print(f"标识列: {identity_cols}")
    print(f"价格列替代: {price_col}")
    print(f"时间列: {time_col}")

    try:
        # 调用特征选择和降维方法
        df_selected, selected_features = FeatureEngineeringPipeline.feature_selection_and_reduction(
            df=df_prepared,
            config=config,
            identity_cols=identity_cols,
            price_col=price_col,
            time_col=time_col
        )

        print(f"\n4. 特征选择结果:")
        original_feature_count = len([col for col in df_prepared.columns if col not in identity_cols + ['target', time_col]])
        print(f"原始特征数量: {original_feature_count}")
        print(f"选择后特征数量: {len(selected_features)}")
        print(f"最终数据形状: {df_selected.shape}")

        print(f"\n选择的特征:")
        for i, feature in enumerate(selected_features, 1):
            print(f"  {i:2d}. {feature}")

        # 特征重要性分析
        if selected_features:
            print(f"\n5. 特征重要性分析:")
            # 计算与目标变量的相关性
            correlations = []
            for feature in selected_features:
                if feature in df_selected.columns and df_selected[feature].dtype in ['int64', 'float64']:
                    corr = df_selected[feature].corr(df_selected['target'])
                    correlations.append((feature, abs(corr)))

            # 按相关性排序
            correlations.sort(key=lambda x: x[1], reverse=True)

            print("与目标变量的相关性（前10个）:")
            for i, (feature, corr) in enumerate(correlations[:10], 1):
                print(f"  {i:2d}. {feature}: {corr:.4f}")

        return df_selected, selected_features

    except Exception as e:
        print(f"特征选择过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return None, None

# 简化的函数调用示例
def simple_feature_selection_example():
    """
    简单的特征选择函数调用示例
    """
    print("=" * 60)
    print("简单函数调用示例")
    print("=" * 60)

    # 加载数据
    df, feature_names, _ = load_breast_cancer_data()

    # 选择部分特征
    selected_features = ['mean radius', 'mean texture', 'mean perimeter', 'mean area', 'mean smoothness']

    # 准备数据
    df_prepared = prepare_breast_cancer_for_selection(df, selected_features)

    # 创建配置
    config = create_breast_cancer_feature_config()

    # 定义参数
    identity_cols = ['sample_id', 'time_index']
    price_col = 'mean_radius'
    time_col = 'time_index'

    # 直接调用特征选择方法
    df_result, selected_feature_list = FeatureEngineeringPipeline.feature_selection_and_reduction(
        df=df_prepared,
        config=config,
        identity_cols=identity_cols,
        price_col=price_col,
        time_col=time_col
    )

    print(f"输入特征: {selected_features}")
    print(f"选择结果: {selected_feature_list}")
    print(f"结果数据形状: {df_result.shape}")

    return df_result, selected_feature_list

def main():
    """主函数"""
    print("乳腺癌数据集特征选择和降维演示")
    print("=" * 60)

    # 1. 加载数据
    df, feature_names, _ = load_breast_cancer_data()

    # 2. 演示1: 使用所有特征
    print("\n" + "="*60)
    print("示例1: 使用所有特征进行选择")
    print("="*60)
    df_selected_all, features_all = demonstrate_feature_selection_and_reduction(df, cols=None)

    # 3. 演示2: 使用部分特征
    print("\n" + "="*60)
    print("示例2: 使用前10个特征进行选择")
    print("="*60)
    partial_features = feature_names[:10]  # 使用前10个特征
    df_selected_partial, features_partial = demonstrate_feature_selection_and_reduction(df, cols=partial_features)

    # 4. 演示3: 简单函数调用示例
    print("\n" + "="*60)
    print("示例3: 简单函数调用示例")
    print("="*60)
    df_simple, features_simple = simple_feature_selection_example()

    # 5. 总结
    print("\n" + "="*60)
    print("总结")
    print("="*60)
    print(f"原始数据集特征数量: {len(feature_names)}")
    if features_all:
        print(f"使用全部特征时的选择结果: {len(features_all)}个特征")
    if features_partial:
        print(f"使用前10个特征时的选择结果: {len(features_partial)}个特征")
    if features_simple:
        print(f"简单调用示例的选择结果: {len(features_simple)}个特征")

    print("\n特征选择方法包括:")
    print("- 方差阈值过滤")
    print("- 相关性过滤")
    print("- 互信息选择")
    print("- PCA降维")
    print("- 递归特征消除(RFE)")
    print("- 基于模型的重要性排序")

if __name__ == "__main__":
    main()