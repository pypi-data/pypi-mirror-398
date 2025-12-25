

import os,sys 
import pandas as pd 
import numpy as np

from tpf import pkl_load,pkl_save 
from tpf.conf import ParamConfig 
pc = ParamConfig()

base_dir = "/ai/data/model"

# 保存选择的特征
selected_features_file = 'selected_features_1.txt'
selected_features_file = os.path.join(os.getcwd(), selected_features_file)
selected_features = pkl_load(selected_features_file)

pc.lg(f"选择的特征数量: {len(selected_features)}")
pc.lg(f"selected_features 3: {selected_features[:3]}")


#----------------------------------------
# 归一化处理
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
"""
         key       time8  amt_count  ...  currency_USD_balance_sum  currency_USD_balance_mean  currency_USD_balance_std
0   HXB_5264  2024-01-30        0.0  ...                       0.0                        0.0                       0.0
1  ICBC_8999  2024-01-30        0.0  ...                       0.0                        0.0                       0.0
2   HXB_7301  2024-02-11        0.0  ...                       0.0                        0.0                       0.0
"""
#----------------------------------------
# 特征选择或降维
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

# 请在下面追加特征选择的逻辑

#----------------------------------------
# 特征选择和降维处理
#----------------------------------------
pc.lg("开始特征选择和降维处理...")

# 导入特征工程模块
from tpf.data.feature.liushui import FeatureEngineeringPipeline, FeatureConfig

# 1. 数据准备和检查
pc.lg(f"当前数据形状: {df1.shape}")
pc.lg(f"当前数据列数: {len(df1.columns)}")
pc.lg(f"身份标识列: {data_config['identity']}")
pc.lg(f"价格列: {data_config['price_col']}")
pc.lg(f"时间列: {data_config['time_col']}")

# 2. 创建特征配置
config = FeatureConfig(
    # 基础特征配置
    basic_features=data_config['available_amt_cols'][:5] if len(data_config['available_amt_cols']) >= 5 else data_config['available_amt_cols'],

    # 移动窗口特征 - 适合交易数据的聚合统计
    moving_windows=[3, 7, 10],  # 短期、中期、长期窗口
    moving_indicators=['mean', 'std', 'min', 'max', 'median'],

    # RSI指标 - 适合交易数据分析
    rsi_periods=[5, 7, 14],

    # 动量指标
    momentum_indicators=['momentum_3', 'momentum_7'],

    # 波动性指标
    volatility_periods=[3, 7, 14],

    # 成交量相关（用交易数量代替）
    volume_windows=[3, 5, 10],

    # 技术指标窗口
    technical_windows=[3, 7, 10],

    # 时间特征
    time_features=['day_of_week', 'month', 'quarter'],

    # 滞后期
    lag_periods=[1, 2, 3],

    # 高阶特征
    high_order_windows=[3, 5],

    # 风险指标
    risk_windows=[3, 6, 10] #[3, 10, 20]

)

pc.lg(f"特征配置创建完成")

