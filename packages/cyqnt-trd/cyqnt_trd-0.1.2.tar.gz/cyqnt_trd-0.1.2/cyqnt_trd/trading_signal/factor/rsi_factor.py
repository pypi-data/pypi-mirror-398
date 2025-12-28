"""
RSI（相对强弱指标）因子

基于RSI指标的交易因子
"""

import pandas as pd
import numpy as np


def rsi_factor(data_slice: 'pd.DataFrame', period: int = 14, oversold: float = 30.0, overbought: float = 70.0) -> float:
    """
    RSI因子
    
    当RSI低于oversold时看多，高于overbought时看空
    
    Args:
        data_slice: 数据切片，必须包含至少 period+1 行数据
                   最后一行是当前数据点，前面 period 行是历史数据
        period: RSI计算周期（默认14）
        oversold: 超卖阈值（默认30）
        overbought: 超买阈值（默认70）
    
    Returns:
        因子值：1.0（看多）、-1.0（看空）或 0（数据不足或中性）
    """
    if len(data_slice) < period + 1:
        return 0.0
    
    # 计算价格变化（使用最后period+1行数据）
    prices = data_slice.iloc[-period-1:]['close_price'].values
    deltas = np.diff(prices)
    
    # 分离上涨和下跌
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    # 计算平均收益和平均损失
    avg_gain = np.mean(gains)
    avg_loss = np.mean(losses)
    
    # 计算RSI
    if avg_loss == 0:
        rsi = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
    
    # 根据RSI值返回因子
    if rsi < oversold:
        return 1.0  # 超卖，看多
    elif rsi > overbought:
        return -1.0  # 超买，看空
    else:
        return 0.0  # 中性

