# -*- coding: utf-8 -*-
"""
Breast Cancer Dataset Feature Selection and Classification Test
Using FeatureSelected class for feature selection, then LightGBM classifier for prediction
"""

import pandas as pd
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import lightgbm as lgb
import matplotlib.pyplot as plt
# import seaborn as sns
import sys
import os

# Set encoding for Chinese characters
if sys.platform.startswith('win'):
    import locale
    locale.setlocale(locale.LC_ALL, 'Chinese (Simplified)_China.936')

# Import our feature selection class
from selected import FeatureSelected

def load_breast_cancer_data():
    """Load breast cancer dataset"""
    # Load sklearn built-in breast cancer dataset
    data = load_breast_cancer()

    # Create DataFrame
    X = pd.DataFrame(data.data, columns=data.feature_names)
    y = pd.Series(data.target, name='target')

    print("=" * 60)
    print("Breast Cancer Dataset Information")
    print("=" * 60)
    print(f"Data shape: {X.shape}")
    print(f"Number of features: {X.shape[1]}")
    print(f"Number of samples: {X.shape[0]}")
    print(f"Class distribution: {y.value_counts().to_dict()}")
    print(f"Feature names: {list(X.columns)}")
    print()

    return X, y

def feature_selection_example(X, y):
    """Use FeatureSelected class for feature selection"""
    print("=" * 60)
    print("Step 1: Feature Selection using FeatureSelected")
    print("=" * 60)

    # Initialize feature selector
    selector = FeatureSelected(
        feature_eval_nums=10,          # Perform 10 rounds of training evaluation
        num_boost_round=30,            # 30 iterations per round
        max_feature_selected_num=10,   # Select maximum 10 features
        corr_line=0.95,                # Correlation threshold 0.95 (higher threshold)
        normalize_features=True,       # Normalize features
        random_state=42
    )

    # Execute feature selection
    X_selected = selector.fit_transform(X, y)

    # Display feature selection results
    selector.summary()

    # Get detailed feature importance information
    importance_df = selector.get_feature_importance()
    correlation_df = selector.get_correlation_pairs()
    selected_features = selector.get_selected_features()

    print("\nSelected feature importance details:")
    print(importance_df.to_string(index=False))

    if len(correlation_df) > 0:
        print("\nHigh correlation feature pairs:")
        print(correlation_df.to_string(index=False))

    return selector, X_selected, importance_df

def train_and_evaluate(X_train, X_test, y_train, y_test, feature_names=None):
    """Train and evaluate model using LightGBM"""
    print("=" * 60)
    print("Step 2: Train and Evaluate Model using LightGBM")
    print("=" * 60)

    # Create LightGBM dataset
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
        'verbose': -1,  # Changed from 0 to -1 to suppress warnings
        'seed': 42
    }

    # Train model
    print("Training model...")
    model = lgb.train(
        params,
        train_data,
        num_boost_round=100,
        valid_sets=[test_data],
        callbacks=[lgb.early_stopping(10), lgb.log_evaluation(0)]
    )

    # Predict
    y_pred_proba = model.predict(X_test, num_iteration=model.best_iteration)
    y_pred = (y_pred_proba >= 0.5).astype(int)

    # Evaluate
    accuracy = accuracy_score(y_test, y_pred)

    print(f"Model evaluation results:")
    print(f"Best iteration: {model.best_iteration}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"\nClassification report:")
    print(classification_report(y_test, y_pred, target_names=['malignant', 'benign']))

    print(f"\nConfusion matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)

    # Feature importance (if using selected features)
    if feature_names is not None:
        feature_importance = model.feature_importance()
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': feature_importance
        }).sort_values('importance', ascending=False)

        print(f"\nModel training feature importance:")
        print(importance_df.to_string(index=False))

    return model, accuracy, y_pred

