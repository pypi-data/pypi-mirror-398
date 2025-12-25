# -*- coding: utf-8 -*-
"""
Debug normalization issues in feature selection
"""

import pandas as pd
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import lightgbm as lgb
from sklearn.preprocessing import MinMaxScaler
from selected import FeatureSelected

def debug_normalization():
    """Debug normalization issues"""
    # Load data
    data = load_breast_cancer()
    X = pd.DataFrame(data.data, columns=data.feature_names)
    y = pd.Series(data.target, name='target')

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    print("=== DEBUGGING NORMALIZATION ===")

    # Test 1: Our selector with normalization OFF
    print("\n1. Feature selector with normalization OFF:")
    selector_no_norm = FeatureSelected(
        feature_eval_nums=5,
        num_boost_round=20,
        max_feature_selected_num=10,
        corr_line=0.98,
        normalize_features=False,  # OFF
        random_state=42
    )
    X_sel_no_norm = selector_no_norm.fit_transform(X_train, y_train)
    sel_features_no_norm = selector_no_norm.get_selected_features()
    print(f"Selected features: {sel_features_no_norm}")
    print(f"X_sel_no_norm range: [{X_sel_no_norm.min().min():.3f}, {X_sel_no_norm.max().max():.3f}]")
    print(f"X_sel_no_norm mean: {X_sel_no_norm.mean().mean():.3f}")

    # Test on test set
    X_test_sel_no_norm = X_test[sel_features_no_norm]
    print(f"X_test_sel_no_norm range: [{X_test_sel_no_norm.min().min():.3f}, {X_test_sel_no_norm.max().max():.3f}]")
    print(f"X_test_sel_no_norm mean: {X_test_sel_no_norm.mean().mean():.3f}")

    acc_no_norm = train_and_evaluate(
        X_sel_no_norm, X_test_sel_no_norm, y_train, y_test,
        "No Normalization"
    )

    # Test 2: Our selector with normalization ON
    print("\n2. Feature selector with normalization ON:")
    selector_norm = FeatureSelected(
        feature_eval_nums=5,
        num_boost_round=20,
        max_feature_selected_num=10,
        corr_line=0.98,
        normalize_features=True,   # ON
        random_state=42
    )
    X_sel_norm = selector_norm.fit_transform(X_train, y_train)
    sel_features_norm = selector_norm.get_selected_features()
    print(f"Selected features: {sel_features_norm}")
    print(f"X_sel_norm range: [{X_sel_norm.min().min():.3f}, {X_sel_norm.max().max():.3f}]")
    print(f"X_sel_norm mean: {X_sel_norm.mean().mean():.3f}")

    # Test on test set
    X_test_sel_norm = selector_norm.transform(X_test)
    print(f"X_test_sel_norm range: [{X_test_sel_norm.min().min():.3f}, {X_test_sel_norm.max().max():.3f}]")
    print(f"X_test_sel_norm mean: {X_test_sel_norm.mean().mean():.3f}")

    acc_norm = train_and_evaluate(
        X_sel_norm, X_test_sel_norm, y_train, y_test,
        "With Normalization"
    )

    # Test 3: Manual normalization of selected features
    print("\n3. Manual normalization of selected features:")
    scaler = MinMaxScaler()
    X_train_manual_norm = pd.DataFrame(
        scaler.fit_transform(X_train[sel_features_no_norm]),
        columns=sel_features_no_norm
    )
    X_test_manual_norm = pd.DataFrame(
        scaler.transform(X_test[sel_features_no_norm]),
        columns=sel_features_no_norm
    )
    print(f"X_train_manual_norm range: [{X_train_manual_norm.min().min():.3f}, {X_train_manual_norm.max().max():.3f}]")
    print(f"X_test_manual_norm range: [{X_test_manual_norm.min().min():.3f}, {X_test_manual_norm.max().max():.3f}]")

    acc_manual_norm = train_and_evaluate(
        X_train_manual_norm, X_test_manual_norm, y_train, y_test,
        "Manual Normalization"
    )

    print("\n=== SUMMARY ===")
    print(f"No normalization:       {acc_no_norm:.4f}")
    print(f"With normalization:      {acc_norm:.4f}")
    print(f"Manual normalization:    {acc_manual_norm:.4f}")

def train_and_evaluate(X_train, X_test, y_train, y_test, test_name):
    """Train LightGBM and return accuracy"""
    print(f"\nTesting: {test_name}")
    print(f"Features: {list(X_train.columns)}")
    print(f"Data shapes: train {X_train.shape}, test {X_test.shape}")

    # Check for data issues
    print(f"Train data - NaN: {X_train.isnull().any().any()}, inf: {np.isinf(X_train.values).any()}")
    print(f"Test data - NaN: {X_test.isnull().any().any()}, inf: {np.isinf(X_test.values).any()}")

    # Create LightGBM datasets
    train_data = lgb.Dataset(X_train, label=y_train)
    test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

    # Set parameters
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
        print(f"Prediction distribution: {np.bincount(y_pred)}")
        return accuracy

    except Exception as e:
        print(f"Training failed: {e}")
        return 0.0

if __name__ == "__main__":
    debug_normalization()