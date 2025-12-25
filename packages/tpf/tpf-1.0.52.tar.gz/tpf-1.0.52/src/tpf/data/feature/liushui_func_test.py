#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
liushui_func.py 的测试文件和使用说明
演示如何使用整合版特征计算函数
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加路径以导入模块
sys.path.append('/ai/wks/aitpf/src')
sys.path.append('/ai/wks/aitpf/src/tpf/data/feature')
from liushui_func import calculate_liushui_features, calculate_features_based_on_selected

def create_sample_data(n_rows=1000):
    """
    创建示例数据用于测试

    Args:
        n_rows: 数据行数

    Returns:
        pd.DataFrame: 包含示例数据的DataFrame
    """
    print(f"创建示例数据，包含 {n_rows} 行...")

    # 创建时间序列
    start_date = datetime(2023, 1, 1)
    dates = [start_date + timedelta(hours=i) for i in range(n_rows)]

    # 创建价格数据（模拟随机游走）
    np.random.seed(42)
    price_changes = np.random.normal(0, 0.02, n_rows)
    prices = [1000.0]  # 起始价格
    for change in price_changes[1:]:
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 100))  # 确保价格不为负

    # 创建余额数据（与价格相关但有波动）
    balances = [p * np.random.uniform(0.8, 1.2) for p in prices]

    # 创建金额数据
    amounts = [p * np.random.uniform(100, 1000) for p in prices]

    # 创建标识列
    account_nums = [f'ACC_{i%100:04d}' for i in range(n_rows)]
    party_ids = [f'PARTY_{i%50:04d}' for i in range(n_rows)]

    # 创建DataFrame
    df = pd.DataFrame({
        'DT_TIME': dates,
        'AMT': prices,
        'ACCBAL': balances,
        'CNY_AMT': amounts,
        'ACCT_NUM': account_nums,
        'PARTY_ID': party_ids,
        'OPP_PARTY_ID': [f'OPP_{i%30:04d}' for i in range(n_rows)],
        'ACCT': [f'ACCT_{i%20:04d}' for i in range(n_rows)],
        'TCAC': [f'TCAC_{i%10:04d}' for i in range(n_rows)],
        'TSTM': [f'TSTM_{i%5:04d}' for i in range(n_rows)]
    })

    print(f"示例数据创建完成，形状: {df.shape}")
    print(f"数据列: {list(df.columns)}")
    print(f"时间范围: {df['DT_TIME'].min()} 到 {df['DT_TIME'].max()}")
    print(f"价格范围: {df['AMT'].min():.2f} 到 {df['AMT'].max():.2f}")

    return df

def example_1_basic_usage():
    """
    示例1: 基础使用方法
    使用所有默认参数计算特征
    """
    print("\n" + "="*60)
    print("示例1: 基础使用方法")
    print("="*60)

    # 创建示例数据
    df = create_sample_data(500)

    # 使用默认参数计算特征
    print("\n使用默认参数计算所有特征...")
    result_df = calculate_liushui_features(df)

    print(f"\n原始数据形状: {df.shape}")
    print(f"特征计算后形状: {result_df.shape}")
    print(f"新增特征数量: {result_df.shape[1] - df.shape[1]}")

    # 显示新增的特征列
    original_cols = set(df.columns)
    new_cols = [col for col in result_df.columns if col not in original_cols]
    print(f"\n新增的特征列（前10个）: {new_cols[:10]}")

    # 显示一些特征统计信息
    if 'price_change_rate' in result_df.columns:
        print(f"\n价格变化率统计:")
        print(f"  均值: {result_df['price_change_rate'].mean():.6f}")
        print(f"  标准差: {result_df['price_change_rate'].std():.6f}")
        print(f"  最小值: {result_df['price_change_rate'].min():.6f}")
        print(f"  最大值: {result_df['price_change_rate'].max():.6f}")

    return result_df

