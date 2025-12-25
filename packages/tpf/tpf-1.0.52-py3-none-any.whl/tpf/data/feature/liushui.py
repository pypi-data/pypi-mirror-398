#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
金融数据特征工程优化版本
将所有方法封装成类的静态方法，支持参数配置和耗时统计
"""

import pandas as pd
import numpy as np
import os
import warnings
import time
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from scipy import stats
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_regression, mutual_info_regression
from sklearn.decomposition import PCA

# 导入原有模块
import sys
sys.path.append('/ai/wks/aitpf/src')
from tpf.data.deal import Data2Feature as dtf
from tpf.conf.common import ParamConfig

# 忽略特定的数值计算警告
warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*invalid value.*')
warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*divide by zero.*')

# 日志工具
class ProgressLogger(ParamConfig):
    """简单的进度日志工具"""
    def __init__(self, usedb=False):
        super().__init__(usedb)
    @staticmethod
    def log(message):
        print(f"[{time.strftime('%H:%M:%S')}] {message}")

pc = ProgressLogger()

@dataclass
class FeatureConfig:
    """特征配置类，定义可配置的参数"""
    # 基础价格特征配置
    basic_features: List[str] = None

    # 移动窗口特征配置
    moving_windows: List[int] = None
    moving_indicators: List[str] = None

    # 动量指标配置
    rsi_periods: List[int] = None
    macd_params: Dict[str, int] = None
    momentum_indicators: List[str] = None

    # 波动率特征配置
    volatility_periods: List[int] = None
    volatility_indicators: List[str] = None

    # 成交量特征配置
    volume_windows: List[int] = None
    volume_indicators: List[str] = None

    # 技术形态特征配置
    technical_windows: List[int] = None
    technical_indicators: List[str] = None

    # 时间特征配置
    time_features: List[str] = None

    # 滞后特征配置
    lag_periods: List[int] = None
    lag_columns: List[str] = None

    # 高阶特征配置
    high_order_windows: List[int] = None
    high_order_indicators: List[str] = None

    # 风险特征配置
    risk_windows: List[int] = None
    risk_indicators: List[str] = None

    def __post_init__(self):
        """设置默认值"""
        if self.basic_features is None:
            self.basic_features = ['price_change_rate', 'log_return', 'price_amplitude',
                                 'opening_gap', 'price_position']

        if self.moving_windows is None:
            # self.moving_windows = [5, 10, 20]
            self.moving_windows = [3, 5, 7]
        if self.moving_indicators is None:
            self.moving_indicators = ['MA', 'EMA', 'STD', 'MAX', 'MIN', 'Q25', 'Q50', 'Q75',
                                    'IQR', 'CV', 'Price_vs_MA', 'Price_ZScore']

        if self.rsi_periods is None:
            self.rsi_periods = [7]
            # self.rsi_periods = [14]
        if self.macd_params is None:
            self.macd_params = {'fast': 4, 'slow': 8, 'signal': 3}
            # self.macd_params = {'fast': 12, 'slow': 26, 'signal': 9}
        if self.momentum_indicators is None:
            self.momentum_indicators = ['RSI', 'MACD', 'Momentum', 'Rate_of_Change']

        if self.volatility_periods is None:
            self.volatility_periods = [3, 5, 10]
            # self.volatility_periods = [5, 10, 20]
        if self.volatility_indicators is None:
            self.volatility_indicators = ['Historical_Volatility', 'ATR', 'Parkinson', 'Garman_Klass']

        if self.volume_windows is None:
            # self.volume_windows = [5, 10, 20]
            self.volume_windows = [2, 5, 10]
        if self.volume_indicators is None:
            self.volume_indicators = ['volume_change_rate', 'VMA', 'VEMA', 'price_volume_corr', 'VWAP', 'OBV']

        if self.technical_windows is None:
            self.technical_windows = [3, 7, 14]
            # self.technical_windows = [10, 20, 50]
        if self.technical_indicators is None:
            self.technical_indicators = ['Support_Resistance', 'Bollinger_Position', 'Williams_R']

        if self.time_features is None:
            self.time_features = ['hour', 'minute', 'day_of_week', 'month', 'is_weekend',
                                'is_month_start', 'is_month_end', 'time_sin_cos', 'seasonal']

        if self.lag_periods is None:
            self.lag_periods = [1, 2, 3, 5, 7, 10]
            # self.lag_periods = [1, 2, 3, 5, 10, 20]
        if self.lag_columns is None:
            self.lag_columns = ['AMT', 'ACCBAL', 'CNY_AMT']

        if self.high_order_windows is None:
            self.high_order_windows = [5, 10, 20]
            # self.high_order_windows = [10, 20, 50]
        if self.high_order_indicators is None:
            self.high_order_indicators = ['derivatives', 'rolling_corr', 'rolling_beta', 'z_score_normalize']

        if self.risk_windows is None:
            self.risk_windows = [7, 14, 20]
            # self.risk_windows = [20, 50, 100]
        if self.risk_indicators is None:
            self.risk_indicators = ['max_drawdown', 'sharpe_ratio', 'calmar_ratio', 'VaR', 'skewness_kurtosis']

class FeatureEngineeringPipeline:
    """特征工程管道类，包含所有特征计算方法"""

    @staticmethod
    def clean_data(df: pd.DataFrame, numeric_cols: List[str]) -> pd.DataFrame:
        """
        通用数据清理函数：处理无穷大值、NaN值和异常值

        Args:
            df: 输入数据框
            numeric_cols: 数值列名列表

        Returns:
            清理后的数据框
        """
        df_clean = df.copy()
        pc.log("开始数据清理...")

        for col in numeric_cols:
            if col in df_clean.columns:
                original_count = len(df_clean[col])

                # 1. 替换无穷大值为NaN
                df_clean[col] = df_clean[col].replace([np.inf, -np.inf], np.nan)

                # 2. 检查数据质量
                nan_count = df_clean[col].isnull().sum()
                valid_count = original_count - nan_count

                if valid_count == 0:
                    pc.log(f"警告：列{col}没有有效数据，用0填充")
                    df_clean[col] = 0
                    continue

                # 3. 处理NaN值
                if nan_count > 0:
                    df_clean[col] = df_clean[col].ffill().interpolate().bfill().fillna(0)
                    pc.log(f"列{col}处理了{nan_count}个缺失值")

                # 4. 检查数值范围
                col_min = df_clean[col].min()
                col_max = df_clean[col].max()

                if abs(col_min) > 1e15 or abs(col_max) > 1e15:
                    pc.log(f"警告：列{col}存在极大数值，进行截断处理")
                    df_clean[col] = df_clean[col].clip(-1e10, 1e10)

                # 5. 检查是否为常数列
                if df_clean[col].nunique() <= 1:
                    pc.log(f"警告：列{col}为常数列，值={df_clean[col].iloc[0]}")

        pc.log("数据清理完成")
        return df_clean

    @staticmethod
    def preprocess_data(df: pd.DataFrame, identity_cols: List[str], numeric_cols: List[str],
                       date_col: str) -> pd.DataFrame:
        """
        数据预处理：时间序列对齐、异常值处理、缺失值填充、标准化

        Args:
            df: 输入数据框
            identity_cols: 标识列列表
            numeric_cols: 数值列列表
            date_col: 日期列名

        Returns:
            预处理后的数据框
        """
        df_processed = df.copy()

        # 1.0 基础数据清理
        df_processed = FeatureEngineeringPipeline.clean_data(df_processed, numeric_cols)

        # 1.1 时间序列对齐和重采样
        df_processed = df_processed.sort_values(date_col).reset_index(drop=True)
        pc.log(f"数据按{date_col}排序完成，共{len(df_processed)}条记录")

        # 1.2 异常值检测和处理
        for col in numeric_cols:
            if col in df_processed.columns:
                cleaned_series = df_processed[col].replace([np.inf, -np.inf], np.nan).dropna()

                if len(cleaned_series) == 0:
                    pc.log(f"警告：列{col}没有有效数据，跳过异常值处理")
                    continue

                if cleaned_series.std() == 0:
                    pc.log(f"警告：列{col}的标准差为0，跳过Z-score异常值检测")
                    continue

                try:
                    z_scores = np.abs(stats.zscore(cleaned_series))
                    outliers = z_scores > 3
                    outlier_count = outliers.sum()

                    if outlier_count > 0:
                        pc.log(f"列{col}检测到{outlier_count}个异常值(Z-score>3)")

                        lower_bound = cleaned_series.quantile(0.01)
                        upper_bound = cleaned_series.quantile(0.99)

                        if lower_bound == upper_bound:
                            mean_val = cleaned_series.mean()
                            std_val = cleaned_series.std()
                            if std_val > 0:
                                lower_bound = mean_val - 3 * std_val
                                upper_bound = mean_val + 3 * std_val
                            else:
                                lower_bound = mean_val - 1
                                upper_bound = mean_val + 1

                        extreme_before = ((df_processed[col] < lower_bound) |
                                        (df_processed[col] > upper_bound)).sum()
                        df_processed[col] = df_processed[col].clip(lower=lower_bound, upper=upper_bound)
                        extreme_after = ((df_processed[col] < lower_bound) |
                                       (df_processed[col] > upper_bound)).sum()
                        pc.log(f"列{col} Winsorization处理完成: {extreme_before} -> {extreme_after}个极值")

                except Exception as e:
                    pc.log(f"警告：列{col}异常值处理失败: {str(e)}")

        # 1.3 缺失值填充
        for col in numeric_cols:
            if col in df_processed.columns:
                missing_before = df_processed[col].isnull().sum()
                if missing_before > 0:
                    df_processed[col] = df_processed[col].ffill().interpolate().bfill().fillna(0)
                    missing_after = df_processed[col].isnull().sum()
                    pc.log(f"列{col}缺失值处理: {missing_before} -> {missing_after}")

        # 1.4 数据标准化
        scaler = StandardScaler()
        for col in numeric_cols:
            if col in df_processed.columns:
                clean_series = df_processed[col].replace([np.inf, -np.inf], np.nan).fillna(0)
                mean_val = clean_series.mean()
                std_val = clean_series.std()

                if std_val > 0 and not (np.isnan(mean_val) or np.isnan(std_val)):
                    try:
                        df_processed[f"{col}_scaled"] = scaler.fit_transform(clean_series.values.reshape(-1, 1))
                        pc.log(f"列{col}标准化完成: 均值={mean_val:.4f}, 标准差={std_val:.4f}")
                    except Exception as e:
                        df_processed[f"{col}_scaled"] = (clean_series - mean_val) / (std_val + 1e-8)
                        pc.log(f"列{col}使用简单标准化完成")
                else:
                    pc.log(f"警告：列{col}标准差为0或包含无效值，跳过标准化")
                    df_processed[f"{col}_scaled"] = clean_series

        pc.log(f"预处理完成，数据维度: {df_processed.shape}")
        return df_processed

    @staticmethod
    def calculate_basic_price_features(df: pd.DataFrame, config: FeatureConfig,
                                     price_col: str = 'AMT', identity_cols: List[str] = None,
                                     time_col: str = 'DT_TIME', balance_col: str = 'ACCBAL') -> pd.DataFrame:
        """
        计算基础价格特征：价格变化率、对数收益率、价格振幅、开盘跳空、收盘价相对位置

        Args:
            df: 输入数据框
            config: 特征配置
            price_col: 价格列名
            identity_cols: 标识列列表
            time_col: 时间列名
            balance_col: 余额列名

        Returns:
            包含基础价格特征的数据框
        """
        if identity_cols is None:
            identity_cols = []

        df_features = df.copy()
        df_features = df_features.sort_values(time_col).reset_index(drop=True)

        epsilon = 1e-8

        # 2.1 价格变化率
        if 'price_change_rate' in config.basic_features:
            df_features['price_change_rate'] = df_features[price_col].pct_change().fillna(0)
            pc.log("已计算价格变化率 (price_change_rate)")

        # 2.2 对数收益率
        if 'log_return' in config.basic_features:
            df_features['log_return'] = (np.log(df_features[price_col] + epsilon) -
                                        np.log(df_features[price_col].shift(1) + epsilon)).fillna(0)
            pc.log("已计算对数收益率 (log_return)")

        # 2.3 价格振幅
        if 'price_amplitude' in config.basic_features and balance_col in df_features.columns:
            window = 5
            df_features['price_high'] = df_features[balance_col].rolling(window=window, min_periods=1).max()
            df_features['price_low'] = df_features[balance_col].rolling(window=window, min_periods=1).min()
            df_features['price_amplitude'] = ((df_features['price_high'] - df_features['price_low']) /
                                             (df_features[price_col].shift(1) + epsilon)).fillna(0)
            pc.log("已计算价格振幅 (price_amplitude)")

        # 2.4 开盘跳空
        if 'opening_gap' in config.basic_features:
            df_features[time_col] = pd.to_datetime(df_features[time_col])
            df_features['time_diff'] = df_features[time_col].diff().dt.total_seconds() / 3600
            df_features['time_diff'] = df_features['time_diff'].fillna(0)
            jump_threshold = 4
            df_features['is_jump'] = (df_features['time_diff'] > jump_threshold).astype(int)
            df_features['opening_gap'] = df_features['price_change_rate'] * df_features['is_jump']
            pc.log("已计算开盘跳空 (opening_gap)")

        # 2.5 收盘价相对位置
        if 'price_position' in config.basic_features:
            if 'price_high' in df_features.columns and 'price_low' in df_features.columns:
                price_range = df_features['price_high'] - df_features['price_low']
                price_range = price_range.replace(0, 1e-8)
                df_features['price_position'] = ((df_features[price_col] - df_features['price_low']) /
                                                price_range).fillna(0.5)
                pc.log("已计算收盘价相对位置 (price_position)")

        return df_features

    @staticmethod
    def calculate_moving_window_features(df: pd.DataFrame, config: FeatureConfig,
                                       price_col: str = 'AMT') -> pd.DataFrame:
        """
        计算移动窗口统计特征

        Args:
            df: 输入数据框
            config: 特征配置
            price_col: 价格列名

        Returns:
            包含移动窗口特征的数据框
        """
        df_features = df.copy()

        for window in config.moving_windows:
            if not isinstance(window, int) or window <= 0:
                continue

            # 3.1 简单移动平均
            if 'MA' in config.moving_indicators:
                df_features[f'MA_{window}'] = df_features[price_col].rolling(
                    window=window, min_periods=1).mean()

            # 3.2 指数移动平均
            if 'EMA' in config.moving_indicators:
                alpha = 2 / (window + 1)
                df_features[f'EMA_{window}'] = df_features[price_col].ewm(
                    alpha=alpha, adjust=False).mean()

            # 3.3 移动标准差
            if 'STD' in config.moving_indicators:
                df_features[f'STD_{window}'] = df_features[price_col].rolling(
                    window=window, min_periods=1).std().fillna(0)

            # 3.4 移动极值
            if 'MAX' in config.moving_indicators:
                df_features[f'MAX_{window}'] = df_features[price_col].rolling(
                    window=window, min_periods=1).max()
            if 'MIN' in config.moving_indicators:
                df_features[f'MIN_{window}'] = df_features[price_col].rolling(
                    window=window, min_periods=1).min()

            # 3.5 移动分位数
            if 'Q25' in config.moving_indicators:
                df_features[f'Q25_{window}'] = df_features[price_col].rolling(
                    window=window, min_periods=1).quantile(0.25)
            if 'Q50' in config.moving_indicators:
                df_features[f'Q50_{window}'] = df_features[price_col].rolling(
                    window=window, min_periods=1).quantile(0.50)
            if 'Q75' in config.moving_indicators:
                df_features[f'Q75_{window}'] = df_features[price_col].rolling(
                    window=window, min_periods=1).quantile(0.75)

            # 3.6 四分位距
            if 'IQR' in config.moving_indicators:
                if f'Q75_{window}' in df_features.columns and f'Q25_{window}' in df_features.columns:
                    df_features[f'IQR_{window}'] = (df_features[f'Q75_{window}'] -
                                                   df_features[f'Q25_{window}']).fillna(0)

            # 3.7 变异系数
            if 'CV' in config.moving_indicators:
                if f'MA_{window}' in df_features.columns and f'STD_{window}' in df_features.columns:
                    mean_vals = df_features[f'MA_{window}']
                    std_vals = df_features[f'STD_{window}']
                    df_features[f'CV_{window}'] = (std_vals / (mean_vals + 1e-8)).fillna(0)

            # 3.8 价格相对移动平均位置
            if 'Price_vs_MA' in config.moving_indicators:
                if f'MA_{window}' in df_features.columns:
                    df_features[f'Price_vs_MA_{window}'] = ((df_features[price_col] -
                                                           df_features[f'MA_{window}']) /
                                                          (df_features[f'MA_{window}'] + 1e-8)).fillna(0)

            # 3.9 价格Z-score标准化
            if 'Price_ZScore' in config.moving_indicators:
                if f'MA_{window}' in df_features.columns and f'STD_{window}' in df_features.columns:
                    df_features[f'Price_ZScore_{window}'] = ((df_features[price_col] -
                                                            df_features[f'MA_{window}']) /
                                                           (df_features[f'STD_{window}'] + 1e-8)).fillna(0)

            pc.log(f"已计算{window}期移动窗口特征")

        return df_features

    @staticmethod
    def calculate_momentum_indicators(df: pd.DataFrame, config: FeatureConfig,
                                    price_col: str = 'AMT') -> pd.DataFrame:
        """
        计算动量指标特征：RSI、MACD、动量指标、变化率指标

        Args:
            df: 输入数据框
            config: 特征配置
            price_col: 价格列名

        Returns:
            包含动量指标特征的数据框
        """
        df_features = df.copy()

        # 4.1 RSI
        if 'RSI' in config.momentum_indicators:
            for period in config.rsi_periods:
                def calculate_rsi(prices, period):
                    delta = prices.diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
                    rs = gain / (loss + 1e-8)
                    rsi = 100 - (100 / (1 + rs))
                    return rsi.fillna(50)

                df_features[f'RSI_{period}'] = calculate_rsi(df_features[price_col], period)
                pc.log(f"已计算{period}期RSI指标")

        # 4.2 MACD
        if 'MACD' in config.momentum_indicators:
            fast = config.macd_params['fast']
            slow = config.macd_params['slow']
            signal = config.macd_params['signal']

            ema_fast = df_features[price_col].ewm(span=fast, adjust=False).mean()
            ema_slow = df_features[price_col].ewm(span=slow, adjust=False).mean()
            df_features['MACD'] = ema_fast - ema_slow
            df_features['MACD_Signal'] = df_features['MACD'].ewm(span=signal, adjust=False).mean()
            df_features['MACD_Histogram'] = df_features['MACD'] - df_features['MACD_Signal']
            pc.log("已计算MACD指标")

        # 4.3 动量指标
        if 'Momentum' in config.momentum_indicators:
            for period in [5, 10, 20]:
                df_features[f'Momentum_{period}'] = df_features[price_col] - df_features[price_col].shift(period)
            pc.log("已计算动量指标")

        # 4.4 变化率指标
        if 'Rate_of_Change' in config.momentum_indicators:
            for period in [5, 10, 20]:
                df_features[f'ROC_{period}'] = ((df_features[price_col] - df_features[price_col].shift(period)) /
                                               (df_features[price_col].shift(period) + 1e-8)).fillna(0)
            pc.log("已计算变化率指标")

        return df_features

    @staticmethod
    def calculate_volatility_features(df: pd.DataFrame, config: FeatureConfig,
                                    price_col: str = 'AMT', balance_col: str = 'ACCBAL') -> pd.DataFrame:
        """
        计算波动率特征：历史波动率、ATR、Parkinson波动率、Garman-Klass波动率

        Args:
            df: 输入数据框
            config: 特征配置
            price_col: 价格列名
            balance_col: 余额列名

        Returns:
            包含波动率特征的数据框
        """
        df_features = df.copy()

        # 5.1 历史波动率
        if 'Historical_Volatility' in config.volatility_indicators:
            log_returns = df_features[price_col].pct_change().fillna(0)
            for period in config.volatility_periods:
                volatility = log_returns.rolling(window=period, min_periods=1).std().fillna(0)
                df_features[f'Historical_Volatility_{period}'] = volatility * np.sqrt(252)
            pc.log("已计算历史波动率")

        # 5.2 ATR
        if 'ATR' in config.volatility_indicators and balance_col in df_features.columns:
            for period in config.volatility_periods:
                high_proxy = df_features[balance_col].rolling(window=period, min_periods=1).max()
                low_proxy = df_features[balance_col].rolling(window=period, min_periods=1).min()
                close_prev = df_features[price_col].shift(1)

                tr1 = high_proxy - low_proxy
                tr2 = abs(high_proxy - close_prev)
                tr3 = abs(low_proxy - close_prev)
                true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                df_features[f'ATR_{period}'] = true_range.rolling(window=period, min_periods=1).mean()
            pc.log("已计算ATR指标")

        # 5.3 Parkinson波动率
        if 'Parkinson' in config.volatility_indicators and balance_col in df_features.columns:
            for period in config.volatility_periods:
                high_proxy = df_features[balance_col].rolling(window=period, min_periods=1).max()
                low_proxy = df_features[balance_col].rolling(window=period, min_periods=1).min()
                parkinson_vol = np.sqrt(0.361 * (np.log(high_proxy / (low_proxy + 1e-8)))**2) * np.sqrt(252)
                df_features[f'Parkinson_Volatility_{period}'] = parkinson_vol.fillna(0)
            pc.log("已计算Parkinson波动率")

        # 5.4 Garman-Klass波动率
        if 'Garman_Klass' in config.volatility_indicators and balance_col in df_features.columns:
            for period in config.volatility_periods:
                high_proxy = df_features[balance_col].rolling(window=period, min_periods=1).max()
                low_proxy = df_features[balance_col].rolling(window=period, min_periods=1).min()
                close = df_features[price_col]
                close_prev = close.shift(1)

                gk_vol = (0.5 * (np.log(high_proxy / (low_proxy + 1e-8)))**2 -
                         (2 * np.log(2) - 1) * (np.log(close / (close_prev + 1e-8)))**2)
                df_features[f'Garman_Klass_Volatility_{period}'] = np.sqrt(gk_vol.fillna(0) * 252)
            pc.log("已计算Garman-Klass波动率")

        return df_features

    @staticmethod
    def calculate_volume_features(df: pd.DataFrame, config: FeatureConfig,
                                price_col: str = 'AMT', volume_proxy_col: str = 'AMT',
                                amount_col: str = 'CNY_AMT') -> pd.DataFrame:
        """
        计算成交量特征：成交量变化率、成交量移动平均、价量相关性、VWAP、OBV

        Args:
            df: 输入数据框
            config: 特征配置
            price_col: 价格列名
            volume_proxy_col: 成交量代理列名
            amount_col: 金额列名

        Returns:
            包含成交量特征的数据框
        """
        df_features = df.copy()

        # 6.1 成交量变化率
        if 'volume_change_rate' in config.volume_indicators:
            df_features['volume_change_rate'] = df_features[volume_proxy_col].pct_change().fillna(0)

        # 6.2 成交量移动平均
        if 'VMA' in config.volume_indicators or 'VEMA' in config.volume_indicators:
            for window in config.volume_windows:
                if 'VMA' in config.volume_indicators:
                    df_features[f'VMA_{window}'] = df_features[volume_proxy_col].rolling(
                        window=window, min_periods=1).mean()
                if 'VEMA' in config.volume_indicators:
                    alpha = 2 / (window + 1)
                    df_features[f'VEMA_{window}'] = df_features[volume_proxy_col].ewm(
                        alpha=alpha, adjust=False).mean()

        # 6.3 价量相关性
        if 'price_volume_corr' in config.volume_indicators:
            for window in config.volume_windows:
                price_change = df_features[price_col].pct_change().fillna(0)
                volume_change = df_features[volume_proxy_col].pct_change().fillna(0)
                correlation = price_change.rolling(window=window, min_periods=1).corr(volume_change)
                df_features[f'Price_Volume_Corr_{window}'] = correlation.fillna(0)

        # 6.4 VWAP
        if 'VWAP' in config.volume_indicators and amount_col in df_features.columns:
            for window in config.volume_windows:
                if df_features[volume_proxy_col].sum() > 0:
                    vwap = (df_features[price_col] * df_features[volume_proxy_col]).rolling(
                        window=window, min_periods=1).sum() / df_features[volume_proxy_col].rolling(
                        window=window, min_periods=1).sum()
                    df_features[f'VWAP_{window}'] = vwap.fillna(df_features[price_col])

        # 6.5 OBV
        if 'OBV' in config.volume_indicators:
            price_change = df_features[price_col].diff()
            obv = np.where(price_change > 0, df_features[volume_proxy_col],
                          np.where(price_change < 0, -df_features[volume_proxy_col], 0))
            df_features['OBV'] = np.cumsum(obv)
            df_features['OBV_MA'] = df_features['OBV'].rolling(window=20, min_periods=1).mean()

        pc.log("已计算成交量特征")
        return df_features

    @staticmethod
    def calculate_technical_pattern_features(df: pd.DataFrame, config: FeatureConfig,
                                           price_col: str = 'AMT', balance_col: str = 'ACCBAL') -> pd.DataFrame:
        """
        计算技术形态特征：支撑阻力位、趋势强度、布林带位置、威廉姆斯%R

        Args:
            df: 输入数据框
            config: 特征配置
            price_col: 价格列名
            balance_col: 余额列名

        Returns:
            包含技术形态特征的数据框
        """
        df_features = df.copy()

        # 7.1 支撑阻力位识别
        if 'Support_Resistance' in config.technical_indicators:
            for window in config.technical_windows:
                df_features[f'Resistance_Level_{window}'] = df_features[price_col].rolling(
                    window=window, min_periods=1).max()
                df_features[f'Support_Level_{window}'] = df_features[price_col].rolling(
                    window=window, min_periods=1).min()

                support = df_features[f'Support_Level_{window}']
                resistance = df_features[f'Resistance_Level_{window}']
                price_range = resistance - support
                price_range = price_range.replace(0, 1e-8)
                df_features[f'Price_Position_{window}'] = ((df_features[price_col] - support) /
                                                         price_range).fillna(0.5)

        # 7.2 布林带位置
        if 'Bollinger_Position' in config.technical_indicators:
            for window in config.technical_windows:
                ma = df_features[price_col].rolling(window=window, min_periods=1).mean()
                std = df_features[price_col].rolling(window=window, min_periods=1).std()
                upper_band = ma + 2 * std
                lower_band = ma - 2 * std

                df_features[f'Bollinger_Upper_{window}'] = upper_band
                df_features[f'Bollinger_Lower_{window}'] = lower_band
                df_features[f'Bollinger_Position_{window}'] = ((df_features[price_col] - lower_band) /
                                                               (upper_band - lower_band + 1e-8)).fillna(0.5)

        # 7.3 威廉姆斯%R
        if 'Williams_R' in config.technical_indicators and balance_col in df_features.columns:
            for window in config.technical_windows:
                high_proxy = df_features[balance_col].rolling(window=window, min_periods=1).max()
                low_proxy = df_features[balance_col].rolling(window=window, min_periods=1).min()

                williams_r = ((high_proxy - df_features[price_col]) /
                             (high_proxy - low_proxy + 1e-8)) * -100
                df_features[f'Williams_R_{window}'] = williams_r.fillna(-50)

        pc.log("已计算技术形态特征")
        return df_features

    @staticmethod
    def calculate_time_features(df: pd.DataFrame, config: FeatureConfig,
                              date_col: str = 'DT_TIME') -> pd.DataFrame:
        """
        计算时间特征：小时/分钟/秒、周几/月份、节假日、交易时段、周期性特征

        Args:
            df: 输入数据框
            config: 特征配置
            date_col: 日期列名

        Returns:
            包含时间特征的数据框
        """
        df_features = df.copy()
        df_features[date_col] = pd.to_datetime(df_features[date_col])

        # 8.1 基础时间特征
        if 'hour' in config.time_features:
            df_features['hour'] = df_features[date_col].dt.hour
        if 'minute' in config.time_features:
            df_features['minute'] = df_features[date_col].dt.minute
        if 'day_of_week' in config.time_features:
            df_features['day_of_week'] = df_features[date_col].dt.dayofweek
        if 'month' in config.time_features:
            df_features['month'] = df_features[date_col].dt.month
        if 'is_weekend' in config.time_features:
            df_features['is_weekend'] = (df_features[date_col].dt.dayofweek >= 5).astype(int)
        if 'is_month_start' in config.time_features:
            df_features['is_month_start'] = (df_features[date_col].dt.is_month_start).astype(int)
        if 'is_month_end' in config.time_features:
            df_features['is_month_end'] = (df_features[date_col].dt.is_month_end).astype(int)

        # 8.2 周期性特征
        if 'time_sin_cos' in config.time_features:
            # 确保基础时间特征存在（依赖关系）
            if 'hour' not in df_features.columns:
                df_features['hour'] = df_features[date_col].dt.hour
            if 'day_of_week' not in df_features.columns:
                df_features['day_of_week'] = df_features[date_col].dt.dayofweek
            if 'month' not in df_features.columns:
                df_features['month'] = df_features[date_col].dt.month

            df_features['hour_sin'] = np.sin(2 * np.pi * df_features['hour'] / 24)
            df_features['hour_cos'] = np.cos(2 * np.pi * df_features['hour'] / 24)
            df_features['day_sin'] = np.sin(2 * np.pi * df_features['day_of_week'] / 7)
            df_features['day_cos'] = np.cos(2 * np.pi * df_features['day_of_week'] / 7)
            df_features['month_sin'] = np.sin(2 * np.pi * df_features['month'] / 12)
            df_features['month_cos'] = np.cos(2 * np.pi * df_features['month'] / 12)

        # 8.3 季节性特征
        if 'seasonal' in config.time_features:
            df_features['quarter'] = df_features[date_col].dt.quarter
            df_features['week_of_year'] = df_features[date_col].dt.isocalendar().week

        pc.log("已计算时间特征")
        return df_features

    @staticmethod
    def calculate_lag_features(df: pd.DataFrame, config: FeatureConfig,
                             price_col: str = 'AMT', balance_col: str = 'ACCBAL',
                             amount_col: str = 'CNY_AMT', time_col: str = 'DT_TIME') -> pd.DataFrame:
        """
        计算滞后特征：多期滞后、滞后收益率、交互项

        Args:
            df: 输入数据框
            config: 特征配置
            price_col: 价格列名
            balance_col: 余额列名
            amount_col: 金额列名
            time_col: 时间列名

        Returns:
            包含滞后特征的数据框
        """
        df_features = df.copy()
        df_features = df_features.sort_values(time_col).reset_index(drop=True)

        # 9.1 多期滞后特征
        main_cols = [price_col, balance_col, amount_col]
        for col in main_cols:
            if col in df_features.columns and col in config.lag_columns:
                for lag in config.lag_periods:
                    df_features[f'{col}_lag_{lag}'] = df_features[col].shift(lag).fillna(0)

        # 9.2 滞后收益率特征
        for lag in config.lag_periods:
            if f'{price_col}_lag_{lag}' in df_features.columns:
                lag_return = (df_features[price_col] - df_features[f'{price_col}_lag_{lag}']) / \
                           (df_features[f'{price_col}_lag_{lag}'] + 1e-8)
                df_features[f'lag_return_{lag}'] = lag_return.fillna(0)

        pc.log("已计算滞后特征")
        return df_features

    @staticmethod
    def calculate_high_order_features(df: pd.DataFrame, config: FeatureConfig,
                                    price_col: str = 'AMT', balance_col: str = 'ACCBAL',
                                    amount_col: str = 'CNY_AMT', time_col: str = 'DT_TIME') -> pd.DataFrame:
        """
        计算高阶特征：价格导数、滚动相关系数、滚动Beta、标准化

        Args:
            df: 输入数据框
            config: 特征配置
            price_col: 价格列名
            balance_col: 余额列名
            amount_col: 金额列名
            time_col: 时间列名

        Returns:
            包含高阶特征的数据框
        """
        df_features = df.copy()
        df_features = df_features.sort_values(time_col).reset_index(drop=True)

        # 10.1 价格导数
        if 'derivatives' in config.high_order_indicators:
            def calculate_derivatives(series):
                first_derivative = series.diff().fillna(0)
                second_derivative = series.diff().diff().fillna(0)
                return first_derivative, second_derivative

            first_deriv, second_deriv = calculate_derivatives(df_features[price_col])
            df_features['price_first_derivative'] = first_deriv
            df_features['price_second_derivative'] = second_deriv

        # 10.2 滚动相关系数
        if 'rolling_corr' in config.high_order_indicators and balance_col in df_features.columns:
            for window in config.high_order_windows:
                corr = df_features[price_col].rolling(window=window, min_periods=1).corr(
                    df_features[balance_col])
                df_features[f'price_balance_corr_{window}'] = corr.fillna(0)

        # 10.3 滚动Beta
        if 'rolling_beta' in config.high_order_indicators and balance_col in df_features.columns:
            for window in config.high_order_windows:
                if window < len(df_features):
                    rolling_cov = df_features[price_col].rolling(window=window).cov(
                        df_features[balance_col])
                    rolling_var = df_features[balance_col].rolling(window=window).var()
                    beta = rolling_cov / (rolling_var + 1e-8)
                    df_features[f'price_beta_{window}'] = beta.fillna(1.0)

        # 10.4 Z-score标准化
        if 'z_score_normalize' in config.high_order_indicators:
            for window in config.high_order_windows:
                rolling_mean = df_features[price_col].rolling(window=window, min_periods=1).mean()
                rolling_std = df_features[price_col].rolling(window=window, min_periods=1).std()
                z_score = (df_features[price_col] - rolling_mean) / (rolling_std + 1e-8)
                df_features[f'price_zscore_{window}'] = z_score.fillna(0)

        pc.log("已计算高阶特征")
        return df_features

    @staticmethod
    def calculate_risk_features(df: pd.DataFrame, config: FeatureConfig,
                              price_col: str = 'AMT', balance_col: str = 'ACCBAL',
                              amount_col: str = 'CNY_AMT', time_col: str = 'DT_TIME') -> pd.DataFrame:
        """
        计算风险指标特征：最大回撤、夏普比率、卡尔马比率、VaR、偏度峰度

        Args:
            df: 输入数据框
            config: 特征配置
            price_col: 价格列名
            balance_col: 余额列名
            amount_col: 金额列名
            time_col: 时间列名

        Returns:
            包含风险指标特征的数据框
        """
        df_features = df.copy()
        df_features = df_features.sort_values(time_col).reset_index(drop=True)

        # 11.1 最大回撤
        if 'max_drawdown' in config.risk_indicators:
            for window in config.risk_windows:
                rolling_max = df_features[price_col].rolling(window=window, min_periods=1).max()
                drawdown = (df_features[price_col] - rolling_max) / (rolling_max + 1e-8)
                max_drawdown = drawdown.rolling(window=window, min_periods=1).min()
                df_features[f'max_drawdown_{window}'] = max_drawdown

        # 11.2 夏普比率
        if 'sharpe_ratio' in config.risk_indicators:
            for window in config.risk_windows:
                returns = df_features[price_col].pct_change().fillna(0)
                excess_return = returns - 0.02/252  # 假设无风险利率2%
                rolling_sharpe = excess_return.rolling(window=window, min_periods=1).mean() / \
                               (excess_return.rolling(window=window, min_periods=1).std() + 1e-8)
                df_features[f'sharpe_ratio_{window}'] = rolling_sharpe * np.sqrt(252)

        # 11.3 VaR
        if 'VaR' in config.risk_indicators:
            for window in config.risk_windows:
                returns = df_features[price_col].pct_change().fillna(0)
                var_95 = returns.rolling(window=window, min_periods=1).quantile(0.05)
                var_99 = returns.rolling(window=window, min_periods=1).quantile(0.01)
                df_features[f'VaR_95_{window}'] = var_95
                df_features[f'VaR_99_{window}'] = var_99

        # 11.4 偏度和峰度
        if 'skewness_kurtosis' in config.risk_indicators:
            for window in config.risk_windows:
                returns = df_features[price_col].pct_change().fillna(0)
                rolling_skew = returns.rolling(window=window, min_periods=1).skew()
                rolling_kurt = returns.rolling(window=window, min_periods=1).kurt()
                df_features[f'skewness_{window}'] = rolling_skew.fillna(0)
                df_features[f'kurtosis_{window}'] = rolling_kurt.fillna(0)

        pc.log("已计算风险指标特征")
        return df_features

    @staticmethod
    def feature_selection_and_reduction(df: pd.DataFrame, config: FeatureConfig,
                                      identity_cols: List[str] = None, price_col: str = 'AMT',
                                      time_col: str = 'DT_TIME') -> Tuple[pd.DataFrame, List[str]]:
        """
        特征选择和降维：相关性过滤、方差阈值、互信息、PCA、RFE

        Args:
            df: 输入数据框
            config: 特征配置
            identity_cols: 标识列列表
            price_col: 价格列名
            time_col: 时间列名

        Returns:
            (处理后的数据框, 选择的特征列表)
        """
        if identity_cols is None:
            identity_cols = []

        df_features = df.copy()
        exclude_cols = identity_cols + [time_col]
        feature_cols = [col for col in df_features.columns if col not in exclude_cols and
                       df_features[col].dtype in ['int64', 'float64']]

        pc.log(f"开始特征选择和降维，共有{len(feature_cols)}个数值特征")

        # 12.1 方差阈值过滤
        if len(feature_cols) > 0:
            X = df_features[feature_cols].fillna(0)
            X_clean = X.copy()

            for col in X.columns:
                X_clean[col] = X_clean[col].replace([np.inf, -np.inf], 0)
                col_max = X_clean[col].max()
                col_min = X_clean[col].min()
                if col_max > 1e10:
                    X_clean[col] = X_clean[col].clip(upper=1e10)
                if col_min < -1e10:
                    X_clean[col] = X_clean[col].clip(lower=-1e10)

            if np.any(np.isinf(X_clean.values)) or np.any(np.isnan(X_clean.values)):
                X_clean = X_clean.replace([np.inf, -np.inf, np.nan], 0)

            variance_threshold = 0.0001
            selector = VarianceThreshold(threshold=variance_threshold)
            X_var_filtered = selector.fit_transform(X_clean)
            var_selected_features = [feature_cols[i] for i in range(len(feature_cols))
                                   if selector.get_support()[i]]
            pc.log(f"方差阈值过滤：{len(feature_cols)} -> {len(var_selected_features)}个特征")

            # 12.2 相关性过滤
            if len(var_selected_features) > 1:
                corr_data = df_features[var_selected_features].copy()
                for col in var_selected_features:
                    corr_data[col] = corr_data[col].replace([np.inf, -np.inf], 0)

                corr_matrix = corr_data.corr().abs()
                high_corr_pairs = []
                threshold = 0.95

                for i in range(len(corr_matrix.columns)):
                    for j in range(i+1, len(corr_matrix.columns)):
                        if corr_matrix.iloc[i, j] > threshold:
                            high_corr_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j],
                                                 corr_matrix.iloc[i, j]))

                features_to_remove = set()
                for col1, col2, corr_value in high_corr_pairs:
                    if df_features[col1].var() < df_features[col2].var():
                        features_to_remove.add(col1)
                    else:
                        features_to_remove.add(col2)

                corr_selected_features = [col for col in var_selected_features
                                        if col not in features_to_remove]
                pc.log(f"相关性过滤：{len(var_selected_features)} -> {len(corr_selected_features)}个特征")
            else:
                corr_selected_features = var_selected_features

            # 12.3 统计特征选择
            if len(corr_selected_features) > 0 and price_col in df_features.columns:
                try:
                    X_selected = X_clean[corr_selected_features]
                    y = df_features[price_col].fillna(0).replace([np.inf, -np.inf], 0)
                    y = y.clip(-1e10, 1e10)

                    if y.std() == 0:
                        pc.log("警告：目标变量方差为0，跳过统计特征选择")
                        f_selected_features = corr_selected_features
                    else:
                        def safe_f_regression(X, y):
                            from sklearn.feature_selection import f_regression
                            try:
                                non_constant_mask = X.var(axis=0) > 1e-10
                                X_filtered = X.iloc[:, non_constant_mask]
                                if X_filtered.shape[1] == 0:
                                    return np.zeros(X.shape[1]), np.zeros(X.shape[1])
                                F, p = f_regression(X_filtered, y)
                                full_scores = np.zeros(X.shape[1])
                                full_pvalues = np.ones(X.shape[1])
                                full_scores[non_constant_mask] = F
                                full_pvalues[non_constant_mask] = p
                                return full_scores, full_pvalues
                            except:
                                return X.var(), np.ones(X.shape[1])

                        k_best = min(50, len(corr_selected_features))
                        selector_f = SelectKBest(score_func=safe_f_regression, k=k_best)
                        X_f_selected = selector_f.fit_transform(X_selected, y)
                        f_selected_features = [corr_selected_features[i] for i in range(len(corr_selected_features))
                                             if selector_f.get_support()[i]]
                        pc.log(f"统计特征选择：{len(corr_selected_features)} -> {len(f_selected_features)}个特征")
                except Exception as e:
                    pc.log(f"特征选择过程中出现错误: {e}")
                    f_selected_features = corr_selected_features
            else:
                f_selected_features = corr_selected_features

            # 12.4 PCA降维
            if len(f_selected_features) > 20:
                try:
                    def safe_standardize(X):
                        X_scaled = np.zeros_like(X)
                        for i in range(X.shape[1]):
                            col_data = X[:, i]
                            if col_data.std() > 1e-10:
                                X_scaled[:, i] = (col_data - col_data.mean()) / col_data.std()
                            else:
                                X_scaled[:, i] = col_data - col_data.mean()
                        return X_scaled

                    X_for_pca = X_clean[f_selected_features].values
                    X_scaled = safe_standardize(X_for_pca)

                    n_components = min(15, len(f_selected_features))
                    pca = PCA(n_components=n_components)
                    X_pca = pca.fit_transform(X_scaled)

                    for i in range(n_components):
                        df_features[f'pca_component_{i+1}'] = X_pca[:, i]

                    explained_variance = pca.explained_variance_ratio_
                    pc.log(f"PCA降维：{len(f_selected_features)} -> {n_components}个主成分")
                except Exception as e:
                    pc.log(f"PCA降维失败: {e}")

            final_features = f_selected_features
        else:
            final_features = []

        pc.log(f"步骤12完成，最终保留{len(final_features)}个特征")
        return df_features, final_features

    @staticmethod
    def calculate_selected_features(df: pd.DataFrame,
                                   selected_features: List[str],
                                   config: FeatureConfig = None,
                                   identity_cols: List[str] = None,
                                   time_col: str = 'DT_TIME',
                                   price_col: str = 'AMT',
                                   balance_col: str = 'ACCBAL') -> pd.DataFrame:
        """
        根据指定的特征列表选择性计算特征，跳过不需要的特征以节省计算时间

        Args:
            df: 输入数据框
            selected_features: 需要计算的特征列表
            config: 特征配置，如果为None则使用默认配置
            identity_cols: 身份列列表
            time_col: 时间列名
            price_col: 价格列名
            balance_col: 余额列名

        Returns:
            包含计算的特征的数据框

        Raises:
            ValueError: 如果特征列表为空或包含无效特征
        """
        if config is None:
            config = FeatureConfig()

        if not selected_features:
            raise ValueError("特征列表不能为空")

        pc.log(f"开始计算指定的 {len(selected_features)} 个特征...")

        # 使用现有的映射方法确定需要计算的特征类别
        feature_mapping = FeatureMapper.map_features_to_indicators(selected_features)

        # 根据特征映射动态调整配置
        if 'risk_windows' in feature_mapping and feature_mapping['risk_windows']:
            config.risk_windows = list(set(feature_mapping['risk_windows']))  # 去重
        if 'moving_windows' in feature_mapping and feature_mapping['moving_windows']:
            config.moving_windows = list(set(feature_mapping['moving_windows']))  # 去重
        if 'rsi_periods' in feature_mapping and feature_mapping['rsi_periods']:
            config.rsi_periods = list(set(feature_mapping['rsi_periods']))  # 去重

        current_df = df.copy()
        calculated_features = set()

        # 基础价格特征
        basic_patterns = ['price_change_rate', 'log_return', 'price_amplitude', 'opening_gap', 'price_position']
        if any(any(pattern in feature for pattern in basic_patterns) for feature in selected_features):
            pc.log("计算基础价格特征...")
            current_df = FeatureEngineeringPipeline.calculate_basic_price_features(
                current_df, config, identity_cols=identity_cols, time_col=time_col)
            calculated_features.update(basic_patterns)

        # 移动窗口特征
        moving_patterns = ['MA_', 'EMA_', 'STD_', 'MAX_', 'MIN_', 'Q25_', 'Q50_', 'Q75_', 'IQR_', 'CV_', 'Price_vs_MA_', 'Price_ZScore_']
        if any(any(pattern in feature for pattern in moving_patterns) for feature in selected_features):
            pc.log("计算移动窗口特征...")
            current_df = FeatureEngineeringPipeline.calculate_moving_window_features(current_df, config)
            calculated_features.update(moving_patterns)

        # 动量指标
        momentum_patterns = ['RSI_', 'MACD', 'Momentum_', 'ROC_']
        if any(any(pattern in feature for pattern in momentum_patterns) for feature in selected_features):
            pc.log("计算动量指标...")
            current_df = FeatureEngineeringPipeline.calculate_momentum_indicators(current_df, config)
            calculated_features.update(momentum_patterns)

        # 波动率特征
        volatility_patterns = ['Historical_Volatility_', 'ATR_', 'Parkinson_Volatility_', 'Garman_Klass_Volatility_']
        if any(any(pattern in feature for pattern in volatility_patterns) for feature in selected_features):
            pc.log("计算波动率特征...")
            current_df = FeatureEngineeringPipeline.calculate_volatility_features(current_df, config)
            calculated_features.update(volatility_patterns)

        # 成交量特征
        volume_patterns = ['volume_change_rate', 'VMA_', 'VEMA_', 'Price_Volume_Corr_', 'VWAP_', 'OBV']
        if any(any(pattern in feature for pattern in volume_patterns) for feature in selected_features):
            pc.log("计算成交量特征...")
            current_df = FeatureEngineeringPipeline.calculate_volume_features(
                current_df, config, price_col=price_col, volume_proxy_col=price_col)
            calculated_features.update(volume_patterns)

        # 技术形态特征
        technical_patterns = ['Resistance_Level_', 'Support_Level_', 'Price_Position_', 'Bollinger_', 'Williams_R_']
        if any(any(pattern in feature for pattern in technical_patterns) for feature in selected_features):
            pc.log("计算技术形态特征...")
            current_df = FeatureEngineeringPipeline.calculate_technical_pattern_features(current_df, config, price_col=price_col)
            calculated_features.update(technical_patterns)

        # 时间特征
        time_patterns = ['hour', 'minute', 'day_of_week', 'month', 'is_weekend', 'is_month_start', 'is_month_end', '_sin', '_cos', 'quarter', 'week_of_year']
        if any(any(pattern in feature for pattern in time_patterns) for feature in selected_features):
            pc.log("计算时间特征...")
            current_df = FeatureEngineeringPipeline.calculate_time_features(current_df, config, date_col=time_col)
            calculated_features.update(time_patterns)

        # 滞后特征
        lag_patterns = ['_lag_', 'lag_return_']
        if any(any(pattern in feature for pattern in lag_patterns) for feature in selected_features):
            pc.log("计算滞后特征...")
            current_df = FeatureEngineeringPipeline.calculate_lag_features(
                current_df, config, price_col=price_col, balance_col=balance_col, time_col=time_col)
            calculated_features.update(lag_patterns)

        # 高阶特征
        high_order_patterns = ['_derivative', '_corr_', '_beta_', '_zscore_']
        if any(any(pattern in feature for pattern in high_order_patterns) for feature in selected_features):
            pc.log("计算高阶特征...")
            current_df = FeatureEngineeringPipeline.calculate_high_order_features(
                current_df, config, price_col=price_col, balance_col=balance_col, time_col=time_col)
            calculated_features.update(high_order_patterns)

        # 风险特征
        risk_patterns = ['max_drawdown_', 'sharpe_ratio_', 'calmar_ratio_', 'VaR_', 'skewness_', 'kurtosis_']
        if any(any(pattern in feature for pattern in risk_patterns) for feature in selected_features):
            pc.log("计算风险特征...")
            current_df = FeatureEngineeringPipeline.calculate_risk_features(
                current_df, config, price_col=price_col, balance_col=balance_col, time_col=time_col)
            calculated_features.update(risk_patterns)

        # 验证所有请求的特征都已计算
        missing_features = []
        available_features = set(current_df.columns)

        for feature in selected_features:
            if feature not in available_features:
                missing_features.append(feature)

        if missing_features:
            pc.log(f"警告: 以下特征未能成功计算: {missing_features}")

        # 只返回请求的特征和身份列
        if identity_cols:
            result_cols = identity_cols + [f for f in selected_features if f in available_features]
        else:
            result_cols = [f for f in selected_features if f in available_features]

        result_df = current_df[result_cols].copy()

        pc.log(f"选择性特征计算完成，计算了 {len([f for f in selected_features if f in available_features])}/{len(selected_features)} 个特征")

        return result_df

class TimingManager:
    """耗时统计管理器"""

    def __init__(self):
        self.timings = {}
        self.start_time = None

    def start_timer(self, name: str):
        """开始计时"""
        self.start_time = time.time()
        self.timings[name] = {'start': self.start_time, 'end': None, 'duration': None}

    def end_timer(self, name: str) -> float:
        """结束计时并返回耗时"""
        if name in self.timings and self.timings[name]['end'] is None:
            end_time = time.time()
            self.timings[name]['end'] = end_time
            self.timings[name]['duration'] = end_time - self.timings[name]['start']
            return self.timings[name]['duration']
        return 0.0

    def get_timing(self, name: str) -> Optional[float]:
        """获取指定步骤的耗时"""
        if name in self.timings and self.timings[name]['duration'] is not None:
            return self.timings[name]['duration']
        return None

    def get_all_timings(self) -> Dict[str, float]:
        """获取所有步骤的耗时"""
        return {name: info['duration'] for name, info in self.timings.items()
                if info['duration'] is not None}

    def print_summary(self):
        """打印耗时统计摘要"""
        timings = self.get_all_timings()
        if not timings:
            pc.log("没有耗时统计信息")
            return

        total_time = sum(timings.values())
        pc.log("=" * 60)
        pc.log("耗时统计摘要")
        pc.log("=" * 60)

        for name, duration in timings.items():
            percentage = (duration / total_time) * 100 if total_time > 0 else 0
            pc.log(f"{name:30s}: {duration:8.2f}s ({percentage:5.1f}%)")

        pc.log("-" * 60)
        pc.log(f"{'总耗时':30s}: {total_time:8.2f}s (100.0%)")
        pc.log("=" * 60)


def load_and_prepare_data(data_file: str = "/ai/wks/leadingtek/scripts/tra11.csv") -> Tuple[pd.DataFrame, Dict]:
    """
    加载和准备数据，包括CSV读取和数据类型转换

    Args:
        data_file: 数据文件路径

    Returns:
        (处理后的数据框, 数据配置信息)

    Returns包含的数据配置信息:
        - identity: 身份列列表
        - num_type: 数值类型列列表
        - date_type: 日期类型列列表
        - time_col: 时间列名
        - cols: 所有使用的列列表
    """
    # 定义数据配置
    identity = ['ACCT_NUM','PARTY_ID','OPP_PARTY_ID','ACCT','TCAC','TSTM']
    cols = ['ACCT_NUM','PARTY_ID','OPP_PARTY_ID','ACCT','TCAC','TSTM', 'DT_TIME', 'PARTY_CLASS_CD',
            'CCY', 'AMT', 'AMT_VAL','CNY_AMT','ACCBAL', 'DEBIT_CREDIT','CASH_FLAG', 'OPP_ORGANKEY',
            'OACCTT', 'OTBKAC', 'CHANNEL', 'RMKS', 'CBCDIR', 'AMTFLG', 'BALFLG', 'RMKCDE', 'TDDS',
            'RCDTYP', 'CCY_A', 'INTAMT_A', 'INTRAT_A', 'PBKTYP', 'CNT_CST_TYPE', 'CNT_INBANK_TYPE',
            'CFRC_COUNTRY', 'CFRC_AREA', 'TRCD_AREA', 'TRCD_COUNTRY', 'TXTPCD', 'RCVPAYFLG', 'SYS_FLAG',
            'TXN_CHNL_TP_ID', 'FLAG', 'OVERAREA_IND']
    num_type = ['AMT', 'AMT_VAL','CNY_AMT','ACCBAL','INTAMT_A', 'INTRAT_A']
    date_type = ['DT_TIME']
    time_col = 'DT_TIME'

    pc.log(f"开始加载数据文件: {data_file}")

    # 加载CSV数据
    df = pd.read_csv(data_file, usecols=cols)
    df = df[cols]  # 确保列顺序一致

    # 数据类型转换
    from tpf.data.deal import Data2Feature as dtf
    df_processed = dtf.data_type_change(df, num_type=num_type, date_type=date_type)

    pc.log(f"数据加载完成，数据维度: {df_processed.shape}")

    # 准备数据配置信息
    data_config = {
        'identity': identity,
        'num_type': num_type,
        'date_type': date_type,
        'time_col': time_col,
        'cols': cols
    }

    return df_processed, data_config


def normalize_data(df: pd.DataFrame, data_config: Dict) -> pd.DataFrame:
    """
    对数据进行预处理和归一化

    Args:
        df: 输入数据框
        data_config: 数据配置信息，包含身份列、数值类型列等

    Returns:
        预处理后的数据框
    """
    pc.log("开始数据预处理和归一化...")

    # 提取配置信息
    identity = data_config['identity']
    num_type = data_config['num_type']
    date_type = data_config['date_type']
    time_col = data_config['time_col']

    # 执行预处理
    df_preprocessed = FeatureEngineeringPipeline.preprocess_data(
        df, identity, num_type, date_type[0])

    pc.log(f"数据预处理完成，数据维度: {df_preprocessed.shape}")

    return df_preprocessed


# 示例：如何独立使用数据加载和预处理方法
def example_usage():
    """
    示例：展示如何独立使用数据加载和预处理方法
    """
    # 1. 独立加载数据
    df_processed, data_config = load_and_prepare_data()
    print(f"加载数据完成，维度: {df_processed.shape}")

    # 2. 独立进行数据预处理
    df_preprocessed = normalize_data(df_processed, data_config)
    print(f"预处理完成，维度: {df_preprocessed.shape}")

    # 3. 提取配置信息
    identity_cols = data_config['identity']
    time_col = data_config['time_col']

    print(f"身份列: {identity_cols}")
    print(f"时间列: {time_col}")

    return df_preprocessed, data_config


def prepare_data_for_feature_calculation(config: FeatureConfig = None,
                                         data_file: str = "/ai/wks/leadingtek/scripts/tra11.csv") -> Tuple[pd.DataFrame, Dict, TimingManager]:
    """
    数据准备方法：负责pandas数据读取、类型转换、归一化等数据预处理工作
    该方法返回预处理完成的数据框，供后续的特征计算方法使用

    Args:
        config: 特征配置，如果为None则使用默认配置
        data_file: 数据文件路径

    Returns:
        (预处理后的数据框, 数据配置信息, 计时管理器)

    Returns包含的数据配置信息:
        - identity: 身份列列表
        - num_type: 数值类型列列表
        - date_type: 日期类型列列表
        - time_col: 时间列名
        - cols: 所有使用的列列表
    """
    if config is None:
        config = FeatureConfig()

    timer = TimingManager()

    # 数据加载
    timer.start_timer("数据加载")
    df_processed, data_config = load_and_prepare_data(data_file)
    timer.end_timer("数据加载")

    # 数据预处理
    timer.start_timer("数据预处理")
    df_preprocessed = normalize_data(df_processed, data_config)
    timer.end_timer("数据预处理")

    return df_preprocessed, data_config, timer


def run_feature_pipeline_with_timing(config: FeatureConfig = None,
                                   selected_features: List[str] = None,
                                   selected_feature_save_file=None,
                                   df_preprocessed: pd.DataFrame = None,
                                   data_config: Dict = None,
                                   timer: TimingManager = None) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    特征指标计算方法：专门负责各种特征指标的计算
    可以接收预处理后的数据框，或自行进行数据准备

    Args:
        config: 特征配置，如果为None则使用默认配置
        selected_features: 指定要计算的特征列表，如果为None则计算所有特征
        selected_feature_save_file: 特征保存文件路径
        df_preprocessed: 预处理后的数据框（可选）
        data_config: 数据配置信息（可选）
        timer: 计时管理器（可选）

    Returns:
        (最终数据框, 耗时统计)
    """
    # 如果没有提供预处理的数据，则进行数据准备
    if df_preprocessed is None:
        df_preprocessed, data_config, timer = prepare_data_for_feature_calculation(config)
    else:
        # 提供了预处理数据，但需要检查其他参数
        if data_config is None:
            raise ValueError("如果提供了df_preprocessed，则必须提供data_config")
        if timer is None:
            timer = TimingManager()

    # 从配置中提取所需信息
    identity = data_config['identity']
    time_col = data_config['time_col']

    # 根据selected_features决定计算哪些特征
    current_df = df_preprocessed

    # 基础价格特征
    if selected_features is None or any(name in selected_features for name in ['price', 'basic']):
        timer.start_timer("基础价格特征")
        current_df = FeatureEngineeringPipeline.calculate_basic_price_features(
            current_df, config, identity_cols=identity, time_col=time_col)
        timer.end_timer("基础价格特征")

    # 移动窗口特征
    if selected_features is None or any(name in selected_features for name in ['moving', 'window']):
        timer.start_timer("移动窗口特征")
        current_df = FeatureEngineeringPipeline.calculate_moving_window_features(current_df, config)
        timer.end_timer("移动窗口特征")

    # 动量指标
    if selected_features is None or any(name in selected_features for name in ['momentum']):
        timer.start_timer("动量指标")
        current_df = FeatureEngineeringPipeline.calculate_momentum_indicators(current_df, config)
        timer.end_timer("动量指标")

    # 波动率特征
    if selected_features is None or any(name in selected_features for name in ['volatility']):
        timer.start_timer("波动率特征")
        current_df = FeatureEngineeringPipeline.calculate_volatility_features(current_df, config)
        timer.end_timer("波动率特征")

    # 成交量特征
    if selected_features is None or any(name in selected_features for name in ['volume']):
        timer.start_timer("成交量特征")
        current_df = FeatureEngineeringPipeline.calculate_volume_features(current_df, config)
        timer.end_timer("成交量特征")

    # 技术形态特征
    if selected_features is None or any(name in selected_features for name in ['technical']):
        timer.start_timer("技术形态特征")
        current_df = FeatureEngineeringPipeline.calculate_technical_pattern_features(current_df, config)
        timer.end_timer("技术形态特征")

    # 时间特征
    if selected_features is None or any(name in selected_features for name in ['time']):
        timer.start_timer("时间特征")
        current_df = FeatureEngineeringPipeline.calculate_time_features(current_df, config)
        timer.end_timer("时间特征")

    # 滞后特征
    if selected_features is None or any(name in selected_features for name in ['lag']):
        timer.start_timer("滞后特征")
        current_df = FeatureEngineeringPipeline.calculate_lag_features(current_df, config, time_col=time_col)
        timer.end_timer("滞后特征")

    # 高阶特征
    if selected_features is None or any(name in selected_features for name in ['high_order', 'higher']):
        timer.start_timer("高阶特征")
        current_df = FeatureEngineeringPipeline.calculate_high_order_features(current_df, config, time_col=time_col)
        timer.end_timer("高阶特征")

    # 风险特征
    if selected_features is None or any(name in selected_features for name in ['risk']):
        timer.start_timer("风险特征")
        current_df = FeatureEngineeringPipeline.calculate_risk_features(current_df, config, time_col=time_col)
        timer.end_timer("风险特征")

    # 特征选择和降维
    if selected_features is None:
        timer.start_timer("特征选择和降维.....................")
        df_final, selected = FeatureEngineeringPipeline.feature_selection_and_reduction(
            current_df, config, identity, time_col=time_col)
        pc.log("特征选择和降维完成........................................")
        pc.log(f"特征选择和降维完成，选择的特征数量: {len(selected)}")
        pc.log(f"特征选择和降维完成，选择的特征: \n{selected}")
        if selected_feature_save_file:
            df_feature_selected = df_final[identity+selected]
            df_feature_selected.to_csv(selected_feature_save_file,index=False)
            pc.log(f"特征选择和降维完成，选择的特征保存于: {selected_feature_save_file}")

            # 使用joblib保存选择的特征名称到单独的文件
            import joblib
            feature_list_file = selected_feature_save_file.replace('.csv', '_features.joblib')
            feature_data = {
                'selected_features': selected,
                'feature_count': len(selected),
                'identity_columns': identity
            }
            joblib.dump(feature_data, feature_list_file)
            pc.log(f"选择的特征列表已通过joblib保存至: {feature_list_file}")
        timer.end_timer("特征选择和降维......................")
    else:
        df_final = current_df
        selected = selected_features

    # 保存结果
    timer.start_timer("结果保存")
    output_file = "/ai/wks/leadingtek/scripts/tra11_features_optimized.csv"
    df_final.to_csv(output_file, index=False)
    pc.log(f"特征工程结果已保存到: {output_file}")
    timer.end_timer("结果保存")

    # 打印统计信息
    pc.log("=" * 50)
    pc.log("特征生成完成统计")
    pc.log("=" * 50)
    pc.log(f"预处理数据维度: {df_preprocessed.shape}")
    pc.log(f"最终数据维度: {df_final.shape}")
    pc.log(f"生成特征总数: {df_final.shape[1] - df_preprocessed.shape[1]}")
    pc.log(f"选择的特征数量: {len(selected)}")

    # 打印耗时统计
    timer.print_summary()

    return df_final, timer.get_all_timings()

