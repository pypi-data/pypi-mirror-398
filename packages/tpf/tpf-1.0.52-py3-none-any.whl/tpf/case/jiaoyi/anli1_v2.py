"""

"""
import os,sys,json,hashlib
import pandas as pd
import numpy as np
from tpf.conf.common import ParamConfig
pc = ParamConfig()
filenum = 0 

base_dir = "/ai/data/model"

from tpf.data.make import JiaoYi as jy
import os
from tpf.data.deal import Data2Feature as dtf

# 配置原始交易数据缓存文件路径
raw_data_file = os.path.join(base_dir, 'raw_transaction_data.csv')

# 检查原始数据缓存文件是否存在
if os.path.exists(raw_data_file):
    pc.lg(f"发现原始数据缓存文件: {raw_data_file}")
    pc.lg("直接加载已生成的原始交易数据...")

    # 加载缓存的原始数据
    import pandas as pd
    df_tra = pd.read_csv(raw_data_file)
    pc.lg(f"已从缓存加载原始数据，形状: {df_tra.shape}")

else:
    pc.lg(f"原始数据缓存文件不存在: {raw_data_file}")
    pc.lg("开始生成原始交易数据...")

    df_tra = jy.make_trans13(
        num_accounts=3000,
        transactions_per_account=100,
        start_date='2024-01-01',
        end_date='2025-02-01',acc1='acc1',time_col='time14',
        num_cols=['amt','balance'], cat_cols=['currency','payment_format'])

    # 保存原始数据到缓存文件
    pc.lg(f"保存原始数据到缓存文件: {raw_data_file}")
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(raw_data_file), exist_ok=True)

        # 保存数据
        df_tra.to_csv(raw_data_file, index=False)
        pc.lg(f"原始数据缓存文件保存成功，文件大小: {os.path.getsize(raw_data_file)} 字节")

    except Exception as e:
        pc.lg(f"保存原始数据缓存文件时出错: {e}")
        pc.lg("程序继续执行，但原始数据未被缓存")
pc.lg(f"df_tra[:3]:\n{df_tra[:3]}")
""" 
        acc1      acc2       time8              time14   risk  label      amt  balance currency payment_format
0  CMBC_9147  BOC_1659  2024-12-24 2024-12-24 07:19:00  0.799      1  2681.46    89604      CNY       Transfer
1  CMBC_9147  CEB_2534  2025-01-12 2025-01-12 03:49:00  0.409      0  5476.58   136525      USD          SWIFT
2  CMBC_9147  PAB_6278  2024-06-30 2024-06-30 16:29:00  0.613      1  5362.70    71713      USD           Wire
"""

pc.lg(f"df_tra.shape:{df_tra.shape}")   # df_tra.shape:(298468, 9)

#----------------------------------------
# 采样
#----------------------------------------
pc.lg("开始调用data_sample_small方法进行数据采样............")
from tpf.data.sample import DataSampler
import os

# 配置缓存文件路径
sampled_data_file = os.path.join(base_dir, 'sampled_transaction_data.csv')

# 检查缓存文件是否存在
if os.path.exists(sampled_data_file):
    pc.lg(f"发现缓存文件: {sampled_data_file}")
    pc.lg("直接加载已采样的数据，跳过采样过程...")

    # 加载缓存的数据
    import pandas as pd
    df = pd.read_csv(sampled_data_file)
    stat = {
        'total_unique_accounts': len(df['acc1'].unique()) if 'acc1' in df.columns else 0,
        'sampled_accounts': len(df['acc1'].unique()) if 'acc1' in df.columns else 0,
        'total_sampled_transactions': len(df),
        'avg_transactions_per_account': len(df) / len(df['acc1'].unique()) if 'acc1' in df.columns and len(df['acc1'].unique()) > 0 else 0,
        'data_source': 'cached_file'
    }
    pc.lg(f"已从缓存加载数据，形状: {df.shape}")

