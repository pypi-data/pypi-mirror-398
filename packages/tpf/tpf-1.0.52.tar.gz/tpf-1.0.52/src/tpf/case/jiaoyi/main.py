from tpf.conf import ParamConfig
pc = ParamConfig()

import sys
import pandas as pd
import numpy as np

# from tpf.data.make import JiaoYi as jy
# df_accounts = jy.make_acc11()
# df_accounts= df_accounts.drop(columns=['Bank'])
# pc.lg(f"df_accounts[:3]:\n{df_accounts[:3]}")



from tpf.data.make import JiaoYi as jy
df_tra = jy.make_trans11()
pc.lg(f"df_tra[:3]:\n{df_tra[:3]}")

from tpf.data.deal import Data2Feature as dtf  
# df = dtf.data_type_change(
#     df=df_tra,
#     num_type=['Amount'],
#     classify_type=['From','To', 'time8','Payment Format', 'Currency'],
#     date_type=['time14']
# )

df_tra = dtf.data_type_change(
    df=df_tra,
    num_type=['Amount'],
    date_type=['time14']
)
pc.lg(f"df[:3]:\n{df_tra[:3]}")
pc.lg(f"df.dtypes:\n{df_tra.dtypes}")
dtf.show_col_type(df_tra[:3])


from tpf.data.deal import DataDeal as dtl
identifys      = [['From','time8'],['To','time8']]
num_type      = ['Amount']
classify_type = ['Payment Format', 'Currency'],


