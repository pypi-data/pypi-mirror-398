# -*- coding: utf-8 -*-
"""
Test the new feature_selection_lgbm function with different parameter settings
"""

import pandas as pd
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import lightgbm as lgb
from selected import feature_selection_lgbm

def test_different_parameters():
    """Test feature_selection_lgbm with different parameter configurations"""
    # Load data
    data = load_breast_cancer()
    X = pd.DataFrame(data.data, columns=data.feature_names)
    y = pd.Series(data.target, name='target')

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    print("=" * 80)
    print("Testing feature_selection_lgbm with Different Parameters")
    print("=" * 80)

    # Test 1: Default parameters
    print("\n" + "="*60)
    print("Test 1: Default Parameters")
    print("="*60)

    selected_features1, importance_df1, correlation_df1, selector1 = feature_selection_lgbm(
        X_train, y_train
    )

    acc1 = evaluate_model(X_train[selected_features1], X_test[selected_features1],
                         y_train, y_test, "Default Parameters")

    # Test 2: Select more features
    print("\n" + "="*60)
    print("Test 2: More Features (15 features)")
    print("="*60)

    selected_features2, importance_df2, correlation_df2, selector2 = feature_selection_lgbm(
        X_train, y_train,
        max_feature_selected_num=15,
        corr_line=0.90
    )

    acc2 = evaluate_model(X_train[selected_features2], X_test[selected_features2],
                         y_train, y_test, "More Features")

    # Test 3: Faster selection (fewer rounds)
    print("\n" + "="*60)
    print("Test 3: Fast Selection (5 rounds, 15 iterations)")
    print("="*60)

    selected_features3, importance_df3, correlation_df3, selector3 = feature_selection_lgbm(
        X_train, y_train,
        feature_eval_nums=5,
        num_boost_round=15,
        max_feature_selected_num=8,
        show_correlation=True
    )

    acc3 = evaluate_model(X_train[selected_features3], X_test[selected_features3],
                         y_train, y_test, "Fast Selection")

    # Test 4: No normalization
    print("\n" + "="*60)
    print("Test 4: No Normalization")
    print("="*60)

    selected_features4, importance_df4, correlation_df4, selector4 = feature_selection_lgbm(
        X_train, y_train,
        max_feature_selected_num=10,
        normalize_features=False
    )

    acc4 = evaluate_model(X_train[selected_features4], X_test[selected_features4],
                         y_train, y_test, "No Normalization")

    # Test 5: Aggressive correlation removal
    print("\n" + "="*60)
    print("Test 5: Aggressive Correlation Removal (threshold=0.85)")
    print("="*60)

    selected_features5, importance_df5, correlation_df5, selector5 = feature_selection_lgbm(
        X_train, y_train,
        max_feature_selected_num=12,
        corr_line=0.85,
        show_correlation=True
    )

    acc5 = evaluate_model(X_train[selected_features5], X_test[selected_features5],
                         y_train, y_test, "Aggressive Correlation Removal")

    # Summary comparison
    print("\n" + "="*80)
    print("COMPARISON SUMMARY")
    print("="*80)
    print(f"{'Configuration':<30} {'Features':<10} {'Accuracy':<10}")
    print("-" * 50)
    print(f"{'Default Parameters':<30} {len(selected_features1):<10} {acc1:<10.4f}")
    print(f"{'More Features (15)':<30} {len(selected_features2):<10} {acc2:<10.4f}")
    print(f"{'Fast Selection':<30} {len(selected_features3):<10} {acc3:<10.4f}")
    print(f"{'No Normalization':<30} {len(selected_features4):<10} {acc4:<10.4f}")
    print(f"{'Aggressive Correlation':<30} {len(selected_features5):<10} {acc5:<10.4f}")

    # Feature overlap analysis
    print("\n" + "="*80)
    print("FEATURE OVERLAP ANALYSIS")
    print("="*80)

    all_features_sets = [
        ("Default", set(selected_features1)),
        ("More Features", set(selected_features2)),
        ("Fast Selection", set(selected_features3)),
        ("No Normalization", set(selected_features4)),
        ("Aggressive Correlation", set(selected_features5))
    ]

    for i, (name1, set1) in enumerate(all_features_sets):
        for j, (name2, set2) in enumerate(all_features_sets):
            if i < j:
                overlap = len(set1.intersection(set2))
                total_min = min(len(set1), len(set2))
                overlap_pct = (overlap / total_min * 100) if total_min > 0 else 0
                print(f"{name1} vs {name2}: {overlap}/{min(len(set1), len(set2))} features ({overlap_pct:.1f}%)")

def evaluate_model(X_train, X_test, y_train, y_test, test_name):
    """Train and evaluate LightGBM model"""
    print(f"\nEvaluating: {test_name}")
    print(f"Features: {X_train.shape[1]}")

    # Train model
    train_data = lgb.Dataset(X_train, label=y_train)
    test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

    params = {
        'objective': 'binary',
        'metric': 'binary_logloss',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'verbose': -1,
        'seed': 42
    }

    try:
        model = lgb.train(
            params,
            train_data,
            num_boost_round=100,
            valid_sets=[test_data],
            callbacks=[lgb.early_stopping(20), lgb.log_evaluation(0)]
        )

        y_pred = (model.predict(X_test, num_iteration=model.best_iteration) >= 0.5).astype(int)
        accuracy = accuracy_score(y_test, y_pred)

        print(f"Accuracy: {accuracy:.4f} (Best iteration: {model.best_iteration})")
        return accuracy

    except Exception as e:
        print(f"Training failed: {e}")
        return 0.0

def test_silent_mode():
    """Test silent mode (no output)"""
    print("\n" + "="*60)
    print("Test 6: Silent Mode")
    print("="*60)

    # Load data
    data = load_breast_cancer()
    X = pd.DataFrame(data.data, columns=data.feature_names)
    y = pd.Series(data.target, name='target')

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    # Silent feature selection
    selected_features, importance_df, correlation_df, selector = feature_selection_lgbm(
        X_train, y_train,
        max_feature_selected_num=8,
        show_summary=False,
        show_importance=False,
        show_correlation=False
    )

    print(f"Silent mode selected {len(selected_features)} features:")
    for i, feat in enumerate(selected_features, 1):
        print(f"{i:2d}. {feat}")

    acc = evaluate_model(X_train[selected_features], X_test[selected_features],
                         y_train, y_test, "Silent Mode")
    print(f"Silent mode accuracy: {acc:.4f}")

if __name__ == "__main__":
    # Run comprehensive tests
    test_different_parameters()
    test_silent_mode()

    print("\n" + "="*80)
    print("All tests completed!")
    print("="*80)