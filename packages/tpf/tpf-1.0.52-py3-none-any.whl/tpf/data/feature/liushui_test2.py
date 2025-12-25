#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Selective Feature Calculation Test
Test FeatureEngineeringPipeline.calculate_selected_features method
"""

import pandas as pd
from typing import List
from liushui import FeatureEngineeringPipeline, pc, load_and_prepare_data, normalize_data


def test_selective_feature_calculation():
    """
    Test selective feature calculation functionality
    """
    try:
        pc.log("Testing selective feature calculation from file----------------2314--------------")

        # Define test feature list
        test_features = ['Bollinger_Position_10', 'minute', 'price_beta_10', 'price_beta_20', 'price_beta_50', 'sharpe_ratio_99']

        # Use optimized data loading and preprocessing methods
        pc.log("Loading data...")
        df_processed, data_config = load_and_prepare_data()

        pc.log("Data preprocessing...")
        df_test_preprocessed = normalize_data(df_processed, data_config)

        # Get identity columns from config
        identity_cols = data_config['identity']

        # Method 1: Direct calculation using feature list
        pc.log("Method 1: Direct calculation using specified feature list...")
        df_result1 = FeatureEngineeringPipeline.calculate_selected_features(
            df_test_preprocessed,
            test_features,
            identity_cols=identity_cols
        )

        print(f"Method 1 result: Data shape {df_result1.shape}, Features: {list(df_result1.columns)}")

        # Validate results
        expected_features = [f for f in test_features if f in df_result1.columns]
        actual_features = [f for f in df_result1.columns if f not in identity_cols]

        pc.log(f"Expected feature count: {len(test_features)}")
        pc.log(f"Actual calculated feature count: {len(actual_features)}")
        pc.log(f"Successfully calculated features: {expected_features}")

        if len(expected_features) == len(actual_features):
            pc.log("✅ Selective feature calculation test successful!")
        else:
            pc.log("⚠️  Some features failed to calculate")

        return df_result1

    except Exception as e:
        pc.log(f"❌ Selective feature calculation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_multiple_feature_scenarios():
    """
    Test multiple feature scenarios
    """
    pc.log("="*60)
    pc.log("Testing Multiple Feature Calculation Scenarios")
    pc.log("="*60)

    # Prepare data
    df_processed, data_config = load_and_prepare_data()
    df_preprocessed = normalize_data(df_processed, data_config)
    identity_cols = data_config['identity']

    # Test scenario 1: Technical pattern features only
    pc.log("\nScenario 1: Technical pattern features only")
    tech_features = ['Bollinger_Position_10', 'Resistance_Level_20', 'Support_Level_10']
    df_tech = FeatureEngineeringPipeline.calculate_selected_features(
        df_preprocessed, tech_features, identity_cols=identity_cols
    )
    pc.log(f"Technical features result: {df_tech.shape}")

    # Test scenario 2: Time features only
    pc.log("\nScenario 2: Time features only")
    time_features = ['hour', 'minute', 'day_of_week', 'month']
    df_time = FeatureEngineeringPipeline.calculate_selected_features(
        df_preprocessed, time_features, identity_cols=identity_cols
    )
    pc.log(f"Time features result: {df_time.shape}")

    # Test scenario 3: Risk features only
    pc.log("\nScenario 3: Risk features only")
    risk_features = ['sharpe_ratio_20', 'max_drawdown_10', 'VaR_95_20']
    df_risk = FeatureEngineeringPipeline.calculate_selected_features(
        df_preprocessed, risk_features, identity_cols=identity_cols
    )
    pc.log(f"Risk features result: {df_risk.shape}")

    # Test scenario 4: Mixed features
    pc.log("\nScenario 4: Mixed features")
    mixed_features = ['Bollinger_Position_10', 'minute', 'sharpe_ratio_20', 'price_beta_50']
    df_mixed = FeatureEngineeringPipeline.calculate_selected_features(
        df_preprocessed, mixed_features, identity_cols=identity_cols
    )
    pc.log(f"Mixed features result: {df_mixed.shape}")

    return df_tech, df_time, df_risk, df_mixed


def main():
    """
    Main test function
    """
    pc.log("="*60)
    pc.log("Selective Feature Calculation Test Suite")
    pc.log("="*60)

    # Basic functionality test
    result = test_selective_feature_calculation()

    if result is not None:
        # Multiple scenario tests
        test_multiple_feature_scenarios()

        pc.log("\n" + "="*60)
        pc.log("All tests completed!")
        pc.log("="*60)
    else:
        pc.log("Basic test failed, skipping scenario tests")


if __name__ == "__main__":
    main()