def data_agg(df,identifys=[['From','time8'],['To','time8']],
             num_type=['Amount'],
             classify_type=['Payment Format', 'Currency'],
             stat_lable=['count','sum','mean','std','min','max','median','q25','q75','skew','kurtosis','cv','iqr','range','se']):
    """
    银行交易流水数据聚合统计方法

    参数:
    df: 输入的交易数据DataFrame
    identifys: 分组标识列列表，默认为[['From','time8'],['To','time8']]
    num_type: 数值类型列名列表，默认为['Amount']
    classify_type: 分类类型列名列表，默认为['Payment Format', 'Currency']
    stat_lable: 需要计算的统计指标列表，支持的指标包括:
               - count: 计数
               - sum: 求和
               - mean: 均值
               - std: 标准差
               - min: 最小值
               - max: 最大值
               - median: 中位数
               - q25: 25%分位数
               - q75: 75%分位数
               - skew: 偏度
               - kurtosis: 峰度
               - cv: 变异系数
               - iqr: 四分位距
               - range: 极差
               - se: 标准误差

    背景:
    1. 银行交易流水数据集，包含From,To,time8,time14,Amount,Payment Format,Currency
    2. From为付款账户，To为收款账户
    3. time8为8位按天的时间，['From','time8']意味着按天对付款账户分类
    4. ['To','time8']意味着将来会按天对收款账户分类

    主要逻辑：
    1. 对于每个identifys[i]：
       - 形成临时df_tmp = num_type + classify_type + identifys[i]的列组合
       - 按identifys[i]分组聚合数据
       - 根据stat_lable参数生成对应的统计结果
    2. 将所有df_tmp合并成新的DataFrame返回
    3. 只计算stat_lable中指定的统计指标，提高计算效率

    示例:
    # 只计算基础统计指标
    df_basic = data_agg(df, stat_lable=['count','sum','mean','std'])

    # 计算完整的波动性指标
    df_full = data_agg(df, stat_lable=['count','sum','mean','std','q25','q75','skew','kurtosis','cv','iqr'])
    """
    import pandas as pd
    import numpy as np

    all_results = []

    # 对identifys中的每个分组键进行处理
    for i, group_cols in enumerate(identifys):
        # print(f"处理分组键 {i+1}/{len(identifys)}: {group_cols}")

        # 构建临时df_tmp的列：num_type + classify_type + group_cols
        tmp_cols = []
        tmp_cols.extend(group_cols)  # 添加分组键列

        # 检查并添加数值类型列
        available_num_cols = [col for col in num_type if col in df.columns]
        tmp_cols.extend(available_num_cols)

        # 检查并添加分类类型列
        available_cat_cols = [col for col in classify_type if col in df.columns]
        tmp_cols.extend(available_cat_cols)

        # 创建临时DataFrame
        df_tmp = df[tmp_cols].copy()
        # print(f"临时DataFrame列: {df_tmp.columns.tolist()}")
        # print(f"临时DataFrame形状: {df_tmp.shape}")

        # 按当前分组键进行聚合
        grouped = df_tmp.groupby(group_cols)

        # 为当前分组创建统计结果
        group_results = []

        print(f"开始数据聚合，统计指标: {stat_lable}")
    print(f"分组标识: {identifys}, 数值列: {num_type}, 分类列: {classify_type}")

    # 对identifys中的每个分组键进行处理
    for i, group_cols in enumerate(identifys):
        print(f"处理分组键 {i+1}/{len(identifys)}: {group_cols}")

        # 构建临时df_tmp的列：num_type + classify_type + group_cols
        tmp_cols = []
        tmp_cols.extend(group_cols)  # 添加分组键列

        # 检查并添加数值类型列
        available_num_cols = [col for col in num_type if col in df.columns]
        tmp_cols.extend(available_num_cols)

        # 检查并添加分类类型列
        available_cat_cols = [col for col in classify_type if col in df.columns]
        tmp_cols.extend(available_cat_cols)

        # 创建临时DataFrame
        df_tmp = df[tmp_cols].copy()
        print(f"临时DataFrame列: {df_tmp.columns.tolist()}")
        print(f"临时DataFrame形状: {df_tmp.shape}")

        # 按当前分组键进行聚合
        grouped = df_tmp.groupby(group_cols)

        # 为当前分组创建统计结果
        group_results = []

        # 1. 对数值列进行统计
        for num_col in available_num_cols:
            print(f"  对数值列 {num_col} 进行统计...")

            # 根据stat_lable参数动态生成统计列名
            stat_columns = []
            for stat in stat_lable:
                stat_columns.append(f'{num_col}_{stat}')

            print(f"  将计算统计列: {stat_columns}")

            # 获取所有唯一的分组组合
            all_groups = df_tmp[group_cols].drop_duplicates()
            # print(f"  发现 {len(all_groups)} 个唯一分组")

            # 创建结果DataFrame，包含所有分组和统计列
            num_result = all_groups.copy()
            for col in stat_columns:
                num_result[col] = 0.0  # 初始化所有统计列为0

            # 创建字典来快速查找分组对应的行索引
            group_to_index = {}
            for idx, row in all_groups.iterrows():
                key = tuple(row[group_cols])
                group_to_index[key] = idx

            # 计算每个分组的统计指标
            for group_key, group_data in grouped:
                # print(f"    处理分组: {group_key}, 数据量: {len(group_data)}")

                try:
                    values = group_data[num_col].dropna()  # 移除NaN值

                    if len(values) == 0:
                        print(f"      警告: 分组 {group_key} 没有有效数据")
                        continue

                    # 基础统计
                    count = len(values)
                    sum_val = values.sum()
                    mean_val = values.mean()
                    std_val = values.std(ddof=0) if count > 1 else 0.0
                    min_val = values.min()
                    max_val = values.max()
                    median_val = values.median()

                    # 分位数
                    q25_val = values.quantile(0.25)
                    q75_val = values.quantile(0.75)

                    # 衍生统计
                    skew_val = values.skew() if count > 2 else 0.0
                    kurt_val = values.kurtosis() if count > 3 else 0.0
                    cv_val = std_val / mean_val if mean_val != 0 else 0.0
                    iqr_val = q75_val - q25_val
                    range_val = max_val - min_val
                    se_val = std_val / np.sqrt(count) if count > 0 else 0.0

                    # 获取该分组在结果DataFrame中的行索引
                    if group_key in group_to_index:
                        row_idx = group_to_index[group_key]

                        # 更新统计值
                        num_result.at[row_idx, f'{num_col}_count'] = count
                        num_result.at[row_idx, f'{num_col}_sum'] = sum_val
                        num_result.at[row_idx, f'{num_col}_mean'] = mean_val
                        num_result.at[row_idx, f'{num_col}_std'] = std_val
                        num_result.at[row_idx, f'{num_col}_min'] = min_val
                        num_result.at[row_idx, f'{num_col}_max'] = max_val
                        num_result.at[row_idx, f'{num_col}_median'] = median_val
                        num_result.at[row_idx, f'{num_col}_q25'] = q25_val
                        num_result.at[row_idx, f'{num_col}_q75'] = q75_val
                        num_result.at[row_idx, f'{num_col}_skew'] = skew_val
                        num_result.at[row_idx, f'{num_col}_kurtosis'] = kurt_val
                        num_result.at[row_idx, f'{num_col}_cv'] = cv_val
                        num_result.at[row_idx, f'{num_col}_iqr'] = iqr_val
                        num_result.at[row_idx, f'{num_col}_range'] = range_val
                        num_result.at[row_idx, f'{num_col}_se'] = se_val

                    # print(f"      完成 {count} 个数据点的统计")

                except Exception as e:
                    print(f"      计算分组 {group_key} 的统计时出错: {e}")
                    continue

            # 确保所有统计列都存在且为数值类型
            for col in stat_columns:
                if col not in num_result.columns:
                    num_result[col] = 0.0
                else:
                    num_result[col] = pd.to_numeric(num_result[col], errors='coerce').fillna(0.0)

            # print(f"  数值列 {num_col} 统计完成，结果形状: {num_result.shape}")
            group_results.append(num_result)

        # 2. 对分类列进行交叉统计
        for cat_col in available_cat_cols:
            # print(f"  对分类列 {cat_col} 进行交叉统计...")

            # 获取唯一值（过滤掉NaN）
            unique_values = df_tmp[cat_col].dropna().unique()

            for num_col in available_num_cols:
                # print(f"    处理分类列 {cat_col} 与数值列 {num_col} 的交叉统计")

                # 预定义所有分类统计列
                cat_stat_columns = []
                for cat_value in unique_values:
                    cat_stat_columns.extend([
                        f'{cat_col}_{cat_value}_{num_col}_count',
                        f'{cat_col}_{cat_value}_{num_col}_sum',
                        f'{cat_col}_{cat_value}_{num_col}_mean',
                        f'{cat_col}_{cat_value}_{num_col}_std'
                    ])

                # 获取所有唯一的分组组合
                all_groups = df_tmp[group_cols].drop_duplicates()

                # 创建分类统计结果DataFrame
                cat_result = all_groups.copy()
                for col in cat_stat_columns:
                    cat_result[col] = 0.0  # 初始化所有分类统计列为0

                # 创建字典来快速查找分组对应的行索引
                group_to_index = {}
                for idx, row in all_groups.iterrows():
                    key = tuple(row[group_cols])
                    group_to_index[key] = idx

                # 计算每个分类值的统计
                for cat_value in unique_values:
                    filtered_data = df_tmp[df_tmp[cat_col] == cat_value]
                    if len(filtered_data) == 0:
                        continue

                    # print(f"      处理分类值 {cat_value}, 数据量: {len(filtered_data)}")

                    # 按分组键和分类值进行分组
                    cat_grouped = filtered_data.groupby(group_cols)

                    for group_key, group_data in cat_grouped:
                        try:
                            values = group_data[num_col].dropna()
                            if len(values) == 0:
                                continue

                            count = len(values)
                            sum_val = values.sum()
                            mean_val = values.mean()
                            std_val = values.std(ddof=0) if count > 1 else 0.0

                            # 更新对应的统计值
                            if group_key in group_to_index:
                                row_idx = group_to_index[group_key]
                                cat_result.at[row_idx, f'{cat_col}_{cat_value}_{num_col}_count'] = count
                                cat_result.at[row_idx, f'{cat_col}_{cat_value}_{num_col}_sum'] = sum_val
                                cat_result.at[row_idx, f'{cat_col}_{cat_value}_{num_col}_mean'] = mean_val
                                cat_result.at[row_idx, f'{cat_col}_{cat_value}_{num_col}_std'] = std_val

                        except Exception as e:
                            print(f"        计算分组 {group_key} 分类统计时出错: {e}")
                            continue

                # 确保所有分类统计列都存在且为数值类型
                for col in cat_stat_columns:
                    if col not in cat_result.columns:
                        cat_result[col] = 0.0
                    else:
                        cat_result[col] = pd.to_numeric(cat_result[col], errors='coerce').fillna(0.0)

                # print(f"      分类列 {cat_col} 与数值列 {num_col} 交叉统计完成，结果形状: {cat_result.shape}")
                group_results.append(cat_result)

        # 3. 合并当前分组的所有统计结果
        if group_results:
            # print(f"  合并 {len(group_results)} 个统计结果...")

            # 获取所有唯一的分组组合（确保包含所有可能的分组）
            all_groups = df_tmp[group_cols].drop_duplicates()

            # 创建包含所有分组的基准DataFrame
            group_final = all_groups.copy()

            # 合并所有统计结果到基准DataFrame
            for i, result_df in enumerate(group_results):
                # print(f"    合并第 {i+1} 个结果，形状: {result_df.shape}")

                # 使用外连接确保所有分组都被保留
                group_final = group_final.merge(
                    result_df,
                    on=group_cols,
                    how='outer'
                )

            # 添加分组标识
            group_final['group_key'] = '_'.join(group_cols)

            # 最终处理所有NaN值：将统计列的NaN转换为0
            for col in group_final.columns:
                if col not in group_cols + ['group_key']:
                    group_final[col] = pd.to_numeric(group_final[col], errors='coerce').fillna(0.0)

            # print(f"  分组 {group_cols} 合并完成，最终形状: {group_final.shape}")
            # print(f"  NaN值数量: {group_final.isnull().sum().sum()}")
            all_results.append(group_final)
    

    # 4. 合并所有分组的最终结果
    if all_results:
        final_result = pd.concat(all_results, ignore_index=True)

        # 最终NaN值处理：确保所有统计列都没有NaN
        stat_cols = [col for col in final_result.columns if col != 'group_key']
        for col in stat_cols:
            if final_result[col].dtype in ['float64', 'int64']:
                final_result[col] = final_result[col].fillna(0)

        # 将group_key列移动到第一列位置
        if 'group_key' in final_result.columns:
            cols = ['group_key'] + [col for col in final_result.columns if col != 'group_key']
            final_result = final_result[cols]

        return final_result
    else:
        return pd.DataFrame()



