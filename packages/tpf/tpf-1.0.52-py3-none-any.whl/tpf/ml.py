"""
机器学习模型接口,机器学习常用算法包,
模型尽量按英文字母排序编写(便于查找)
"""

import tpf.d1 as d1 
from sklearn.feature_selection import RFE
from sklearn.linear_model import LogisticRegression
import numpy as np 

from tpf.params import TPF_MODELDIR
from tpf import pkl_load,pkl_save

# 模型保存加载 开始-----------------------------------

import joblib 
class ModelLoad():
    def __init__(self) -> None:
        pass

    @staticmethod
    def model_save_joblib(model,file_path):
        """
        joblib模型保存
        ---------------------------
        model_save_path = os.path.join(BASE_DIR,"model/model1.m")
        ml.model_save_joblib(model,model_save_path)
        """
        joblib.dump(model,file_path)

    @staticmethod
    def model_load_joblib(file_path):
        """
        joblib模型加载
        ------------------------------
        m1 = ml.model_load_joblib(model_save_path)
        print("加载K=1模型,训练得分:{}".format(m1.score(x,y)))
        """
        model = joblib.load(file_path)
        return model 


def model_save_joblib(model,file_path):
    """
    模型保存与加载


    模型保存
    ---------------------------
    model_save_path = os.path.join(BASE_DIR,"model/model1.m")
    ml.model_save_joblib(model,model_save_path)


    模型加载
    ------------------------------
    m1 = ml.model_load_joblib(model_save_path)
    print("加载K=1模型,训练得分:{}".format(m1.score(x,y)))
    """
    joblib.dump(model,file_path)

def model_load_joblib(file_path):
    model = joblib.load(file_path)
    return model 


# 模型保存加载 结束-----------------------------------



# 常用模型 开始-----------------------------------
from sklearn.neighbors import KNeighborsClassifier
class KNClassifier():
    """K个近邻分类算法

    示例
    ----------------------------
    knn = KNClassifier()

    knn.fit(X=X_train,y=y_train)

    y_pred=knn.predict(X=X_test)
    
    print(y_pred)

    print(knn.score(X=X_test,y=y_test))

    """
    def __init__(self,n_neighbors=5) -> None:
        self.n_neighbors = n_neighbors

    def fit(self,X,y):
        self.X = np.array(X) 
        self.y = np.array(y)

    def predict(self,X):
        """求距离最近样本标签

        输入:
            X (2维数组): n个预测样本
        """
        X = np.array(X)
        if X.ndim != 2:
            raise Exception(f"当前输入维度为{X.ndim},要求输入维度为2维")

        result = []
        for x in X: # 循环遍历所有输入样本
            # 然后计算每个输入样本与整个训练集的距离 
            distance = np.sqrt(((self.X - x)**2).sum(axis=1))

            # 从训练集中取出与样本距离最近的样本 对应的标签
            label=self.y[np.argsort(distance)[:self.n_neighbors]]

            # 求个数最多的标签的值 
            y = max(set(label),key=label.tolist().count)
            result.append(y)

        return np.array(result) 

    def score(self,X,y):
        y_pred = self.predict(X=X)
        acc = (y_pred==y).mean()
        return acc 

