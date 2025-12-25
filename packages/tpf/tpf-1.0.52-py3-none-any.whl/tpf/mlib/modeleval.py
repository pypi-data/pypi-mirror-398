
import sys
import numpy as np

# Check if torch is available
try:
    import torch
    from torch import nn
    from torch.nn import functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
from sklearn.metrics import accuracy_score,roc_auc_score, confusion_matrix, classification_report, roc_curve, auc,f1_score
from sklearn.metrics import roc_curve
import matplotlib.pyplot as plt

from tpf.mlib.models import MLib
from tpf.d1 import is_single_label

# Import SeqOne only if torch is available
if TORCH_AVAILABLE:
    from tpf.mlib.seq import SeqOne
else:
    SeqOne = None 

import pandas as pd 
def model_evaluate(y_probs, y_test,yuzhi=0.5,desired_tpr = None):
    """模型评估
    params
    -------------------------------------------------------
    - y_probs:模型概率输出,1维，每个元素为 标签1的概率，即正样本概率列表
    - y_test:真实标签，1维

    return
    -------------------------
    - acc,precision,recall,f1,auc ,依次为准确率，精确率，召回率，f1值，AUC
    - 其中精确率，召回率只针对 正样本-1

    examples
    --------------------------------------------------------
    acc,precision,recall,f1,auc  = model_evaluate(y_probs,y_test)
    """
    if y_probs.ndim != 1:
        raise Exception(f"y_probs必须为1维，实际为{y_probs.ndim}维")
    # 定义预测结果：概率>0.5则预测结果为 1 即可疑；概率<=0.5则预测结果为0 即不可疑
    y_pred = np.where(y_probs > yuzhi, 1, 0)
    is_single_value = is_single_label(y_test, y_pred)
    if is_single_value:
        roc_auc = 1
    else:
        # auc = roc_auc_score(y_test, y_pred)
        # 计算ROC曲线和AUC值
        fpr, tpr, thresholds = roc_curve(y_test, y_probs)
        roc_auc = auc(fpr, tpr)
        if desired_tpr is not None:
            closest_threshold = thresholds[np.argmin(np.abs(tpr - desired_tpr))]
            y_pred = (y_probs >= closest_threshold).astype(int)

    conf_matrix = confusion_matrix(y_test, y_pred)
    acc = (conf_matrix[0, 0] + conf_matrix[1, 1]) / (
                conf_matrix[0, 0] + conf_matrix[1, 0] + conf_matrix[0, 1] + conf_matrix[1, 1])

    # 对正样本的预测精度
    pre_1 = conf_matrix[0, 1] + conf_matrix[1, 1]
    true_1 = conf_matrix[1, 0] + conf_matrix[1, 1]
    if pre_1 == 0 and true_1 > 0:  # 真实1个数不为0，但预测为1的个数为0，则精确率为0
        precision = 0
    elif pre_1 == 0:  # 预测可疑样本数为0 这个很可能会出现  比如一批样本中真的就没有可疑的 模型本身预测正样本的能力也差
        precision = 1
    else:
        precision = float(conf_matrix[1, 1]) / pre_1

    # Recall 召回率
    real_1_num = conf_matrix[1, 0] + conf_matrix[1, 1]
    if real_1_num == 0:  # 即真实的可疑样本个数为0，即一批样本中的数据都是正常的
        recall = 1
    else:
        recall = float(conf_matrix[1, 1]) / real_1_num

    f1 = 2 / (1 / (precision + 1e-6) + 1 / (recall + 1e-6))

    # 保留2位有效数字
    acc = np.around(acc, decimals=4)
    precision = np.around(precision, decimals=4)
    recall = np.around(recall, decimals=4)
    f1 = np.around(f1, decimals=4)
    roc_auc = np.around(roc_auc, decimals=4)

    # 默认AI预测达不到1 即达不到100%准确,最多99%
    if acc >= 1:
        acc = 0.9999
    if precision >= 1:
        precision = 0.9999
    if recall >= 1:
        recall = 0.9999
    if f1 >= 1:
        f1 = 0.9999
    if roc_auc >= 1:
        roc_auc = 0.9999
    return acc, precision, recall, f1, roc_auc


