#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 liushui.py 提取的特征工程管道测试代码
"""

import os

import pandas as pd
from typing import Dict, List, Optional, Union, Tuple
from liushui import (
    FeatureEngineeringPipeline,
    FeatureConfig,
    run_feature_pipeline_with_timing,
    save_selected_features,
    run_optimized_feature_pipeline,
    pc,
    prepare_data_for_feature_calculation,
    load_and_prepare_data
)


def load_and_prepare_data(data_file: str = "/ai/wks/leadingtek/scripts/tra11.csv") -> Tuple[pd.DataFrame, Dict]:
    """
    加载和准备数据，包括CSV读取和数据类型转换

    Args:
        data_file: 数据文件路径

    Returns:
        (处理后的数据框, 数据配置信息)

    Returns包含的数据配置信息:
        - identity: 身份列列表
        - num_type: 数值类型列列表
        - date_type: 日期类型列列表
        - time_col: 时间列名
        - cols: 所有使用的列列表
    """
    # 定义数据配置
    identity = ['ACCT_NUM','PARTY_ID','OPP_PARTY_ID','ACCT','TCAC','TSTM']
    cols = ['ACCT_NUM','PARTY_ID','OPP_PARTY_ID','ACCT','TCAC','TSTM', 'DT_TIME', 'PARTY_CLASS_CD',
            'CCY', 'AMT', 'AMT_VAL','CNY_AMT','ACCBAL', 'DEBIT_CREDIT','CASH_FLAG', 'OPP_ORGANKEY',
            'OACCTT', 'OTBKAC', 'CHANNEL', 'RMKS', 'CBCDIR', 'AMTFLG', 'BALFLG', 'RMKCDE', 'TDDS',
            'RCDTYP', 'CCY_A', 'INTAMT_A', 'INTRAT_A', 'PBKTYP', 'CNT_CST_TYPE', 'CNT_INBANK_TYPE',
            'CFRC_COUNTRY', 'CFRC_AREA', 'TRCD_AREA', 'TRCD_COUNTRY', 'TXTPCD', 'RCVPAYFLG', 'SYS_FLAG',
            'TXN_CHNL_TP_ID', 'FLAG', 'OVERAREA_IND']
    num_type = ['AMT', 'AMT_VAL','CNY_AMT','ACCBAL','INTAMT_A', 'INTRAT_A']
    date_type = ['DT_TIME']
    time_col = 'DT_TIME'

    pc.log(f"开始加载数据文件: {data_file}")

    # 加载CSV数据
    df = pd.read_csv(data_file, usecols=cols)
    df = df[cols]  # 确保列顺序一致

    # 数据类型转换
    from tpf.data.deal import Data2Feature as dtf
    df_processed = dtf.data_type_change(df, num_type=num_type, date_type=date_type)

    pc.log(f"数据加载完成，数据维度: {df_processed.shape}")

    # 准备数据配置信息
    data_config = {
        'identity': identity,
        'num_type': num_type,
        'date_type': date_type,
        'time_col': time_col,
        'cols': cols
    }

    return df_processed, data_config



def main():
    """
    运行完整特征工程管道并保存选择特征
    """
    print("="*60)
    print("运行完整特征工程管道并保存选择特征")
    print("="*60)

    # 运行完整管道并保存选择特征
    pc.log(f"使用优化配置运行管道------------1913------------------")
    config = FeatureConfig()
    
    # load_and_prepare_data + 归化一处理
    # df_preprocessed, data_config, timer = prepare_data_for_feature_calculation(config)  
    
    data_file = "/ai/wks/leadingtek/scripts/tra11.csv"
    df_processed, data_config = load_and_prepare_data(data_file)
    df_full, timings = run_feature_pipeline_with_timing(config=config,
                                                        df_preprocessed=df_processed,
                                                        data_config=data_config)

    # 获取选择的特征（从特征选择结果中获取）
    identity_cols = ['ACCT_NUM','PARTY_ID','OPP_PARTY_ID','ACCT','TCAC','TSTM']
    time_col = 'DT_TIME'
    all_numeric_cols = [col for col in df_full.columns if df_full[col].dtype in ['int64', 'float64']]
    selected_features = [col for col in all_numeric_cols if col not in identity_cols + [time_col]]

    # 保存选择的特征
    saved_file = save_selected_features(selected_features)

    print("\n" + "="*60)
    print("特征工程完成！")
    print(f"选择的特征数量: {len(selected_features)}")
    print(f"最终数据维度: {df_full.shape}")
    print(f"总耗时: {sum(timings.values()):.4f}s")
    print(f"特征文件已保存到: {saved_file}")
    print("="*60)

    print("\n" + "="*60)
    print("测试重新计算功能")
    print("="*60)

    # 测试重新计算功能
    pc.log("使用保存的选择特征进行重新计算测试----------------2340--------------")
    try:
        df_recomputed, recompute_selected_features, recompute_timings = run_optimized_feature_pipeline(saved_file)
    except Exception as e:
        pc.log(f"重新计算时出现错误: {e}")
        pc.log("尝试使用完整的特征文件路径...")
        # 使用绝对路径
        df_recomputed, recompute_selected_features, recompute_timings = run_optimized_feature_pipeline(
            f"/ai/wks/leadingtek/scripts/{os.path.basename(saved_file)}"
        )

    print("\n" + "="*60)
    print("重新计算完成！")
    print(f"重新计算耗时: {sum(recompute_timings.values()):.4f}s")
    print(f"性能提升: {sum(timings.values()) / sum(recompute_timings.values()):.2f}x")
    print("="*60)

    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)


if __name__ == "__main__":
    main()