class KNSelector(d1.Stat):
    """K个近邻分类算法
    定义数种不同的参数，以观察效果；
    """
    def KNN_BASE(self,data_list,k=3,weights='uniform',algorithm='auto',isfit=True):
        """训练计算得分

        Args:
            data_list (_type_): x_train,y_train,x_test,y_test或x_train,y_train格式的数据列表，有测试集时会给出测试集的得分

            k (int, optional): 最近样本个数. Defaults to 3.
            weights (str, optional): 样本权重加成. Defaults to 'uniform'.
            algorithm (str, optional): _description_. Defaults to 'auto'.
            isfit (bool, optional): 不训练的话，返回未经训练的模型，可以再另行训练. Defaults to True.

        Returns:
            model: 训练好的模型
        """
        if len(data_list) == 4:
            x_train,y_train,x_test,y_test = data_list[0],data_list[1],data_list[2],data_list[3]
        elif len(data_list) == 2:
             x_train,y_train = data_list[0],data_list[1]

        model = KNeighborsClassifier(n_neighbors=k,weights=weights,algorithm=algorithm)
        if isfit:
            model.fit(x_train,y_train)
            print("----------------------------------------")
            self.log("K={},weights='{}',algorithm='{}',train set score：{}".format(k,weights,algorithm, model.score(x_train,y_train)))
            if len(data_list) == 4:
                self.log("K={},test set score：{}".format(k, model.score(x_test, y_test)))
        return model  

    def KNN_1(self,data_list,k=1,weights='uniform',algorithm='auto',isfit=True):
        model = self.KNN_BASE(data_list,k=k,weights=weights,algorithm=algorithm,isfit=isfit)
        return model 

    def KNN_2(self,data_list,k=2,weights='uniform',algorithm='kd_tree',isfit=True):
        model = self.KNN_BASE(data_list,k=k,weights=weights,algorithm=algorithm,isfit=isfit)
        return model 

    def KNN_3(self,data_list,k=3,weights='distance',algorithm='kd_tree',isfit=True):
        model = self.KNN_BASE(data_list,k=k,weights=weights,algorithm=algorithm,isfit=isfit)
        return model 

    def KNN_4(self,data_list,k=3,weights='uniform',algorithm='brute',isfit=True):
        model = self.KNN_BASE(data_list,k=k,weights=weights,algorithm=algorithm,isfit=isfit)
        return model 
    
    @staticmethod
    def sample1():
        knn1 = KNeighborsClassifier(n_neighbors=5)
        knn1.fit(X=X_train, y=y_train)
        y_pred=knn1.predict(X=X_test)
        acc = (y_pred == y_test).mean()
        print(f"(y_pred == y_test).mean()     :{acc}")                             # 0.9385964912280702
        print(f"knn1.score(X=X_test, y=y_test):{knn1.score(X=X_test, y=y_test)}")  # 0.9385964912280702


from sklearn import svm
class SVM(d1.Stat):
    def svm_1(self,data_list,kernel = 'linear',isfit=True):
        if len(data_list) == 4:
            x_train,y_train,x_test,y_test = data_list[0],data_list[1],data_list[2],data_list[3]
        elif len(data_list) == 2:
             x_train,y_train = data_list[0],data_list[1]

        model = svm.SVC(kernel = kernel) 
        if isfit:
            model.fit(x_train,y_train)
            print("----------------------------------------")
            self.log("训练集得分：{}".format(model.score(x_train,y_train)))
            if len(data_list) == 4:
                self.log("测试集得分：{}".format(model.score(x_test, y_test)))
        return model 


# 常用模型 结束-----------------------------------
from sklearn.tree import DecisionTreeClassifier,DecisionTreeRegressor
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier


class ModelBase(d1.Stat):
    _score_list = []
    _model_define = {}

    def __init__(self,data_list=[],print_level=2) -> None:
        if len(data_list) == 4:
            self.x_train,self.y_train,self.x_test,self.y_test = data_list[0],data_list[1],data_list[2],data_list[3]
        elif len(data_list) == 2:
             self.x_train,self.y_train = data_list[0],data_list[1]
        self.pprint_level = print_level
    
    def score_list_clear(self):
        self._score_list = []
    
    def score_list_get(self):
        return self._score_list

    def score_list(self,print_level=2):
        if self.print_level >= print_level:
            for score in self._score_list:
                self.log(score,print_level)
        return self._score_list

    def has_model(self,model_name):
        flag = False
        for key in self._model_define.keys():
            if key == model_name:
                flag = True
                break
        return flag 


