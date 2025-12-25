# -*- coding: utf-8 -*-
"""
Simple test to debug feature selection issues
"""

import pandas as pd
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import lightgbm as lgb
from sklearn.preprocessing import MinMaxScaler

def simple_feature_test():
    """Simple test with manually selected top features"""
    # Load data
    data = load_breast_cancer()
    X = pd.DataFrame(data.data, columns=data.feature_names)
    y = pd.Series(data.target, name='target')

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    print("Original data shapes:")
    print(f"X_train: {X_train.shape}, y_train: {y_train.shape}")
    print(f"X_test: {X_test.shape}, y_test: {y_test.shape}")
    print(f"y_train distribution: {y_train.value_counts().to_dict()}")
    print(f"y_test distribution: {y_test.value_counts().to_dict()}")

    # Test 1: Raw data
    print("\n" + "="*50)
    print("Test 1: Raw data (no normalization)")
    print("="*50)
    train_lightgbm(X_train, X_test, y_train, y_test, "Raw Data")

    # Test 2: Normalized data
    print("\n" + "="*50)
    print("Test 2: Normalized data")
    print("="*50)
    scaler = MinMaxScaler()
    X_train_norm = pd.DataFrame(scaler.fit_transform(X_train), columns=X_train.columns)
    X_test_norm = pd.DataFrame(scaler.transform(X_test), columns=X_test.columns)
    train_lightgbm(X_train_norm, X_test_norm, y_train, y_test, "Normalized Data")

    # Test 3: Top 10 features based on domain knowledge
    print("\n" + "="*50)
    print("Test 3: Top 10 features (based on research)")
    print("="*50)
    top_features = [
        'worst concave points', 'worst perimeter', 'worst radius', 'worst area',
        'mean concave points', 'mean perimeter', 'mean radius', 'mean area',
        'worst texture', 'mean texture'
    ]
    X_train_top = X_train[top_features]
    X_test_top = X_test[top_features]
    train_lightgbm(X_train_top, X_test_top, y_train, y_test, "Top 10 Features")

    # Test 4: Top 10 normalized features
    print("\n" + "="*50)
    print("Test 4: Top 10 normalized features")
    print("="*50)
    X_train_top_norm = X_train_norm[top_features]
    X_test_top_norm = X_test_norm[top_features]
    train_lightgbm(X_train_top_norm, X_test_top_norm, y_train, y_test, "Top 10 Normalized Features")

def train_lightgbm(X_train, X_test, y_train, y_test, test_name):
    """Train LightGBM and return accuracy"""
    print(f"\nTraining with {test_name}")
    print(f"Feature count: {X_train.shape[1]}")
    print(f"Feature names: {list(X_train.columns)}")

    # Check data quality
    print(f"X_train contains NaN: {X_train.isnull().any().any()}")
    print(f"X_test contains NaN: {X_test.isnull().any().any()}")
    print(f"X_train range: [{X_train.min().min():.3f}, {X_train.max().max():.3f}]")
    print(f"X_test range: [{X_test.min().min():.3f}, {X_test.max().max():.3f}]")

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
        'feature_fraction': 0.9,
        'verbose': -1,
        'seed': 42
    }

    # Train model
    try:
        model = lgb.train(
            params,
            train_data,
            num_boost_round=100,
            valid_sets=[test_data],
            callbacks=[lgb.early_stopping(20), lgb.log_evaluation(0)]
        )

        # Predict
        y_pred_proba = model.predict(X_test, num_iteration=model.best_iteration)
        y_pred = (y_pred_proba >= 0.5).astype(int)

        # Evaluate
        accuracy = accuracy_score(y_test, y_pred)

        print(f"Best iteration: {model.best_iteration}")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"Predicted classes distribution: {np.bincount(y_pred)}")

        # Feature importance
        if hasattr(model, 'feature_importance'):
            importance = model.feature_importance()
            feature_imp = pd.DataFrame({
                'feature': X_train.columns,
                'importance': importance
            }).sort_values('importance', ascending=False)
            print("Top 5 important features:")
            print(feature_imp.head().to_string(index=False))

        return accuracy

    except Exception as e:
        print(f"Training failed: {e}")
        return 0.0

if __name__ == "__main__":
    simple_feature_test()