class ModelEval():
    def __init__(self):
        """模型评估类
        - 支持传统机器学习和深度学习模型评估
        - 深度学习功能需要安装PyTorch
        """
        pass

    @staticmethod
    def _check_torch_availability():
        """检查torch是否可用"""
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is not installed. Please install torch to use deep learning evaluation functionality.")
        return True


    @staticmethod
    def acc_label(df,use_cols=['sim_label','real_label']):
        """类别准确率，一个类别label下只要有一个匹配，就算类别匹配成功
        - use_cols:有两列,第2列为真实标签/类别列
        """
        df25 = df.copy()
        sim_label = use_cols[0]
        real_label = use_cols[1]
        df25['match'] =  df25[sim_label]==df25[real_label]

        # 对df_topk按real_label分组合并，增加列is_ok
        # 如果一个real_label下有match为True的数据，该label的is_ok为1，否则为0
        df_label_summary = df25.groupby(real_label).agg(
            is_ok=('match', lambda x: 1 if x.any() else 0),
            match_count=('match', 'sum'),
            total_count=('match', 'count')
        ).reset_index()
        acc_bylabel = df_label_summary['is_ok'].sum() / len(df_label_summary)
        acc_bylabel = np.array(acc_bylabel).round(4)

        # 将is_ok信息合并回原始数据框
        df_topk = df25.merge(df_label_summary[[real_label, 'is_ok']], on=real_label, how='left')

        
        # 显示统计信息
        print(f"\n整体统计:")
        print(f"总记录数: {len(df_topk)}")
        print(f"匹配成功记录数: {df_topk['match'].sum()}")
        print(f"有成功匹配的标签数: {df_label_summary['is_ok'].sum()}")
        print(f"总标签数: {len(df_label_summary)}")
        print(f"标签级准确率: {df_label_summary['is_ok'].sum() / len(df_label_summary):.2%}")
        print(f"记录级准确率: {df_topk['match'].sum() / len(df_topk):.2%}")
        
        return df_topk,acc_bylabel 


    @staticmethod
    def cls_report(*,y_label, y_pred, label_names=None, output_path=None, is_extend=False):
        """
        生成分类报告CSV文件，列为label_name, precision, recall, f1-score, support

        Args:
            y_label: 索引编码的标签列表
            target_names (list): 目标类别名称列表,其顺序按索引编码的顺序，即0,1,2,...
            output_path (str): 输出CSV文件路径
        """
        
        if label_names:
            report = classification_report(y_label, y_pred,
                                  target_names=label_names,
                                  output_dict=True)
        else:
            report = classification_report(y_label, y_pred,
                                           zero_division=0,
                                           output_dict=True)
        if label_names is None:
            label_names = list(set(list(report.keys()))-set(['accuracy', 'macro avg', 'weighted avg']))
        
        acc = report['accuracy']
        
        # 提取各类别的指标
        class_data = []
        for class_name in label_names:
            if class_name in report:
                class_metrics = report[class_name]
                class_data.append({
                    'label_name': class_name,
                    'precision': round(class_metrics['precision'], 2),
                    'recall': round(class_metrics['recall'], 2),
                    'f1-score': round(class_metrics['f1-score'], 2),
                    'support': int(class_metrics['support'])
                })

        # 添加宏平均和加权平均
        if is_extend:
            class_data.extend([
                {
                    'label_name': 'macro avg',
                    'precision': round(report['macro avg']['precision'], 2),
                    'recall': round(report['macro avg']['recall'], 2),
                    'f1-score': round(report['macro avg']['f1-score'], 2),
                    'support': ''
                },
                {
                    'label_name': 'weighted avg',
                    'precision': round(report['weighted avg']['precision'], 2),
                    'recall': round(report['weighted avg']['recall'], 2),
                    'f1-score': round(report['weighted avg']['f1-score'], 2),
                    'support': int(report['weighted avg']['support'])
                }
            ])
            
        # 按precision从高到低排序
        class_data = sorted(class_data, key=lambda x: x['precision'], reverse=True)

        # 创建DataFrame并保存为CSV
        df = pd.DataFrame(class_data)
        if output_path:
            df.to_csv(output_path, index=False, encoding='utf-8')
            print(f"\n分类报告CSV已保存到: {output_path}")




        return df,acc


    def cls_mat(*,y_label, y_pred, label_names=None, output_path=None):
        """
        生成混淆矩阵CSV文件，第一行列为" ",label1,label2,...第一列为" ",label1,label2,...

        Args:
    
            target_names (list): 目标类别名称列表
            output_path (str): 输出CSV文件路径
        """
        if label_names is None:
            label_names = list(set(list(y_label)) | set(list(y_pred)))
            # label_names = list(set(list(y_label)))
            
        cm = confusion_matrix(y_label, y_pred)
        
        # 创建DataFrame，第一行第一列为空格
        cm_df = pd.DataFrame(cm, columns=label_names, index=label_names)

        # 重置索引，将标签作为第一列
        cm_df.reset_index(inplace=True)
        cm_df.rename(columns={'index': ' '}, inplace=True)

        # 在列名前添加空格作为第一列的标题
        cm_df.columns = [' '] + list(label_names)

        # 保存为CSV文件
        if output_path:
            cm_df.to_csv(output_path, index=False, encoding='utf-8')
            print(f"\n混淆矩阵CSV已保存到: {output_path}")

        return cm_df



    @staticmethod
    def evaluate(*, y_test,y_probs,yuzhi=0.5,desired_tpr = None):
        """模型评估
        params
        -------------------------------------------------------
        - y_probs:模型概率输出,1维，每个元素为 标签1的概率，即正样本概率列表
        - y_test:真实标签，1维

        return
        -------------------------
        - acc,precision,recall,f1,auc ,依次为准确率，精确率，召回率，f1值，AUC
        - 其中精确率，召回率只针对 正样本-1

        examples
        --------------------------------------------------------
        acc,precision,recall,f1,auc  = me.evaluate(y_probs,y_test)

        """
        return model_evaluate(y_probs, y_test, yuzhi=yuzhi, desired_tpr=desired_tpr)

    @staticmethod
    def eval_prob_interval( *, y_test, y_probs, interval=0.01):
        """
        1. y_probs中值大于yuzhi的预测结果为1 否则为0；但实际上y_probs的值是一个概率，
        2. 现在对y_probs按interval划分区间，比如y_probs的最小值为min,最大值为max,在[min,min+0.1]的范围内，y_test中1的个数是多少，y_probs在[min+0.1,min+0.2]的概率区中，y_test中1的个数是多少，以此类推，直到y_probs的最小值和最大值之间的区间，返回一个列表，列表中每个元素为[min,min+interval]的概率区间中，y_test中1的个数是多少
        3. 返回一个列表，列表中每个元素为[min,min+interval]的概率区间中，y_test中1的个数是多少
        4. 首先划定y_probs的[min,min+interval]区间，然后求y_probs在这个区间中的索引index,然后统计y_test[index]中1的个数，通过index一一对应
        4. 最后的结果是一个四元组列表，[(min, max, count_ones, count_total)]，按count_ones降序排列

        """
        # 输入验证
        if y_probs.ndim != 1:
            raise Exception(f"y_probs必须为1维，实际为{y_probs.ndim}维")
        if y_test.ndim != 1:
            raise Exception(f"y_test必须为1维，实际为{y_test.ndim}维")
        if len(y_probs) != len(y_test):
            raise Exception(f"y_probs和y_test长度必须相同，实际分别为{len(y_probs)}和{len(y_test)}")
        if interval <= 0:
            raise Exception(f"interval必须大于0，实际为{interval}")

        # 获取y_probs的最小值和最大值
        min_val = np.min(y_probs)
        max_val = np.max(y_probs)

        # 如果最大值等于最小值，返回单个区间
        if max_val == min_val:
            count_ones = np.sum(y_test == 1)
            count_total = len(y_test)
            return [(float(min_val), float(max_val), int(count_ones), int(count_total))]

        # 计算区间数量，确保覆盖整个范围
        num_intervals = int(np.ceil((max_val - min_val) / interval))

        result = []

        # 遍历每个区间
        for i in range(num_intervals):
            # 计算当前区间的最小值和最大值
            interval_min = min_val + i * interval
            interval_max = min_val + (i + 1) * interval

            # 对于最后一个区间，确保包含最大值
            if i == num_intervals - 1:
                interval_max = max_val + 1e-10  # 添加一个小的epsilon以包含最大值

            # 找到在当前区间内的y_probs的索引
            interval_indices = np.where((y_probs >= interval_min) & (y_probs < interval_max))[0]

            # 统计对应索引位置上y_test中为1的个数
            count_ones = np.sum(y_test[interval_indices] == 1)

            # 统计该区间内y_probs的总个数
            count_total = len(interval_indices)

            # 添加到结果列表中
            result.append((float(interval_min), float(interval_max), int(count_ones), int(count_total)))

        # 按count_ones降序排列
        result.sort(key=lambda x: x[2], reverse=True)

        return result 

    @staticmethod
    def eval_num_interval(*, y_test,y_probs, interval=10):
        """
        按y_probs值从高到低取固定个数进行统计分析

        与eval_prob_interval方法不同，此方法按y_probs中值从高到低取个数分组，
        比如y_probs中值最大为0.7，从0.7开始往下数interval个样本，然后统计对应
        y_test中标签为1的个数

        参数:
        - y_probs: 模型概率输出，1维数组，每个元素为正样本概率
        - y_test: 真实标签，1维数组
        - yuzhi: 阈值（此方法中不使用，保留参数一致性）
        - interval: 每组样本数量，默认为10

        返回:
        - 四元组列表 [(min_prob, max_prob, count_ones, cumulative_count), ...]
          - min_prob: 当前组的最小概率值
          - max_prob: 当前组的最大概率值
          - count_ones: 当前组中y_test标签为1的个数
          - cumulative_count: 当前组的累积样本数（第1组为interval，第2组为2*interval，以此类推）
        """
        # 输入验证
        if y_probs.ndim != 1:
            raise Exception(f"y_probs必须为1维，实际为{y_probs.ndim}维")
        if y_test.ndim != 1:
            raise Exception(f"y_test必须为1维，实际为{y_test.ndim}维")
        if len(y_probs) != len(y_test):
            raise Exception(f"y_probs和y_test长度必须相同，实际分别为{len(y_probs)}和{len(y_test)}")
        if interval <= 0:
            raise Exception(f"interval必须大于0，实际为{interval}")

        # 获取原始索引，并按y_probs值降序排列
        sorted_indices = np.argsort(y_probs)[::-1]  # 降序排列的索引
        sorted_y_probs = y_probs[sorted_indices]    # 排序后的概率值
        sorted_y_test = y_test[sorted_indices]     # 对应的真实标签

        total_samples = len(y_probs)
        result = []

        # 按interval大小分组处理
        for start_idx in range(0, total_samples, interval):
            end_idx = min(start_idx + interval, total_samples)

            # 当前组的概率范围
            current_probs = sorted_y_probs[start_idx:end_idx]
            current_labels = sorted_y_test[start_idx:end_idx]

            min_prob = float(np.min(current_probs))
            max_prob = float(np.max(current_probs))

            # 统计当前组中标签为1的个数
            count_ones = int(np.sum(current_labels == 1))

            # 累积样本数（当前组的结束位置）
            cumulative_count = end_idx

            result.append((min_prob, max_prob, count_ones, cumulative_count))

        return result 

    @staticmethod
    def confusion_matrix(*, y_test,y_probs):
        """

        examples
        ------------------------------------
        ## 混淆矩阵
        confusion_matrix = me.confusion_matrix(y_probs,y_test)
        print("\nconfusion_matrix:\n",confusion_matrix)


                    pre
                    0  1
        real    0
                1
        """
        if y_probs.ndim != 1:
            raise Exception(f"y_probs必须为1维，实际为{y_probs.ndim}维")
        # 定义预测结果：概率>0.5则预测结果为 1 即可疑；概率<=0.5则预测结果为0 即不可疑
        y_pred = np.where(y_probs > 0.5, 1, 0)
        is_single_value = is_single_label(y_test, y_pred)
        if is_single_value:
            roc_auc = 1
        else:
            # auc = roc_auc_score(y_test, y_pred)
            # 计算ROC曲线和AUC值
            fpr, tpr, thresholds = roc_curve(y_test, y_probs)
            roc_auc = auc(fpr, tpr)
        if isinstance(y_test, pd.DataFrame):
            print("label value count:\n", y_test.value_counts())
        else: 
            y_label = pd.DataFrame(y_test, dtype=np.int32)
            print("label value count:\n", y_label.value_counts())
            
        conf_matrix = confusion_matrix(y_test, y_pred)
        return conf_matrix

    @staticmethod
    def classification_report(*, y_test,y_probs):
        """分类报告

        examples
        ----------------------------------------------------
        ## 分类报告
        print("\nclassification_report:\n",me.classification_report(y_probs,y_test))

        """
        y_pred = np.where(y_probs > 0.5, 1, 0)
        report = classification_report(y_test, y_pred)
        return report

    @staticmethod
    def interval_distribution(*, y_test, y_probs,interval=100):
        """计算y_test在y_probs区间内的分布，按区间最小值升序排列

        params
        -------------------------------------------------------
        - y_probs: 模型概率输出,1维数组，每个元素为正样本概率
        - y_test: 真实标签,1维数组，二分类标签(0或1)
        - interval: 区间数量，默认为100，即将概率范围划分为100个等宽区间

        return
        -------------------------
        - count_max_list: 三元组列表，每个元素格式为 (zero_count, positive_count, interval_min)
                         - zero_count: 该区间内标签为0的样本数量
                         - positive_count: 该区间内标签为1的样本数量
                         - interval_min: 该区间的最小概率值
                         - 列表按interval_min升序排列，仅包含有正样本的区间
        - interval_width: 每个区间的宽度值，计算方式为 (max_val - min_val) / interval

        实际逻辑说明：
        1. 将y_probs的取值范围[min_val, max_val]等分为interval个区间
        2. 统计每个区间内y_test中标签为1和标签为0的样本数量
        3. 只返回有正样本(count > 0)的区间信息
        4. 按区间最小值(interval_min)升序排列结果

        examples
        --------------------------------------------------------
        count_max_list, interval_width = ModelEval.interval_distribution(y_probs, y_test)
        # count_max_list: [(zero_count1, positive_count1, interval_min1),
        #                  (zero_count2, positive_count2, interval_min2), ...]
        # interval_width: 浮点数，表示每个区间的宽度

        for zero_count, positive_count, interval_min in count_max_list:
            print(f"区间[{interval_min:.3f}, {interval_min+interval_width:.3f}): "
                  f"正样本{positive_count}个, 负样本{zero_count}个")
        """
        if y_probs.ndim != 1:
            raise Exception(f"y_probs必须为1维，实际为{y_probs.ndim}维")

        min_val = np.min(y_probs)
        max_val = np.max(y_probs)
        interval_width = (max_val - min_val) / interval

        result = []
        for i in range(interval):
            interval_min = min_val + i * interval_width
            interval_max = min_val + (i + 1) * interval_width

            # 找到该区间对应的y_probs的索引
            interval_indices = np.where((y_probs >= interval_min) & (y_probs < interval_max))[0]

            # 统计相同索引位置上y_test中为1的个数
            count = np.sum(y_test[interval_indices] == 1)

            result.append((round(float(interval_min),4),  round(float(interval_max),4), int(count)))

        count_max_list = sorted([(np.sum(y_test[interval_indices] == 0), count, interval_min)
                              for interval_min, interval_max, count in result
                              if count > 0
                              for interval_indices in [np.where((y_probs >= interval_min) & (y_probs < interval_max))[0]]],
                              key=lambda x: x[2])

        count_max_list = [(int(zero_count), int(count), round(float(interval_min), 4))
                         for zero_count, count, interval_min in count_max_list]

        return count_max_list, interval_width

    @staticmethod
    def ks(*,y_label,y_pred_proba, is_show=False):
        # 创建一个包含真实标签和预测概率的DataFrame
        
        df_ks = pd.DataFrame()
        df_ks['true_label'] = y_label
        df_ks['pred_proba'] = y_pred_proba
        
        # 按预测概率降序排列
        df_ks = df_ks.sort_values(by='pred_proba', ascending=False).reset_index(drop=True)

        # 计算总的正负样本数
        total_malignant = df_ks['true_label'].sum() # 正样本总数（恶性）
        total_benign = len(df_ks) - total_malignant # 负样本总数（良性）
        
        # 计算累积的正负样本数量
        df_ks['cum_malignant'] = df_ks['true_label'].cumsum()
        df_ks['cum_benign'] = (1 - df_ks['true_label']).cumsum()
        
        # 计算累积的正负样本比例
        df_ks['cum_malignant_rate'] = df_ks['cum_malignant'] / total_malignant
        df_ks['cum_benign_rate'] = df_ks['cum_benign'] / total_benign

        # 计算每一步的KS值
        df_ks['ks'] = (df_ks['cum_malignant_rate'] - df_ks['cum_benign_rate']).abs()
        
        # 找到KS值及其对应的位置
        max_ks = df_ks['ks'].max()
        max_ks_index = df_ks['ks'].idxmax()
        max_ks_proba = df_ks.loc[max_ks_index, 'pred_proba']

        mks       = max_ks.round(4)
        mks_proba = max_ks_proba.round(4)
        print(f"KS值为: {mks}")
        print(f"在概率为 {mks_proba} 的划分点处取得。")
        

        if is_show:
            # 绘制KS曲线
                    
            plt.figure(figsize=(10, 6))
            plt.plot(df_ks['pred_proba'], df_ks['cum_malignant_rate'], label='Cumulative % Malignant', color='red')
            plt.plot(df_ks['pred_proba'], df_ks['cum_benign_rate'], label='Cumulative % Benign', color='blue')
            plt.axvline(x=max_ks_proba, color='gray', linestyle='--', label=f'KS Point (prob={max_ks_proba:.2f})')
            plt.axhline(y=df_ks.loc[max_ks_index, 'cum_malignant_rate'], color='gray', linestyle='--')
            plt.axhline(y=df_ks.loc[max_ks_index, 'cum_benign_rate'], color='gray', linestyle='--')
            
            # 标记KS值
            plt.plot([max_ks_proba, max_ks_proba],
                    [df_ks.loc[max_ks_index, 'cum_benign_rate'], df_ks.loc[max_ks_index, 'cum_malignant_rate']],
                    'o-', color='black', label=f'KS = {max_ks:.3f}')
            
            plt.xlabel('Predicted Probability (Malignant)')
            plt.ylabel('Cumulative Percentage')
            plt.title('KS Curve')
            plt.legend()
            plt.grid(True)
            plt.show()
        else:
            return mks,mks_proba
                    
    @staticmethod
    def ks_roc(*, y_label,y_prob):
        # 使用sklearn的roc_curve计算
        fpr, tpr, thresholds = roc_curve(y_label, y_prob)
        ks_from_sklearn = (tpr - fpr).max()
        threshold_at_ks = thresholds[(tpr - fpr).argmax()]
        
        print(f"通过SKlearn ROC曲线计算的KS值为: {ks_from_sklearn:.4f}")
        print(f"对应的阈值为: {threshold_at_ks:.4f}")
        mks       = ks_from_sklearn.round(4)
        mks_proba = threshold_at_ks.round(4)
        return float(mks),float(mks_proba) 
        
    @staticmethod
    def acc_lr(*,y_label,y_pred):
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import recall_score
        recall = recall_score(y_label, y_pred)

        # 计算预测为1的数据中真实为1的比例（精确率）
        from sklearn.metrics import precision_score
        precision = precision_score(y_label, y_pred)
        fenmu = (y_pred==1).sum()
        fenzi = y_pred[(y_pred==1) & (y_label==1)].sum()

        # print(f"模型训练完成，准确率: {round(score,4)}")
        print(f"模型召回率: {round(recall,4)}")
        
        print(f"预测为1的数据中真实为1的比例（精确率）: {round(precision,4)},{fenzi}/{fenmu}={round(fenzi/fenmu,4)}")
        return round(precision,4)