def cols_more2one(df, cols=['From','To'], new_col_name='key'):
    """多列互斥合并为一列
    cols中的列是互斥的，同一行只能有一个列有值，其余列为NaN,现在将这些列合并为一个列,新列名为new_col_name
    """

    # 验证输入列是否存在
    missing_cols = [col for col in cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"以下列在DataFrame中不存在: {missing_cols}")

    # 创建新列，使用bfill或ffill来填充非NaN值
    # 方法1: 使用combine_first方法
    result_df = df.copy()

    # 初始化新列为NaN
    result_df[new_col_name] = np.nan

    # 按顺序合并列，后面的列会填充前面列的NaN位置
    # 使用更简单的方法避免StringDtype问题
    for col in cols:
        # 找出新列中为NaN但在当前列中不为NaN的位置
        mask = result_df[new_col_name].isna() & result_df[col].notna()
        # 在这些位置上用当前列的值填充
        result_df.loc[mask, new_col_name] = result_df.loc[mask, col]

    # 验证合并结果：检查是否存在冲突（即原数据中同一行有多个非NaN值）
    # 计算每行非NaN值的数量
    non_nan_count = df[cols].notna().sum(axis=1)
    conflicts = non_nan_count > 1

    if conflicts.any():
        print(f"警告: 发现 {conflicts.sum()} 行数据存在冲突（多列同时有值）")
        print("冲突行示例:")
        print(df[conflicts][cols].head())

        # 对于冲突行，优先使用第一个非NaN值
        for idx in df[conflicts].index:
            for col in cols:
                if pd.notna(df.loc[idx, col]):
                    result_df.loc[idx, new_col_name] = df.loc[idx, col]
                    break

    # 删除原始列
    result_df = result_df.drop(columns=cols)

    # 将新列移动到第一列位置
    cols = [new_col_name] + [col for col in result_df.columns if col != new_col_name]
    result_df = result_df[cols]

    # print(f"成功将 {len(cols)-1} 列合并为 '{new_col_name}' 列")
    # print(f"合并后的非NaN值数量: {result_df[new_col_name].notna().sum()}")

    return result_df 


