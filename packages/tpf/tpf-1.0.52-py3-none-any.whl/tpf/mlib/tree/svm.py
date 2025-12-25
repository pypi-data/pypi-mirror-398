

import numpy as np
from sklearn.svm import SVC


def svc_base_line(X_train, y_train, C=1.0, kernel='rbf'):
    """
    SVM基线模型（简化版本）
    
    Parameters:
    -----------
    C : float, 正则化参数
    kernel : str, 核函数类型
    """
    label = np.array(y_train)
    if label.ndim > 1:
        label = label.ravel()  # 转换为一维数组
    
    # 使用简化的参数配置
    model = SVC(kernel=kernel, gamma='auto', C=C, probability=True)
    model.fit(X_train, label)
    
    return model


def svc_01(X_train, y_train, params=None, **kwargs):
    """
    SVM 分类器训练函数（XGBoost 风格）
    
    Parameters
    ----------
    X_train : array-like, shape (n_samples, n_features)
    y_train : array-like, shape (n_samples,)
    params  : dict or None
        用户自定义超参，会覆盖对应默认值
    **kwargs:
        其余将被直接更新到参数表里
    
    Returns
    -------
    model : sklearn.svm.SVC
        已训练好的 SVM 模型
    """
    # 1. 默认参数表 —— 一目了然
    default_params = {
        'C': 1.0,
        'kernel': 'rbf',
        'degree': 3,          # 仅 poly 有效，rbf 自动忽略
        'gamma': 'scale',
        'coef0': 0.0,
        'shrinking': True,
        'probability': True,  # 多数场景需要概率
        'tol': 1e-3,
        'cache_size': 200,
        'class_weight': None,
        'verbose': False,
        'max_iter': -1,
        'decision_function_shape': 'ovr',
        'break_ties': False,
        'random_state': None,
    }

    # 2. 合并参数
    merged_params = default_params.copy()
    if params is not None:
        merged_params.update(params)
    merged_params.update(kwargs)

    # 3. 标签转 1-D
    y_train = np.asarray(y_train).ravel()

    # 4. 训练 & 返回
    model = SVC(**merged_params)
    model.fit(X_train, y_train)
    return model