def example_2_selective_features():
    """
    示例2: 选择性计算特征
    只计算特定类型的特征
    """
    print("\n" + "="*60)
    print("示例2: 选择性计算特征")
    print("="*60)

    # 创建示例数据
    df = create_sample_data(300)

    # 只计算基础价格特征和移动窗口特征
    print("\n只计算基础价格特征和移动窗口特征...")
    result_df = calculate_liushui_features(
        df,
        # 基础价格特征
        calc_price_change_rate=True,
        calc_log_return=True,
        calc_price_amplitude=False,  # 关闭
        calc_opening_gap=False,      # 关闭
        calc_price_position=False,   # 关闭

        # 移动窗口特征
        moving_windows=[5, 10],
        calc_ma=True,
        calc_ema=True,
        calc_std=True,
        calc_max=False,              # 关闭
        calc_min=False,              # 关闭

        # 关闭其他所有特征
        calc_momentum=False,
        calc_roc=False,
        calc_historical_volatility=False,
        calc_volume_change_rate=False,
        calc_resistance_level=False,
        calc_hour=False,
        calc_derivatives=False,
        calc_var=False,

        verbose=True
    )

    print(f"\n原始数据形状: {df.shape}")
    print(f"选择性特征计算后形状: {result_df.shape}")
    print(f"新增特征数量: {result_df.shape[1] - df.shape[1]}")

    # 显示移动平均特征
    ma_cols = [col for col in result_df.columns if 'MA_' in col]
    print(f"\n移动平均特征: {ma_cols}")

    return result_df

def example_3_custom_parameters():
    """
    示例3: 自定义参数
    使用自定义的窗口参数和其他配置
    """
    print("\n" + "="*60)
    print("示例3: 自定义参数")
    print("="*60)

    # 创建示例数据
    df = create_sample_data(200)

    # 使用自定义参数
    print("\n使用自定义窗口参数...")
    result_df = calculate_liushui_features(
        df,

        # 自定义窗口参数
        moving_windows=[3, 7, 14, 21],
        rsi_periods=[9, 14, 21],
        volatility_periods=[7, 14, 30],
        volume_windows=[5, 10, 20],
        technical_windows=[10, 20, 30],
        lag_periods=[1, 3, 5],
        high_order_windows=[3, 5],
        risk_windows=[10, 20, 30],

        # MACD参数
        macd_fast=10,
        macd_slow=20,
        macd_signal=8,

        # 选择特定特征
        calc_price_change_rate=True,
        calc_log_return=True,
        calc_ma=True,
        calc_ema=True,
        calc_std=True,

        # 动量指标
        calc_momentum=True,
        calc_roc=True,

        # 波动率指标
        calc_historical_volatility=True,
        calc_atr=True,

        # 风险指标
        calc_var=True,
        calc_max_drawdown=True,
        calc_sharpe_ratio=True,

        # 数据清理
        handle_outliers=True,
        outlier_threshold=2.5,

        verbose=True
    )

    print(f"\n原始数据形状: {df.shape}")
    print(f"自定义参数计算后形状: {result_df.shape}")
    print(f"新增特征数量: {result_df.shape[1] - df.shape[1]}")

    # 显示RSI特征
    rsi_cols = [col for col in result_df.columns if 'RSI_' in col]
    print(f"\nRSI特征: {rsi_cols}")

    # 显示风险特征
    risk_cols = [col for col in result_df.columns if any(x in col for x in ['VaR_', 'max_drawdown', 'sharpe_ratio'])]
    print(f"\n风险特征: {risk_cols[:5]}...")  # 只显示前5个

    print(f"\n result_df.shape: {result_df.shape}")


    return result_df

def example_4_feature_selection():
    """
    示例4: 特征选择
    启用自动特征选择功能
    """
    print("\n" + "="*60)
    print("示例4: 特征选择")
    print("="*60)

    # 创建示例数据
    df = create_sample_data(400)

    # 计算特征并启用特征选择
    print("\n计算特征并启用自动特征选择...")
    result_df = calculate_liushui_features(
        df,

        # 计算多种特征
        moving_windows=[3, 5, 7],
        rsi_periods=[7, 14],
        volatility_periods=[5, 10],

        # 启用特征选择
        enable_feature_selection=True,
        variance_threshold=0.001,  # 方差阈值
        k_best_features=30,        # 选择前30个特征
        verbose=True
    )

    print(f"\n原始数据形状: {df.shape}")
    print(f"特征选择后形状: {result_df.shape}")

    # 获取特征列
    identity_cols = ['ACCT_NUM', 'PARTY_ID', 'OPP_PARTY_ID', 'ACCT', 'TCAC', 'TSTM', 'DT_TIME']
    feature_cols = [col for col in result_df.columns if col not in identity_cols]
    print(f"最终特征数量: {len(feature_cols)}")
    print(f"特征列示例: {feature_cols[:10]}")

    return result_df, feature_cols