else:
    pc.lg(f"缓存文件不存在: {sampled_data_file}")
    pc.lg("开始进行数据采样...")

    dsm = DataSampler(start_date='2024-01-01',
        end_date='2025-02-01',
        excluded_accounts=['BOC_5000', 'CEB_4925'],
        sample_size=1000,
        records_per_account=50,
        acc1='acc1',
        acc2='acc2',
        time_col='time14',
        amt_col='amt')

    df,stat = dsm.sample(df_tra)

    # 保存采样的数据到缓存文件
    pc.lg(f"保存采样数据到缓存文件: {sampled_data_file}")
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(sampled_data_file), exist_ok=True)

        # 保存数据
        df.to_csv(sampled_data_file, index=False)
        pc.lg(f"缓存文件保存成功，文件大小: {os.path.getsize(sampled_data_file)} 字节")

        # 同时保存统计信息
        import json
        stat_file = sampled_data_file.replace('.csv', '_stats.json')
        with open(stat_file, 'w', encoding='utf-8') as f:
            json.dump(stat, f, ensure_ascii=False, indent=2)
        pc.lg(f"统计信息已保存到: {stat_file}")

    except Exception as e:
        pc.lg(f"保存缓存文件时出错: {e}")
        pc.lg("程序继续执行，但数据未被缓存")

    stat['data_source'] = 'fresh_sample'
pc.lg(f"df[:3]:\n{df[:3]}")
"""
        acc1       acc2       time8              time14   risk  label       amt  balance currency payment_format
0  CMBC_9098   BOC_3719  2025-01-31 2025-01-31 04:47:00  0.941      1   4247.97   135877      CNY          SWIFT
1  CMBC_9098  CMBC_9511  2025-01-26 2025-01-26 11:17:00  0.232      0  10121.17   132797      CNY           Wire
2  CMBC_9098   ABC_4435  2025-01-21 2025-01-21 18:42:00  0.707      1   8059.96   112014      CNY          SWIFT
"""
pc.lg(f"df.shape:{df.shape}")  # df.shape:(50000, 10)


#----------------------------------------
# 类别编码
#----------------------------------------
dtf.show_col_type(df, non_numeric_only=True)
"""
非数值列类型：
acc1              object
acc2              object
time8             object
time14            object
currency          object
payment_format    object
dtype: object
"""

dtf.show_date_type(df[:3])
"""
日期列汇总:
  总列数: 2
  总数据量: 3 行
  datetime类型列: 0
  字符串日期列: 2
{'time8': 'object', 'time14': 'object'}
"""
pc.lg("开始调用tonum_col2index方法进行类别编码............")

# 配置列编码缓存文件路径
# 生成基于参数的唯一文件名，确保不同参数组合不会冲突
col2index_params = {
    'identity': ['acc1','acc2','time8','time14'],
    'is_pre': False,
    'start_index': 1000,
    'input_shape': df.shape,
    'input_columns': list(df.columns)
}

# 生成参数哈希值作为文件名的一部分
params_str = json.dumps(col2index_params, sort_keys=True)
params_hash = hashlib.md5(params_str.encode('utf-8')).hexdigest()[:8]
col2index_data_file = os.path.join(base_dir, f'col2index_data_{params_hash}.csv')
col2index_save_file = os.path.join(base_dir, 'col2index_file.dict')

# 检查列编码数据缓存文件是否存在，以及字典文件是否存在
if os.path.exists(col2index_data_file) and os.path.exists(col2index_save_file):
    pc.lg(f"发现列编码缓存文件: {col2index_data_file}")
    pc.lg(f"发现编码字典文件: {col2index_save_file}")
    pc.lg("直接加载已编码的数据，跳过编码过程...")

    # 加载缓存的编码数据
    df = pd.read_csv(col2index_data_file)
    pc.lg(f"已从缓存加载编码数据，形状: {df.shape}")