class TreeModel(ModelBase,d1.Stat):

    def __init__(self,data_list=[],print_level=2) -> None:
        super().__init__(data_list=data_list,print_level=print_level)
        

    def decision_tree_classifier_1(self,max_depth=5):
        model = DecisionTreeClassifier(max_depth=max_depth)
        return model


    def gradient_boosting(self,data_list, depth=10, estimator=50, learn_rage=0.05,isfit=True):
        model = GradientBoostingClassifier(learning_rate= learn_rage,
                                    n_estimators=estimator,
                                    criterion='friedman_mse',
                                    max_depth=depth,
                                    random_state=None)

        if len(data_list) == 4:
            x_train,y_train,x_test,y_test = data_list[0],data_list[1],data_list[2],data_list[3]
        elif len(data_list) == 2:
             x_train,y_train = data_list[0],data_list[1]

        if isfit:

            model.fit(x_train,y_train)
            sc = model.score(x_train,y_train)
            

            print("训练集 learning_rate:{},树深度：{}, 树个数:{},score:{}".format(learn_rage, depth, estimator, sc))


            if len(data_list) == 4:
                sc = model.score(x_test,y_test)
                print("测试集 learning_rate:{},树深度：{}, 树个数:{},score:{}".format(learn_rage, depth, estimator, sc))
        
        
        return model 



    def rf_1(self,max_depth=5,tree_num=5,isfit=True,ispre=False,print_level=2,loops=1):
        """
        随机森林

        loops:循环次数


        用法示例
        -------------------------------



        import aisty.box.dataset as dt 

        data_list = dt.load_iris()

        import aisty.box.ml as ml 
        model = ml.TreeModel(data_list=data_list)

        for i in range(20):
            i = i + 10
            model.rf_1(max_depth=5,tree_num=i,print_level=3)

        model.score_list()

        model.rf_1(max_depth=5,tree_num=10,print_level=3,loops=100)

        """
        if not self.has_model("mode_rf_1"):
            self._model_define["mode_rf_1"] = RandomForestClassifier(criterion='gini',
                                    max_depth=max_depth,
                                    n_estimators=tree_num,
                                    oob_score=True)
        model = self._model_define["mode_rf_1"]
   
            
        score = {}

        if ispre:  # 预测
            sc = model.score(self.x_test, self.y_test)
            msg = "测试集 树深度：{}, 树个数:{},score:{}".format(max_depth, tree_num, sc)
            self.log(msg,print_level=print_level)
            score["test_score"]= sc 
            self._score_list.append(score)
            return model

        if not isfit:  # 不训练也不预测只是返回一个模型
            return model

        if isfit:
            for i in range(loops):
            
                model.fit(self.x_train,self.y_train)
                sc = model.oob_score_
                msg = "训练集 ,树深度：{}, 树个数:{},score:{}".format(max_depth, tree_num, sc)
                self.log(msg,print_level=print_level)

                score["depth"] = max_depth
                score["tree_num"]= tree_num
                score["train_score"]= sc 
                self._score_list.append(score)

        return model