def example_5_selected_features():
    """
    示例5: 基于选定特征计算指标
    使用已选择的特征计算相关指标，提高效率和针对性
    """
    print("\n" + "="*60)
    print("示例5: 基于选定特征计算指标")
    print("="*60)

    # 创建示例数据
    df = create_sample_data(500)

    # 1. 首先使用特征选择获取目标特征
    print("1. 使用特征选择获取目标特征...")
    selected_df, selected_features = example_4_feature_selection()

    print(f"目标特征数量: {len(selected_features)}")
    print(f"目标特征示例: {selected_features[:5]}")

    # 2. 使用新方法基于选定特征计算
    print("\n2. 基于选定特征计算指标...")
    result_df = calculate_features_based_on_selected(
        df,
        selected_features=selected_features,
        moving_windows=[3, 5, 7],
        volume_windows=[3, 5, 7],
        technical_windows=[5, 10, 20],
        lag_periods=[1, 2, 3],
        verbose=True
    )

    print(f"\n基于选定特征计算结果:")
    print(f"原始数据形状: {df.shape}")
    print(f"计算结果形状: {result_df.shape}")

    # 获取计算的特征列
    identity_cols = ['ACCT_NUM', 'PARTY_ID', 'OPP_PARTY_ID', 'ACCT', 'TCAC', 'TSTM', 'DT_TIME']
    computed_features = [col for col in result_df.columns if col not in identity_cols]

    print(f"成功计算的特征数量: {len(computed_features)}")
    print(f"特征覆盖率: {len(computed_features)/len(selected_features):.1%}")

    # 3. 性能对比
    print("\n3. 性能对比...")
    import time

    # 原始方法
    start_time = time.time()
    original_result = calculate_liushui_features(
        df,
        enable_feature_selection=True,
        k_best_features=len(selected_features),
        verbose=False
    )
    original_time = time.time() - start_time

    # 新方法
    start_time = time.time()
    new_result = calculate_features_based_on_selected(
        df,
        selected_features=selected_features,
        verbose=False
    )
    new_time = time.time() - start_time

    print(f"原始方法时间: {original_time:.3f}秒")
    print(f"新方法时间: {new_time:.3f}秒")
    print(f"性能提升: {original_time/new_time:.1f}倍")
    print(f"时间节省: {(original_time-new_time)/original_time:.1%}")

    # 4. 显示部分结果
    print(f"\n4. 计算结果示例...")
    print(f"特征列示例: {computed_features[:8]}")

    # 显示前几行数据
    display_cols = identity_cols[:2] + computed_features[:4]
    print(f"\n前3行数据:")
    print(result_df[display_cols].head(3))

    return result_df