class FeatureMapper:
    """特征映射器，用于根据特征名称推断需要计算的指标"""

    @staticmethod
    def map_features_to_indicators(selected_feature_names: List[str]) -> Dict[str, List[str]]:
        """
        将选择的特征名称映射到需要计算的指标

        Args:
            selected_feature_names: 选择的特征名称列表

        Returns:
            包含需要计算的指标类别的字典
        """
        # 定义基础数据字段（不需要计算的原始数据）
        raw_data_fields = {
            'patterns': ['AMT', 'AMT_VAL', 'CNY_AMT', 'ACCBAL', 'INTAMT_A', 'INTRAT_A'],
            'indicators': []  # 原始数据，不需要计算
        }

        # 定义标准化字段（在预处理中生成的）
        scaled_fields = {
            'patterns': ['AMT_scaled', 'AMT_VAL_scaled', 'CNY_AMT_scaled', 'ACCBAL_scaled', 'INTAMT_A_scaled', 'INTRAT_A_scaled'],
            'indicators': []  # 预处理生成，不需要单独计算
        }

        # 定义中间计算字段（在特征计算过程中自动生成）
        intermediate_fields = {
            'patterns': ['price_high', 'price_low', 'time_diff', 'is_jump'],
            'indicators': []  # 中间字段，不需要单独计算
        }

        # 定义特征名称模式到指标类别的映射
        mapping_rules = {
            'basic_features': {
                'patterns': ['price_change_rate', 'log_return', 'price_amplitude', 'opening_gap', 'price_position'],
                'indicators': ['price_change_rate', 'log_return', 'price_amplitude', 'opening_gap', 'price_position']
            },
            'moving_features': {
                'patterns': ['MA_', 'EMA_', 'STD_', 'MAX_', 'MIN_', 'Q25_', 'Q50_', 'Q75_', 'IQR_', 'CV_', 'Price_vs_MA_', 'Price_ZScore_'],
                'indicators': ['MA', 'EMA', 'STD', 'MAX', 'MIN', 'Q25', 'Q50', 'Q75', 'IQR', 'CV', 'Price_vs_MA', 'Price_ZScore']
            },
            'momentum_features': {
                'patterns': ['RSI_', 'MACD', 'Momentum_', 'ROC_'],
                'indicators': ['RSI', 'MACD', 'Momentum', 'Rate_of_Change']
            },
            'volatility_features': {
                'patterns': ['Historical_Volatility_', 'ATR_', 'Parkinson_Volatility_', 'Garman_Klass_Volatility_'],
                'indicators': ['Historical_Volatility', 'ATR', 'Parkinson', 'Garman_Klass']
            },
            'volume_features': {
                'patterns': ['volume_change_rate', 'VMA_', 'VEMA_', 'Price_Volume_Corr_', 'VWAP_', 'OBV'],
                'indicators': ['volume_change_rate', 'VMA', 'VEMA', 'price_volume_corr', 'VWAP', 'OBV']
            },
            'technical_features': {
                'patterns': ['Resistance_Level_', 'Support_Level_', 'Price_Position_', 'Bollinger_', 'Williams_R_'],
                'indicators': ['Support_Resistance', 'Bollinger_Position', 'Williams_R']
            },
            'time_features': {
                'patterns': ['hour', 'minute', 'day_of_week', 'month', 'is_weekend', 'is_month_start', 'is_month_end', '_sin', '_cos', 'quarter', 'week_of_year'],
                'indicators': ['hour', 'minute', 'day_of_week', 'month', 'is_weekend', 'is_month_start', 'is_month_end', 'time_sin_cos', 'seasonal']
            },
            'lag_features': {
                'patterns': ['_lag_', 'lag_return_'],
                'indicators': ['lag_columns']  # 这需要特殊处理
            },
            'high_order_features': {
                'patterns': ['_derivative', '_corr_', '_beta_', '_zscore_'],
                'indicators': ['derivatives', 'rolling_corr', 'rolling_beta', 'z_score_normalize']
            },
            'risk_features': {
                'patterns': ['max_drawdown_', 'sharpe_ratio_', 'calmar_ratio_', 'VaR_', 'skewness_', 'kurtosis_'],
                'indicators': ['max_drawdown', 'sharpe_ratio', 'calmar_ratio', 'VaR', 'skewness_kurtosis']
            }
        }

        required_indicators = {}
        required_windows = {}
        required_periods = {}
        required_columns = {}

        for feature_name in selected_feature_names:
            feature_matched = False

            # 首先检查是否为原始数据字段（不需要计算）
            if any(pattern in feature_name for pattern in raw_data_fields['patterns']):
                if feature_name in raw_data_fields['patterns']:
                    feature_matched = True
                    pc.log(f"信息：'{feature_name}' 是原始数据字段，无需计算")
                continue

            # 检查是否为标准化字段（预处理中自动生成）
            if any(pattern in feature_name for pattern in scaled_fields['patterns']):
                if feature_name in scaled_fields['patterns']:
                    feature_matched = True
                    pc.log(f"信息：'{feature_name}' 是标准化字段，在预处理中自动生成")
                continue

            # 检查是否为中间计算字段（特征计算过程中自动生成）
            if any(pattern in feature_name for pattern in intermediate_fields['patterns']):
                if feature_name in intermediate_fields['patterns']:
                    feature_matched = True
                    pc.log(f"信息：'{feature_name}' 是中间计算字段，在特征计算过程中自动生成")
                continue

            # 检查每个特征类别
            for category, rules in mapping_rules.items():
                if any(pattern in feature_name for pattern in rules['patterns']):
                    feature_matched = True
                    if category not in required_indicators:
                        required_indicators[category] = []

                    # 提取特定的窗口、周期等参数
                    if category == 'moving_features':
                        if 'MA_' in feature_name:
                            required_indicators[category].append('MA')
                            window = FeatureMapper._extract_window_number(feature_name)
                            if window:
                                if 'moving_windows' not in required_windows:
                                    required_windows['moving_windows'] = []
                                required_windows['moving_windows'].append(window)
                        elif 'EMA_' in feature_name:
                            required_indicators[category].append('EMA')
                            window = FeatureMapper._extract_window_number(feature_name)
                            if window:
                                if 'moving_windows' not in required_windows:
                                    required_windows['moving_windows'] = []
                                required_windows['moving_windows'].append(window)
                        elif 'STD_' in feature_name:
                            required_indicators[category].append('STD')
                            window = FeatureMapper._extract_window_number(feature_name)
                            if window:
                                if 'moving_windows' not in required_windows:
                                    required_windows['moving_windows'] = []
                                required_windows['moving_windows'].append(window)
                        elif 'MAX_' in feature_name or 'MIN_' in feature_name:
                            if 'MAX_' in feature_name:
                                required_indicators[category].append('MAX')
                            if 'MIN_' in feature_name:
                                required_indicators[category].append('MIN')
                            window = FeatureMapper._extract_window_number(feature_name)
                            if window:
                                if 'moving_windows' not in required_windows:
                                    required_windows['moving_windows'] = []
                                required_windows['moving_windows'].append(window)
                        elif 'Q' in feature_name and '_' in feature_name.split('Q')[1]:
                            required_indicators[category].extend(['Q25', 'Q50', 'Q75'])
                            window = FeatureMapper._extract_window_number(feature_name)
                            if window:
                                if 'moving_windows' not in required_windows:
                                    required_windows['moving_windows'] = []
                                required_windows['moving_windows'].append(window)
                        elif 'IQR_' in feature_name:
                            required_indicators[category].append('IQR')
                            window = FeatureMapper._extract_window_number(feature_name)
                            if window:
                                if 'moving_windows' not in required_windows:
                                    required_windows['moving_windows'] = []
                                required_windows['moving_windows'].append(window)
                        elif 'CV_' in feature_name:
                            required_indicators[category].append('CV')
                            window = FeatureMapper._extract_window_number(feature_name)
                            if window:
                                if 'moving_windows' not in required_windows:
                                    required_windows['moving_windows'] = []
                                required_windows['moving_windows'].append(window)
                        elif 'Price_vs_MA_' in feature_name:
                            required_indicators[category].append('Price_vs_MA')
                            window = FeatureMapper._extract_window_number(feature_name)
                            if window:
                                if 'moving_windows' not in required_windows:
                                    required_windows['moving_windows'] = []
                                required_windows['moving_windows'].append(window)
                        elif 'Price_ZScore_' in feature_name:
                            required_indicators[category].append('Price_ZScore')
                            window = FeatureMapper._extract_window_number(feature_name)
                            if window:
                                if 'moving_windows' not in required_windows:
                                    required_windows['moving_windows'] = []
                                required_windows['moving_windows'].append(window)

                    elif category == 'momentum_features':
                        if 'RSI_' in feature_name:
                            required_indicators[category].append('RSI')
                            period = FeatureMapper._extract_window_number(feature_name)
                            if period:
                                if 'rsi_periods' not in required_periods:
                                    required_periods['rsi_periods'] = []
                                required_periods['rsi_periods'].append(period)
                        elif 'MACD' in feature_name:
                            required_indicators[category].append('MACD')
                        elif 'Momentum_' in feature_name:
                            required_indicators[category].append('Momentum')
                            period = FeatureMapper._extract_window_number(feature_name)
                            if period:
                                if 'momentum_periods' not in required_periods:
                                    required_periods['momentum_periods'] = []
                                required_periods['momentum_periods'].append(period)
                        elif 'ROC_' in feature_name:
                            required_indicators[category].append('Rate_of_Change')
                            period = FeatureMapper._extract_window_number(feature_name)
                            if period:
                                if 'roc_periods' not in required_periods:
                                    required_periods['roc_periods'] = []
                                required_periods['roc_periods'].append(period)

                    elif category == 'volatility_features':
                        if 'Historical_Volatility_' in feature_name:
                            required_indicators[category].append('Historical_Volatility')
                            period = FeatureMapper._extract_window_number(feature_name)
                            if period:
                                if 'volatility_periods' not in required_periods:
                                    required_periods['volatility_periods'] = []
                                required_periods['volatility_periods'].append(period)
                        elif 'ATR_' in feature_name:
                            required_indicators[category].append('ATR')
                            period = FeatureMapper._extract_window_number(feature_name)
                            if period:
                                if 'volatility_periods' not in required_periods:
                                    required_periods['volatility_periods'] = []
                                required_periods['volatility_periods'].append(period)
                        elif 'Parkinson_Volatility_' in feature_name:
                            required_indicators[category].append('Parkinson')
                            period = FeatureMapper._extract_window_number(feature_name)
                            if period:
                                if 'volatility_periods' not in required_periods:
                                    required_periods['volatility_periods'] = []
                                required_periods['volatility_periods'].append(period)
                        elif 'Garman_Klass_Volatility_' in feature_name:
                            required_indicators[category].append('Garman_Klass')
                            period = FeatureMapper._extract_window_number(feature_name)
                            if period:
                                if 'volatility_periods' not in required_periods:
                                    required_periods['volatility_periods'] = []
                                required_periods['volatility_periods'].append(period)

                    elif category == 'volume_features':
                        if 'volume_change_rate' in feature_name:
                            required_indicators[category].append('volume_change_rate')
                        elif 'VMA_' in feature_name or 'VEMA_' in feature_name:
                            if 'VMA_' in feature_name:
                                required_indicators[category].append('VMA')
                            if 'VEMA_' in feature_name:
                                required_indicators[category].append('VEMA')
                            window = FeatureMapper._extract_window_number(feature_name)
                            if window:
                                if 'volume_windows' not in required_windows:
                                    required_windows['volume_windows'] = []
                                required_windows['volume_windows'].append(window)
                        elif 'Price_Volume_Corr_' in feature_name:
                            required_indicators[category].append('price_volume_corr')
                            window = FeatureMapper._extract_window_number(feature_name)
                            if window:
                                if 'volume_windows' not in required_windows:
                                    required_windows['volume_windows'] = []
                                required_windows['volume_windows'].append(window)
                        elif 'VWAP_' in feature_name:
                            required_indicators[category].append('VWAP')
                            window = FeatureMapper._extract_window_number(feature_name)
                            if window:
                                if 'volume_windows' not in required_windows:
                                    required_windows['volume_windows'] = []
                                required_windows['volume_windows'].append(window)
                        elif 'OBV' in feature_name:
                            required_indicators[category].append('OBV')

                    elif category == 'technical_features':
                        if 'Resistance_Level_' in feature_name or 'Support_Level_' in feature_name:
                            required_indicators[category].append('Support_Resistance')
                            window = FeatureMapper._extract_window_number(feature_name)
                            if window:
                                if 'technical_windows' not in required_windows:
                                    required_windows['technical_windows'] = []
                                required_windows['technical_windows'].append(window)
                        elif 'Bollinger_' in feature_name:
                            required_indicators[category].append('Bollinger_Position')
                            window = FeatureMapper._extract_window_number(feature_name)
                            if window:
                                if 'technical_windows' not in required_windows:
                                    required_windows['technical_windows'] = []
                                required_windows['technical_windows'].append(window)
                        elif 'Williams_R_' in feature_name:
                            required_indicators[category].append('Williams_R')
                            window = FeatureMapper._extract_window_number(feature_name)
                            if window:
                                if 'technical_windows' not in required_windows:
                                    required_windows['technical_windows'] = []
                                required_windows['technical_windows'].append(window)

                    elif category == 'time_features':
                        time_features = []
                        if 'hour' in feature_name:
                            time_features.append('hour')
                        if 'minute' in feature_name:
                            time_features.append('minute')
                        if 'day_of_week' in feature_name:
                            time_features.append('day_of_week')
                        if 'month' in feature_name:
                            time_features.append('month')
                        if 'is_weekend' in feature_name:
                            time_features.append('is_weekend')
                        if 'is_month_start' in feature_name:
                            time_features.append('is_month_start')
                        if 'is_month_end' in feature_name:
                            time_features.append('is_month_end')
                        if '_sin' in feature_name or '_cos' in feature_name:
                            time_features.append('time_sin_cos')
                        if 'quarter' in feature_name or 'week_of_year' in feature_name:
                            time_features.append('seasonal')
                        required_indicators[category] = list(set(required_indicators[category] + time_features))

                    elif category == 'lag_features':
                        if '_lag_' in feature_name:
                            # 提取列名
                            parts = feature_name.split('_lag_')
                            if len(parts) > 0:
                                col_name = parts[0]
                                if 'lag_columns' not in required_columns:
                                    required_columns['lag_columns'] = []
                                if col_name not in required_columns['lag_columns']:
                                    required_columns['lag_columns'].append(col_name)
                                # 提取滞后期
                                lag_period = FeatureMapper._extract_lag_period(feature_name)
                                if lag_period:
                                    if 'lag_periods' not in required_periods:
                                        required_periods['lag_periods'] = []
                                    if lag_period not in required_periods['lag_periods']:
                                        required_periods['lag_periods'].append(lag_period)
                        elif 'lag_return_' in feature_name:
                            # 提取滞后期
                            lag_period = FeatureMapper._extract_lag_period(feature_name)
                            if lag_period:
                                if 'lag_periods' not in required_periods:
                                    required_periods['lag_periods'] = []
                                if lag_period not in required_periods['lag_periods']:
                                    required_periods['lag_periods'].append(lag_period)

                    elif category == 'high_order_features':
                        if '_derivative' in feature_name:
                            required_indicators[category].append('derivatives')
                        elif '_corr_' in feature_name:
                            required_indicators[category].append('rolling_corr')
                            window = FeatureMapper._extract_window_number(feature_name)
                            if window:
                                if 'high_order_windows' not in required_windows:
                                    required_windows['high_order_windows'] = []
                                required_windows['high_order_windows'].append(window)
                        elif '_beta_' in feature_name:
                            required_indicators[category].append('rolling_beta')
                            window = FeatureMapper._extract_window_number(feature_name)
                            if window:
                                if 'high_order_windows' not in required_windows:
                                    required_windows['high_order_windows'] = []
                                required_windows['high_order_windows'].append(window)
                        elif '_zscore_' in feature_name:
                            required_indicators[category].append('z_score_normalize')
                            window = FeatureMapper._extract_window_number(feature_name)
                            if window:
                                if 'high_order_windows' not in required_windows:
                                    required_windows['high_order_windows'] = []
                                required_windows['high_order_windows'].append(window)

                    elif category == 'risk_features':
                        if 'max_drawdown_' in feature_name:
                            required_indicators[category].append('max_drawdown')
                            window = FeatureMapper._extract_window_number(feature_name)
                            if window:
                                if 'risk_windows' not in required_windows:
                                    required_windows['risk_windows'] = []
                                required_windows['risk_windows'].append(window)
                        elif 'sharpe_ratio_' in feature_name:
                            required_indicators[category].append('sharpe_ratio')
                            window = FeatureMapper._extract_window_number(feature_name)
                            if window:
                                if 'risk_windows' not in required_windows:
                                    required_windows['risk_windows'] = []
                                required_windows['risk_windows'].append(window)
                        elif 'calmar_ratio_' in feature_name:
                            required_indicators[category].append('calmar_ratio')
                            window = FeatureMapper._extract_window_number(feature_name)
                            if window:
                                if 'risk_windows' not in required_windows:
                                    required_windows['risk_windows'] = []
                                required_windows['risk_windows'].append(window)
                        elif 'VaR_' in feature_name:
                            required_indicators[category].append('VaR')
                            window = FeatureMapper._extract_window_number(feature_name)
                            if window:
                                if 'risk_windows' not in required_windows:
                                    required_windows['risk_windows'] = []
                                required_windows['risk_windows'].append(window)
                        elif 'skewness_' in feature_name or 'kurtosis_' in feature_name:
                            required_indicators[category].append('skewness_kurtosis')
                            window = FeatureMapper._extract_window_number(feature_name)
                            if window:
                                if 'risk_windows' not in required_windows:
                                    required_windows['risk_windows'] = []
                                required_windows['risk_windows'].append(window)

                    break

            if not feature_matched:
                pc.log(f"警告：无法识别特征 '{feature_name}'，将包含在所有特征计算中")

        # 去重并整理结果
        result = {}
        for category, indicators in required_indicators.items():
            result[category] = list(set(indicators))

        # 添加窗口、周期、列信息
        for key, values in required_windows.items():
            result[key] = list(set(values))
        for key, values in required_periods.items():
            result[key] = list(set(values))
        for key, values in required_columns.items():
            result[key] = list(set(values))

        return result

    @staticmethod
    def _extract_window_number(feature_name: str) -> Optional[int]:
        """从特征名称中提取窗口数字"""
        import re
        match = re.search(r'_(\d+)(?:_|$)', feature_name)
        return int(match.group(1)) if match else None

    @staticmethod
    def _extract_lag_period(feature_name: str) -> Optional[int]:
        """从滞后特征名称中提取滞后期"""
        import re
        match = re.search(r'lag(?:_return)?_(\d+)', feature_name)
        return int(match.group(1)) if match else None

    @staticmethod
    def load_selected_features(feature_file_path: str) -> Dict:
        """
        从joblib文件中加载选择的特征数据

        Args:
            feature_file_path: 特征文件路径，应该是 .joblib 文件

        Returns:
            包含以下键的字典:
            - selected_features: 选择的特征列表
            - feature_count: 特征数量
            - identity_columns: 身份列列表

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不正确或不是预期的特征文件
        """
        import joblib
        import os

        if not os.path.exists(feature_file_path):
            raise FileNotFoundError(f"特征文件不存在: {feature_file_path}")

        try:
            feature_data = joblib.load(feature_file_path)

            # 验证数据格式
            if not isinstance(feature_data, dict):
                raise ValueError("特征文件格式不正确：应该包含字典数据")

            required_keys = ['selected_features', 'feature_count', 'identity_columns']
            missing_keys = [key for key in required_keys if key not in feature_data]

            if missing_keys:
                raise ValueError(f"特征文件缺少必需的键: {missing_keys}")

            if not isinstance(feature_data['selected_features'], list):
                raise ValueError("selected_features 应该是列表类型")

            if not isinstance(feature_data['feature_count'], int):
                raise ValueError("feature_count 应该是整数类型")

            if not isinstance(feature_data['identity_columns'], list):
                raise ValueError("identity_columns 应该是列表类型")

            print(f"成功加载特征文件: {feature_file_path}")
            print(f"特征数量: {feature_data['feature_count']}")
            print(f"身份列: {feature_data['identity_columns']}")

            return feature_data

        except Exception as e:
            if isinstance(e, (FileNotFoundError, ValueError)):
                raise
            raise ValueError(f"加载特征文件时发生错误: {str(e)}")

