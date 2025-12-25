"""
方法直接放tpf的__init__方法中
除以下两个
python基础方法，
data集获取方法
"""
import numpy as np
# import torch 

import lightgbm as lgb
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression

from tpf.d1 import pkl_load,pkl_save,is_single_label


class MLib():

    @staticmethod
    def copod_base_line(contamination=0.05):
        from tpf.mlib.copod import COPODModel
        model = COPODModel(contamination=0.05)
        return model

    @staticmethod
    def lgbm_params():
        params = """

        # 设置LightGBM参数
        params = {
            'objective': 'binary',  # 目标函数为二分类
            'metric': 'auc',  # 评估指标为AUC
            'max_depth': 6,  # 树的最大深度
            'num_leaves': 31,  # 叶子节点数
            'learning_rate': 0.02,  # 学习率
            'bagging_fraction': 0.8,  # 每次迭代时用的数据比例
            'bagging_freq':3,
            'feature_fraction': 0.8,  # 每次迭代中随机选择特征的比例
            'min_child_samples':3,  # 一个叶子节点上数据的最小数量
            'min_data_in_leaf':100,
            'verbose': -1,  # 是否打印训练过程中的信息，-1表示不打印
            'max_bin':3,
            'min_gain_to_split':0,
            'min_data_in_leaf':10,
            'force_col_wise':True
        }
        ## num_boost_round
        -提升算法是一种集成学习技术，它通过结合多个弱学习器（通常是决策树）来形成一个强学习器。
        -每一轮（round）中，算法都会根据当前模型的预测误差来构建一个新的弱学习器，
        -并将其添加到已有的模型集合中，以此来减少总体误差。
        -num_boost_round参数指的是算法将执行的提升（boosting）轮次的数量。
        -
        简单说，就是num_boost_round控制了lightgbm训练的轮次
        ## min_data_in_leaf
        - 默认是20，减少这个值可以让模型在叶子节点中包含更少的数据点，这有助于在数据较少的情况下进行分裂。
        - 因样本数据非常少的情况下，可以适当降低这个值
        ## force_col_wise
        - 在内存不足的情况下，force_col_wise为True，有助于模型训练
        ## max_bin
        - 每个特征 最多 划分为多少个箱子
        - 模型只是参考用户所输入的参数，具体如何分箱，全体数据集划分多少个箱子，仍以模型的自我决定为主
        - 这个参数通常是先让模型自主决定，出现问题时再人工介入调整
        ## max_depth
        －　default = -1, type = int
            limit the max depth for tree model. 
            This is used to deal with over-fitting when #data is small. 
            Tree still grows leaf-wise
            <= 0 means no limit
        - 决策树划分时，从root节点开始，到叶子节点分支上的节点个数，为树的深度(depth)，
        - 叶子节点存储的是分类结果，不再划分数据,比如min_data_in_leaf参数可以确定一个叶子最多存储多少个数据
        - 如果只有一次划分，就是一个root节点，加上两个叶子节点，此时的depth为1,max_depth亦为1
        - 有多个分支时，max_depth是所有分支中最大的depth

        ## num_leaves 
        - max number of leaves in one tree
        - default = 31, 
        - type = int, 
        - aliases: num_leaf, max_leaves, max_leaf, max_leaf_nodes, 
        - constraints: 1 < num_leaves <= 131072
        - 影响模型复杂度和拟合能力
        ## feature_fraction 
        -当设置 feature_fraction=0.9 时，它意味着在构建每一棵树时，
        -算法会随机选择大约90%的特征来进行树的分裂操作，而不是全部特征。
        ## bagging_fraction与bagging_freq
        - 当 `bagging_fraction=0.9` 时，表示每次构建树模型时将从原始训练数据集中随机抽取 90% 的数据样本用于训练该树。这种做法可以增加模型的多样性，并有助于提高模型的泛化能力。
        - `bagging_freq` 指定每多少次迭代执行一次 bagging（数据采样）操作。例如，如果 `bagging_freq=2`，则表示每两次迭代执行一次 bagging。
        ## max_bin
        - 每个特征 最多 划分为多少个箱子
        - 模型只是参考用户所输入的参数，具体如何分箱，全体数据集划分多少个箱子，仍以模型的自我决定为主
        - 这个参数通常是先让模型自主决定，出现问题时再人工介入调整

        """
        return params

    @staticmethod
    def lgbm1(X_train, y_train, X_test, y_test):
        """
        params = {
            'objective': 'binary',  # 目标函数为二分类
            'metric': 'auc',  # 评估指标为AUC
            'num_leaves': 31,  # 叶子节点数
            'max_depth': 6,  # 树的最大深度
            'learning_rate': 0.02,  # 学习率
            'bagging_fraction': 0.8,  # 每次迭代时用的数据比例
            'feature_fraction': 0.8,  # 每次迭代中随机选择特征的比例
            'min_child_samples': 25,  # 一个叶子节点上数据的最小数量
            'verbose': -1  # 是否打印训练过程中的信息，-1表示不打印
        }

        # 训练LightGBM模型
        model = lgb.LGBMClassifier(**params)
        model.fit(X_train, y_train, eval_set=[(X_train, y_train), (X_test, y_test)],
                eval_metric=['auc', 'binary_logloss'])

        """
        # 设置LightGBM参数
        params = {
            'objective': 'binary',  # 目标函数为二分类
            'metric': 'auc',  # 评估指标为AUC
            'boosting_type': 'gbdt',
            'num_leaves': 31,  # 叶子节点数
            'max_depth': 6,  # 树的最大深度
            'learning_rate': 0.02,  # 学习率
            'bagging_fraction': 0.8,  # 每次迭代时用的数据比例
            'feature_fraction': 0.8,  # 每次迭代中随机选择特征的比例
            'min_child_samples': 25,  # 一个叶子节点上数据的最小数量
            'verbose': -1  # 是否打印训练过程中的信息，-1表示不打印
        }

        # 训练LightGBM模型
        model = lgb.LGBMClassifier(**params)
        model.fit(X_train, y_train, eval_set=[(X_train, y_train), (X_test, y_test)],
                  eval_metric=['auc', 'binary_logloss'])
        return model

    @staticmethod
    def lgbm2(X_train, y_train, X_test, y_test, cat_features, num_boost_round, params=None):
        """
        # free_raw_data=False是因为在数据上设置部分列为category类型,此时lightgbm要求这个数据集不能被释放
        train_data = lgb.Dataset(X_train, label=y_train, free_raw_data=False, categorical_feature=cat_features)
        test_data = lgb.Dataset(X_test, label=y_test,  reference=train_data)

        # 设置参数并训练模型
        if params is None:
            params = {
                'objective': 'binary',
                'metric': 'binary_logloss',
                'boosting_type': 'gbdt',
                'max_depth': 3,
                'num_leaves': 3,
                'max_bin':3,
                'min_gain_to_split':0,
                'min_data_in_leaf':10,
                'force_col_wise':True}
        lgb_model = lgb.train(params, train_data, num_boost_round=num_boost_round,  valid_sets=[test_data],)

        """
        # 创建LightGBM数据集，并指定分类特征
        # free_raw_data=False是因为在数据上设置部分列为category类型,此时lightgbm要求这个数据集不能被释放
        train_data = lgb.Dataset(X_train, label=y_train, free_raw_data=False, categorical_feature=cat_features)
        test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

        # 设置参数并训练模型
        if params is None:
            params = {
                'objective': 'binary',
                'metric': 'binary_logloss',
                'boosting_type': 'gbdt',
                'max_depth': 3,
                'num_leaves': 3,
                'max_bin': 3,
                'min_gain_to_split': 0,
                'min_data_in_leaf': 10,
                'force_col_wise': True}
        lgb_model = lgb.train(params, train_data, num_boost_round=num_boost_round, valid_sets=[test_data], )
        return lgb_model

    @staticmethod
    def lgbm_baseline(X_train, y_train, X_test, y_test, cat_features, num_boost_round, params=None):
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
        cat_features = list(set(cat_features))
        X_train[cat_features] = X_train[cat_features].astype("category")
        X_test[cat_features] = X_test[cat_features].astype("category")

        # 创建LightGBM数据集，并指定分类特征
        # free_raw_data=False是因为在数据上设置部分列为category类型,此时lightgbm要求这个数据集不能被释放
        train_data = lgb.Dataset(X_train, label=y_train, free_raw_data=False, categorical_feature=cat_features)
        test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

        # 设置参数并训练模型
        if params is None:
            params = {
                'objective': 'binary',
                'metric': 'binary_logloss',
                'boosting_type': 'gbdt',
                'force_col_wise': True}
        lgb_model = lgb.train(params, train_data, num_boost_round=num_boost_round, valid_sets=[test_data], )
        return lgb_model

    @staticmethod
    def model_save(model, model_path):
        if model_path.endswith(".dict"):
            import torch
            torch.save(model.state_dict(), model_path)
        else:
            pkl_save(model, file_path=model_path, use_joblib=True)

    @staticmethod
    def model_load(model_path, model=None):
        if model is None:
            model = pkl_load(file_path=model_path, use_joblib=True)
        elif model_path.endswith(".dict"):
            import torch
            model.load_state_dict(torch.load(model_path,weights_only=True))
        return model

    @staticmethod
    def lr_base_line(X_train, y_train, max_iter=10000):
        label = np.array(y_train)
        if label.ndim > 1:
            label = label.ravel()  # 转换为一维数组

        # 初始化逻辑回归模型
        lr = LogisticRegression(max_iter=max_iter)  # 增加迭代次数以确保收敛

        # 训练模型
        lr.fit(X_train, label)
        return lr

    

    @staticmethod
    def lgbm_cv1(train_data, num_boost_round=1, nfold=3):
        """交叉验证示例
        """
        # 设置参数并训练模型
        params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'boosting_type': 'gbdt',
            'max_depth': 3,
            'num_leaves': 3,
            'min_gain_to_split': 0,
            'min_data_in_leaf': 10,
            'force_col_wise': True}
        cv_results = lgb.cv(params, train_data, num_boost_round=num_boost_round, nfold=3, stratified=True,
                            metrics=['binary_logloss'])
        return cv_results

    @staticmethod
    def svc_base_line(X_train, y_train, C=1.0, kernel='rbf'):
        """
        params
        -----------------------------
        - C: 越大越准，但会过拟合，受噪声影响大；越小越简单，欠拟合，预测能力弱
        - kernel: 线性核函数（linear）、多项式核函数（polynomial）、高斯核函数（rbf）等

        """
        label = np.array(y_train)
        if label.ndim > 1:
            label = label.ravel()  # 转换为一维数组
        # 训练SVC模型，并设置probability=True以生成预测概率
        svc = SVC(kernel=kernel, gamma='auto', C=C, probability=True)
        svc.fit(X_train, label)
        return svc


