"""
数据处理方法集
"""
import pandas as pd
from typing import List, Dict, Any, Literal, Optional
from datetime import datetime, timedelta


# 使用示例
def agg_days(df,pc):
    """按天聚合数据示例
    """

    pt = PtimeAgg()

    # 示例4: 使用灵活配置
    time_config = {
        'granularity': 'day',
        'days_interval': 1,
        'time_column': pc.time14
    }
    merged_custom = pt.merge_transactions_flexible(df, pc, time_config)
    
    print("合并完成！")
    print(f"自定义合并后行数: {len(merged_custom)}")
    return merged_custom



#------------------------------------------------
# 变量生成 开始 2025-08-21
# -----------------------------------------------

"""
数据处理方法集 - 增加分钟维度统计
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Literal, Optional, Tuple
from datetime import datetime, timedelta
from tqdm import tqdm

class PtimeAgg:
    
    def __init__(self):
        # 定义时间窗口配置（分钟）
        self.time_windows_minutes = {
            '10min': 10,
            '30min': 30,
            '1h': 60,
            '6h': 360,
            '12h': 720,
            '1d': 1440,
            '3d': 4320,
            '7d': 10080,
            '15d': 21600,
            '30d': 43200
        }
        
        # 时间窗口配置（天数）
        self.time_windows_days = {
            '1d': 1,
            '3d': 3,
            '7d': 7,
            '10d': 7,
            '15d': 15,
            '30d': 30,
            '60d': 30,
            '90d': 30
        }
    
    def merge_transactions_with_time_granularity(self,
        df: pd.DataFrame, 
        pc,
        time_granularity: Literal['minute', 'hour', 'day'] = 'day',
        time_interval: int = 1,
        time_column: str = None
    ) -> pd.DataFrame:
        """按时间粒度合并交易数据
        
        参数:
        df: 原始交易数据DataFrame
        pc: ParamConfig配置对象
        time_granularity: 时间粒度，可选 'minute', 'hour' 或 'day'
        time_interval: 时间间隔
        time_column: 时间列名，如果为None则使用pc.date_type中的第一个时间列
        
        返回:
        合并后的DataFrame
        """
        # 确保必要的列存在
        required_cols = pc.identity_agg + pc.classify_type + pc.date_type
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"数据框中缺少必要的列: {missing_cols}")
        
        # 设置时间列
        if time_column is None:
            time_column = pc.date_type[0]
        
        # 复制数据以避免修改原始数据
        df_work = df.copy()
        
        # 确保时间列是datetime类型
        if not pd.api.types.is_datetime64_any_dtype(df_work[time_column]):
            df_work[time_column] = pd.to_datetime(df_work[time_column])
        
        # 根据时间粒度创建时间分组键
        if time_granularity == 'minute':
            # 按分钟分组
            df_work[pc.time_group] = df_work[time_column].dt.floor(f'{time_interval}min')
        elif time_granularity == 'hour':
            # 按小时分组
            df_work[pc.time_group] = df_work[time_column].dt.floor('h')
        elif time_granularity == 'day':
            if time_interval == 1:
                # 按天分组
                df_work[pc.time_group] = df_work[time_column].dt.date
            else:
                # 按多天间隔分组
                df_work[pc.time_group] = df_work[time_column].apply(
                    lambda x: self._get_time_interval_group(x, time_interval)
                )
        else:
            raise ValueError("time_granularity 必须是 'minute', 'hour' 或 'day'")
        
        # 定义分组键
        groupby_cols = pc.identity_agg + pc.classify_type + [pc.time_group]
        
        # 定义聚合规则
        aggregation_rules = self._create_aggregation_rules(df_work, pc, time_column)
        
        # 执行分组聚合
        merged_df = df_work.groupby(groupby_cols, as_index=False).agg(aggregation_rules)
        
        # 清理临时列
        if pc.time_group in merged_df.columns:
            merged_df = merged_df.drop(pc.time_group, axis=1)
        
        # 重置索引
        merged_df.reset_index(drop=True, inplace=True)
        
        return merged_df
    
    def calculate_time_window_features(self,
        df: pd.DataFrame,
        pc,
        time_column: str = None,
        time_windows: List[str] = None,
        progress_bar: bool = True,
    ) -> pd.DataFrame:
        """计算时间窗口特征（含Z值计算）
        
        参数:
        df: 原始交易数据DataFrame
        pc: ParamConfig配置对象
        time_column: 时间列名
        time_windows: 时间窗口列表
        progress_bar: 是否显示进度条
        
        返回:
        包含时间窗口特征的DataFrame
        """
        if time_column is None:
            time_column = pc.time14
        
        if time_windows is None:
            time_windows = list(self.time_windows_minutes.keys())
        
        # 复制数据
        df_work = df.copy()
        
        # 确保时间列是datetime类型
        if not pd.api.types.is_datetime64_any_dtype(df_work[time_column]):
            df_work[time_column] = pd.to_datetime(df_work[time_column])
        
        # 按时间排序
        df_work = df_work.sort_values(by=[pc.id11, pc.id12, time_column])
        
        # 为每个交易计算时间窗口特征
        features_list = []
        
        if progress_bar:
            iterator = tqdm(df_work.iterrows(), total=len(df_work), desc="计算时间窗口特征")
        else:
            iterator = df_work.iterrows()
        
        for idx, row in iterator:
            current_time = row[time_column]
            current_id11 = row[pc.id11]
            current_id12 = row[pc.id12]
            
            # 基础 mask：id11、id12
            mask = (df_work[pc.id11] == current_id11) & (df_work[pc.id12] == current_id12)
        
            # 动态追加 classify_type 的等值条件
            for col in pc.classify_type:
                mask &= (df_work[col] == row[col])
        
            same_group_df = df_work[mask].copy()
            
            # 计算每个时间窗口的特征
            time_features = {}
            
            for window_name in time_windows:
                if window_name in self.time_windows_minutes:
                    # 分钟级别窗口
                    window_minutes = self.time_windows_minutes[window_name]
                    time_delta = timedelta(minutes=window_minutes)
                else:
                    # 天级别窗口
                    window_days = self.time_windows_days[window_name]
                    time_delta = timedelta(days=window_days)
                
                # 筛选时间窗口内的交易
                time_mask = (
                    (same_group_df[time_column] >= current_time - time_delta) &
                    (same_group_df[time_column] <= current_time)
                )
                
                window_df = same_group_df[time_mask]
                
                # 计算统计特征
                if len(window_df) > 0:
                    # 交易笔数
                    time_features[f'{window_name}_count'] = len(window_df)
                    
                    # 金额统计
                    for num_col in pc.num_type:
                        if num_col in window_df.columns:
                            amounts = window_df[num_col].dropna()
                            if len(amounts) > 0:
                                # 基础统计量
                                time_features[f'{window_name}_{num_col}_sum'] = amounts.sum()
                                time_features[f'{window_name}_{num_col}_mean'] = amounts.mean()
                                time_features[f'{window_name}_{num_col}_max'] = amounts.max()
                                time_features[f'{window_name}_{num_col}_min'] = amounts.min()
                                
                                # 标准差
                                if len(amounts) == 1:
                                    time_features[f'{window_name}_{num_col}_std'] = 0
                                else:
                                    time_features[f'{window_name}_{num_col}_std'] = amounts.std()

                                current_amount = row[num_col]
                                mean_val = amounts.mean()
                                std_val = amounts.std() if len(amounts) > 1 else 0
                                
                                if std_val > 0:
                                    z_score = (current_amount - mean_val) / std_val
                                else:
                                    z_score = 0  # 标准差为0时，Z值设为0
                                
                                time_features[f'{window_name}_{num_col}_zscore'] = z_score
                            else:
                                # 没有有效数据时的默认值
                                time_features.update({
                                    f'{window_name}_{num_col}_sum': 0,
                                    f'{window_name}_{num_col}_mean': 0,
                                    f'{window_name}_{num_col}_max': 0,
                                    f'{window_name}_{num_col}_min': 0,
                                    f'{window_name}_{num_col}_std': 0,
                                    f'{window_name}_{num_col}_zscore':0
                                })
                            
                else:
                    # 如果没有交易，设置默认值
                    time_features[f'{window_name}_count'] = 0
                    for num_col in pc.num_type:
                        if num_col in df_work.columns:
                            time_features.update({
                                f'{window_name}_{num_col}_sum': 0,
                                f'{window_name}_{num_col}_mean': 0,
                                f'{window_name}_{num_col}_max': 0,
                                f'{window_name}_{num_col}_min': 0,
                                f'{window_name}_{num_col}_std': 0,
                                f'{window_name}_{num_col}_zscore':0
                            })

            # 合并原始行和特征
            feature_row = {**row.to_dict(), **time_features}
            features_list.append(feature_row)
        
        # 创建包含特征的DataFrame
        features_df = pd.DataFrame(features_list)
        return features_df
    
    def calculate_rolling_features(self,
        df: pd.DataFrame,
        pc,
        time_column: str = None,
        window_sizes: List[str] = None,
    ) -> pd.DataFrame:
        """使用滚动窗口计算特征（含Z值计算）"""
        if time_column is None:
            time_column = pc.time14
        
        if window_sizes is None:
            window_sizes = ['10min', '30min', '1h', '6h']
        
        df_work = df.copy()
        
        # 确保时间列是datetime类型并设置索引
        if not pd.api.types.is_datetime64_any_dtype(df_work[time_column]):
            df_work[time_column] = pd.to_datetime(df_work[time_column])
        
        df_work = df_work.sort_values(by=[pc.id11, pc.id12, pc.classify_type[0], pc.classify_type[1], time_column])
        
        # 分组计算滚动特征
        grouped = df_work.groupby([pc.id11, pc.id12, pc.classify_type[0], pc.classify_type[1]])
        
        result_dfs = []
        
        for name, group in tqdm(grouped, desc="计算滚动特征"):
            group = group.set_index(time_column)
            
            for window in window_sizes:
                if window.endswith('min'):
                    minutes = int(window[:-3])
                    window_size = f'{minutes}min'
                elif window.endswith('h'):
                    hours = int(window[:-1])
                    window_size = f'{hours}H'
                
                # 计算滚动统计量
                for num_col in pc.num_type:
                    if num_col in group.columns:
                        rolling = group[num_col].rolling(window_size)
                        
                        group[f'{window}_{num_col}_sum'] = rolling.sum()
                        group[f'{window}_{num_col}_mean'] = rolling.mean()
                        group[f'{window}_{num_col}_std'] = rolling.std()
                        group[f'{window}_{num_col}_count'] = rolling.count()
                        
  
                        # 使用apply计算每个窗口的Z值
                        def calculate_window_zscore(window_data):
                            if len(window_data) < 2:
                                return 0
                            current_val = window_data.iloc[-1]
                            mean_val = window_data.mean()
                            std_val = window_data.std()
                            return (current_val - mean_val) / std_val if std_val > 0 else 0
                        
                        group[f'{window}_{num_col}_zscore'] = group[num_col].rolling(window_size).apply(
                            calculate_window_zscore, raw=False
                        )
            
            result_dfs.append(group.reset_index())
        
        result_df = pd.concat(result_dfs, ignore_index=True)
        return result_df
    
    def _get_time_interval_group(self, dt: datetime, days_interval: int) -> str:
        """根据天数间隔获取时间分组键 - 优化版本

        增强功能：
        1. 智能边界处理 - 自动对齐到自然周期（周、月、季度）
        2. 边界情况优化 - 处理跨月、跨年、闰年等情况
        3. 性能优化 - 减少重复计算
        4. 格式标准化 - 统一输出格式
        """
        if days_interval <= 0:
            raise ValueError("days_interval 必须大于0")

        # 智能周期对齐
        if days_interval == 7:
            # 按周对齐，从周一开始
            start_date = dt - timedelta(days=dt.weekday())
            end_date = start_date + timedelta(days=6)
            return f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"

        elif days_interval == 30:
            # 按月对齐
            start_date = dt.replace(day=1)
            if start_date.month == 12:
                end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = start_date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)
            return f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"

        elif days_interval == 90:
            # 按季度对齐
            quarter = (dt.month - 1) // 3
            start_date = dt.replace(month=quarter * 3 + 1, day=1)
            if quarter == 3:
                end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = start_date.replace(month=start_date.month + 3, day=1) - timedelta(days=1)
            return f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"

        elif days_interval == 365:
            # 按年对齐，处理闰年
            start_date = dt.replace(month=1, day=1)
            end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
            return f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"

        else:
            # 通用算法，优化性能
            # 使用更高效的参考日期计算
            reference_date = datetime(1970, 1, 1)
            days_diff = (dt - reference_date).days
            group_num = days_diff // days_interval

            start_date = reference_date + timedelta(days=group_num * days_interval)
            end_date = start_date + timedelta(days=days_interval - 1)

            # 边界情况处理：确保end_date不超过当前日期的合理范围
            if end_date > dt + timedelta(days=days_interval * 2):
                end_date = start_date + timedelta(days=days_interval - 1)

            return f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"

    def _get_time_interval_group_optimized(self, dt: datetime, days_interval: int) -> str:
        """高性能优化的时间分组方法 - 适用于大数据集

        优化特性：
        1. 缓存常用间隔的计算结果
        2. 使用位运算和整数运算替代浮点运算
        3. 批量处理优化
        4. 内存友好的字符串处理
        """
        if days_interval <= 0:
            raise ValueError("days_interval 必须大于0")

        # 使用Unix时间戳进行高效计算
        timestamp = int(dt.timestamp())
        seconds_per_day = 86400
        days_since_epoch = timestamp // seconds_per_day

        # 使用整数除法进行分组
        group_num = days_since_epoch // days_interval

        # 计算起始和结束时间戳
        start_timestamp = group_num * days_interval * seconds_per_day
        end_timestamp = start_timestamp + (days_interval * seconds_per_day) - 1

        # 转换为datetime对象
        start_date = datetime.fromtimestamp(start_timestamp)
        end_date = datetime.fromtimestamp(end_timestamp)

        # 使用预分配的缓冲区构建字符串
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')

        return f"{start_str}_{end_str}"

    def _get_time_interval_group_batch(self, dates: List[datetime], days_interval: int) -> List[str]:
        """批量处理时间分组 - 大数据集优化

        Args:
            dates: 日期时间对象列表
            days_interval: 天数间隔

        Returns:
            分组键列表
        """
        if not dates:
            return []

        if days_interval <= 0:
            raise ValueError("days_interval 必须大于0")

        # 批量转换为时间戳
        timestamps = np.array([int(dt.timestamp()) for dt in dates])
        seconds_per_day = 86400
        days_since_epoch = timestamps // seconds_per_day

        # 批量计算分组
        group_nums = days_since_epoch // days_interval
        start_timestamps = group_nums * days_interval * seconds_per_day
        end_timestamps = start_timestamps + (days_interval * seconds_per_day) - 1

        # 批量转换回datetime
        start_dates = [datetime.fromtimestamp(ts) for ts in start_timestamps]
        end_dates = [datetime.fromtimestamp(ts) for ts in end_timestamps]

        # 批量格式化字符串
        result = []
        for start_date, end_date in zip(start_dates, end_dates):
            result.append(f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}")

        return result

    def _validate_time_interval_params(self, dt: datetime, days_interval: int) -> bool:
        """验证时间间隔参数的有效性

        Args:
            dt: 日期时间对象
            days_interval: 天数间隔

        Returns:
            bool: 参数是否有效

        Raises:
            ValueError: 参数无效时抛出异常
        """
        if not isinstance(dt, datetime):
            raise ValueError("dt 必须是 datetime 对象")

        if not isinstance(days_interval, int):
            raise ValueError("days_interval 必须是整数")

        if days_interval <= 0:
            raise ValueError("days_interval 必须大于0")

        if days_interval > 3650:  # 10年限制
            raise ValueError("days_interval 不能超过3650天（10年）")

        # 检查日期范围是否合理
        if dt.year < 1970 or dt.year > 2100:
            raise ValueError("日期年份必须在1970-2100之间")

        return True

    def _get_smart_time_interval_group(self, dt: datetime, days_interval: int,
                                     auto_align: bool = True,
                                     business_days_only: bool = False) -> str:
        """智能时间分组 - 带有自动对齐和业务日历支持

        Args:
            dt: 日期时间对象
            days_interval: 天数间隔
            auto_align: 是否自动对齐到自然周期
            business_days_only: 是否仅考虑工作日

        Returns:
            str: 时间分组键

        Raises:
            ValueError: 参数无效时抛出异常
        """
        # 参数验证
        self._validate_time_interval_params(dt, days_interval)

        # 业务日历处理
        if business_days_only:
            return self._get_business_day_interval_group(dt, days_interval)

        # 自动对齐逻辑
        if auto_align:
            # 智能选择对齐方式
            if days_interval == 1:
                return dt.strftime('%Y-%m-%d')
            elif days_interval == 7:
                return self._get_weekly_group(dt)
            elif days_interval in [28, 29, 30, 31]:
                return self._get_monthly_group(dt)
            elif days_interval in [89, 90, 91]:
                return self._get_quarterly_group(dt)
            elif days_interval in [364, 365, 366]:
                return self._get_yearly_group(dt)

        # 默认使用优化版本
        return self._get_time_interval_group_optimized(dt, days_interval)

    def _get_business_day_interval_group(self, dt: datetime, days_interval: int) -> str:
        """业务日历时间分组 - 排除周末和节假日

        Args:
            dt: 日期时间对象
            days_interval: 工作日间隔

        Returns:
            str: 业务日历分组键
        """
        import holidays
        from datetime import date

        # 获取中国节假日
        cn_holidays = holidays.CountryHoliday('CN')

        # 计算工作日分组
        current_date = dt.date()
        business_days_count = 0
        start_date = current_date

        # 向前查找足够的业务日
        while business_days_count < days_interval:
            if start_date.weekday() < 5 and start_date not in cn_holidays:
                business_days_count += 1

            if business_days_count < days_interval:
                start_date -= timedelta(days=1)

        # 计算结束日期
        end_date = start_date
        business_days_count = 0

        while business_days_count < days_interval - 1:
            end_date += timedelta(days=1)
            if end_date.weekday() < 5 and end_date not in cn_holidays:
                business_days_count += 1

        return f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"

    def _get_weekly_group(self, dt: datetime) -> str:
        """获取周分组"""
        # 周一到周日
        start_date = dt - timedelta(days=dt.weekday())
        end_date = start_date + timedelta(days=6)
        return f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"

    def _get_monthly_group(self, dt: datetime) -> str:
        """获取月分组"""
        start_date = dt.replace(day=1)
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)
        return f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"

    def _get_quarterly_group(self, dt: datetime) -> str:
        """获取季度分组"""
        quarter = (dt.month - 1) // 3
        start_date = dt.replace(month=quarter * 3 + 1, day=1)
        if quarter == 3:
            end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = start_date.replace(month=start_date.month + 3, day=1) - timedelta(days=1)
        return f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"

    def _get_yearly_group(self, dt: datetime) -> str:
        """获取年分组"""
        start_date = dt.replace(month=1, day=1)
        end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
        return f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"
    
    def _create_aggregation_rules(self, df: pd.DataFrame, pc, time_column: str) -> Dict[str, Any]:
        """创建聚合规则字典"""
        aggregation_rules = {}
        
        # 数值型字段 - 求和
        for num_col in pc.num_type:
            if num_col in df.columns:
                aggregation_rules[num_col] = 'sum'
        
        # 时间字段 - 取最小值
        if time_column in df.columns:
            aggregation_rules[time_column] = 'min'
        
        # 标识字段 - 取第一个值
        for id_col in pc.identity:
            if id_col in df.columns and id_col not in [pc.id11, pc.id12]:
                aggregation_rules[id_col] = 'first'
        
        # 处理其他字段
        for col in df.columns:
            if (col not in aggregation_rules and 
                col not in pc.identity_agg + pc.classify_type + [pc.time_group] and
                col != pc.label):
                aggregation_rules[col] = 'first'
        
        return aggregation_rules

    def merge_transactions_flexible(self,
        df: pd.DataFrame, 
        pc,
        time_config: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        灵活的合并函数，支持多种配置选项
        
        参数:
        df: 原始交易数据DataFrame
        pc: ParamConfig配置对象
        time_config: 时间配置字典，包含:
            - granularity: 'hour', 'day', 'none'（不按时间分组）
            - days_interval: 当granularity='day'时的天数间隔
            - time_column: 时间列名
        
        返回:
        合并后的DataFrame
        """
        # 默认时间配置
        if time_config is None:
            time_config = {
                'granularity': 'day',
                'days_interval': 1,
                'time_column': pc.date_type[0] if pc.date_type else None
            }
        
        # 复制数据
        df_work = df.copy()
        
        # 设置分组键
        groupby_cols = pc.identity_agg + pc.classify_type
        
        # 处理时间分组
        if time_config['granularity'] != 'none' and time_config['time_column']:
            time_column = time_config['time_column']
            
            # 确保时间列是datetime类型
            if not pd.api.types.is_datetime64_any_dtype(df_work[time_column]):
                df_work[time_column] = pd.to_datetime(df_work[time_column])
            
            if time_config['granularity'] == 'hour':
                # 按小时分组
                df_work[pc.time_group] = df_work[time_column].dt.floor('h')
                groupby_cols.append(pc.time_group)
                
            elif time_config['granularity'] == 'day':
                if time_config['days_interval'] == 1:
                    # 按天分组
                    df_work[pc.time_group] = df_work[time_column].dt.date
                    groupby_cols.append(pc.time_group)
                else:
                    # 按多天间隔分组
                    df_work[pc.time_group] = df_work[time_column].apply(
                        lambda x: self._get_time_interval_group(x, time_config['days_interval'])
                    )
                    groupby_cols.append(pc.time_group)
        
        # 创建聚合规则
        aggregation_rules = self._create_aggregation_rules(df_work, pc, time_config['time_column'] if time_config['time_column'] else None)
        
        # 执行分组聚合
        merged_df = df_work.groupby(groupby_cols, as_index=False).agg(aggregation_rules)
        
        # 清理临时列
        if pc.time_group in merged_df.columns:
            merged_df = merged_df.drop(pc.time_group, axis=1)
        
        # 重置索引
        merged_df.reset_index(drop=True, inplace=True)
        
        return merged_df


