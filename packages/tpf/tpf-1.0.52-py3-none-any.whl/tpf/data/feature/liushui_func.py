#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合版金融数据特征工程
- amt在时间上的特征 
将liushui.py中的所有类和方法合并为一个单一的函数
"""

import pandas as pd
import numpy as np
import warnings
import time
from typing import Dict, List, Optional, Union, Tuple
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_regression

# 忽略特定的数值计算警告
warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*invalid value.*')
warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*divide by zero.*')

def calculate_liushui_features(
    df: pd.DataFrame,
    # 基础数据列配置
    time_col: str = 'DT_TIME',
    price_col: str = 'AMT',
    balance_col: str = 'ACCBAL',
    amount_col: str = 'CNY_AMT',
    identity_cols: List[str] = None,

    # 特征计算配置 - 基础价格特征
    calc_price_change_rate: bool = True,
    calc_log_return: bool = True,
    calc_price_amplitude: bool = True,
    calc_opening_gap: bool = True,
    calc_price_position: bool = True,

    # 移动窗口特征配置
    moving_windows: List[int] = None,
    calc_ma: bool = True,
    calc_ema: bool = True,
    calc_std: bool = True,
    calc_max: bool = True,
    calc_min: bool = True,
    calc_q25: bool = True,
    calc_q50: bool = True,
    calc_q75: bool = True,
    calc_iqr: bool = True,
    calc_cv: bool = True,
    calc_price_vs_ma: bool = True,
    calc_price_zscore: bool = True,

    # 动量指标配置
    rsi_periods: List[int] = None,
    macd_fast: int = 12,
    macd_slow: int = 26,
    macd_signal: int = 9,
    calc_momentum: bool = True,
    calc_roc: bool = True,

    # 波动率特征配置
    volatility_periods: List[int] = None,
    calc_historical_volatility: bool = True,
    calc_atr: bool = True,
    calc_parkinson_volatility: bool = True,
    calc_garman_klass_volatility: bool = True,

    # 成交量特征配置
    volume_windows: List[int] = None,
    calc_volume_change_rate: bool = True,
    calc_vma: bool = True,
    calc_vema: bool = True,
    calc_price_volume_corr: bool = True,
    calc_vwap: bool = True,
    calc_obv: bool = True,

    # 技术形态特征配置
    technical_windows: List[int] = None,
    calc_resistance_level: bool = True,
    calc_support_level: bool = True,
    calc_price_position_tech: bool = True,
    calc_bollinger: bool = True,
    calc_williams_r: bool = True,

    # 时间特征配置
    calc_hour: bool = True,
    calc_minute: bool = True,
    calc_day_of_week: bool = True,
    calc_month: bool = True,
    calc_is_weekend: bool = True,
    calc_is_month_start: bool = True,
    calc_is_month_end: bool = True,
    calc_time_cyclical: bool = True,
    calc_quarter: bool = True,
    calc_week_of_year: bool = True,

    # 滞后特征配置
    lag_periods: List[int] = None,
    lag_columns: List[str] = None,

    # 高阶特征配置
    high_order_windows: List[int] = None,
    calc_derivatives: bool = True,
    calc_acceleration: bool = True,
    calc_curvature: bool = True,

    # 风险特征配置
    risk_windows: List[int] = None,
    calc_var: bool = True,
    calc_cvar: bool = True,
    calc_max_drawdown: bool = True,
    calc_sharpe_ratio: bool = True,
    calc_calmar_ratio: bool = True,
    calc_sortino_ratio: bool = True,

    # 数据清理配置
    clean_infinite: bool = True,
    fill_missing: bool = True,
    handle_outliers: bool = True,
    outlier_threshold: float = 3.0,

    # 特征选择配置
    enable_feature_selection: bool = False,
    variance_threshold: float = 0.01,
    k_best_features: int = 50,

    # 打印配置
    verbose: bool = True
) -> pd.DataFrame:
    """
    整合的特征计算函数，包含原liushui.py中所有的特征计算逻辑

    Args:
        df: 输入数据框
        time_col: 时间列名，默认为'DT_TIME'
        price_col: 价格列名，默认为'AMT'
        balance_col: 余额列名，默认为'ACCBAL'
        amount_col: 金额列名，默认为'CNY_AMT'
        identity_cols: 标识列列表，默认为['ACCT_NUM', 'PARTY_ID', 'OPP_PARTY_ID', 'ACCT', 'TCAC', 'TSTM']

        # 基础价格特征开关
        calc_price_change_rate: 是否计算价格变化率
        calc_log_return: 是否计算对数收益率
        calc_price_amplitude: 是否计算价格振幅
        calc_opening_gap: 是否计算开盘缺口
        calc_price_position: 是否计算价格位置

        # 移动窗口特征配置
        moving_windows: 移动窗口周期列表，默认为[3, 5, 7]
        calc_ma: 是否计算简单移动平均
        calc_ema: 是否计算指数移动平均
        calc_std: 是否计算标准差
        calc_max: 是否计算最大值
        calc_min: 是否计算最小值
        calc_q25: 是否计算25分位数
        calc_q50: 是否计算50分位数
        calc_q75: 是否计算75分位数
        calc_iqr: 是否计算四分位距
        calc_cv: 是否计算变异系数
        calc_price_vs_ma: 是否计算价格与移动平均的比值
        calc_price_zscore: 是否计算价格Z分数

        # 动量指标配置
        rsi_periods: RSI计算周期列表，默认为[7]
        macd_fast: MACD快线周期，默认为12
        macd_slow: MACD慢线周期，默认为26
        macd_signal: MACD信号线周期，默认为9
        calc_momentum: 是否计算动量指标
        calc_roc: 是否计算变化率

        # 波动率特征配置
        volatility_periods: 波动率计算周期列表，默认为[3, 5, 7]
        calc_historical_volatility: 是否计算历史波动率
        calc_atr: 是否计算平均真实波幅
        calc_parkinson_volatility: 是否计算Parkinson波动率
        calc_garman_klass_volatility: 是否计算Garman-Klass波动率

        # 成交量特征配置
        volume_windows: 成交量窗口周期列表，默认为[3, 5, 7]
        calc_volume_change_rate: 是否计算成交量变化率
        calc_vma: 是否计算成交量移动平均
        calc_vema: 是否计算成交量指数移动平均
        calc_price_volume_corr: 是否计算价量相关性
        calc_vwap: 是否计算成交量加权平均价
        calc_obv: 是否计算能量潮指标

        # 技术形态特征配置
        technical_windows: 技术分析窗口周期列表，默认为[5, 10, 20]
        calc_resistance_level: 是否计算阻力位
        calc_support_level: 是否计算支撑位
        calc_price_position_tech: 是否计算价格技术位置
        calc_bollinger: 是否计算布林带
        calc_williams_r: 是否计算威廉指标

        # 时间特征配置
        calc_hour: 是否计算小时特征
        calc_minute: 是否计算分钟特征
        calc_day_of_week: 是否计算星期特征
        calc_month: 是否计算月份特征
        calc_is_weekend: 是否计算周末标识
        calc_is_month_start: 是否计算月初标识
        calc_is_month_end: 是否计算月末标识
        calc_time_cyclical: 是否计算周期性时间特征
        calc_quarter: 是否计算季度特征
        calc_week_of_year: 是否计算一年中的周数

        # 滞后特征配置
        lag_periods: 滞后期数列表，默认为[1, 2, 3]
        lag_columns: 需要计算滞后特征的列名列表，默认为[price_col]

        # 高阶特征配置
        high_order_windows: 高阶特征窗口列表，默认为[2, 3]
        calc_derivatives: 是否计算导数特征
        calc_acceleration: 是否计算加速度特征
        calc_curvature: 是否计算曲率特征

        # 风险特征配置
        risk_windows: 风险计算窗口列表，默认为[5, 10, 20]
        calc_var: 是否计算风险价值
        calc_cvar: 是否计算条件风险价值
        calc_max_drawdown: 是否计算最大回撤
        calc_sharpe_ratio: 是否计算夏普比率
        calc_calmar_ratio: 是否计算卡尔玛比率
        calc_sortino_ratio: 是否计算索提诺比率

        # 数据清理配置
        clean_infinite: 是否清理无穷大值，默认为True
        fill_missing: 是否填充缺失值，默认为True
        handle_outliers: 是否处理异常值，默认为True
        outlier_threshold: 异常值阈值，默认为3.0

        # 特征选择配置
        enable_feature_selection: 是否启用特征选择，默认为False
        variance_threshold: 方差阈值，默认为0.01
        k_best_features: 选择的最佳特征数量，默认为50

        verbose: 是否打印详细日志，默认为True

    Returns:
        pd.DataFrame: 包含所有计算特征的数据框
    """

    # 设置默认值
    if identity_cols is None:
        identity_cols = ['ACCT_NUM', 'PARTY_ID', 'OPP_PARTY_ID', 'ACCT', 'TCAC', 'TSTM']

    if moving_windows is None:
        moving_windows = [3, 5, 7]
    if rsi_periods is None:
        rsi_periods = [7]
    if volatility_periods is None:
        volatility_periods = [3, 5, 7]
    if volume_windows is None:
        volume_windows = [3, 5, 7]
    if technical_windows is None:
        technical_windows = [5, 10, 20]
    if lag_periods is None:
        lag_periods = [1, 2, 3]
    if lag_columns is None:
        lag_columns = [price_col]
    if high_order_windows is None:
        high_order_windows = [2, 3]
    if risk_windows is None:
        risk_windows = [5, 10, 20]

    def log(message):
        """简单的日志函数"""
        if verbose:
            print(f"[{time.strftime('%H:%M:%S')}] {message}")

    log("开始整合特征计算...")
    result_df = df.copy()

    # ==================== 数据清理 ====================
    log("开始数据清理...")
    numeric_cols = [col for col in result_df.columns if result_df[col].dtype in ['int64', 'float64']]

    for col in numeric_cols:
        if col in result_df.columns:
            # 处理无穷大值
            if clean_infinite:
                result_df[col] = result_df[col].replace([np.inf, -np.inf], np.nan)

            # 处理缺失值
            if fill_missing:
                nan_count = result_df[col].isnull().sum()
                if nan_count > 0:
                    result_df[col] = result_df[col].ffill().interpolate().bfill().fillna(0)
                    if verbose:
                        log(f"列{col}处理了{nan_count}个缺失值")

            # 处理异常值
            if handle_outliers and result_df[col].dtype in ['int64', 'float64']:
                cleaned_series = result_df[col].dropna()
                if len(cleaned_series) > 0 and cleaned_series.std() > 0:
                    try:
                        z_scores = np.abs(stats.zscore(cleaned_series))
                        outliers = z_scores > outlier_threshold
                        if outliers.sum() > 0:
                            lower_bound = cleaned_series.quantile(0.01)
                            upper_bound = cleaned_series.quantile(0.99)
                            result_df[col] = result_df[col].clip(lower_bound, upper_bound)
                            if verbose:
                                log(f"列{col}处理了{outliers.sum()}个异常值")
                    except:
                        pass

    # ==================== 基础价格特征 ====================
    if any([calc_price_change_rate, calc_log_return, calc_price_amplitude, calc_opening_gap, calc_price_position]):
        log("计算基础价格特征...")

        # 确保数据按时间排序
        result_df = result_df.sort_values(time_col).reset_index(drop=True)

        epsilon = 1e-8

        if calc_price_change_rate and price_col in result_df.columns:
            result_df['price_change_rate'] = result_df[price_col].pct_change().fillna(0)

        if calc_log_return and price_col in result_df.columns:
            result_df['log_return'] = (np.log(result_df[price_col] + epsilon) -
                                      np.log(result_df[price_col].shift(1) + epsilon)).fillna(0)

        if calc_price_amplitude and balance_col in result_df.columns:
            # 使用余额列计算高低价，与原始逻辑一致
            window = 5
            result_df['price_high'] = result_df[balance_col].rolling(window=window, min_periods=1).max()
            result_df['price_low'] = result_df[balance_col].rolling(window=window, min_periods=1).min()
            result_df['price_amplitude'] = ((result_df['price_high'] - result_df['price_low']) /
                                           (result_df[price_col].shift(1) + epsilon)).fillna(0)

        if calc_opening_gap and price_col in result_df.columns:
            # 确保时间列是datetime类型
            if not pd.api.types.is_datetime64_any_dtype(result_df[time_col]):
                result_df[time_col] = pd.to_datetime(result_df[time_col])

            result_df['time_diff'] = result_df[time_col].diff().dt.total_seconds() / 3600
            result_df['time_diff'] = result_df['time_diff'].fillna(0)
            jump_threshold = 4
            result_df['is_jump'] = (result_df['time_diff'] > jump_threshold).astype(int)
            result_df['opening_gap'] = result_df['price_change_rate'] * result_df['is_jump']

        if calc_price_position and price_col in result_df.columns:
            if 'price_high' in result_df.columns and 'price_low' in result_df.columns:
                price_range = result_df['price_high'] - result_df['price_low']
                price_range = price_range.replace(0, epsilon)  # 避免除零
                result_df['price_position'] = ((result_df[price_col] - result_df['price_low']) /
                                              price_range).fillna(0.5)

    # ==================== 移动窗口特征 ====================
    if any([calc_ma, calc_ema, calc_std, calc_max, calc_min, calc_q25, calc_q50, calc_q75, calc_iqr, calc_cv, calc_price_vs_ma, calc_price_zscore]):
        log("计算移动窗口特征...")

        if price_col in result_df.columns:
            for window in moving_windows:
                if calc_ma:
                    result_df[f'MA_{window}'] = result_df[price_col].rolling(window=window, min_periods=1).mean()

                if calc_ema:
                    alpha = 2 / (window + 1)
                    result_df[f'EMA_{window}'] = result_df[price_col].ewm(alpha=alpha, adjust=False).mean()

                if calc_std:
                    result_df[f'STD_{window}'] = result_df[price_col].rolling(window=window, min_periods=1).std().fillna(0)

                if calc_max:
                    result_df[f'MAX_{window}'] = result_df[price_col].rolling(window=window, min_periods=1).max()

                if calc_min:
                    result_df[f'MIN_{window}'] = result_df[price_col].rolling(window=window, min_periods=1).min()

                if calc_q25:
                    result_df[f'Q25_{window}'] = result_df[price_col].rolling(window=window, min_periods=1).quantile(0.25)

                if calc_q50:
                    result_df[f'Q50_{window}'] = result_df[price_col].rolling(window=window, min_periods=1).quantile(0.50)

                if calc_q75:
                    result_df[f'Q75_{window}'] = result_df[price_col].rolling(window=window, min_periods=1).quantile(0.75)

                if calc_iqr:
                    result_df[f'IQR_{window}'] = (result_df[f'Q75_{window}'] - result_df[f'Q25_{window}']).fillna(0)

                if calc_cv:
                    mean_vals = result_df[f'MA_{window}']
                    std_vals = result_df[f'STD_{window}']
                    result_df[f'CV_{window}'] = (std_vals / (mean_vals + 1e-8)).fillna(0)

                if calc_price_vs_ma:
                    result_df[f'Price_vs_MA_{window}'] = ((result_df[price_col] - result_df[f'MA_{window}']) /
                                                         (result_df[f'MA_{window}'] + 1e-8)).fillna(0)

                if calc_price_zscore:
                    result_df[f'Price_ZScore_{window}'] = ((result_df[price_col] - result_df[f'MA_{window}']) /
                                                          (result_df[f'STD_{window}'] + 1e-8)).fillna(0)

    # ==================== 动量指标 ====================
    if any([calc_momentum, calc_roc]) or rsi_periods:
        log("计算动量指标...")

        if price_col in result_df.columns:
            # RSI
            for period in rsi_periods:
                delta = result_df[price_col].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
                rs = gain / loss.replace(0, np.nan)
                result_df[f'RSI_{period}'] = 100 - (100 / (1 + rs))

            # MACD
            if macd_fast < len(result_df) and macd_slow < len(result_df):
                ema_fast = result_df[price_col].ewm(span=macd_fast, adjust=False).mean()
                ema_slow = result_df[price_col].ewm(span=macd_slow, adjust=False).mean()
                result_df['MACD'] = ema_fast - ema_slow
                result_df['MACD_Signal'] = result_df['MACD'].ewm(span=macd_signal, adjust=False).mean()
                result_df['MACD_Histogram'] = result_df['MACD'] - result_df['MACD_Signal']

            # Momentum
            if calc_momentum:
                for period in [5, 10, 20]:  # 使用固定周期，与原始代码一致
                    result_df[f'Momentum_{period}'] = result_df[price_col] - result_df[price_col].shift(period)

            # Rate of Change (ROC)
            if calc_roc:
                for period in [5, 10, 20]:  # 使用固定周期，与原始代码一致
                    result_df[f'ROC_{period}'] = ((result_df[price_col] - result_df[price_col].shift(period)) /
                                                (result_df[price_col].shift(period) + 1e-8)).fillna(0)

    # ==================== 波动率特征 ====================
    if any([calc_historical_volatility, calc_atr, calc_parkinson_volatility, calc_garman_klass_volatility]):
        log("计算波动率特征...")

        if price_col in result_df.columns:
            # Historical Volatility
            if calc_historical_volatility:
                log_return = np.log(result_df[price_col] / result_df[price_col].shift(1)).fillna(0)
                for period in volatility_periods:
                    volatility = log_return.rolling(window=period, min_periods=1).std()
                    result_df[f'Historical_Volatility_{period}'] = volatility * np.sqrt(252)

            # ATR (Average True Range) - 需要最高价和最低价
            if calc_atr and balance_col in result_df.columns:
                # 使用balance_col作为高低价数据源
                for period in volatility_periods:
                    high = result_df[balance_col].rolling(window=5, min_periods=1).max()
                    low = result_df[balance_col].rolling(window=5, min_periods=1).min()
                    close_prev = result_df[price_col].shift(1)

                    tr1 = high - low
                    tr2 = abs(high - close_prev)
                    tr3 = abs(low - close_prev)

                    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                    result_df[f'ATR_{period}'] = true_range.rolling(window=period, min_periods=1).mean()

            # Parkinson Volatility
            if calc_parkinson_volatility and balance_col in result_df.columns:
                for period in volatility_periods:
                    high = result_df[balance_col].rolling(window=5, min_periods=1).max()
                    low = result_df[balance_col].rolling(window=5, min_periods=1).min()
                    hl_ratio = np.log(high / low)
                    parkinson_vol = np.sqrt(0.361 * (hl_ratio ** 2).rolling(window=period, min_periods=1).sum())
                    result_df[f'Parkinson_Volatility_{period}'] = parkinson_vol.fillna(0)

            # Garman-Klass Volatility
            if calc_garman_klass_volatility and balance_col in result_df.columns:
                for period in volatility_periods:
                    high = result_df[balance_col].rolling(window=5, min_periods=1).max()
                    low = result_df[balance_col].rolling(window=5, min_periods=1).min()
                    open_price = result_df[price_col].shift(1)  # 用前一天收盘价作为开盘价
                    close_price = result_df[price_col]

                    gk_vol = (0.5 * (np.log(high / low) ** 2) -
                             (2 * np.log(2) - 1) * (np.log(close_price / open_price) ** 2))
                    result_df[f'Garman_Klass_Volatility_{period}'] = np.sqrt(gk_vol.fillna(0) * 252)

    # ==================== 成交量特征 ====================
    if any([calc_volume_change_rate, calc_vma, calc_vema, calc_price_volume_corr, calc_vwap, calc_obv]):
        log("计算成交量特征...")

        # 使用价格列作为成交量代理（如果没有专门的成交量列）
        volume_col = price_col

        if calc_volume_change_rate:
            result_df['volume_change_rate'] = result_df[volume_col].pct_change().fillna(0)

        for window in volume_windows:
            if calc_vma:
                result_df[f'VMA_{window}'] = result_df[volume_col].rolling(window=window, min_periods=1).mean()
            if calc_vema:
                alpha = 2 / (window + 1)
                result_df[f'VEMA_{window}'] = result_df[volume_col].ewm(alpha=alpha, adjust=False).mean()

        if calc_price_volume_corr and price_col in result_df.columns:
            for window in volume_windows:
                correlation = result_df[price_col].rolling(window=window, min_periods=1).corr(result_df[volume_col])
                result_df[f'Price_Volume_Corr_{window}'] = correlation.fillna(0)

        if calc_vwap and price_col in result_df.columns and amount_col in result_df.columns:
            # VWAP = Volume Weighted Average Price
            for window in volume_windows:
                if result_df[volume_col].sum() > 0:
                    vwap = (result_df[price_col] * result_df[volume_col]).rolling(window=window, min_periods=1).sum() / \
                           result_df[volume_col].rolling(window=window, min_periods=1).sum()
                    result_df[f'VWAP_{window}'] = vwap.fillna(result_df[price_col])

        if calc_obv and price_col in result_df.columns:
            # On Balance Volume
            price_change = result_df[price_col].diff()
            obv = np.where(price_change > 0, result_df[volume_col],
                          np.where(price_change < 0, -result_df[volume_col], 0))
            result_df['OBV'] = np.cumsum(obv)
            result_df['OBV_MA'] = result_df['OBV'].rolling(window=20, min_periods=1).mean()

    # ==================== 技术形态特征 ====================
    if any([calc_resistance_level, calc_support_level, calc_price_position_tech, calc_bollinger, calc_williams_r]):
        log("计算技术形态特征...")

        if price_col in result_df.columns:
            # Resistance and Support Levels
            for window in technical_windows:
                # 先计算支撑位和阻力位
                support_level = None
                resistance_level = None

                if calc_support_level:
                    support_level = result_df[price_col].rolling(window=window, min_periods=1).min()
                    result_df[f'Support_Level_{window}'] = support_level

                if calc_resistance_level:
                    resistance_level = result_df[price_col].rolling(window=window, min_periods=1).max()
                    result_df[f'Resistance_Level_{window}'] = resistance_level

                # 计算价格位置（如果需要）
                if calc_price_position_tech:
                    # 如果没有计算支撑位或阻力位，则直接使用价格数据计算
                    if support_level is None:
                        support_level = result_df[price_col].rolling(window=window, min_periods=1).min()
                    if resistance_level is None:
                        resistance_level = result_df[price_col].rolling(window=window, min_periods=1).max()

                    price_range = resistance_level - support_level
                    price_range = price_range.replace(0, 1e-8)  # 避免除零
                    result_df[f'Price_Position_{window}'] = ((result_df[price_col] - support_level) / price_range).fillna(0.5)

            # Bollinger Bands Position
            if calc_bollinger:
                for window in technical_windows:
                    ma = result_df[price_col].rolling(window=window, min_periods=1).mean()
                    std = result_df[price_col].rolling(window=window, min_periods=1).std()
                    upper_band = ma + (2 * std)
                    lower_band = ma - (2 * std)

                    result_df[f'Bollinger_Upper_{window}'] = upper_band
                    result_df[f'Bollinger_Lower_{window}'] = lower_band
                    result_df[f'Bollinger_Position_{window}'] = ((result_df[price_col] - lower_band) /
                                                                (upper_band - lower_band + 1e-8)).fillna(0.5)

            # Williams %R
            if calc_williams_r and balance_col in result_df.columns:
                for window in technical_windows:
                    high = result_df[balance_col].rolling(window=5, min_periods=1).max()
                    low = result_df[balance_col].rolling(window=5, min_periods=1).min()
                    williams_r = ((high - result_df[price_col]) / (high - low)) * -100
                    result_df[f'Williams_R_{window}'] = williams_r.fillna(-50)

    # ==================== 时间特征 ====================
    if any([calc_hour, calc_minute, calc_day_of_week, calc_month, calc_is_weekend, calc_is_month_start, calc_is_month_end, calc_time_cyclical, calc_quarter, calc_week_of_year]):
        log("计算时间特征...")

        if time_col in result_df.columns:
            # 确保时间列是datetime类型
            if not pd.api.types.is_datetime64_any_dtype(result_df[time_col]):
                result_df[time_col] = pd.to_datetime(result_df[time_col])

            # 基础时间特征
            if calc_hour:
                result_df['hour'] = result_df[time_col].dt.hour
            if calc_minute:
                result_df['minute'] = result_df[time_col].dt.minute
            if calc_day_of_week:
                result_df['day_of_week'] = result_df[time_col].dt.dayofweek
            if calc_month:
                result_df['month'] = result_df[time_col].dt.month
            if calc_is_weekend:
                result_df['is_weekend'] = (result_df[time_col].dt.dayofweek >= 5).astype(int)
            if calc_is_month_start:
                result_df['is_month_start'] = (result_df[time_col].dt.is_month_start).astype(int)
            if calc_is_month_end:
                result_df['is_month_end'] = (result_df[time_col].dt.is_month_end).astype(int)

            # 周期性特征
            if calc_time_cyclical:
                # 确保基础时间特征存在（依赖关系）
                if 'hour' not in result_df.columns:
                    result_df['hour'] = result_df[time_col].dt.hour
                if 'day_of_week' not in result_df.columns:
                    result_df['day_of_week'] = result_df[time_col].dt.dayofweek
                if 'month' not in result_df.columns:
                    result_df['month'] = result_df[time_col].dt.month

                result_df['hour_sin'] = np.sin(2 * np.pi * result_df['hour'] / 24)
                result_df['hour_cos'] = np.cos(2 * np.pi * result_df['hour'] / 24)
                result_df['day_sin'] = np.sin(2 * np.pi * result_df['day_of_week'] / 7)
                result_df['day_cos'] = np.cos(2 * np.pi * result_df['day_of_week'] / 7)
                result_df['month_sin'] = np.sin(2 * np.pi * result_df['month'] / 12)
                result_df['month_cos'] = np.cos(2 * np.pi * result_df['month'] / 12)

            # 季节性特征
            if calc_quarter:
                result_df['quarter'] = result_df[time_col].dt.quarter
            if calc_week_of_year:
                result_df['week_of_year'] = result_df[time_col].dt.isocalendar().week

    # ==================== 滞后特征 ====================
    if lag_periods and lag_columns:
        log("计算滞后特征...")

        for col in lag_columns:
            if col in result_df.columns:
                for period in lag_periods:
                    result_df[f'{col}_lag_{period}'] = result_df[col].shift(period).fillna(0)

        # 滞后收益率特征
        for lag in lag_periods:
            if f'{price_col}_lag_{lag}' in result_df.columns:
                lag_return = (result_df[price_col] - result_df[f'{price_col}_lag_{lag}']) / \
                            (result_df[f'{price_col}_lag_{lag}'] + 1e-8)
                result_df[f'lag_return_{lag}'] = lag_return.fillna(0)

    # ==================== 高阶特征 ====================
    if any([calc_derivatives, calc_acceleration, calc_curvature]):
        log("计算高阶特征...")

        if price_col in result_df.columns:
            # 一阶和二阶导数
            if calc_derivatives:
                def calculate_derivatives(series):
                    """计算一阶和二阶导数"""
                    first_deriv = series.diff().fillna(0)
                    second_deriv = first_deriv.diff().fillna(0)
                    return first_deriv, second_deriv

                first_deriv, second_deriv = calculate_derivatives(result_df[price_col])
                result_df['price_first_derivative'] = first_deriv
                result_df['price_second_derivative'] = second_deriv

            # 滚动相关系数
            if balance_col in result_df.columns:
                for window in high_order_windows:
                    corr = result_df[price_col].rolling(window=window, min_periods=1).corr(result_df[balance_col])
                    result_df[f'price_balance_corr_{window}'] = corr.fillna(0)

            # 滚动Beta
            if balance_col in result_df.columns:
                for window in high_order_windows:
                    if window < len(result_df):
                        rolling_cov = result_df[price_col].rolling(window=window, min_periods=1).cov(result_df[balance_col])
                        rolling_var = result_df[balance_col].rolling(window=window, min_periods=1).var()
                        beta = rolling_cov / rolling_var.replace(0, 1)
                        result_df[f'price_beta_{window}'] = beta.fillna(1.0)

            # Z-score标准化
            for window in high_order_windows:
                rolling_mean = result_df[price_col].rolling(window=window, min_periods=1).mean()
                rolling_std = result_df[price_col].rolling(window=window, min_periods=1).std()
                z_score = (result_df[price_col] - rolling_mean) / (rolling_std + 1e-8)
                result_df[f'price_zscore_{window}'] = z_score.fillna(0)

    # ==================== 风险特征 ====================
    if any([calc_var, calc_cvar, calc_max_drawdown, calc_sharpe_ratio, calc_calmar_ratio, calc_sortino_ratio]):
        log("计算风险特征...")

        if price_col in result_df.columns:
            returns = result_df[price_col].pct_change().fillna(0)

            for window in risk_windows:
                if len(returns) >= window:
                    window_returns = returns.rolling(window=window, min_periods=1)

                    # Maximum Drawdown
                    if calc_max_drawdown:
                        # 计算累积收益
                        cumulative = (1 + returns).cumprod()
                        rolling_max = cumulative.rolling(window=window, min_periods=1).max()
                        drawdown = (cumulative - rolling_max) / rolling_max
                        max_drawdown = drawdown.rolling(window=window, min_periods=1).min()
                        result_df[f'max_drawdown_{window}'] = max_drawdown

                    # 夏普比率
                    if calc_sharpe_ratio:
                        returns_window = returns.rolling(window=window, min_periods=1)
                        rolling_sharpe = returns_window.mean() / returns_window.std()
                        result_df[f'sharpe_ratio_{window}'] = rolling_sharpe * np.sqrt(252)

                    # VaR (Value at Risk)
                    if calc_var:
                        var_95 = window_returns.quantile(0.05)
                        var_99 = window_returns.quantile(0.01)
                        result_df[f'VaR_95_{window}'] = var_95
                        result_df[f'VaR_99_{window}'] = var_99

                    # 偏度和峰度
                    # 添加偏度和峰度的计算
                    rolling_skew = window_returns.skew()
                    rolling_kurt = window_returns.kurt()
                    result_df[f'skewness_{window}'] = rolling_skew.fillna(0)
                    result_df[f'kurtosis_{window}'] = rolling_kurt.fillna(0)

    # ==================== 特征选择 ====================
    if enable_feature_selection:
        log("进行特征选择...")

        # 获取数值特征列
        feature_cols = [col for col in result_df.columns
                       if col not in identity_cols + [time_col]
                       and result_df[col].dtype in ['int64', 'float64']]

        if len(feature_cols) > 0:
            # 移除常数特征
            selector = VarianceThreshold(threshold=variance_threshold)
            feature_data = result_df[feature_cols].fillna(0)

            # 确保数据清理：替换无穷大值并检查数据有效性
            feature_data = feature_data.replace([np.inf, -np.inf], np.nan).fillna(0)

            # 检查是否还有无效数值
            if not np.all(np.isfinite(feature_data.values)):
                if verbose:
                    log("发现无效数值，进行额外清理...")
                feature_data = feature_data.astype(np.float64)
                feature_data = feature_data.clip(-1e10, 1e10)  # 限制数值范围
                feature_data = feature_data.fillna(0)

            try:
                # 方差阈值选择
                variance_selected = selector.fit_transform(feature_data)
                variance_mask = selector.get_support()
                selected_cols = [col for col, selected in zip(feature_cols, variance_mask) if selected]

                if verbose:
                    log(f"方差阈值过滤: 原始特征数={len(feature_cols)}, 过滤后特征数={len(selected_cols)}, k_best_features={k_best_features}")

                # 选择top K特征
                if len(selected_cols) > k_best_features:
                    if verbose:
                        log(f"执行k_best特征选择: {len(selected_cols)} > {k_best_features}")

                    # 使用简单的方法选择特征 - 基于方差
                    feature_variances = result_df[selected_cols].var()
                    top_k_features = feature_variances.nlargest(k_best_features).index.tolist()
                    result_df = result_df[identity_cols + [time_col] + top_k_features]

                    if verbose:
                        log(f"特征选择完成，从{len(feature_cols)}个特征中选择了{len(top_k_features)}个")
                else:
                    if verbose:
                        log(f"跳过k_best选择: {len(selected_cols)} <= {k_best_features}")

                    # 即使selected_cols数量 <= k_best_features，也要确保应用方差过滤
                    result_df = result_df[identity_cols + [time_col] + selected_cols]
                    if verbose:
                        log(f"特征选择完成，从{len(feature_cols)}个特征中保留了{len(selected_cols)}个特征")

            except Exception as e:
                if verbose:
                    log(f"特征选择失败: {e}，保留所有特征")

    # 最终清理
    log("进行最终数据清理...")
    # 替换剩余的无穷大值和NaN
    result_df = result_df.replace([np.inf, -np.inf], np.nan)
    result_df = result_df.fillna(0)

    log(f"特征计算完成！结果数据框形状: {result_df.shape}")
    return result_df


def calculate_features_based_on_selected(
    df: pd.DataFrame,
    selected_features: List[str],
    # 基础数据列配置
    time_col: str = 'DT_TIME',
    price_col: str = 'AMT',
    balance_col: str = 'ACCBAL',
    amount_col: str = 'CNY_AMT',
    identity_cols: List[str] = None,

    # 基础参数
    moving_windows: List[int] = None,
    volume_windows: List[int] = None,
    technical_windows: List[int] = None,
    lag_periods: List[int] = None,

    # 数据清理配置
    clean_infinite: bool = True,
    fill_missing: bool = True,
    handle_outliers: bool = True,
    outlier_threshold: float = 3.0,

    # 打印配置
    verbose: bool = True
) -> pd.DataFrame:
    """
    基于已选择的特征计算相关指标，提高计算效率和针对性

    Args:
        df: 输入数据框
        selected_features: 已选择的特征列名列表
        time_col: 时间列名，默认为'DT_TIME'
        price_col: 价格列名，默认为'AMT'
        balance_col: 余额列名，默认为'ACCBAL'
        amount_col: 金额列名，默认为'CNY_AMT'
        identity_cols: 标识列列表，默认为['ACCT_NUM', 'PARTY_ID', 'OPP_PARTY_ID', 'ACCT', 'TCAC', 'TSTM']
        moving_windows: 移动窗口周期列表，默认为[3, 5, 7]
        volume_windows: 成交量窗口周期列表，默认为[3, 5, 7]
        technical_windows: 技术分析窗口周期列表，默认为[5, 10, 20]
        lag_periods: 滞后期数列表，默认为[1, 2, 3]
        clean_infinite: 是否清理无穷大值，默认为True
        fill_missing: 是否填充缺失值，默认为True
        handle_outliers: 是否处理异常值，默认为True
        outlier_threshold: 异常值阈值，默认为3.0
        verbose: 是否打印详细日志，默认为True

    Returns:
        pd.DataFrame: 包含指定特征指标的数据框
    """

    # 设置默认值
    if identity_cols is None:
        identity_cols = ['ACCT_NUM', 'PARTY_ID', 'OPP_PARTY_ID', 'ACCT', 'TCAC', 'TSTM']

    if moving_windows is None:
        moving_windows = [3, 5, 7]
    if volume_windows is None:
        volume_windows = [3, 5, 7]
    if technical_windows is None:
        technical_windows = [5, 10, 20]
    if lag_periods is None:
        lag_periods = [1, 2, 3]

    def log(message):
        """简单的日志函数"""
        if verbose:
            print(f"[{time.strftime('%H:%M:%S')}] {message}")

    log(f"开始基于选定特征计算指标，目标特征数: {len(selected_features)}")
    result_df = df.copy()

    # ==================== 数据清理 ====================
    log("开始数据清理...")
    numeric_cols = [col for col in result_df.columns if result_df[col].dtype in ['int64', 'float64']]

    for col in numeric_cols:
        if col in result_df.columns:
            # 处理无穷大值
            if clean_infinite:
                result_df[col] = result_df[col].replace([np.inf, -np.inf], np.nan)

            # 处理缺失值
            if fill_missing:
                nan_count = result_df[col].isnull().sum()
                if nan_count > 0:
                    result_df[col] = result_df[col].ffill().interpolate().bfill().fillna(0)
                    if verbose:
                        log(f"列{col}处理了{nan_count}个缺失值")

            # 处理异常值
            if handle_outliers and result_df[col].dtype in ['int64', 'float64']:
                cleaned_series = result_df[col].dropna()
                if len(cleaned_series) > 0 and cleaned_series.std() > 0:
                    try:
                        z_scores = np.abs(stats.zscore(cleaned_series))
                        outliers = z_scores > outlier_threshold
                        if outliers.sum() > 0:
                            lower_bound = cleaned_series.quantile(0.01)
                            upper_bound = cleaned_series.quantile(0.99)
                            result_df[col] = result_df[col].clip(lower_bound, upper_bound)
                            if verbose:
                                log(f"列{col}处理了{outliers.sum()}个异常值")
                    except:
                        pass

    # ==================== 分析选定特征并计算相关指标 ====================
    # 将特征按类别分组
    lag_return_features = [col for col in selected_features if 'lag_return' in col]
    lag_price_features = [col for col in selected_features if col.endswith('_lag_1') or col.endswith('_lag_2') or col.endswith('_lag_3')]
    price_position_features = [col for col in selected_features if 'price_position' in col]
    obv_features = [col for col in selected_features if 'OBV' in col]
    bollinger_features = [col for col in selected_features if 'Bollinger' in col]
    resistance_features = [col for col in selected_features if 'Resistance_Level' in col]
    max_features = [col for col in selected_features if col.startswith('MAX_')]
    quantile_features = [col for col in selected_features if col.startswith('Q') and ('_3' in col or '_5' in col or '_7' in col)]
    vwap_features = [col for col in selected_features if 'VWAP' in col]
    ma_features = [col for col in selected_features if col.startswith('MA_') and len(col) <= 5]
    vma_features = [col for col in selected_features if col.startswith('VMA_')]
    price_high_low_features = [col for col in selected_features if col in ['price_high', 'price_low']]

    # 计算滞后收益特征
    if lag_return_features:
        log("计算滞后收益特征...")
        if price_col in result_df.columns:
            for lag in lag_periods:
                if f'{price_col}_lag_{lag}' not in result_df.columns:
                    result_df[f'{price_col}_lag_{lag}'] = result_df[price_col].shift(lag).fillna(0)

                if f'lag_return_{lag}' not in result_df.columns:
                    lag_return = (result_df[price_col] - result_df[f'{price_col}_lag_{lag}']) / \
                                (result_df[f'{price_col}_lag_{lag}'] + 1e-8)
                    result_df[f'lag_return_{lag}'] = lag_return.fillna(0)

    # 计算价格位置特征
    if price_position_features:
        log("计算价格位置特征...")
        if price_col in result_df.columns:
            # 计算高低价
            window = 5
            if balance_col in result_df.columns:
                result_df['price_high'] = result_df[balance_col].rolling(window=window, min_periods=1).max()
                result_df['price_low'] = result_df[balance_col].rolling(window=window, min_periods=1).min()

            if 'price_high' in result_df.columns and 'price_low' in result_df.columns:
                epsilon = 1e-8
                price_range = result_df['price_high'] - result_df['price_low']
                price_range = price_range.replace(0, epsilon)
                result_df['price_position'] = ((result_df[price_col] - result_df['price_low']) / price_range).fillna(0.5)

    # 计算移动平均特征
    if ma_features:
        log("计算移动平均特征...")
        if price_col in result_df.columns:
            for feature in ma_features:
                if feature == 'MA_3' and 3 in moving_windows:
                    result_df['MA_3'] = result_df[price_col].rolling(window=3, min_periods=1).mean()
                elif feature == 'MA_5' and 5 in moving_windows:
                    result_df['MA_5'] = result_df[price_col].rolling(window=5, min_periods=1).mean()
                elif feature == 'MA_7' and 7 in moving_windows:
                    result_df['MA_7'] = result_df[price_col].rolling(window=7, min_periods=1).mean()

    # 计算最大值特征
    if max_features:
        log("计算最大值特征...")
        if price_col in result_df.columns:
            for feature in max_features:
                window = int(feature.split('_')[1])
                if window in moving_windows:
                    result_df[feature] = result_df[price_col].rolling(window=window, min_periods=1).max()

    # 计算分位数特征
    if quantile_features:
        log("计算分位数特征...")
        if price_col in result_df.columns:
            for feature in quantile_features:
                if feature.startswith('Q75_'):
                    window = int(feature.split('_')[1])
                    if window in moving_windows:
                        result_df[feature] = result_df[price_col].rolling(window=window, min_periods=1).quantile(0.75)
                elif feature.startswith('Q50_'):
                    window = int(feature.split('_')[1])
                    if window in moving_windows:
                        result_df[feature] = result_df[price_col].rolling(window=window, min_periods=1).quantile(0.50)

    # 计算布林带特征
    if bollinger_features:
        log("计算布林带特征...")
        if price_col in result_df.columns:
            for feature in bollinger_features:
                if 'Upper' in feature:
                    window = int(feature.split('_')[2])
                    if window in technical_windows:
                        ma = result_df[price_col].rolling(window=window, min_periods=1).mean()
                        std = result_df[price_col].rolling(window=window, min_periods=1).std()
                        result_df[feature] = ma + (2 * std)

    # 计算阻力位特征
    if resistance_features:
        log("计算阻力位特征...")
        if price_col in result_df.columns:
            for feature in resistance_features:
                window = int(feature.split('_')[2])
                if window in technical_windows:
                    result_df[feature] = result_df[price_col].rolling(window=window, min_periods=1).max()

    # 计算成交量指标
    if obv_features:
        log("计算成交量指标...")
        volume_col = price_col  # 使用价格列作为成交量代理

        if 'OBV' in obv_features:
            price_change = result_df[volume_col].diff()
            obv = np.where(price_change > 0, result_df[volume_col],
                          np.where(price_change < 0, -result_df[volume_col], 0))
            result_df['OBV'] = np.cumsum(obv)

        if 'OBV_MA' in obv_features:
            if 'OBV' not in result_df.columns:
                price_change = result_df[volume_col].diff()
                obv = np.where(price_change > 0, result_df[volume_col],
                              np.where(price_change < 0, -result_df[volume_col], 0))
                result_df['OBV'] = np.cumsum(obv)
            result_df['OBV_MA'] = result_df['OBV'].rolling(window=20, min_periods=1).mean()

    # 计算VWAP特征
    if vwap_features:
        log("计算VWAP特征...")
        if price_col in result_df.columns and amount_col in result_df.columns:
            volume_col = price_col
            for feature in vwap_features:
                window = int(feature.split('_')[1])
                if window in volume_windows:
                    if result_df[volume_col].sum() > 0:
                        vwap = (result_df[price_col] * result_df[volume_col]).rolling(window=window, min_periods=1).sum() / \
                               result_df[volume_col].rolling(window=window, min_periods=1).sum()
                        result_df[feature] = vwap.fillna(result_df[price_col])

    # 计算成交量移动平均
    if vma_features:
        log("计算成交量移动平均...")
        volume_col = price_col
        for feature in vma_features:
            window = int(feature.split('_')[1])
            if window in volume_windows:
                result_df[feature] = result_df[volume_col].rolling(window=window, min_periods=1).mean()

    # 确保数据按时间排序
    if time_col in result_df.columns:
        result_df = result_df.sort_values(time_col).reset_index(drop=True)

    # 最终清理
    log("进行最终数据清理...")
    result_df = result_df.replace([np.inf, -np.inf], np.nan)
    result_df = result_df.fillna(0)

    # 选择最终需要的列
    available_features = [col for col in selected_features if col in result_df.columns]
    final_cols = identity_cols + [time_col] + available_features
    final_cols = [col for col in final_cols if col in result_df.columns]

    result_df = result_df[final_cols]

    log(f"基于选定特征的指标计算完成！结果数据框形状: {result_df.shape}")
    log(f"成功计算的特征: {len(available_features)}/{len(selected_features)}")

    return result_df