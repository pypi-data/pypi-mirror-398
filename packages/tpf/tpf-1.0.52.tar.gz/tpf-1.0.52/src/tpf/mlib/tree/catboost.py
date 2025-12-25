import sys 
import numpy as np
from catboost import CatBoostClassifier, Pool

def catboostc_01(X_train, y_train, X_valid=None, y_valid=None, 
                 cat_features=None, params =None):
    """
    根据数据库表中的参数配置训练 CatBoost 模型
    支持验证集（eval_set）、早停、分类特征、日志输出等功能
    """

    # 获取数据库配置参数
    if params is None:
        params = {}
    

    # 设置默认参数（仅设置 CatBoost 特有参数）
    default_params = {
        "iterations": 1000,           # 等价于 n_estimators
        "learning_rate": 0.03,
        "depth": 6,                   # 树深度
        "l2_leaf_reg": 3.0,           # L2 正则化
        "random_strength": 1.0,       # 随机分裂强度
        "bagging_temperature": 1.0,   # 温度采样（0: 关闭，1: 启用）
        "grow_policy": 'SymmetricTree',
        "eval_metric": 'Logloss',
        "verbose": 100,               # 每100轮输出一次日志
        "task_type": 'CPU',
        "subsample": 1.0,             # 行采样
        "rsm": 1.0,                   # 列采样（feature_fraction）
        "border_count": 254,
        "loss_function": 'Logloss',
        "early_stopping_rounds": 50   # 新增：早停轮数
    }

    # 补全缺失参数
    for k, v in default_params.items():
        if k not in params:
            params[k] = v

    # 提取早停轮数（用于 eval_set）
    early_stopping_rounds = params.pop("early_stopping_rounds", 50)
    verbose = params.pop("verbose", 100)

    # 处理分类特征
    if cat_features and len(cat_features) > 0:
        cat_features = list(set(cat_features))
        # 转为 category 类型（推荐）
        X_train[cat_features] = X_train[cat_features].astype("category")
        if X_valid is not None:
            X_valid[cat_features] = X_valid[cat_features].astype("category")
    else:
        cat_features = None

    # 构建训练集和验证集（使用 Pool）
    train_pool = Pool(X_train, y_train, cat_features=cat_features)

    # 初始化模型（不传 eval_set）
    model = CatBoostClassifier(**params)

    # 准备 eval_set
    eval_set = train_pool
    if X_valid is not None and y_valid is not None:
        valid_pool = Pool(X_valid, y_valid, cat_features=cat_features)
        eval_set = (train_pool, valid_pool)
    else:
        eval_set = train_pool  # 只有训练集

    # 训练模型
    model.fit(
        X_train, y_train,
        cat_features=cat_features,           # 分类特征
        eval_set=eval_set,                   # 验证集
        early_stopping_rounds=early_stopping_rounds,  # 早停
        verbose=verbose                      # 日志频率
    )

    return model


def catboostc_01(X_train, y_train, X_valid=None, y_valid=None, 
                cat_features=None, params = None):
    """根据数据库表中的参数配置训练CatBoost模型，支持验证集和早停
    """

    # 设置默认参数
    default_params = {
        "iterations": 1000,
        "learning_rate": 0.03,
        "depth": 6,
        "l2_leaf_reg": 3.0,
        "random_strength": 1.0,
        "bagging_temperature": 1.0,
        "grow_policy": 'SymmetricTree',
        "eval_metric": 'Logloss',
        "verbose": 100,
        "early_stopping_rounds": 50,  # 默认早停轮数
        "task_type": 'CPU',
        "subsample": 1.0,
        "rsm": 1.0,
        "border_count": 254,
        "loss_function": 'Logloss',
        "use_best_model": True,  # 使用最佳模型
        "od_type": 'Iter',  # 早停类型
        "od_wait": None  # 早停等待轮数
    }
    
    # 更新参数，优先使用传入的参数
    for key, value in default_params.items():
        if key not in params:
            params[key] = value

    # 提取早停相关参数
    early_stopping_rounds = params.pop('early_stopping_rounds', 50)
    use_best_model = params.pop('use_best_model', True)
    od_type = params.pop('od_type', 'Iter')
    od_wait = params.pop('od_wait', None)

    # 准备eval_set
    eval_set = None
    if X_valid is not None and y_valid is not None:
        # 创建验证集的Pool对象，支持分类特征
        if cat_features and len(cat_features) > 0:
            eval_set = Pool(X_valid, y_valid, cat_features=cat_features)
        else:
            eval_set = Pool(X_valid, y_valid)

    # 初始化CatBoost模型
    model = CatBoostClassifier(
        iterations=params["iterations"],
        learning_rate=params["learning_rate"],
        depth=params["depth"],
        l2_leaf_reg=params["l2_leaf_reg"],
        random_strength=params["random_strength"],
        bagging_temperature=params["bagging_temperature"],
        grow_policy=params["grow_policy"],
        eval_metric=params["eval_metric"],
        verbose=params["verbose"],
        task_type=params["task_type"],
        subsample=params["subsample"],
        rsm=params["rsm"],
        border_count=params["border_count"],
        loss_function=params["loss_function"],
        use_best_model=use_best_model,  # 使用验证集上的最佳模型
        od_type=od_type,  # 早停类型
        od_wait=od_wait if od_wait is not None else early_stopping_rounds
    )

    # 训练模型
    if eval_set is not None:
        # 有验证集时使用早停
        model.fit(
            X_train, y_train,
            cat_features=cat_features,  # 分类特征
            eval_set=eval_set,  # 验证集
            # early_stopping_rounds=early_stopping_rounds,  # CatBoost使用od_wait参数
            use_best_model=use_best_model  # 使用最佳模型
        )
    else:
        # 没有验证集时正常训练
        model.fit(
            X_train, y_train,
            cat_features=cat_features
        )

    return model

# 更高级的版本，支持多个eval_set和更灵活的配置
def catboostc_03(X_train, y_train, X_valid=None, y_valid=None, 
                cat_features=None, params = None, **kwargs):
 
    # 合并参数，kwargs优先，然后是数据库参数，最后是默认值
    merged_params = {
        "iterations": 1000,
        "learning_rate": 0.03,
        "depth": 6,
        "l2_leaf_reg": 3.0,
        "random_strength": 1.0,
        "bagging_temperature": 1.0,
        "grow_policy": 'SymmetricTree',
        "eval_metric": 'Logloss',
        "verbose": 100,
        "early_stopping_rounds": 50,
        "task_type": 'CPU',
        "subsample": 1.0,
        "rsm": 1.0,
        "border_count": 254,
        "loss_function": 'Logloss',
        "use_best_model": True,
        "od_type": 'Iter'
    }
    
    # 更新参数
    merged_params.update(params)
    merged_params.update(kwargs)

    # 准备eval_set
    eval_set = None
    if X_valid is not None and y_valid is not None:
        if cat_features and len(cat_features) > 0:
            eval_set = Pool(X_valid, y_valid, cat_features=cat_features)
        else:
            eval_set = Pool(X_valid, y_valid)

    # 初始化模型
    model = CatBoostClassifier(**{k: v for k, v in merged_params.items() 
                                 if k not in ['early_stopping_rounds']})

    # 训练模型
    fit_params = {
        'cat_features': cat_features,
        'early_stopping_rounds':merged_params.get('early_stopping_rounds',10),
        'use_best_model': merged_params.get('use_best_model', True)
    }
    
    if eval_set is not None:
        fit_params['eval_set'] = eval_set

    model.fit(X_train, y_train, **fit_params)

    return model