def print_usage_guide():
    """
    打印详细的使用指南
    """
    print("\n" + "="*80)
    print("calculate_liushui_features 函数使用指南")
    print("="*80)

    guide = """
基本语法:
    result_df = calculate_liushui_features(df, **kwargs)

参数说明:

1. 数据参数:
    - df: 输入的DataFrame，必须包含时间、价格、余额等列
    - time_col: 时间列名，默认为'DT_TIME'
    - price_col: 价格列名，默认为'AMT'
    - balance_col: 余额列名，默认为'ACCBAL'
    - amount_col: 金额列名，默认为'CNY_AMT'
    - identity_cols: 标识列列表，默认为常用账户相关列

2. 特征类型开关参数 (计算控制):
    基础价格特征:
    - calc_price_change_rate: 价格变化率
    - calc_log_return: 对数收益率
    - calc_price_amplitude: 价格振幅
    - calc_opening_gap: 开盘跳空
    - calc_price_position: 价格位置

    移动窗口特征:
    - calc_ma: 简单移动平均
    - calc_ema: 指数移动平均
    - calc_std: 标准差
    - calc_max/min: 最大最小值
    - calc_q25/q50/q75: 分位数
    - calc_iqr: 四分位距
    - calc_cv: 变异系数
    - calc_price_vs_ma: 价格与移动平均比值
    - calc_price_zscore: 价格Z分数

    动量指标:
    - calc_momentum: 动量指标
    - calc_roc: 变化率指标

    波动率指标:
    - calc_historical_volatility: 历史波动率
    - calc_atr: 平均真实波幅
    - calc_parkinson_volatility: Parkinson波动率
    - calc_garman_klass_volatility: Garman-Klass波动率

    成交量特征:
    - calc_volume_change_rate: 成交量变化率
    - calc_vma: 成交量移动平均
    - calc_vema: 成交量指数移动平均
    - calc_price_volume_corr: 价量相关性
    - calc_vwap: 成交量加权平均价
    - calc_obv: 能量潮指标

    技术形态:
    - calc_resistance_level: 阻力位
    - calc_support_level: 支撑位
    - calc_price_position_tech: 价格技术位置
    - calc_bollinger: 布林带
    - calc_williams_r: 威廉指标

    时间特征:
    - calc_hour/minute: 小时/分钟
    - calc_day_of_week: 星期
    - calc_month: 月份
    - calc_is_weekend: 周末标识
    - calc_is_month_start/end: 月初/月末标识
    - calc_time_cyclical: 周期性时间特征
    - calc_quarter: 季度
    - calc_week_of_year: 一年中的周数

    高阶特征:
    - calc_derivatives: 导数特征
    - calc_acceleration: 加速度特征
    - calc_curvature: 曲率特征

    风险特征:
    - calc_var: 风险价值
    - calc_cvar: 条件风险价值
    - calc_max_drawdown: 最大回撤
    - calc_sharpe_ratio: 夏普比率
    - calc_calmar_ratio: 卡尔玛比率
    - calc_sortino_ratio: 索提诺比率

3. 窗口参数:
    - moving_windows: 移动窗口列表，默认[3,5,7]
    - rsi_periods: RSI周期列表，默认[7]
    - volatility_periods: 波动率周期列表，默认[3,5,7]
    - volume_windows: 成交量窗口列表，默认[3,5,7]
    - technical_windows: 技术分析窗口列表，默认[5,10,20]
    - lag_periods: 滞后周期列表，默认[1,2,3]
    - high_order_windows: 高阶特征窗口列表，默认[2,3]
    - risk_windows: 风险计算窗口列表，默认[5,10,20]

4. 数据处理参数:
    - clean_infinite: 清理无穷大值，默认True
    - fill_missing: 填充缺失值，默认True
    - handle_outliers: 处理异常值，默认True
    - outlier_threshold: 异常值阈值，默认3.0

5. 特征选择参数:
    - enable_feature_selection: 启用特征选择，默认False
    - variance_threshold: 方差阈值，默认0.01
    - k_best_features: 选择特征数量，默认50

6. 其他参数:
    - verbose: 是否打印详细日志，默认True

使用建议:

1. 大数据集时，建议只选择需要的特征类型以提高性能
2. 使用特征选择功能可以减少维度，避免过拟合
3. 调整窗口参数以适应不同的时间尺度
4. 根据具体业务需求选择合适的特征组合

示例用法:
    # 最简单的用法
    result = calculate_liushui_features(df)

    # 只计算基本特征
    result = calculate_liushui_features(
        df,
        calc_price_change_rate=True,
        calc_ma=True,
        moving_windows=[5,10,20]
    )

    # 自定义参数并启用特征选择
    result = calculate_liushui_features(
        df,
        moving_windows=[5,15,30],
        rsi_periods=[14,21],
        enable_feature_selection=True,
        k_best_features=50
    )
"""

    print(guide)

def run_all_examples():
    """
    运行所有示例
    """
    print("开始运行 liushui_func.py 使用示例")
    print("=" * 80)

    try:
        # 运行各个示例
        example_1_basic_usage()
        example_2_selective_features()
        example_3_custom_parameters()
        example_4_feature_selection()
        example_5_selected_features()

        print("\n" + "="*80)
        print("所有示例运行完成！")
        print("="*80)

    except Exception as e:
        print(f"\n运行示例时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    """
    主函数：可以选择运行特定的示例或全部示例
    """
    if len(sys.argv) > 1:
        if sys.argv[1] == '--guide':
            print_usage_guide()
        elif sys.argv[1] == '--all':
            run_all_examples()
        elif sys.argv[1].startswith('--example'):
            example_num = int(sys.argv[1].split('=')[1]) if '=' in sys.argv[1] else 1
            if example_num == 1:
                example_1_basic_usage()
            elif example_num == 2:
                example_2_selective_features()
            elif example_num == 3:
                example_3_custom_parameters()
            elif example_num == 4:
                example_4_feature_selection()
            elif example_num == 5:
                example_5_selected_features()
            else:
                print("示例编号必须是1-5")
        else:
            print("未知参数，使用 --help 查看帮助")
    else:
        print("请使用参数运行:")
        print("python liushui_func_test.py --guide     # 显示使用指南")
        print("python liushui_func_test.py --all       # 运行所有示例")
        print("python liushui_func_test.py --example=1 # 运行示例1")