import os,sys 
import pandas as pd 
import numpy as np

from tpf import pkl_load,pkl_save 
from tpf.data.deal import Data2Feature as dtf 
from tpf.conf import ParamConfig 
pc = ParamConfig()

base_dir = "/ai/data/model"

#----------------------------------------
# 读取训练所需要的数据
#----------------------------------------

# 特征列表读取
#----------------------------------------
selected_feature_save_file = os.path.join(base_dir, "selected_features_last.pkl")
selected_feature_list = pkl_load(selected_feature_save_file)
pc.lg(f"选择的特征数量: {len(selected_feature_list)}")
pc.lg(f"selected_feature_list: {selected_feature_list[:10]}")


# 归一化数据读取
#----------------------------------------
import os,json,hashlib
base_dir = "/ai/data/model"
mm_scaler_file = os.path.join(base_dir, 'min_max_scaler.pkl')   

# 生成参数哈希值作为文件名的一部分
norm_data_file = "/ai/data/model/normalized_data_e6099a31.csv"
mm_scaler_file = "/ai/data/model/min_max_scaler.pkl"

# 加载缓存的归一化数据
df1 = pd.read_csv(norm_data_file)
pc.lg(f"已从缓存加载归一化数据，形状: {df1.shape}")
pc.lg(f"df1[:3]: \n{df1[:3]}")


# 特征选择
#----------------------------------------
data_config_file = "/ai/wks/aitpf/src/tpf/case/jiaoyi/data_config_1.pkl"
data_config = pkl_load(data_config_file)
pc.lg(f"data_config: \n{data_config}")
"""
{
'identity': ['key', 'time8'], 
'num_type': ['amt_sum', 'amt_mean', 'amt_count', 'amt_q75', 'balance'], 'date_type': ['time8'], 'time_col': 'time8', 'cols': ['key', 'time8', 'amt_count', 'amt_sum', 'amt_mean', 'amt_std', 'amt_min', 'amt_max', 'amt_median', 'amt_q25', 'amt_q75', 'amt_skew', 'amt_kurtosis', 'amt_cv', 'amt_iqr', 'amt_range', 'amt_se', 'balance_count', 'balance_sum', 'balance_mean', 'balance_std', 'balance_min', 'balance_max', 'balance_median', 'balance_q25', 'balance_q75', 'balance_skew', 'balance_kurtosis', 'balance_cv', 'balance_iqr', 'balance_range', 'balance_se', 'payment_format_SWIFT_amt_count', 'payment_format_SWIFT_amt_sum', 'payment_format_SWIFT_amt_mean', 'payment_format_SWIFT_amt_std', 'payment_format_SWIFT_balance_count', 'payment_format_SWIFT_balance_sum', 'payment_format_SWIFT_balance_mean', 'payment_format_SWIFT_balance_std', 'currency_CNY_amt_count', 'currency_CNY_amt_sum', 'currency_CNY_amt_mean', 'currency_CNY_amt_std', 'currency_CNY_balance_count', 'currency_CNY_balance_sum', 'currency_CNY_balance_mean', 'currency_CNY_balance_std', 'payment_format_Transfer_amt_count', 'payment_format_Transfer_amt_sum', 'payment_format_Transfer_amt_mean', 'payment_format_Transfer_amt_std', 'payment_format_ACH_amt_count', 'payment_format_ACH_amt_sum', 'payment_format_ACH_amt_mean', 'payment_format_ACH_amt_std', 'payment_format_Transfer_balance_count', 'payment_format_Transfer_balance_sum', 'payment_format_Transfer_balance_mean', 'payment_format_Transfer_balance_std', 'payment_format_ACH_balance_count', 'payment_format_ACH_balance_sum', 'payment_format_ACH_balance_mean', 'payment_format_ACH_balance_std', 'payment_format_Wire_amt_count', 'payment_format_Wire_amt_sum', 'payment_format_Wire_amt_mean', 'payment_format_Wire_amt_std', 'payment_format_Wire_balance_count', 'payment_format_Wire_balance_sum', 'payment_format_Wire_balance_mean', 'payment_format_Wire_balance_std', 'currency_USD_amt_count', 'currency_USD_amt_sum', 'currency_USD_amt_mean', 'currency_USD_amt_std', 'currency_USD_balance_count', 'currency_USD_balance_sum', 'currency_USD_balance_mean', 'currency_USD_balance_std'], 'price_col': 'amt_count', 'base_amt_col': 'amt', 'available_amt_cols': ['amt_count', 'amt_sum', 'amt_mean', 'amt_std', 'amt_min', 'amt_max', 'amt_median', 'amt_q25', 'amt_q75', 'amt_skew', 'amt_kurtosis', 'amt_cv', 'amt_iqr', 'amt_range', 'amt_se', 'payment_format_SWIFT_amt_count', 'payment_format_SWIFT_amt_sum', 'payment_format_SWIFT_amt_mean', 'payment_format_SWIFT_amt_std', 'currency_CNY_amt_count', 'currency_CNY_amt_sum', 'currency_CNY_amt_mean', 'currency_CNY_amt_std', 'payment_format_Transfer_amt_count', 'payment_format_Transfer_amt_sum', 'payment_format_Transfer_amt_mean', 'payment_format_Transfer_amt_std', 'payment_format_ACH_amt_count', 'payment_format_ACH_amt_sum', 'payment_format_ACH_amt_mean', 'payment_format_ACH_amt_std', 'payment_format_Wire_amt_count', 'payment_format_Wire_amt_sum', 'payment_format_Wire_amt_mean', 'payment_format_Wire_amt_std', 'currency_USD_amt_count', 'currency_USD_amt_sum', 'currency_USD_amt_mean', 'currency_USD_amt_std'], 
'dt_time_col': 'time8', 
'available_time_cols': ['time8']}
"""
cols = data_config['identity'] + selected_feature_list
df_tra=df1[cols]
pc.lg(f"df_tra[:3]: \n{df_tra[:3]}")
"""
         key       time8  ...  payment_format_Transfer_amt_std  payment_format_Wire_amt_std
0   HXB_5264  2024-01-30  ...                              0.0                          0.0
1  ICBC_8999  2024-01-30  ...                              0.0                          0.0
2   HXB_7301  2024-02-11  ...                              0.0                          0.0
"""
pc.lg(f"df_tra.shape: {df_tra.shape}")
dtf.show_one_row(df_tra,n=10)
"""
[2025-10-16 09:43:46] df_tra.shape: (92441, 25)
[2025-10-16 09:43:46] DataFrame形状: (92441, 25)
[2025-10-16 09:43:46] 显示第 0 行（索引: 0）
[2025-10-16 09:43:46] 总字段数: 25
[2025-10-16 09:43:46] 显示前 10 个字段:
[2025-10-16 09:43:46] ------------------------------------------------------------
[2025-10-16 09:43:46] key                           : HXB_5264
[2025-10-16 09:43:46] time8                         : 2024-01-30
[2025-10-16 09:43:46] balance_count                 : 0.000000
[2025-10-16 09:43:46] balance_range                 : 0.000000
[2025-10-16 09:43:46] balance_iqr                   : 0.000000
[2025-10-16 09:43:46] amt_range                     : 0.000000
[2025-10-16 09:43:46] balance_std                   : 0.000000
[2025-10-16 09:43:46] amt_iqr                       : 0.000000
[2025-10-16 09:43:46] amt_std                       : 0.000000
[2025-10-16 09:43:46] balance_se                    : 0.000000
[2025-10-16 09:43:46] ------------------------------------------------------------
[2025-10-16 09:43:46] 还有 15 个字段未显示，使用 show_all=True 可显示全部
"""