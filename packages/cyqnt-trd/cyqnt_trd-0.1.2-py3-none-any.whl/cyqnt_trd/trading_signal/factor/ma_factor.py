"""
移动平均线因子

包含基于移动平均线的各种因子
"""

import pandas as pd
import numpy as np


def ma_factor(data_slice: 'pd.DataFrame', period: int = 5) -> float:
    """
    简单移动平均线因子
    
    如果当前价格高于过去period期的平均价格，返回1（看多）
    否则返回-1（看空）
    
    Args:
        data_slice: 数据切片，必须包含至少 period+1 行数据
                   最后一行是当前数据点，前面 period 行是历史数据
        period: 移动平均周期（默认5）
    
    Returns:
        因子值：1.0（看多）、-1.0（看空）或 0（数据不足）
    """
    if len(data_slice) < period + 1:
        return 0.0
    
    # 最后一行是当前数据点
    current_price = data_slice.iloc[-1]['close_price']
    # 前period行是历史数据（不包括最后一行）
    # 使用最后period行数据计算MA
    ma = data_slice.iloc[-period-1:-1]['close_price'].mean()
    
    if current_price > ma:
        return 1.0  # 看多
    else:
        return -1.0  # 看空


def ma_cross_factor(data_slice: 'pd.DataFrame', short_period: int = 5, long_period: int = 20) -> float:
    """
    移动平均线交叉因子
    
    当短期均线上穿长期均线时看多，下穿时看空
    
    Args:
        data_slice: 数据切片，必须包含至少 long_period+2 行数据
                   最后一行是当前数据点，前面 long_period+1 行是历史数据
        short_period: 短期均线周期（默认5）
        long_period: 长期均线周期（默认20）
    
    Returns:
        因子值：1.0（看多）、-1.0（看空）或 0（数据不足）
    """
    if len(data_slice) < long_period + 2:
        return 0.0
    
    # 计算当前周期的均线（使用最后period行数据，不包括最后一行）
    short_ma_current = data_slice.iloc[-short_period-1:-1]['close_price'].mean()
    long_ma_current = data_slice.iloc[-long_period-1:-1]['close_price'].mean()
    
    # 计算上一周期的均线（使用倒数第二行之前的数据）
    short_ma_prev = data_slice.iloc[-short_period-2:-2]['close_price'].mean()
    long_ma_prev = data_slice.iloc[-long_period-2:-2]['close_price'].mean()
    
    # 上穿：之前短期均线在长期均线下方，现在在上方
    if short_ma_prev <= long_ma_prev and short_ma_current > long_ma_current:
        return 1.0  # 看多
    # 下穿：之前短期均线在长期均线上方，现在在下方
    elif short_ma_prev >= long_ma_prev and short_ma_current < long_ma_current:
        return -1.0  # 看空
    else:
        return 0.0  # 中性