else:
    pc.lg(f"列编码缓存文件不存在: {col2index_data_file}")
    pc.lg("开始进行列编码...")

    df = dtf.tonum_col2index(df,
        identity=['acc1','acc2','time8','time14'],
        dict_file=col2index_save_file,
        is_pre=False,
        start_index=1)

    # 保存编码数据到缓存文件
    pc.lg(f"保存编码数据到缓存文件: {col2index_data_file}")
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(col2index_data_file), exist_ok=True)

        # 保存数据
        df.to_csv(col2index_data_file, index=False)
        pc.lg(f"编码数据缓存文件保存成功，文件大小: {os.path.getsize(col2index_data_file)} 字节")

        # 同时保存编码参数信息
        col2index_info_file = col2index_data_file.replace('.csv', '_params.json')
        col2index_info = {
            'parameters': col2index_params,
            'input_shape': col2index_params['input_shape'],
            'output_shape': df.shape,
            'timestamp': pd.Timestamp.now().isoformat()
        }
        with open(col2index_info_file, 'w', encoding='utf-8') as f:
            json.dump(col2index_info, f, ensure_ascii=False, indent=2)
        pc.lg(f"编码参数信息已保存到: {col2index_info_file}")

    except Exception as e:
        pc.lg(f"保存编码数据缓存文件时出错: {e}")
        pc.lg("程序继续执行，但编码数据未被缓存")

pc.lg(f"df[:3]:\n{df[:3]}")
dtf.show_one_row(df, show_all=True)



#----------------------------------------
# 按天聚合 
#----------------------------------------
pc.lg("开始调用data_agg_byday方法进行按天聚合....这一步自动删除了time14列........")

import hashlib
import json

# 配置聚合数据缓存文件路径
# 生成基于参数的唯一文件名，确保不同参数组合不会冲突
agg_params = {
    'col_time': 'time8',
    'interval': 1,
    'win_len': 1,
    'identifys': [['acc1','time8'],['acc2','time8']],
    'num_type': ['amt','balance'],
    'classify_type': ['payment_format', 'currency'],
    'merge_del_cols': ['acc1','acc2'],
    'new_col_name': 'key'
}

# 生成参数哈希值作为文件名的一部分
params_str = json.dumps(agg_params, sort_keys=True)
params_hash = hashlib.md5(params_str.encode('utf-8')).hexdigest()[:8]
agg_data_file = os.path.join(base_dir, f'aggregated_data_{params_hash}.csv')

# 检查聚合数据缓存文件是否存在
if os.path.exists(agg_data_file):
    pc.lg(f"发现聚合数据缓存文件: {agg_data_file}")
    pc.lg("直接加载已聚合的数据，跳过聚合过程...")

    # 加载缓存的聚合数据
    df_final_result = pd.read_csv(agg_data_file)
    pc.lg(f"已从缓存加载聚合数据，形状: {df_final_result.shape}")

else:
    pc.lg(f"聚合数据缓存文件不存在: {agg_data_file}")
    pc.lg("开始进行数据聚合...")

    print("开始调用data_agg_byday方法进行按天聚合...")
    df_final_result = dtf.data_agg_byday(
        df=df,
        col_time='time8',
        interval=1,
        win_len=1,
        identifys=[['acc1','time8'],['acc2','time8']],
        num_type=['amt','balance'],
        classify_type=['payment_format', 'currency'],
        merge_del_cols=['acc1','acc2'],
        new_col_name='key'
    )

    # 保存聚合数据到缓存文件
    pc.lg(f"保存聚合数据到缓存文件: {agg_data_file}")
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(agg_data_file), exist_ok=True)

        # 保存数据
        df_final_result.to_csv(agg_data_file, index=False)
        pc.lg(f"聚合数据缓存文件保存成功，文件大小: {os.path.getsize(agg_data_file)} 字节")

        # 同时保存聚合参数信息
        agg_info_file = agg_data_file.replace('.csv', '_params.json')
        agg_info = {
            'parameters': agg_params,
            'input_shape': df.shape,
            'output_shape': df_final_result.shape,
            'timestamp': pd.Timestamp.now().isoformat()
        }
        with open(agg_info_file, 'w', encoding='utf-8') as f:
            json.dump(agg_info, f, ensure_ascii=False, indent=2)
        pc.lg(f"聚合参数信息已保存到: {agg_info_file}")

    except Exception as e:
        pc.lg(f"保存聚合数据缓存文件时出错: {e}")
        pc.lg("程序继续执行，但聚合数据未被缓存")

