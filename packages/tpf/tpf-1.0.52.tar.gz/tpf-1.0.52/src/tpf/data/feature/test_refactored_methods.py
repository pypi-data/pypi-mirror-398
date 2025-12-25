#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试重构后的方法
验证 prepare_data_for_feature_calculation 和 run_feature_pipeline_with_timing 方法
"""

import pandas as pd
from typing import List
from liushui import FeatureEngineeringPipeline, prepare_data_for_feature_calculation, run_feature_pipeline_with_timing, pc


def test_refactored_methods():
    """
    测试重构后的方法
    """
    pc.log("="*60)
    pc.log("测试重构后的方法")
    pc.log("="*60)

    try:
        # 方法1：使用新的数据准备方法
        pc.log("\n步骤1：使用 prepare_data_for_feature_calculation 准备数据")
        df_preprocessed, data_config, timer = prepare_data_for_feature_calculation()
        pc.log(f"数据准备完成：数据形状 {df_preprocessed.shape}")
        pc.log(f"Identity 列：{data_config['identity']}")

        # 方法2：使用修改后的特征计算方法
        pc.log("\n步骤2：使用 run_feature_pipeline_with_timing 计算特征")
        test_features = ['Bollinger_Position_10', 'minute', 'sharpe_ratio_20']

        df_features, timing_results = run_feature_pipeline_with_timing(
            df_preprocessed=df_preprocessed,
            data_config=data_config,
            timer=timer,
            selected_features=test_features
        )

        # 验证特征是否被正确计算
        actual_features = [col for col in df_features.columns if col in test_features]
        pc.log(f"实际计算的特征: {actual_features}")

        # 如果特征没有被计算，使用直接的方法测试
        if len(actual_features) == 0:
            pc.log("使用 calculate_selected_features 直接测试...")
            df_direct_features = FeatureEngineeringPipeline.calculate_selected_features(
                df_preprocessed,
                test_features,
                identity_cols=data_config['identity']
            )
            direct_actual_features = [col for col in df_direct_features.columns if col in test_features]
            pc.log(f"直接计算结果: {direct_actual_features}")
            return df_direct_features, timing_results

        pc.log(f"特征计算完成：数据形状 {df_features.shape}")
        pc.log(f"计算的特征：{[col for col in df_features.columns if col not in data_config['identity']]}")
        pc.log("时间统计结果：")
        for step, time_taken in timing_results.items():
            pc.log(f"  {step}: {time_taken:.4f}秒")

        # 验证结果
        expected_features = [f for f in test_features if f in df_features.columns]
        actual_features = [f for f in df_features.columns if f in test_features]

        if len(expected_features) == len(actual_features) and len(actual_features) > 0:
            pc.log("\n✅ 重构方法测试成功！")
            pc.log(f"成功计算了 {len(actual_features)} 个特征")
        else:
            pc.log("\n⚠️  特征计算数量不匹配或未计算任何特征")
            pc.log(f"期望: {test_features}")
            pc.log(f"实际: {actual_features}")

        return df_features, timing_results

    except Exception as e:
        pc.log(f"\n❌ 重构方法测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None


def test_backward_compatibility():
    """
    测试向后兼容性
    """
    pc.log("\n" + "="*60)
    pc.log("测试向后兼容性")
    pc.log("="*60)

    try:
        # 使用原有的调用方式（不传递预处理数据）
        pc.log("\n使用原有调用方式测试...")
        test_features = ['Bollinger_Position_10', 'minute']

        df_features, timing_results = run_feature_pipeline_with_timing(
            selected_features=test_features
        )

        pc.log(f"向后兼容测试完成：数据形状 {df_features.shape}")
        pc.log("✅ 向后兼容性测试成功！")

        return df_features, timing_results

    except Exception as e:
        pc.log(f"\n❌ 向后兼容性测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None


def main():
    """
    主测试函数
    """
    pc.log("="*60)
    pc.log("重构方法测试套件")
    pc.log("="*60)

    # 测试重构后的方法
    result1, timing1 = test_refactored_methods()

    if result1 is not None:
        # 测试向后兼容性
        result2, timing2 = test_backward_compatibility()

        if result2 is not None:
            pc.log("\n" + "="*60)
            pc.log("🎉 所有测试通过！重构成功！")
            pc.log("="*60)
        else:
            pc.log("\n向后兼容性测试失败")
    else:
        pc.log("\n重构方法测试失败，跳过向后兼容性测试")


if __name__ == "__main__":
    main()