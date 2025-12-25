# -*- coding: utf-8 -*-
"""
Compare our feature selector with manual selection
"""

import pandas as pd
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import lightgbm as lgb
from sklearn.preprocessing import MinMaxScaler
from selected import FeatureSelected

def compare_feature_selection():
    """Compare different feature selection methods"""
    # Load data
    data = load_breast_cancer()
    X = pd.DataFrame(data.data, columns=data.feature_names)
    y = pd.Series(data.target, name='target')

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    print("Manual top features (based on domain knowledge):")
    manual_top = [
        'worst concave points', 'worst perimeter', 'worst radius', 'worst area',
        'mean concave points', 'mean perimeter', 'mean radius', 'mean area',
        'worst texture', 'mean texture'
    ]
    print(manual_top)

    # Test our feature selector
    print("\nTesting our FeatureSelected...")
    selector = FeatureSelected(
        feature_eval_nums=5,          # Fewer rounds for speed
        num_boost_round=20,            # Fewer iterations
        max_feature_selected_num=10,   # Select 10 features
        corr_line=0.98,                # High threshold to avoid over-removal
        normalize_features=False,      # Don't normalize for now
        random_state=42
    )

    X_selected = selector.fit_transform(X_train, y_train)
    our_top = selector.get_selected_features()
    print(f"Our selector chose: {our_top}")

    # Compare results
    print("\n" + "="*60)
    print("COMPARISON TEST")
    print("="*60)

    # Test 1: All features
    acc_all = test_features(X_train, X_test, y_train, y_test, "All Features")

    # Test 2: Manual top 10
    acc_manual = test_features(
        X_train[manual_top], X_test[manual_top],
        y_train, y_test, "Manual Top 10"
    )

    # Test 3: Our selector features
    acc_ours = test_features(
        X_train[our_top], X_test[our_top],
        y_train, y_test, "Our Selector Features"
    )

    # Test 4: Normalized manual top 10
    scaler = MinMaxScaler()
    X_train_norm = pd.DataFrame(scaler.fit_transform(X_train), columns=X_train.columns)
    X_test_norm = pd.DataFrame(scaler.transform(X_test), columns=X_test.columns)
    acc_manual_norm = test_features(
        X_train_norm[manual_top], X_test_norm[manual_top],
        y_train, y_test, "Normalized Manual Top 10"
    )

    # Test 5: Our selector with normalized data
    selector_norm = FeatureSelected(
        feature_eval_nums=5,
        num_boost_round=20,
        max_feature_selected_num=10,
        corr_line=0.98,
        normalize_features=True,
        random_state=42
    )
    X_selected_norm = selector_norm.fit_transform(X_train, y_train)
    our_top_norm = selector_norm.get_selected_features()
    print(f"Our normalized selector chose: {our_top_norm}")
    acc_ours_norm = test_features(
        X_train_norm[our_top_norm], X_test_norm[our_top_norm],
        y_train, y_test, "Our Normalized Selector"
    )

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"All features:          {acc_all:.4f}")
    print(f"Manual top 10:         {acc_manual:.4f}")
    print(f"Our selector:          {acc_ours:.4f}")
    print(f"Manual top 10 (norm):  {acc_manual_norm:.4f}")
    print(f"Our selector (norm):   {acc_ours_norm:.4f}")

    # Feature overlap analysis
    print(f"\nFeature overlap analysis:")
    manual_set = set(manual_top)
    our_set = set(our_top)
    overlap = manual_set.intersection(our_set)
    print(f"Manual vs Our selector overlap: {len(overlap)}/10 features")
    print(f"Overlapping features: {list(overlap)}")
    print(f"Features we missed: {manual_set - our_set}")
    print(f"Extra features we chose: {our_set - manual_set}")

def test_features(X_train, X_test, y_train, y_test, test_name):
    """Test feature set and return accuracy"""
    print(f"\nTesting: {test_name}")
    print(f"Features: {X_train.shape[1]}")
    if X_train.shape[1] <= 10:
        print(f"Feature names: {list(X_train.columns)}")

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

if __name__ == "__main__":
    compare_feature_selection()