def data_agg_byday(df,
            col_time='time8',
            interval=1,
            win_len=1,
            identifys=[['From','time8'],['To','time8']],
            num_type =['Amount'],
            classify_type=['Payment Format', 'Currency'],
            merge_del_cols=['From','To'],
            new_col_name='key'):
    """
    按天滚动窗口聚合交易数据

    参数:
    df: 输入的交易数据DataFrame
    col_time: 时间列名，默认为'time8'
    interval: 滚动间隔，默认为1天
    win_len: 窗口长度，默认为1天
    identifys: 分组标识列列表，默认为[['From','time8'],['To','time8']]
    num_type: 数值类型列名列表，默认为['Amount']
    classify_type: 分类类型列名列表，默认为['Payment Format', 'Currency']
    merge_del_cols: 需要合并的列名列表，默认为['From','To']
    new_col_name: 合并后的新列名，默认为'key'

    返回:
    df_final: 合并所有窗口结果的DataFrame

    功能说明:
    1. 使用滚动窗口按天处理交易数据
    2. 对每个窗口的数据进行聚合统计（调用data_agg方法）
    3. 将多个标识列合并为一个统一的关键列（调用cols_more2one方法）
    4. 将所有窗口的结果合并为一个最终DataFrame返回
    """

    # 创建空的DataFrame用于存储所有窗口的结果
    df_final = pd.DataFrame()

    print(f"开始按天滚动窗口聚合，时间列: {col_time}, 间隔: {interval}, 窗口长度: {win_len}")
    # print(f"分组标识: {identifys}, 数值列: {num_type}, 分类列: {classify_type}")

    window_count = 0

    # 一次提取一天的数据，滚动窗口处理
    for s, e, df_sub in dtl.rolling_windows(
        df=df,
        col_time=col_time,
        interval=interval,
        win_len=win_len):

        window_count += 1
        print(f'\n处理第 {window_count} 个窗口: {s} ~ {e}，记录数 {len(df_sub)}')

        if len(df_sub) == 0:
            # print(f"  窗口 {s} ~ {e} 没有数据，跳过")
            continue

        # 1. 对当前窗口数据进行聚合统计
        # print(f"  开始聚合统计...")
        df_agg_by_day = data_agg(df_sub,
                identifys=identifys,
                num_type=num_type,
                classify_type=classify_type)

        # print(f"  聚合完成，结果形状: {df_agg_by_day.shape}")

        # 2. 将多个标识列合并为一个关键列
        if merge_del_cols and all(col in df_agg_by_day.columns for col in merge_del_cols):
            # print(f"  合并列 {merge_del_cols} 为新列 '{new_col_name}'...")
            df_agg_by_day = cols_more2one(df_agg_by_day,
                                    cols=merge_del_cols,
                                    new_col_name=new_col_name)
            # print(f"  列合并完成，结果形状: {df_agg_by_day.shape}")
        else:
            print(f"  跳过列合并，检查列是否存在: {merge_del_cols}")
            print(f"  DataFrame列: {df_agg_by_day.columns.tolist()}")

        # 3. 添加窗口时间信息
        df_agg_by_day['window_start'] = s
        df_agg_by_day['window_end'] = e
        df_agg_by_day['window_seq'] = window_count

        # 4. 将当前窗口结果合并到最终结果中
        if df_final.empty:
            df_final = df_agg_by_day.copy()
            print(f"  初始化最终结果DataFrame，形状: {df_final.shape}")
        else:
            # 使用concat合并，保持列对齐
            df_final = pd.concat([df_final, df_agg_by_day], ignore_index=True)
            # print(f"  合并当前窗口结果，最终形状: {df_final.shape}")

        # 可选：记录详细信息（如果需要调试）
        # pc.lg(f"窗口 {s} ~ {e} 聚合完成，结果形状: {df_agg_by_day.shape}")
        # pc.lg(f"窗口 {s} ~ {e} 聚合结果示例:\n{df_agg_by_day[:3]}")

    print(f"\n所有窗口处理完成，共处理 {window_count} 个窗口")
    print(f"最终结果形状: {df_final.shape}")

    if not df_final.empty:
        print(f"最终结果列: {df_final.columns.tolist()}")
        print(f"窗口序列范围: {df_final['window_seq'].min()} ~ {df_final['window_seq'].max()}")

        # 将窗口信息列移到最后
        info_cols = ['window_start', 'window_end', 'window_seq']
        other_cols = [col for col in df_final.columns if col not in info_cols]
        df_final = df_final[other_cols]

        # 将df_final中的NaN值替换为0
        print(f"开始处理df_final中的NaN值...")
        nan_before = df_final.isnull().sum().sum()
        print(f"处理前NaN值总数: {nan_before}")

        if nan_before > 0:
            # 显示每列的NaN值数量
            nan_by_col = df_final.isnull().sum()
            cols_with_nan = nan_by_col[nan_by_col > 0]
            if len(cols_with_nan) > 0:
                # print("各列NaN值数量:")
                for col, count in cols_with_nan.items():
                    print(f"  {col}: {count}")

            # 替换NaN值为0
            df_final = df_final.fillna(0)

            nan_after = df_final.isnull().sum().sum()
            print(f"处理后NaN值总数: {nan_after}")
            print("✓ 所有NaN值已替换为0")
        else:
            print("✓ df_final中没有NaN值")

    return df_final



# 调用按天聚合方法
print("开始调用data_agg_byday方法进行按天聚合...")
df_final_result = data_agg_byday(
    df=df_tra,
    col_time='time8',
    interval=1,
    win_len=1,
    identifys=[['From','time8'],['To','time8']],
    num_type=['Amount'],
    classify_type=['Payment Format', 'Currency'],
    merge_del_cols=['From','To'],
    new_col_name='key'
)

pc.lg(f"\n按天聚合完成，最终结果形状: {df_final_result.shape}")
if not df_final_result.empty:
    pc.lg(f"最终结果列名: {df_final_result.columns.tolist()}")
    pc.lg(f"最终结果前6行:\n{df_final_result.head(6)}")

# 示例调用
if 'df_final_result' in locals() and not df_final_result.empty:
    dtf.show_one_row(df_final_result, row_idx=0, n=10)
else:
    pc.lg("df_final_result 不存在或为空，跳过显示")