pc.lg(f"按天聚合完成，最终结果形状: {df_final_result.shape}")
pc.lg(f"df_final_result[:3]:\n{df_final_result[:3]}")

dtf.show_one_row(df_final_result,n=10)

"""
[2025-10-15 16:06:56] DataFrame形状: (92441, 81)
[2025-10-15 16:06:56] 显示第 0 行（索引: 0）
[2025-10-15 16:06:56] 总字段数: 81
[2025-10-15 16:06:56] 显示前 10 个字段:
[2025-10-15 16:06:56] ------------------------------------------------------------
[2025-10-15 16:06:56] key                           : HXB_5264
[2025-10-15 16:06:56] group_key                     : acc1_time8
[2025-10-15 16:06:56] time8                         : 2024-01-30 00:00:00
[2025-10-15 16:06:56] amt_count                     : 1.000
[2025-10-15 16:06:56] amt_sum                       : 5648.490
[2025-10-15 16:06:56] amt_mean                      : 5648.490
[2025-10-15 16:06:56] amt_std                       : 0.000000
[2025-10-15 16:06:56] amt_min                       : 5648.490
[2025-10-15 16:06:56] amt_max                       : 5648.490
[2025-10-15 16:06:56] amt_median                    : 5648.490
[2025-10-15 16:06:56] ------------------------------------------------------------
[2025-10-15 16:06:56] 还有 71 个字段未显示，使用 show_all=True 可显示全部
"""
df = df_final_result.drop(columns=['group_key'])
pc.lg(f"df.shape:{df.shape}")  # df.shape:(92441, 80)
col_all = df.columns.tolist()
pc.lg(f"col_all:{col_all}")

dtf.show_col_type(df,non_numeric_only=True )
"""
非数值列类型：
key      object
time8    object
dtype: object
"""

#----------------------------------------
# 归一化处理
#----------------------------------------

# from tpf.data.deal import Data2Feature as dtf
# df_processed = dtf.data_type_change(df, num_type=num_type, date_type=date_type)
import os
base_dir = "/ai/data/model"
mm_scaler_file = os.path.join(base_dir, 'min_max_scaler.pkl')   

# 配置归一化数据缓存文件路径
# 生成基于参数的唯一文件名，确保不同参数组合不会冲突
norm_params = {
    'model_path': mm_scaler_file,
    'is_train': True,
    'input_shape': df.shape,
    'input_columns': list(df.columns)
}

# 生成参数哈希值作为文件名的一部分
params_str = json.dumps(norm_params, sort_keys=True)
params_hash = hashlib.md5(params_str.encode('utf-8')).hexdigest()[:8]
norm_data_file = os.path.join(base_dir, f'normalized_data_{params_hash}.csv')

# 检查归一化数据缓存文件是否存在，以及scaler模型文件是否存在
if os.path.exists(norm_data_file) and os.path.exists(mm_scaler_file):
    pc.lg(f"发现归一化数据缓存文件: {norm_data_file}")
    pc.lg(f"发现scaler模型文件: {mm_scaler_file}")
    pc.lg("直接加载已归一化的数据，跳过归一化过程...")

    # 加载缓存的归一化数据
    df1 = pd.read_csv(norm_data_file)
    pc.lg(f"已从缓存加载归一化数据，形状: {df1.shape}")