def compare_results():
    """Compare model performance before and after feature selection"""
    print("=" * 60)
    print("Breast Cancer Dataset Feature Selection and Classification Experiment")
    print("=" * 60)

    # 1. Load data
    X, y = load_breast_cancer_data()

    # 2. Split train test set
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    print(f"Training set size: {X_train.shape}")
    print(f"Test set size: {X_test.shape}")
    print()

    # 3. Feature selection
    selector, X_selected, importance_df = feature_selection_example(X_train, y_train)

    # 4. Apply feature selection to test set
    X_test_selected = selector.transform(X_test)

    # 5. Train model using all features
    print("\n" + "="*60)
    print("Comparison Experiment 1: Using all features ({})".format(X_train.shape[1]))
    print("="*60)
    model_all, acc_all, pred_all = train_and_evaluate(
        X_train, X_test, y_train, y_test, X_train.columns.tolist()
    )

    # 6. Train model using selected features
    print("\n" + "="*60)
    print("Comparison Experiment 2: Using selected features ({})".format(len(selector.get_selected_features())))
    print("="*60)
    model_selected, acc_selected, pred_selected = train_and_evaluate(
        X_selected, X_test_selected, y_train, y_test,
        selector.get_selected_features()
    )

    # 7. Summary comparison
    print("\n" + "="*60)
    print("Experiment Summary")
    print("="*60)
    print(f"All features model accuracy: {acc_all:.4f}")
    print(f"Selected features model accuracy: {acc_selected:.4f}")
    print(f"Accuracy change: {acc_selected - acc_all:+.4f}")
    print(f"Feature count change: {X_train.shape[1]} → {len(selector.get_selected_features())} (-{X_train.shape[1] - len(selector.get_selected_features())})")

    if acc_selected >= acc_all:
        print("✓ Performance maintained or improved after feature selection")
    else:
        print("⚠ Performance slightly decreased after feature selection, but feature count greatly reduced")

    # 8. Visualize feature importance
    try:
        plt.figure(figsize=(12, 8))

        plt.subplot(2, 1, 1)
        top_features = importance_df.head(10)
        plt.barh(range(len(top_features)), top_features['importance'])
        plt.yticks(range(len(top_features)), top_features['feature'])
        plt.xlabel('Feature Importance')
        plt.title('Top 10 Important Features Selected by FeatureSelected')
        plt.gca().invert_yaxis()

        plt.subplot(2, 1, 2)
        model_importance = pd.DataFrame({
            'feature': selector.get_selected_features(),
            'importance': model_selected.feature_importance()
        }).sort_values('importance', ascending=True)

        plt.barh(range(len(model_importance)), model_importance['importance'])
        plt.yticks(range(len(model_importance)), model_importance['feature'])
        plt.xlabel('Feature Importance')
        plt.title('Feature Importance After LightGBM Model Training')
        plt.gca().invert_yaxis()

        plt.tight_layout()

        # Save with full path
        save_path = '/ai/wks/aitpf/src/tpf/data/feature/feature_importance_comparison.png'
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\nFeature importance comparison plot saved to: {save_path}")

    except Exception as e:
        print(f"Plotting failed: {e}")

    return {
        'all_features_accuracy': acc_all,
        'selected_features_accuracy': acc_selected,
        'selected_features': selector.get_selected_features(),
        'feature_importance': importance_df,
        'correlation_pairs': selector.get_correlation_pairs()
    }

def main():
    """Main function"""
    # Set matplotlib to handle Chinese characters
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'SimHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False

    # Run complete comparison experiment
    results = compare_results()

    print("\n" + "="*60)
    print("Experiment Completed!")
    print("="*60)
    print("Main Conclusions:")
    print(f"1. Original feature count: 30")
    print(f"2. Selected feature count: {len(results['selected_features'])}")
    print(f"3. Feature selection accuracy: {results['selected_features_accuracy']:.4f}")
    print(f"4. All features accuracy: {results['all_features_accuracy']:.4f}")
    print(f"5. Final selected features: {results['selected_features']}")

if __name__ == "__main__":
    main()
    """
    ============================================================
    Experiment Completed!
    ============================================================
    Main Conclusions:
    1. Original feature count: 30
    2. Selected feature count: 17
    3. Feature selection accuracy: 0.9532
    4. All features accuracy: 0.9591
    5. Final selected features: ['worst concave points', 'worst texture', 'mean texture', 'worst radius', 'mean concave points', 'compactness error', 'worst smoothness', 'worst symmetry', 'texture error', 'area error', 'worst concavity', 'worst compactness', 'mean concavity', 'concave points error', 'symmetry error', 'fractal dimension error', 'mean smoothness']

    """