class FeatureSelectionModel(ModelBase,d1.Stat):

    tree_model = TreeModel()

    def set_model(self,model):
        self.model = model

    def get_model_lg(self,max_iter=10000):
        model = LogisticRegression(max_iter=max_iter)
        return model

    def get_model_svm(self,data_list,kernel = 'linear'):
        model = SVM()
        return model.svm_1(data_list=data_list,kernel = kernel,isfit=False)



    def rfe_base(self, model, n_features_to_select=None,ispre=False,loops=1,model_name=""):
        """
        n_features_to_select:默认为所有特征 
        """
        # if len(data_list) == 4:
        #     x_train,y_train,x_test,y_test = data_list[0],data_list[1],data_list[2],data_list[3]
        # elif len(data_list) == 2:
        #      x_train,y_train = data_list[0],data_list[1]

        score_dict = {}

        if not self.has_model(model_name=model_name):
            self._model_define[model_name] = RFE(model, n_features_to_select=n_features_to_select)

        rfe = self._model_define[model_name]

        if ispre:
            score = rfe.score(self.x_test,self.y_test)
            self.log("测试集得分:{}".format(score))
            score_dict["test_score"] = score

            self._score_list.append(score_dict)
            return rfe 

        for i in range(loops):
            i = i + 1 
            rfe.fit(self.x_train,self.y_train)
            if i%10==1:
                self.log("support_:{}".format(rfe.support_))
                self.log("ranking_ 1最重要,2次之------------------")
                self.log("ranking_:{}".format(rfe.ranking_))

            score = rfe.score(self.x_train,self.y_train)
            self.log("loops:{},训练集得分:{}".format(i,score))

            score_dict = {"features_to_select":n_features_to_select,
                        "train_score":score}
        
            self._score_list.append(score_dict)

        return rfe 

    def rfe_lg(self, data_list, n_features_to_select=None):
        """
        RFE 进行特征选择,模型使用LogisticRegression
        """
        model = self.get_model_lg()
        self.rfe_base(data_list,model,n_features_to_select,model_name="rfe_lg")
        return model 

    def rfe_decision_tree_classifier_1(self, data_list, n_features_to_select=5, max_depth= 5,loops=1):
        model = self.tree_model.decision_tree_classifier_1(max_depth=max_depth)
        model = self.rfe_base(data_list,model,n_features_to_select,model_name="rfe_decision_tree_classifier_1",loops=loops)
        return model 

    def rfe_gradient_boosting(self, data_list, n_features_to_select=5, max_depth= 5,tree_num=50,learn_rage=0.05,isfit=True,loops=1):
        model = self.tree_model.gradient_boosting(data_list,depth=max_depth,estimator=tree_num,learn_rage=learn_rage,isfit=isfit)
        model = self.rfe_base(data_list,model,n_features_to_select,model_name="rfe_gradient_boosting",loops=loops)
        return model 

    def rfe_svm_1(self, data_list, n_features_to_select=5, isfit=True,loops=1):
        model = self.get_model_svm(data_list)
        model = self.rfe_base(data_list,model,n_features_to_select,model_name="rfe_svm_1",loops=loops)
        return model 

    def rfe_rf_1(self, n_features_to_select=5, max_depth= 5,tree_num=50, isfit=False,ifpre=False,loops=1):
        """
        用法示例
        -----------------------------
        model = ml.FeatureSelectionModel(data_list=data_list)
        model.rfe_rf_1(loops=3,n_features_to_select=3)
        """
        model = self.tree_model.rf_1(isfit=isfit,max_depth=max_depth,tree_num=tree_num)
        model = self.rfe_base(model,n_features_to_select,ispre=ifpre,loops=loops,model_name="rfe_rf_1")
        return model 



import os
class MlTrain():
    """机器学习训练器 
    """
    @staticmethod
    def train(X_train, y_train, X_test, y_test,
              model,save_path,epoch=10,loss_break=0.1):
        loss_start=0

        if not save_path.startswith("/"):
            save_path=os.path.join(TPF_MODELDIR,save_path) 

        # print("save_path:",save_path)

        #直接使用上次预测的结果，因为有时预测的结果也会震荡
        if os.path.exists(save_path):
            model,loss = pkl_load(file_path=save_path)
            loss_start=loss
            print("loss_start:",loss_start)
            
        for i in range(epoch):
            model.fit(X_train,y_train)
            y_pred_dtr = model.predict(X_test)
            loss=((y_pred_dtr - y_test)**2).mean()
            if i==0 and not os.path.exists(save_path):
                loss_start=loss
                print("loss_start:",loss_start)
                pkl_save((model,loss),file_path=save_path)
            elif loss<loss_start:
                loss_start=loss
                print(loss)
                pkl_save((model,loss),file_path=save_path)
            if loss<loss_break:
                print(loss)
                break
      