def calculate_features_from_file(df: pd.DataFrame,
                                feature_file_path: str,
                                config: FeatureConfig = None,
                                identity_cols: List[str] = None,
                                time_col: str = 'DT_TIME',
                                price_col: str = 'AMT',
                                balance_col: str = 'ACCBAL') -> pd.DataFrame:
    """
    便捷函数：从特征文件加载特征列表并计算指定特征

    Args:
        df: 输入数据框
        feature_file_path: 特征文件路径（.joblib文件）
        config: 特征配置，如果为None则使用默认配置
        identity_cols: 身份列列表，如果为None则从特征文件中读取
        time_col: 时间列名
        price_col: 价格列名
        balance_col: 余额列名

    Returns:
        包含计算的特征的数据框

    Example:
        # 使用方式1：直接从文件加载并计算特征
        df_with_features = calculate_features_from_file(
            df,
            '/path/to/features.joblib'
        )

        # 使用方式2：加载特征文件后单独使用特征列表
        feature_data = FeatureEngineeringPipeline.load_selected_features('/path/to/features.joblib')
        df_with_features = FeatureEngineeringPipeline.calculate_selected_features(
            df,
            feature_data['selected_features'],
            identity_cols=feature_data['identity_columns']
        )
    """
    # 加载特征数据
    feature_data = FeatureEngineeringPipeline.load_selected_features(feature_file_path)

    # 如果没有指定身份列，使用文件中的身份列
    if identity_cols is None:
        identity_cols = feature_data['identity_columns']

    # 计算指定的特征
    result_df = FeatureEngineeringPipeline.calculate_selected_features(
        df=df,
        selected_features=feature_data['selected_features'],
        config=config,
        identity_cols=identity_cols,
        time_col=time_col,
        price_col=price_col,
        balance_col=balance_col
    )

    return result_df

