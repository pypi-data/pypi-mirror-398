
from tpf.mlib.modelbase import ModelBase
from tpf.mlib.modelpre import ModelPre as mp 

from tpf.mlib.tree import lgbm_baseline
from tpf.mlib.tree import lgbmc_02
from tpf.mlib.tree import catboostc_03
from tpf.mlib.tree import xgbc_01
from tpf.mlib.tree import svc_01
from tpf.mlib.dlbase import lr_03 
from tpf.mlib.seq import SeqOne
from tpf.mlib.seq import T11,DataSet11 
from tpf.conf.common import ParamConfig
from tpf.d1 import to_numpy
import numpy as np 

class ModelTrain(ModelBase):
    
    def __init__(self):
        super().__init__()
        self._lgbm_name_list = ["LightGBM".lower(),"lgbm","LightGBM"]
        self._lgbmc_name_list = ["LGBMClassifier".lower(),"lgbmc"]
        self._svm_name_list = ["svm","svc","SVM"]
        self._lr_name_list = ["lr","LR","LogisticRegression","logisticregression"]
        self.alg_types = self._lgbm_name_list+["lgbm","lgbmc","xgbc","catboost","copod","svm","svc","lr","LR","SVM","LightGBM","COPOD","LGBMClassifier","DLSeqOne","dlseqone","DLSEQONE","XGBClassifier","XGBClassifier".lower(), "CatBoostClassifier", "CatBoostClassifier".lower()]

    def train(self,alg_type="lgbm",
            X_train=None,y_train=None,X_test=None,y_test=None,
            cat_features=None,params=None, pc:ParamConfig=None,**kwargs):
        """
        Train a machine learning model using the specified algorithm.

        Args:
            alg_type (str): Type of algorithm to use (default: "lgbm")
            X_train: Training feature data
            y_train: Training target labels
            X_test: Test feature data for validation
            y_test: Test target labels for validation
            cat_features: List of categorical feature indices
            params: Model parameters (default: None, will use default params)
            **kwargs: Additional keyword arguments

        Returns:
            Trained model object

        Raises:
            Exception: If algorithm type is not supported
        """

        # Use default parameters if none provided
        if params is None:
            params = self.get_params(alg_type)

        # Train LightGBM regression model
        if alg_type.lower() in self._lgbm_name_list :
            num_boost_round = params.pop('num_boost_round',100)
            y_train = np.array(y_train).reshape(-1)
            y_test = np.array(y_test).reshape(-1)

            model = lgbm_baseline(
                X_train,y_train,
                X_test,y_test,
                cat_features=cat_features,
                num_boost_round=num_boost_round,
                params=params)

        # Train LightGBM classification model
        elif alg_type.lower() in self._lgbmc_name_list :
            y_train = np.array(y_train).reshape(-1)
            y_test = np.array(y_test).reshape(-1)
            model = lgbmc_02(X_train, y_train, X_valid=X_test, y_valid=y_test,
                     cat_features=cat_features,params=params)

        # Train XGBoost classification model
        elif alg_type.lower() in ["xgbc"] :
            # X_train = np.array(X_train)
            # X_test = np.array(X_test)
            y_train = np.array(y_train).reshape(-1)
            y_test = np.array(y_test).reshape(-1)
            model = xgbc_01(
                X_train, y_train,
                X_valid=X_test, y_valid=y_test,
                params=params,
                **kwargs
            )

        # Train CatBoost classification model
        elif alg_type.lower() in ["catboost"] :
            y_train = np.array(y_train).reshape(-1)
            y_test = np.array(y_test).reshape(-1)
            model = catboostc_03(X_train, y_train, X_valid=X_test, y_valid=y_test,
                cat_features=cat_features, params = params, **kwargs)

        elif alg_type.lower() in self._svm_name_list:
            model = svc_01(X_train, y_train, params=params, **kwargs)

        # Train Logistic Regression model
        elif alg_type.lower() in self._lr_name_list:
            y_train = np.array(y_train).reshape(-1)
            y_test = np.array(y_test).reshape(-1) if y_test is not None else None
            model = lr_03(X_train, y_train, X_valid=None, y_valid=None,
                        cat_features=cat_features, params=params, **kwargs)

        elif alg_type.lower() in ["seqone","seqonedl"]:
            # model = COPODModel(contamination=0.05)
            print("seqone------------------------------------------------------------")
            X_train = to_numpy(X_train)
            y_train = to_numpy(y_train)
            def train_data_set():
                return DataSet11(X=X_train, y=y_train, nums_per_label = 1280, n_class=2)

            def test_data_set():
                return DataSet11(X=X_test, y=y_test, nums_per_label = 1000, n_class=2)

            model = SeqOne(seq_len=X_train.shape[1], out_features=2) 
            # T.train(model, 
            #         epochs=50000, 
            #         batch_size=512,
            #         learning_rate=1e-3,
            #         model_param_path=model_param_path,        
            #         train_dataset_func=train_data_set, 
            #         test_dataset_func=test_data_set,
            #         log_file="/tmp/train.log",
            #         per_epoch=10) 
            T11.train(model, X_train,  y_train, X_test, y_test,
                    epochs=5, 
                    batch_size=512,
                    learning_rate=1e-4,
                    model_param_path="model_params_12.pkl.dict",        
                    log_file="/tmp/train.log",
                    per_epoch=100)

        # Validate algorithm type
        else:
            raise Exception(f"alg_type={alg_type},Currently only supported types:{self.alg_types}")

        return model

    @classmethod
    def predict_proba(cls, data, model_path=None, model_type=None,model=None,cat_features=None):
        y_prob = mp.predict_proba(data, model_path=model_path, model_type=model_type,model=model,cat_features=cat_features)
        return y_prob
    
    def get_params(self, alg_type):
        if alg_type.lower() in ["lgbm"] :
            params = {
                'bagging_fraction': 0.8,
                    'feature_fraction': 0.9,
                    'lambda_l1': 0.001,
                    'lambda_l2': 0.001,
                    'learning_rate': 0.01,
                    'max_depth': 5,
                    'metric': 'binary_logloss',
                    'min_child_samples': 10,
                    'min_data_in_leaf': 10,
                    'min_gain_to_split': 1e-4,
                    'n_estimators': 100,
                    'num_leaves': 5,
                    'num_threads': 4,
                    'objective': 'binary',
                    'num_boost_round':100}
            
        if alg_type.lower() in ["lgbmc"] :
            params={
                "boosting_type": 'gbdt',
                "objective": 'binary',
                "class_weight": None,
                "learning_rate":0.01,
                "max_depth": -1,
                "lambda_l1": 0.01,
                "lambda_l2": 0.01,
                "min_child_samples": 10,
                "min_data_in_leaf": 30,
                "bagging_fraction": 0.8,
                "feature_fraction": 0.9,
                "early_stopping_rounds":20,
                "n_estimators":300,
                "num_leaves":30,
                "verbose": -1
            }
        if alg_type.lower() in ["xgbc"] :
            params =  {
                "booster": 'gbtree',
                "objective": 'binary:logistic',
                "max_depth": 6,
                "learning_rate": 0.03,
                "n_estimators": 1000,
                "min_child_weight": 1,
                "gamma": 0,
                "subsample": 1.0,
                "colsample_bytree": 1.0,
                "reg_alpha": 0,
                "reg_lambda": 1,
                "verbosity": 1,
                "eval_metric": 'logloss',
                "use_best_model": True,
                "early_stopping_rounds": 20
            }
        if alg_type.lower() in ["catboost"] :
            params = {
                "iterations": 1000,   #与num_trees,num_boost_round,n_estimators同义
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
        if alg_type.lower() in self._lr_name_list:
            params = {
                'penalty': 'l2',
                'C': 0.1,                     # 较强的正则化防止过拟合
                'fit_intercept': True,
                'solver': 'lbfgs',
                'max_iter': 10000,
                'multi_class': 'auto',
                'class_weight': 'balanced',    # 处理类别不平衡
                'random_state': 42,
                'tol': 1e-4,
                'verbose': 0,
                'n_jobs': -1,                 # 使用所有CPU核心
                'l1_ratio': None,
            }

        return params
    
        
    
    

            
            
        