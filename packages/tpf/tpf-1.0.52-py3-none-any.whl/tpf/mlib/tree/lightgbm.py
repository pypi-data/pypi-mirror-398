

import numpy as np
import lightgbm as lgb

def dataset_pre(data_pd, cat_features):
    cat_features = list(set(cat_features))
    data_pd[cat_features] = data_pd[cat_features].astype("category")
    return data_pd

def lgbm_baseline(X_train, y_train, X_test, y_test, 
                   cat_features=None, num_boost_round=100, 
                   params={'bagging_fraction': 0.8,
                        'feature_fraction': 0.9,
                        'lambda_l1': 0.01,
                        'lambda_l2': 0.01,
                        'learning_rate': 0.1,
                        'max_depth': -1,
                        'metric': 'binary_logloss',
                        'min_child_samples': 10,
                        'min_data_in_leaf': 20,
                        'min_gain_to_split': 0,
                        'n_estimators': 100,
                        'num_leaves': 31,
                        'num_threads': 4,
                        'objective': 'binary',
                        "early_stopping_rounds":10}):
    """
    # 创建LightGBM数据集，并指定分类特征
    # free_raw_data=False是因为在数据上设置部分列为category类型,此时lightgbm要求这个数据集不能被释放
train_data = lgb.Dataset(X_train, label=y_train, free_raw_data=False, categorical_feature=cat_features)
    test_data = lgb.Dataset(X_test, label=y_test,  reference=train_data)

    # 设置参数并训练模型
    if params is None:
        params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'boosting_type': 'gbdt',
            'force_col_wise':True}
    lgb_model = lgb.train(params, train_data, num_boost_round=num_boost_round,  valid_sets=[test_data],)

    """
    if cat_features and len(cat_features)>0:
        cat_features = list(set(cat_features))
        X_train[cat_features] = X_train[cat_features].astype("category")
        X_test[cat_features] = X_test[cat_features].astype("category")

        # 创建LightGBM数据集，并指定分类特征
        # free_raw_data=False是因为在数据上设置部分列为category类型,此时lightgbm要求这个数据集不能被释放
        train_data = lgb.Dataset(X_train, label=y_train, free_raw_data=False, categorical_feature=cat_features)
        test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

    else:
        train_data = lgb.Dataset(X_train, label=y_train, free_raw_data=False)
        test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

        
    # 设置参数并训练模型
    if params is None:
        params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'boosting_type': 'gbdt',
            'force_col_wise': True}
    # if "verbose_eval" not in params.keys():
    #     params["verbose_eval"] = 10

    if "early_stopping_rounds" not in params.keys():
        params["early_stopping_rounds"] = 10
    
    lgb_model = lgb.train(params, train_data, 
                          num_boost_round=num_boost_round, 
                          valid_sets=[test_data], )
    return lgb_model