else:
    pc.lg(f"归一化数据缓存文件不存在: {norm_data_file}")
    pc.lg("开始进行数据归一化...")

    #归一化时的列应该使用全部
    df1 = dtf.norm_min_max_scaler(df.copy(),
        model_path=mm_scaler_file,
        is_train=True,)

    # 保存归一化数据到缓存文件
    pc.lg(f"保存归一化数据到缓存文件: {norm_data_file}")
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(norm_data_file), exist_ok=True)

        # 保存数据
        df1.to_csv(norm_data_file, index=False)
        pc.lg(f"归一化数据缓存文件保存成功，文件大小: {os.path.getsize(norm_data_file)} 字节")

        # 同时保存归一化参数信息
        norm_info_file = norm_data_file.replace('.csv', '_params.json')
        norm_info = {
            'parameters': norm_params,
            'input_shape': norm_params['input_shape'],
            'output_shape': df1.shape,
            'timestamp': pd.Timestamp.now().isoformat()
        }
        with open(norm_info_file, 'w', encoding='utf-8') as f:
            json.dump(norm_info, f, ensure_ascii=False, indent=2)
        pc.lg(f"归一化参数信息已保存到: {norm_info_file}")

    except Exception as e:
        pc.lg(f"保存归一化数据缓存文件时出错: {e}")
        pc.lg("程序继续执行，但归一化数据未被缓存")
pc.lg(f"df1.shape:{df1.shape}")  #df1.shape:(92441, 80)
pc.lg(f"df1[:3]:\n{df1[:3]}")
"""
         key       time8  amt_count   amt_sum  ...  currency_USD_balance_count  currency_USD_balance_sum  currency_USD_balance_mean  currency_USD_balance_std
0   HXB_5264  2024-01-30        0.0  0.142288  ...                         0.0                       0.0                        0.0                       0.0
1  ICBC_8999  2024-01-30        0.0  0.142288  ...                         0.0                       0.0                        0.0                       0.0
2   HXB_7301  2024-02-11        0.0  0.194262  ...                         0.0                       0.0                        0.0                       0.0
"""

dtf.show_one_row(df1,n=10)


#----------------------------------------
# 特征生成
#----------------------------------------
from typing import Dict, List, Optional, Union, Tuple
from tpf.data.feature.liushui import (
    FeatureEngineeringPipeline,
    FeatureConfig,
    run_feature_pipeline_with_timing,
    save_selected_features,
    run_optimized_feature_pipeline,
    pc,
    prepare_data_for_feature_calculation,
    load_and_prepare_data
)

amt_type=['amt','balance']
identity=['key','time8']
num_type = [f"{amt_type[0]}_sum",f"{amt_type[0]}_mean",f"{amt_type[0]}_count",f"{amt_type[0]}_q75",amt_type[1]]
date_type = ['time8']
time_col = 'time8'
cols = df.columns.tolist()

# 检查可用的列，用于调试
pc.lg(f"当前DataFrame列名: {list(df1.columns)}")
pc.lg(f"num_type列: {num_type}")
pc.lg(f"amt相关列: {[col for col in df1.columns if 'amt' in col.lower()]}")

# 确定正确的price_col
available_amt_cols = [col for col in df1.columns if 'amt' in col.lower()]
if available_amt_cols:
    price_col = available_amt_cols[0]  # 使用第一个找到的amt相关列
    pc.lg(f"使用price_col: {price_col}")
else:
    price_col = None
    pc.lg("警告: 未找到amt相关列")

data_config = {
    'identity': identity,
    'num_type': num_type,
    'date_type': date_type,
    'time_col': time_col,
    'cols': cols,
    'price_col': price_col,      # 动态确定的价格列名
    'base_amt_col': 'amt',       # 基础金额列名，用于向后兼容
    'available_amt_cols': available_amt_cols  # 可用的amt相关列列表
}
pc.lg(f"开始特征生成..........................")