def create_config_from_selected_features(selected_feature_names: List[str]) -> FeatureConfig:
    """
    根据选择的特征名称创建配置

    Args:
        selected_feature_names: 选择的特征名称列表

    Returns:
        根据选择特征优化的配置
    """
    mapping = FeatureMapper.map_features_to_indicators(selected_feature_names)
    config = FeatureConfig()

    # 根据映射结果设置配置
    if 'basic_features' in mapping:
        config.basic_features = mapping['basic_features']
    else:
        config.basic_features = []

    if 'moving_features' in mapping:
        config.moving_indicators = mapping['moving_features']
        if 'moving_windows' in mapping:
            config.moving_windows = mapping['moving_windows']
    else:
        config.moving_indicators = []

    if 'momentum_features' in mapping:
        config.momentum_indicators = mapping['momentum_features']
        if 'rsi_periods' in mapping:
            config.rsi_periods = mapping['rsi_periods']
    else:
        config.momentum_indicators = []

    if 'volatility_features' in mapping:
        config.volatility_indicators = mapping['volatility_features']
        if 'volatility_periods' in mapping:
            config.volatility_periods = mapping['volatility_periods']
    else:
        config.volatility_indicators = []

    if 'volume_features' in mapping:
        config.volume_indicators = mapping['volume_features']
        if 'volume_windows' in mapping:
            config.volume_windows = mapping['volume_windows']
    else:
        config.volume_indicators = []

    if 'technical_features' in mapping:
        config.technical_indicators = mapping['technical_features']
        if 'technical_windows' in mapping:
            config.technical_windows = mapping['technical_windows']
    else:
        config.technical_indicators = []

    if 'time_features' in mapping:
        config.time_features = mapping['time_features']
    else:
        config.time_features = []

    if 'lag_features' in mapping:
        if 'lag_columns' in mapping:
            config.lag_columns = mapping['lag_columns']
        if 'lag_periods' in mapping:
            config.lag_periods = mapping['lag_periods']
    else:
        config.lag_columns = []

    if 'high_order_features' in mapping:
        config.high_order_indicators = mapping['high_order_features']
        if 'high_order_windows' in mapping:
            config.high_order_windows = mapping['high_order_windows']
    else:
        config.high_order_indicators = []

    if 'risk_features' in mapping:
        config.risk_indicators = mapping['risk_features']
        if 'risk_windows' in mapping:
            config.risk_windows = mapping['risk_windows']
    else:
        config.risk_indicators = []

    return config