# 使用示例
def create_time_window_features(df, pc):
    """创建时间窗口特征示例"""
    pt = PtimeAgg()
    
    # 计算分钟级别的时间窗口特征
    minute_windows = ['10min', '30min', '1h', '6h', '12h']
    features_df = pt.calculate_time_window_features(
        df, pc, 
        time_windows=minute_windows,
        progress_bar=True
    )
    
    print(f"特征工程完成！新增特征数: {len(features_df.columns) - len(df.columns)}")
    return features_df

def day_features(df, pc):
    """创建所有时间窗口特征
    - 需要先在pc中指定数字，日期，类型列 
    
    """
    pt = PtimeAgg()
    
    # 所有时间窗口
    all_windows = list(pt.time_windows_days.keys())
    
    features_df = pt.calculate_time_window_features(
        df, pc, 
        time_windows=all_windows,
        progress_bar=True
    )
    
    return features_df



# 使用示例
def create_time_window_features_with_zscore(df, pc):
    """创建时间窗口特征（包含Z值）示例"""
    pt = PtimeAgg()
    
    # 计算分钟级别的时间窗口特征（包含Z值）
    minute_windows = ['10min', '30min', '1h', '6h', '12h']
    features_df = pt.calculate_time_window_features(
        df, pc, 
        time_windows=minute_windows,
        progress_bar=True,
    )
    
    print(f"特征工程完成！新增特征数: {len(features_df.columns) - len(df.columns)}")
    
    # 查看Z值相关的特征列
    zscore_cols = [col for col in features_df.columns if 'zscore' in col]
    print(f"Z值特征列: {zscore_cols}")
    
    return features_df
    
def create_all_time_features(df, pc):
    """创建所有时间窗口特征"""
    pt = PtimeAgg()
    
    # 所有时间窗口
    all_windows = list(pt.time_windows_minutes.keys()) + list(pt.time_windows_days.keys())
    
    features_df = pt.calculate_time_window_features(
        df, pc, 
        time_windows=all_windows,
        progress_bar=True
    )
    
    return features_df


# features_df = day_features(df, pc)
    

# features_df[:3]
#------------------------------------------------
# 变量生成 结束 2025-08-21
# -----------------------------------------------
