
import numpy as np
from sklearn.linear_model import LogisticRegression


def lr_base_line(X_train, y_train, max_iter=10000):
    """
    Logistic Regression基线模型（简化版本）

    Parameters:
    -----------
    X_train : array-like, 训练特征数据
    y_train : array-like, 训练标签数据
    max_iter : int, 最大迭代次数

    Returns:
    --------
    model : LogisticRegression, 已训练的逻辑回归模型
    """
    label = np.array(y_train)
    if label.ndim > 1:
        label = label.ravel()  # 转换为一维数组

    # 初始化逻辑回归模型
    lr = LogisticRegression(max_iter=max_iter)  # 增加迭代次数以确保收敛

    # 训练模型
    lr.fit(X_train, label)
    return lr


def lr_01(X_train, y_train, params=None, **kwargs):
    """
    Logistic Regression 分类器训练函数（XGBoost 风格）

    Parameters
    ----------
    X_train : array-like, shape (n_samples, n_features)
        训练特征数据
    y_train : array-like, shape (n_samples,)
        训练标签数据
    params : dict or None
        用户自定义超参，会覆盖对应默认值
    **kwargs:
        其余参数将被直接更新到参数表里

    Returns
    -------
    model : sklearn.linear_model.LogisticRegression
        已训练好的逻辑回归模型
    """
    # 1. 默认参数表 —— 一目了然
    default_params = {
        'penalty': 'l2',              # 正则化类型：l1, l2, elasticnet, None
        'C': 1.0,                     # 正则化强度的倒数
        'fit_intercept': True,        # 是否拟合截距项
        'solver': 'lbfgs',            # 优化算法：liblinear, lbfgs, newton-cg, sag, saga
        'max_iter': 10000,            # 最大迭代次数
        'class_weight': None,         # 类别权重：None, balanced, or dict
        'random_state': 42,           # 随机种子
        'tol': 1e-4,                  # 收敛容差
        'verbose': 0,                 # 输出详细程度
        'n_jobs': None,               # 并行计算核心数
        'l1_ratio': None,             # elasticnet混合参数（仅当penalty='elasticnet'时有效）
    }

    # 2. 合并参数
    merged_params = default_params.copy()
    if params is not None:
        merged_params.update(params)
    merged_params.update(kwargs)

    # 3. 标签转 1-D
    y_train = np.asarray(y_train).ravel()

    # 4. 训练 & 返回
    model = LogisticRegression(**merged_params)
    model.fit(X_train, y_train)
    return model


def lr_02(X_train, y_train, X_valid=None, y_valid=None, params=None, **kwargs):
    """
    Logistic Regression 分类器训练函数（支持验证集和早停）

    Parameters
    ----------
    X_train : array-like, shape (n_samples, n_features)
        训练特征数据
    y_train : array-like, shape (n_samples,)
        训练标签数据
    X_valid : array-like, shape (n_samples, n_features), optional
        验证特征数据
    y_valid : array-like, shape (n_samples,), optional
        验证标签数据
    params : dict or None
        用户自定义超参，会覆盖对应默认值
    **kwargs:
        其余参数将被直接更新到参数表里

    Returns
    -------
    model : sklearn.linear_model.LogisticRegression
        已训练好的逻辑回归模型
    """
    # 1. 默认参数表
    default_params = {
        'penalty': 'l2',
        'C': 1.0,
        'fit_intercept': True,
        'solver': 'lbfgs',
        'max_iter': 10000,
        'class_weight': None,
        'random_state': 42,
        'tol': 1e-4,
        'verbose': 0,
        'n_jobs': None,
        'l1_ratio': None,
    }

    # 2. 合并参数
    merged_params = default_params.copy()
    if params is not None:
        merged_params.update(params)
    merged_params.update(kwargs)

    # 3. 标签转 1-D
    y_train = np.asarray(y_train).ravel()

    # 4. 如果有验证集，使用warm_start进行早停（部分solver支持）
    if X_valid is not None and y_valid is not None and merged_params['solver'] in ['sag', 'saga', 'liblinear']:
        y_valid = np.asarray(y_valid).ravel()

        # 设置warm_start以支持增量训练
        merged_params['warm_start'] = True
        merged_params['max_iter'] = 100  # 每次训练的迭代次数

        # 初始化模型
        model = LogisticRegression(**merged_params)

        # 简单的早停逻辑：验证集性能不再提升时停止
        best_score = -np.inf
        patience = 50  # 容忍轮数
        no_improve_count = 0
        max_epochs = 1000

        for epoch in range(max_epochs):
            model.fit(X_train, y_train)

            # 在验证集上评估
            valid_score = model.score(X_valid, y_valid)

            if valid_score > best_score:
                best_score = valid_score
                no_improve_count = 0
            else:
                no_improve_count += 1

            if no_improve_count >= patience:
                print(f"Early stopping at epoch {epoch}, best validation score: {best_score:.4f}")
                break
    else:
        # 没有验证集或不支持warm_start，直接训练
        model = LogisticRegression(**merged_params)
        model.fit(X_train, y_train)

    return model


def lr_03(X_train, y_train, X_valid=None, y_valid=None, cat_features=None, params=None, **kwargs):
    """
    Logistic Regression 分类器训练函数（完整版本，支持分类特征和灵活配置）

    Parameters
    ----------
    X_train : array-like, shape (n_samples, n_features)
        训练特征数据
    y_train : array-like, shape (n_samples,)
        训练标签数据
    X_valid : array-like, shape (n_samples, n_features), optional
        验证特征数据
    y_valid : array-like, shape (n_samples,), optional
        验证标签数据
    cat_features : list or None, optional
        分类特征列名或索引列表
    params : dict or None
        用户自定义超参，会覆盖对应默认值
    **kwargs:
        其余参数将被直接更新到参数表里

    Returns
    -------
    model : sklearn.linear_model.LogisticRegression
        已训练好的逻辑回归模型
    """
    # 1. 默认参数表 - 适用于金融欺诈检测场景
    default_params = {
        'penalty': 'l2',
        'C': 0.1,                     # 较强的正则化防止过拟合
        'fit_intercept': True,
        'solver': 'lbfgs',
        'max_iter': 10000,
        'class_weight': 'balanced',    # 处理类别不平衡
        'random_state': 42,
        'tol': 1e-4,
        'verbose': 0,
        'n_jobs': -1,                 # 使用所有CPU核心
        'l1_ratio': None,
    }

    # 2. 合并参数，kwargs优先，然后是数据库参数，最后是默认值
    merged_params = default_params.copy()
    if params is not None:
        merged_params.update(params)
    merged_params.update(kwargs)

    # 3. 标签转 1-D
    y_train = np.asarray(y_train).ravel()

    # 4. 处理分类特征（如果有）
    if cat_features is not None and len(cat_features) > 0:
        # 对于逻辑回归，分类特征需要编码
        # 这里假设输入已经是编码后的特征，或者需要进行额外的预处理
        import warnings
        warnings.warn("LogisticRegression requires categorical features to be encoded. Make sure they are properly preprocessed.")

    # 5. 训练模型
    model = LogisticRegression(**merged_params)
    model.fit(X_train, y_train)

    # 6. 可选：如果有验证集，输出验证集性能
    if X_valid is not None and y_valid is not None:
        y_valid = np.asarray(y_valid).ravel()
        valid_score = model.score(X_valid, y_valid)
        print(f"Validation accuracy: {valid_score:.4f}")

    return model