def save_selected_features(selected_features: List[str], filename: str = None) -> str:
    """
    保存选择的特征名称到文件

    Args:
        selected_features: 选择的特征名称列表
        filename: 保存的文件名，如果为None则使用默认名称

    Returns:
        保存的文件路径
    """
    if filename is None:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/ai/wks/leadingtek/scripts/selected_features_{timestamp}.txt"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# 选择的特征列表\n")
        f.write(f"# 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# 特征数量: {len(selected_features)}\n")
        f.write("#" + "="*50 + "\n\n")

        for i, feature in enumerate(selected_features, 1):
            f.write(f"{i:3d}. {feature}\n")

    pc.log(f"已保存 {len(selected_features)} 个选择的特征到: {filename}")
    return filename

def load_selected_features(filename: str) -> List[str]:
    """
    从文件加载选择的特征名称

    Args:
        filename: 特征文件路径

    Returns:
        特征名称列表
    """
    selected_features = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if line.startswith('#') or not line:
                    continue
                # 提取特征名称（去掉行号）
                if '. ' in line:
                    feature_name = line.split('. ', 1)[1].strip()
                    selected_features.append(feature_name)

        pc.log(f"从文件加载了 {len(selected_features)} 个特征: {filename}")
        return selected_features
    except Exception as e:
        pc.log(f"加载特征文件失败: {e}")
        return []

