# -*- coding: utf-8 -*-
"""
LightGBM Classification Algorithm with Confusion Matrix Example
Using Breast Cancer Dataset for Binary Classification Demonstration
"""

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns

# Set matplotlib configuration
plt.rcParams['axes.unicode_minus'] = False

def load_and_prepare_data():
    """Load and prepare breast cancer dataset"""
    print("Loading breast cancer dataset...")

    # Load dataset
    data = load_breast_cancer()
    X = data.data
    y = data.target

    # Create DataFrame for better visualization
    df = pd.DataFrame(X, columns=data.feature_names)
    df['target'] = y

    print(f"Dataset shape: {df.shape}")
    print(f"Number of features: {len(data.feature_names)}")
    print(f"Class distribution: {np.bincount(y)}")
    print(f"Class names: {data.target_names}")

    return X, y, data

def train_lightgbm_model(X_train, y_train, X_val, y_val):
    """Train LightGBM classification model"""
    print("\nTraining LightGBM model...")

    # Create LightGBM datasets
    train_data = lgb.Dataset(X_train, label=y_train)
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)

    # Set model parameters
    params = {
        'objective': 'binary',
        'metric': 'binary_logloss',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': 0,
        'random_state': 42
    }

    # Train model
    model = lgb.train(
        params,
        train_data,
        valid_sets=[val_data],
        num_boost_round=100,
        callbacks=[lgb.early_stopping(10), lgb.log_evaluation(0)]
    )

    print("Model training completed!")
    return model

def plot_confusion_matrix(cm, class_names, title="Confusion Matrix"):
    """Plot confusion matrix heatmap"""
    plt.figure(figsize=(10, 8))

    # Create heatmap using seaborn
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=class_names, yticklabels=class_names,
                cbar_kws={'label': 'Sample Count'},
                annot_kws={'size': 14, 'weight': 'bold'})

    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Predicted Label', fontsize=14, labelpad=15)
    plt.ylabel('True Label', fontsize=14, labelpad=15)

    # Add percentage in each cell
    cm_percent = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis] * 100
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j + 0.5, i + 0.25, f'({cm_percent[i, j]:.1f}%)',
                    ha='center', va='center', fontsize=11, color='red', weight='bold')

    # Increase tick label size
    plt.tick_params(axis='both', which='major', labelsize=12)
    plt.tight_layout()
    plt.show()

def analyze_confusion_matrix(y_true, y_pred, class_names):
    """Detailed analysis of confusion matrix"""
    cm = confusion_matrix(y_true, y_pred)

    print("\n=== Confusion Matrix Detailed Analysis ===")
    print(f"Confusion Matrix:\n{cm}")

    # Calculate matrix elements
    tn, fp, fn, tp = cm.ravel()

    print(f"\nMatrix Elements Explanation:")
    print(f"True Negative (TN): {tn} - Actually Malignant, Predicted Malignant")
    print(f"False Positive (FP): {fp} - Actually Malignant, Predicted Benign")
    print(f"False Negative (FN): {fn} - Actually Benign, Predicted Malignant")
    print(f"True Positive (TP): {tp} - Actually Benign, Predicted Benign")

    # Calculate performance metrics
    accuracy = (tp + tn) / (tp + tn + fp + fn)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    print(f"\nPerformance Metrics:")
    print(f"Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"Precision: {precision:.4f} ({precision*100:.2f}%)")
    print(f"Recall (Sensitivity): {recall:.4f} ({recall*100:.2f}%)")
    print(f"Specificity: {specificity:.4f} ({specificity*100:.2f}%)")
    print(f"F1-Score: {f1_score:.4f}")

    return cm

def plot_feature_importance(model, feature_names):
    """Plot feature importance"""
    feature_importance = model.feature_importance(importance_type='gain')

    # Create feature importance DataFrame
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': feature_importance
    }).sort_values('importance', ascending=False)

    print(f"\n=== Top 10 Most Important Features ===")
    print(importance_df.head(10))

    # Plot feature importance
    plt.figure(figsize=(12, 8))
    top_features = importance_df.head(15)

    bars = plt.barh(range(len(top_features)), top_features['importance'],
                    color='skyblue', alpha=0.8)
    plt.yticks(range(len(top_features)), top_features['feature'], fontsize=10)
    plt.xlabel('Feature Importance', fontsize=12)
    plt.title('LightGBM Model - Top 15 Important Features', fontsize=14, fontweight='bold')
    plt.gca().invert_yaxis()

    # Add value labels on bars
    for i, bar in enumerate(bars):
        width = bar.get_width()
        plt.text(width + width*0.01, bar.get_y() + bar.get_height()/2,
                f'{width:.2f}', ha='left', va='center', fontsize=9)

    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.show()

def plot_learning_curves(model, train_data, val_data):
    """Plot learning curves if available"""
    # This is a placeholder for learning curves
    # In practice, you would need to capture evaluation results during training
    pass

def main():
    """Main function"""
    print("=== LightGBM Breast Cancer Classification with Confusion Matrix Demo ===\n")

    # 1. Load data
    X, y, data = load_and_prepare_data()

    # 2. Data preprocessing and splitting
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
    )

    # Feature scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)

    print(f"\nData Split:")
    print(f"Training set: {X_train_scaled.shape}")
    print(f"Validation set: {X_val_scaled.shape}")
    print(f"Test set: {X_test_scaled.shape}")

    # 3. Train model
    model = train_lightgbm_model(X_train_scaled, y_train, X_val_scaled, y_val)

    # 4. Predict on test set
    print("\nMaking predictions on test set...")
    y_pred_proba = model.predict(X_test_scaled, num_iteration=model.best_iteration)
    y_prob_file = "/ai/data/tmp/y_prob.csv"
    data_dict = {"y_prob": y_pred_proba, "y_label": y_test}
    df_prob = pd.DataFrame(data_dict)
    df_prob.to_csv(y_prob_file, index=False)
    
    y_pred = (y_pred_proba > 0.5).astype(int)

    # 5. Confusion matrix analysis
    class_names = ['Malignant', 'Benign']
    cm = analyze_confusion_matrix(y_test, y_pred, class_names)

    # 6. Plot confusion matrix
    plot_confusion_matrix(cm, class_names, "LightGBM Breast Cancer Classification - Confusion Matrix")

    # 7. Detailed classification report
    print(f"\n=== Detailed Classification Report ===")
    print(classification_report(y_test, y_pred,
                              target_names=class_names, digits=4))

    # 8. Feature importance analysis
    plot_feature_importance(model, data.feature_names)

    # 9. ROC Curve and AUC
    from sklearn.metrics import roc_curve, auc
    fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
    roc_auc = auc(fpr, tpr)

    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2,
             label=f'ROC curve (AUC = {roc_auc:.4f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--',
             label='Random classifier')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate', fontsize=12)
    plt.ylabel('True Positive Rate', fontsize=12)
    plt.title('Receiver Operating Characteristic (ROC) Curve', fontsize=14, fontweight='bold')
    plt.legend(loc="lower right", fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

    print(f"\n=== Confusion Matrix Usage Summary ===")
    print("1. Confusion matrix shows the relationship between predicted and true labels")
    print("2. Diagonal elements represent correctly classified samples")
    print("3. Off-diagonal elements represent misclassified samples")
    print("4. Through confusion matrix, we can calculate accuracy, precision, recall, and other important metrics")
    print("5. In medical diagnosis, recall is often more important as the cost of missing a diagnosis is high")
    print(f"6. ROC AUC score: {roc_auc:.4f} indicates the model's discriminatory power")

if __name__ == "__main__":
    main()