# -*- coding: utf-8 -*-
"""
Debug script to analyze feature selection performance issues
"""

import pandas as pd
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import lightgbm as lgb
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt

def analyze_feature_importance():
    """Analyze feature importance using full dataset"""
    # Load data
    data = load_breast_cancer()
    X = pd.DataFrame(data.data, columns=data.feature_names)
    y = pd.Series(data.target, name='target')

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    # Normalize data
    scaler = MinMaxScaler()
    X_train_norm = pd.DataFrame(scaler.fit_transform(X_train), columns=X_train.columns)
    X_test_norm = pd.DataFrame(scaler.transform(X_test), columns=X_test.columns)

    # Train model on all features
    print("Training model on ALL features...")
    train_data = lgb.Dataset(X_train_norm, label=y_train)
    test_data = lgb.Dataset(X_test_norm, label=y_test, reference=train_data)

    params = {
        'objective': 'binary',
        'metric': 'binary_logloss',
        'boosting_type': 'gbdt',
        'force_col_wise': True,
        'verbose': -1,
        'seed': 42
    }

    model_all = lgb.train(
        params, train_data, num_boost_round=100,
        valid_sets=[test_data], callbacks=[lgb.early_stopping(10), lgb.log_evaluation(0)]
    )

    # Get feature importance
    importance_all = model_all.feature_importance()
    feature_names = X_train_norm.columns.tolist()

    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importance_all
    }).sort_values('importance', ascending=False)

    print("Top 15 most important features (ALL features):")
    print(importance_df.head(15).to_string(index=False))

    # Calculate correlation with target
    corr_with_target = []
    for col in X_train_norm.columns:
        corr_val = np.corrcoef(X_train_norm[col], y_train)[0, 1]
        if np.isnan(corr_val):
            corr_val = 0
        corr_with_target.append(abs(corr_val))

    corr_df = pd.DataFrame({
        'feature': X_train_norm.columns,
        'abs_corr_with_target': corr_with_target
    }).sort_values('abs_corr_with_target', ascending=False)

    print("\nTop 15 features by absolute correlation with target:")
    print(corr_df.head(15).to_string(index=False))

    # Analyze feature correlations
    corr_matrix = X_train_norm.corr().abs()
    high_corr_pairs = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            if corr_matrix.iloc[i, j] > 0.9:
                high_corr_pairs.append({
                    'feature1': corr_matrix.columns[i],
                    'feature2': corr_matrix.columns[j],
                    'correlation': corr_matrix.iloc[i, j]
                })

    print(f"\nHigh correlation pairs (>0.9): {len(high_corr_pairs)}")
    for pair in high_corr_pairs[:10]:
        print(f"{pair['feature1']} <-> {pair['feature2']}: {pair['correlation']:.3f}")

    # Test different feature subsets
    print("\n" + "="*60)
    print("Testing different feature selection strategies")
    print("="*60)

    # Strategy 1: Top N by importance
    for n in [5, 10, 15, 20]:
        top_features = importance_df.head(n)['feature'].tolist()
        X_train_subset = X_train_norm[top_features]
        X_test_subset = X_test_norm[top_features]

        # Train model
        train_data = lgb.Dataset(X_train_subset, label=y_train)
        test_data = lgb.Dataset(X_test_subset, label=y_test, reference=train_data)

        model = lgb.train(
            params, train_data, num_boost_round=100,
            valid_sets=[test_data], callbacks=[lgb.early_stopping(10), lgb.log_evaluation(0)]
        )

        # Predict and evaluate
        y_pred = (model.predict(X_test_subset, num_iteration=model.best_iteration) >= 0.5).astype(int)
        accuracy = accuracy_score(y_test, y_pred)

        print(f"Top {n} by importance - Accuracy: {accuracy:.4f}")

    # Strategy 2: Top N by correlation with target
    for n in [5, 10, 15, 20]:
        top_features = corr_df.head(n)['feature'].tolist()
        X_train_subset = X_train_norm[top_features]
        X_test_subset = X_test_norm[top_features]

        # Train model
        train_data = lgb.Dataset(X_train_subset, label=y_train)
        test_data = lgb.Dataset(X_test_subset, label=y_test, reference=train_data)

        model = lgb.train(
            params, train_data, num_boost_round=100,
            valid_sets=[test_data], callbacks=[lgb.early_stopping(10), lgb.log_evaluation(0)]
        )

        # Predict and evaluate
        y_pred = (model.predict(X_test_subset, num_iteration=model.best_iteration) >= 0.5).astype(int)
        accuracy = accuracy_score(y_test, y_pred)

        print(f"Top {n} by correlation - Accuracy: {accuracy:.4f}")

    return importance_df, corr_df, high_corr_pairs

if __name__ == "__main__":
    importance_df, corr_df, high_corr_pairs = analyze_feature_importance()