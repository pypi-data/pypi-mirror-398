import sys
import numpy as np
import xgboost as xgb
import pandas as pd

def xgbc_01(X_train, y_train, X_valid=None, y_valid=None,
                    params=None, **kwargs):
    """
    XGBoost 分类器训练函数
    """
    # if isinstance(X_train,pd.DataFrame):  #xgbc只支持数字类型
    #     X_train = X_train.astype(np.float32)

    # 默认参数
    default_params = {
        "booster": 'gbtree',
        "objective": 'binary:logistic',
        "max_depth": 6,
        "learning_rate": 0.03,
        "n_estimators": 100,
        "min_child_weight": 1,
        "gamma": 0,
        "subsample": 1.0,
        "colsample_bytree": 1.0,
        "reg_alpha": 0,
        "reg_lambda": 1,
        "verbosity": 1,
        "eval_metric": 'logloss',
        "use_best_model": True,
    }

    # 参数合并
    merged_params = default_params.copy()
    if params is not None:
        merged_params.update(params)
    merged_params.update(kwargs)

    # Python 3.6 版本兼容性处理
    if sys.version_info[:2] == (3, 6):
        merged_params['enable_categorical'] = False
        # 将数据集转换为np.float32类型以确保兼容性
        if isinstance(X_train, pd.DataFrame):
            X_train = X_train.astype(np.float32)
        if X_valid is not None and isinstance(X_valid, pd.DataFrame):
            X_valid = X_valid.astype(np.float32)

    # 构建 eval_set: 必须是 [(X_valid, y_valid)]
    eval_set = []
    if X_valid is not None and y_valid is not None:
        # if isinstance(X_valid, pd.DataFrame):
        #     X_valid = X_valid.astype(np.float32)
        eval_set = [(X_valid, y_valid)]  # 注意：必须是列表，元素是元组

    # 提取 fit 参数
    fit_params = {
        'eval_set': eval_set,
        'verbose': merged_params.get('verbosity', 1) > 0
    }

    # 只有当 eval_set 存在时，才能启用 early_stopping_rounds
    # if eval_set:
    #     fit_params['early_stopping_rounds'] = merged_params.get('early_stopping_rounds', 10)
    # 注意：XGBoost 会自动使用 eval_set 和 early_stopping_rounds 实现 use_best_model

    # 构建模型参数（移除 fit 专用参数）
    model_params = {k: v for k, v in merged_params.items() 
                    if k not in ['verbosity', 'use_best_model']}

    model = xgb.XGBClassifier(**model_params)

    # 训练模型
    model.fit(X_train, y_train, **fit_params)

    return model