# 为向后兼容性，如果方法期望'AMT'列但不存在，则创建兼容列
pc.lg(f"检查AMT列存在性: {'AMT' in df1.columns}")
if 'AMT' not in df1.columns:
    if price_col and price_col in df1.columns:
        pc.lg(f"创建兼容性列: AMT = {price_col}")
        df1 = df1.copy()
        df1['AMT'] = df1[price_col]
    elif available_amt_cols:
        # 如果没有指定的price_col但有其他amt相关列，使用第一个
        fallback_col = available_amt_cols[0]
        pc.lg(f"使用fallback列创建AMT兼容列: AMT = {fallback_col}")
        df1 = df1.copy()
        df1['AMT'] = df1[fallback_col]
    else:
        pc.lg("警告: 无法创建AMT兼容列，使用默认值0")
        # 创建一个默认的AMT列以避免KeyError
        df1 = df1.copy()
        df1['AMT'] = 0  # 默认值
else:
    pc.lg("AMT列已存在，无需创建兼容列")

# 验证AMT列已创建
pc.lg(f"验证AMT列: {'AMT' in df1.columns}")
if 'AMT' in df1.columns:
    pc.lg(f"AMT列数据类型: {df1['AMT'].dtype}")
    pc.lg(f"AMT列前5个值: {df1['AMT'].head().tolist()}")

# 为calculate_time_features方法添加DT_TIME兼容性
time_cols_in_data = [col for col in df1.columns if any(keyword in col.lower() for keyword in ['time', 'date', 'dt'])]
pc.lg(f"发现的时间相关列: {time_cols_in_data}")

# 确定正确的时间列用于DT_TIME兼容性
dt_time_col = None
if time_col in df1.columns:
    dt_time_col = time_col
    pc.lg(f"使用配置的time_col作为DT_TIME: {dt_time_col}")
elif 'time8' in df1.columns:
    dt_time_col = 'time8'
    pc.lg(f"使用time8作为DT_TIME: {dt_time_col}")
elif time_cols_in_data:
    dt_time_col = time_cols_in_data[0]
    pc.lg(f"使用第一个时间列作为DT_TIME: {dt_time_col}")
else:
    pc.lg("警告: 未找到任何时间相关列")

# 添加DT_TIME兼容性逻辑
pc.lg(f"检查DT_TIME列存在性: {'DT_TIME' in df1.columns}")
if 'DT_TIME' not in df1.columns:
    if dt_time_col and dt_time_col in df1.columns:
        pc.lg(f"创建DT_TIME兼容列: DT_TIME = {dt_time_col}")
        df1['DT_TIME'] = df1[dt_time_col]
    else:
        pc.lg("警告: 无法创建DT_TIME兼容列，使用当前日期")
        # 创建一个默认的DT_TIME列以避免KeyError
        import datetime
        df1['DT_TIME'] = datetime.datetime.now().strftime('%Y-%m-%d')
else:
    pc.lg("DT_TIME列已存在，无需创建兼容列")

# 验证DT_TIME列已创建
pc.lg(f"验证DT_TIME列: {'DT_TIME' in df1.columns}")
if 'DT_TIME' in df1.columns:
    pc.lg(f"DT_TIME列数据类型: {df1['DT_TIME'].dtype}")
    pc.lg(f"DT_TIME列前5个值: {df1['DT_TIME'].head().tolist()}")

# 更新data_config以包含时间列信息
data_config.update({
    'dt_time_col': dt_time_col,
    'available_time_cols': time_cols_in_data
})

config = FeatureConfig()
df_full, timings = run_feature_pipeline_with_timing(config=config,
                                                        df_preprocessed=df1,
                                                        data_config=data_config)

# 获取选择的特征（从特征选择结果中获取）
identity_cols = data_config['identity']
time_col = time_col
all_numeric_cols = [col for col in df_full.columns if df_full[col].dtype in ['int64', 'float64']]
selected_features = [col for col in all_numeric_cols if col not in identity_cols + [time_col]]

# saved_file = save_selected_features(selected_features)
pc.lg(f"选择的特征数量: {len(selected_features)}")
pc.lg(f"selected_features: {selected_features}")

# 保存选择的特征
selected_features_file = 'selected_features_1.txt'
selected_features_file = os.path.join(os.getcwd(), selected_features_file)