# 3. 执行特征选择和降维
try:
    pc.lg("开始调用特征选择和降维方法...")

    # 调用特征选择方法
    df_selected, selected_feature_list = FeatureEngineeringPipeline.feature_selection_and_reduction(
        df=df1,
        config=config,
        identity_cols=data_config['identity'],
        price_col=data_config['price_col'],
        time_col=data_config['time_col']
    )

    # 4. 结果分析
    pc.lg("特征选择完成！")
    pc.lg(f"原始特征数量: {len([col for col in df1.columns if col not in data_config['identity'] + [data_config['time_col']]])}")
    pc.lg(f"选择后特征数量: {len(selected_feature_list)}")
    pc.lg(f"最终数据形状: {df_selected.shape}")

    # 显示选择的特征（前20个）
    pc.lg(f"选择的特征列表（前20个）:")
    for i, feature in enumerate(selected_feature_list[:20], 1):
        pc.lg(f"  {i:2d}. {feature}")

    if len(selected_feature_list) > 20:
        pc.lg(f"  ... 还有 {len(selected_feature_list) - 20} 个特征")

    # 5. 检查PCA成分（如果生成）
    pca_features = [col for col in df_selected.columns if col.startswith('pca_component_')]
    if pca_features:
        pc.lg(f"生成的PCA成分数量: {len(pca_features)}")
        pc.lg(f"PCA成分: {pca_features[:5]}" + ("..." if len(pca_features) > 5 else ""))

    # 6. 特征重要性分析
    if selected_feature_list:
        pc.lg("进行特征重要性分析...")

        # 计算与价格列的相关性
        correlations = []
        price_col = data_config['price_col']

        for feature in selected_feature_list:
            if feature in df_selected.columns and feature != price_col:
                if df_selected[feature].dtype in ['int64', 'float64']:
                    try:
                        corr = df_selected[feature].corr(df_selected[price_col])
                        correlations.append((feature, abs(corr), corr))
                    except:
                        correlations.append((feature, 0.0, 0.0))

        # 按相关性排序
        correlations.sort(key=lambda x: x[1], reverse=True)

        pc.lg(f"特征重要性排序（按与{price_col}的绝对相关性，前15个）:")
        for i, (feature, abs_corr, corr) in enumerate(correlations[:15], 1):
            direction = "正相关" if corr > 0 else "负相关"
            pc.lg(f"  {i:2d}. {feature}: {abs_corr:.4f} ({direction})")

    # 7. 保存选择后的数据和特征列表
    selected_data_file = "/ai/data/model/selected_features_data.csv"
    selected_features_list_file = "/ai/data/model/selected_features_list.pkl"

    # 保存选择后的数据
    df_selected.to_csv(selected_data_file, index=False)
    pc.lg(f"选择后的数据已保存到: {selected_data_file}")

    # 保存选择的特征列表
    pkl_save(selected_feature_list, selected_features_list_file)
    pc.lg(f"选择的特征列表已保存到: {selected_features_list_file}")

    # 8. 更新数据配置
    data_config['selected_features'] = selected_feature_list
    data_config['selected_data_file'] = selected_data_file
    updated_config_file = "/ai/data/model/data_config_updated.pkl"
    pkl_save(updated_config_file, data_config)
    pc.lg(f"更新的数据配置已保存到: {updated_config_file}")

    pc.lg("特征选择和降维处理全部完成！")

except Exception as e:
    pc.lg(f"特征选择过程中出现错误: {e}")
    import traceback
    pc.lg(f"错误详情: {traceback.format_exc()}")

    # 备用方案：简单的相关性过滤
    pc.lg("使用备用方案：简单的相关性过滤")

    # 计算与价格列的相关性
    price_col = data_config['price_col']
    exclude_cols = data_config['identity'] + [data_config['time_col'], price_col]

    correlations = {}
    for col in df1.columns:
        if col not in exclude_cols and df1[col].dtype in ['int64', 'float64']:
            try:
                corr = df1[col].corr(df1[price_col])
                if not np.isnan(corr):
                    correlations[col] = abs(corr)
            except:
                continue

    # 选择相关性最高的特征
    if correlations:
        # 选择相关性前30%的特征，最少10个，最多50个
        sorted_features = sorted(correlations.items(), key=lambda x: x[1], reverse=True)
        num_features = max(10, min(50, int(len(sorted_features) * 0.3)))
        selected_feature_list = [feature for feature, _ in sorted_features[:num_features]]

        pc.lg(f"备用方案选择了 {len(selected_feature_list)} 个特征")
        pc.lg(f"选择的特征（前10个）: {selected_feature_list[:10]}")

        # 创建选择后的数据
        selected_cols = data_config['identity'] + [data_config['time_col'], price_col] + selected_feature_list
        df_selected = df1[selected_cols].copy()

        # 保存结果
        df_selected.to_csv(selected_data_file, index=False)
        pkl_save(selected_feature_list, selected_features_list_file)

        pc.lg(f"备用方案完成，数据已保存")
    else:
        pc.lg("无法进行特征选择，使用原始数据")
        df_selected = df1.copy()
        selected_feature_list = [col for col in df1.columns if col not in exclude_cols]

#----------------------------------------
# 特征选择完成，数据已准备好用于模型训练
#----------------------------------------
pc.lg("=" * 50)
pc.lg("特征选择和降维处理总结:")
pc.lg(f"原始数据形状: {df1.shape}")
pc.lg(f"处理后数据形状: {df_selected.shape}")
pc.lg(f"选择的特征数量: {len(selected_feature_list)}")
pc.lg(f"数据准备完成，可以进行下一步的模型训练")
pc.lg("=" * 50)

selected_feature_save_file = os.path.join(base_dir, "selected_features_last.pkl")
pkl_save(selected_feature_list, selected_feature_save_file)
pc.lg(f"保存选择的特征列表到: {selected_feature_save_file}")