def run_optimized_feature_pipeline(selected_features_file: str = None) -> Tuple[pd.DataFrame, List[str], Dict[str, float]]:
    """
    运行优化的特征工程管道：保存选择的特征并重新计算

    Args:
        selected_features_file: 如果提供，从此文件加载特征；否则运行完整管道并保存

    Returns:
        (最终数据框, 选择的特征列表, 耗时统计)
    """
    if selected_features_file and os.path.exists(selected_features_file):
        # 加载已选择的特征并重新计算
        pc.log("=" * 60)
        pc.log("从文件加载选择特征并重新计算")
        pc.log("=" * 60)

        selected_features = load_selected_features(selected_features_file)
        pc.log(f"加载了 {len(selected_features)} 个选择的特征")

        # 根据选择的特征创建优化配置
        optimized_config = create_config_from_selected_features(selected_features)
        pc.log("已创建优化的特征配置")

        # 使用优化配置运行管道
        pc.log(f"使用优化配置运行管道------------1846------------------")
        df_result, timings = run_feature_pipeline_with_timing(optimized_config,selected_feature_save_file="/tmp/feature_selected_2.csv")

        # 验证生成的特征
        generated_features = [col for col in df_result.columns if col not in
                           ['ACCT_NUM','PARTY_ID','OPP_PARTY_ID','ACCT','TCAC','TSTM','DT_TIME']]

        missing_features = [f for f in selected_features if f not in generated_features]
        extra_features = [f for f in generated_features if f not in selected_features]

        pc.log(f"重新计算结果:")
        pc.log(f"  目标特征: {len(selected_features)}")
        pc.log(f"  生成特征: {len(generated_features)}")
        pc.log(f"  成功生成: {len(selected_features) - len(missing_features)}")
        pc.log(f"  缺失特征: {len(missing_features)}")
        pc.log(f"  额外特征: {len(extra_features)}")

        if missing_features:
            pc.log(f"缺失的特征: {missing_features}")

        return df_result, selected_features, timings

    else:
        # 运行完整管道并保存选择特征
        pc.log("=" * 60)
        pc.log("运行完整特征工程管道")
        pc.log("=" * 60)

        # 运行完整管道
        pc.log(f"使用优化配置运行管道------------1875------------------")
        df_full, timings = run_feature_pipeline_with_timing()

        # 获取选择的特征（这里需要从特征选择结果中获取）
        # 由于我们的管道会进行特征选择，我们需要从结果中提取选择的特征
        identity_cols = ['ACCT_NUM','PARTY_ID','OPP_PARTY_ID','ACCT','TCAC','TSTM']
        time_col = 'DT_TIME'
        all_numeric_cols = [col for col in df_full.columns if df_full[col].dtype in ['int64', 'float64']]
        selected_features = [col for col in all_numeric_cols if col not in identity_cols + [time_col]]

        # 保存选择的特征
        saved_file = save_selected_features(selected_features)

        # 使用保存的特征进行重新计算测试
        pc.log("\n" + "=" * 60)
        pc.log("使用保存的选择特征进行重新计算测试")
        pc.log("=" * 60)

        df_recomputed, recomputed_timings = run_optimized_feature_pipeline(saved_file)

        # 比较结果
        pc.log("\n" + "=" * 60)
        pc.log("性能对比")
        pc.log("=" * 60)
        pc.log(f"完整管道耗时: {sum(timings.values()):.4f}s")
        pc.log(f"优化管道耗时: {sum(recomputed_timings.values()):.4f}s")
        pc.log(f"性能提升: {(sum(timings.values()) / sum(recomputed_timings.values())):.2f}x")

        return df_recomputed, selected_features, recomputed_timings

