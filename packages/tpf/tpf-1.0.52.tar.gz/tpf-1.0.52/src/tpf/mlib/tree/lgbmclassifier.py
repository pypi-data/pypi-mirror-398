
import sys 
import numpy as np
from lightgbm import LGBMClassifier
from lightgbm import log_evaluation, early_stopping


def lgbmc_01(X_train, y_train, params=None):
    """根据数据库表中的参数配置训练模型
    """

    if "boosting_type" not in params.keys():
        params["boosting_type"] = 'gbdt'

    if "objective" not in params.keys():
        params["objective"] = 'binary'

    if "class_weight" not in params.keys():
        params["class_weight"] = None

    if "max_depth" not in params.keys():
        params["max_depth"] = -1

    if "lambda_l1" not in params.keys():
        params["lambda_l1"] = 0.01
    if "lambda_l2" not in params.keys():
        params["lambda_l2"] = 0.01

    if "min_child_samples" not in params.keys():
        params["min_child_samples"] = 10

    if "min_data_in_leaf" not in params.keys():
        params["min_data_in_leaf"] = 30

    if "bagging_fraction" not in params.keys():
        params["bagging_fraction"] = 0.8

    if "feature_fraction" not in params.keys():
        params["feature_fraction"] = 0.9

    # 初始化模型
    model = LGBMClassifier(
        boosting_type=params["boosting_type"],
        objective=params["objective"],
        class_weight=params["class_weight"],
        max_depth=params["max_depth"],
        lambda_l1=params["lambda_l1"],  # L1正则化项权重
        lambda_l2=params["lambda_l2"],  # L2正则化项权重
        min_child_samples=params["min_child_samples"],
        min_data_in_leaf=params["min_data_in_leaf"],
        bagging_fraction=params["bagging_fraction"],
        feature_fraction=params["feature_fraction"],
        verbose=-1
    )

    # 训练模型（假设X_train和y_train是已经准备好的训练数据和标签）
    model.fit(X_train, y_train)

    return model

def lgbmc_02(X_train, y_train, X_valid=None, y_valid=None, 
             cat_features=None,params={
        "boosting_type": 'gbdt',
        "objective": 'binary',
        "class_weight": None,
        "max_depth": -1,
        "lambda_l1": 0.01,
        "lambda_l2": 0.01,
        "min_child_samples": 10,
        "min_data_in_leaf": 30,
        "bagging_fraction": 0.8,
        "feature_fraction": 0.9,
        "early_stopping_rounds":10,
        "n_estimators":100,
        "verbose": -1
    }):
    """
    训练 LGBMClassifier 模型，并支持验证集（eval_set）、早停等功能
    """
    if params is None:
        params = {}

    # 补全默认参数
    default_params = {
        "boosting_type": 'gbdt',
        "objective": 'binary',
        "class_weight": None,
        "num_leaves":30,
        "max_depth": -1,
        "lambda_l1": 0.01,
        "lambda_l2": 0.01,
        "min_child_samples": 10,
        "min_data_in_leaf": 30,
        "bagging_fraction": 0.8,
        "feature_fraction": 0.9,
        "verbose": -1
    }
    
    # 更新缺失的参数
    for k, v in default_params.items():
        if k not in params:
            params[k] = v

    # 提取 eval_set 相关参数
    early_stopping_rounds = params.pop('early_stopping_rounds', 10)
    # verbose = params.pop('verbose', -1)  # 控制日志输出
    # early_stopping_rounds = params.get('early_stopping_rounds', 10)

    if cat_features and len(cat_features)>0:
        cat_features = list(set(cat_features))
        X_train[cat_features] = X_train[cat_features].astype("category")
        X_valid[cat_features] = X_valid[cat_features].astype("category")

    # 初始化模型（不传 eval 相关参数）
    # model = LGBMClassifier(
    #     boosting_type=params["boosting_type"],
    #     objective=params["objective"],
    #     class_weight=params["class_weight"],
    #     max_depth=params["max_depth"],
    #     lambda_l1=params["lambda_l1"],
    #     lambda_l2=params["lambda_l2"],
    #     min_child_samples=params["min_child_samples"],
    #     min_data_in_leaf=params["min_data_in_leaf"],
    #     bagging_fraction=params["bagging_fraction"],
    #     feature_fraction=params["feature_fraction"],
    #     n_estimators=params["n_estimators"],
    #     learning_rate=params["learning_rate"],
    #     num_leaves=params.get("num_leaves",30),
    #     verbose= verbose  # 这里设为 -1，由 fit 的 verbose 控制
    # )
    model = LGBMClassifier(**params)

    # 准备 eval_set
    eval_set = []
    eval_names = []
    
    # 训练集也可以监控（可选）
    eval_set.append((X_train, y_train))
    eval_names.append('train')
    
    # 添加验证集（如果提供）
    if X_valid is not None and y_valid is not None:
        eval_set.append((X_valid, y_valid))
        eval_names.append('valid')

    # 训练模型，支持验证集和早停
    model.fit(
        X_train, y_train,
        categorical_feature=cat_features,
        eval_set=eval_set,
        eval_names=eval_names,
        callbacks=[early_stopping(early_stopping_rounds), log_evaluation(early_stopping_rounds)]  # 早停 + 日志输出
        # verbose=verbose  # 控制每多少轮输出一次日志
    )

    return model