if __name__ == "__main__":
    import os

    print("="*60)
    print("运行完整特征工程管道并保存选择特征")
    print("="*60)

    # 运行完整管道并保存选择特征
    pc.log(f"使用优化配置运行管道------------1913------------------")
    df_full, timings = run_feature_pipeline_with_timing()

    # 获取选择的特征（从特征选择结果中获取）
    identity_cols = ['ACCT_NUM','PARTY_ID','OPP_PARTY_ID','ACCT','TCAC','TSTM']
    time_col = 'DT_TIME'
    all_numeric_cols = [col for col in df_full.columns if df_full[col].dtype in ['int64', 'float64']]
    selected_features = [col for col in all_numeric_cols if col not in identity_cols + [time_col]]

    # 保存选择的特征
    saved_file = save_selected_features(selected_features)

    print("\n" + "="*60)
    print("特征工程完成！")
    print(f"选择的特征数量: {len(selected_features)}")
    print(f"最终数据维度: {df_full.shape}")
    print(f"总耗时: {sum(timings.values()):.4f}s")
    print(f"特征文件已保存到: {saved_file}")
    print("="*60)

    print("\n" + "="*60)
    print("测试重新计算功能")
    print("="*60)

    # 测试重新计算功能
    pc.log("使用保存的选择特征进行重新计算测试----------------2340--------------")
    df_recomputed, recompute_selected_features, recompute_timings = run_optimized_feature_pipeline(saved_file)

    print("\n" + "="*60)
    print("重新计算完成！")
    print(f"重新计算耗时: {sum(recompute_timings.values()):.4f}s")
    print(f"性能提升: {sum(timings.values()) / sum(recompute_timings.values()):.2f}x")
    print("="*60)

    print("\n" + "="*60)
    print("测试选择性特征计算功能")
    print("="*60)

    # 测试选择性特征计算功能
    try:
        pc.log("测试从文件加载特征并选择性计算----------------1939--------------")

        # 使用之前保存的特征文件中的部分特征进行测试
        test_features = ['Bollinger_Position_10', 'minute', 'price_beta_10', 'price_beta_20', 'price_beta_50', 'sharpe_ratio_99']

        # 读取原始数据
        data_file = "/ai/wks/leadingtek/scripts/tra11.csv"
        cols = ['ACCT_NUM','PARTY_ID','OPP_PARTY_ID','ACCT','TCAC','TSTM', 'DT_TIME', 'PARTY_CLASS_CD',
                'CCY', 'AMT', 'AMT_VAL','CNY_AMT','ACCBAL', 'DEBIT_CREDIT','CASH_FLAG', 'OPP_ORGANKEY',
                'OACCTT', 'OTBKAC', 'CHANNEL', 'RMKS', 'CBCDIR', 'AMTFLG', 'BALFLG', 'RMKCDE', 'TDDS',
                'RCDTYP', 'CCY_A', 'INTAMT_A', 'INTRAT_A', 'PBKTYP', 'CNT_CST_TYPE', 'CNT_INBANK_TYPE',
                'CFRC_COUNTRY', 'CFRC_AREA', 'TRCD_AREA', 'TRCD_COUNTRY', 'TXTPCD', 'RCVPAYFLG', 'SYS_FLAG',
                'TXN_CHNL_TP_ID', 'FLAG', 'OVERAREA_IND']
        df_test = pd.read_csv(data_file, usecols=cols)

        # 数据预处理
        from tpf.data.deal import Data2Feature as dtf
        num_type = ['AMT', 'AMT_VAL','CNY_AMT','ACCBAL','INTAMT_A', 'INTRAT_A']
        date_type=['DT_TIME']
        df_test_processed = dtf.data_type_change(df_test, num_type=num_type, date_type=date_type)

        identity_cols = ['ACCT_NUM','PARTY_ID','OPP_PARTY_ID','ACCT','TCAC','TSTM']
        
        df_test_preprocessed = FeatureEngineeringPipeline.preprocess_data(
            df_test_processed, identity_cols, num_type, date_type[0])

        # 方法1：直接使用特征列表计算
        pc.log("方法1：使用特征列表直接计算指定特征...")
        df_result1 = FeatureEngineeringPipeline.calculate_selected_features(
            df_test_preprocessed,
            test_features,
            identity_cols=identity_cols
        )

        print(f"方法1结果: 数据形状 {df_result1.shape}, 包含特征: {list(df_result1.columns)}")

        # 方法2：从特征文件加载并计算（如果特征文件存在）
        if saved_file and saved_file.replace('.csv', '_features.joblib') in [f for f in os.listdir('/ai/wks/leadingtek/scripts/') if f.endswith('.joblib')]:
            feature_joblib_file = saved_file.replace('.csv', '_features.joblib')
            pc.log("方法2：从特征文件加载并计算特征...")
            df_result2 = calculate_features_from_file(
                df_test_preprocessed,
                feature_joblib_file
            )
            print(f"方法2结果: 数据形状 {df_result2.shape}")

        print("选择性特征计算测试完成！")

    except Exception as e:
        pc.log(f"选择性特征计算测试出现错误: {str(e)}")
        print(f"错误详情: {e}")

    print("="*60)