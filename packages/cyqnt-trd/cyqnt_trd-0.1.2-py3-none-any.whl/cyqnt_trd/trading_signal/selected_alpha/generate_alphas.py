"""
生成所有101个Alpha因子文件的脚本

这个脚本读取alpha_cal_reference.py并生成适配crypto数据格式的alpha因子文件。
"""

import re
import os

# Alpha因子定义（从reference文件中提取）
ALPHA_DEFINITIONS = {
    1: ("rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) -0.5", 
        "rank(Ts_ArgMax(SignedPower(((returns<0)?stddev(returns,20):close),2.),5))-0.5)"),
    2: ("-1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6)", 
        "-1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6)"),
    3: ("-1 * correlation(rank(open), rank(volume), 10)", 
        "-1 * correlation(rank(open), rank(volume), 10)"),
    4: ("-1 * Ts_Rank(rank(low), 9)", 
        "-1 * ts_rank(rank(low), 9)"),
    5: ("(rank((open - (sum(vwap, 10) / 10))) * (-1 * abs(rank((close - vwap)))))", 
        "(rank((open - (ts_sum(vwap, 10) / 10))) * (-1 * abs(rank((close - vwap)))))"),
    6: ("-1 * correlation(open, volume, 10)", 
        "-1 * correlation(open, volume, 10)"),
    7: ("((adv20 < volume) ? ((-1 * ts_rank(abs(delta(close, 7)), 60)) * sign(delta(close, 7))) : (-1* 1))", 
        "((adv20 < volume) ? ((-1 * ts_rank(abs(delta(close, 7)), 60)) * sign(delta(close, 7))) : (-1* 1))"),
    8: ("-1 * rank(((sum(open, 5) * sum(returns, 5)) - delay((sum(open, 5) * sum(returns, 5)),10))))", 
        "-1 * rank(((ts_sum(open, 5) * ts_sum(returns, 5)) - delay((ts_sum(open, 5) * ts_sum(returns, 5)),10))))"),
    9: ("((0 < ts_min(delta(close, 1), 5)) ? delta(close, 1) : ((ts_max(delta(close, 1), 5) < 0) ?delta(close, 1) : (-1 * delta(close, 1))))", 
        "((0 < ts_min(delta(close, 1), 5)) ? delta(close, 1) : ((ts_max(delta(close, 1), 5) < 0) ?delta(close, 1) : (-1 * delta(close, 1))))"),
    10: ("rank(((0 < ts_min(delta(close, 1), 4)) ? delta(close, 1) : ((ts_max(delta(close, 1), 4) < 0)? delta(close, 1) : (-1 * delta(close, 1)))))", 
         "rank(((0 < ts_min(delta(close, 1), 4)) ? delta(close, 1) : ((ts_max(delta(close, 1), 4) < 0)? delta(close, 1) : (-1 * delta(close, 1)))))"),
}

def generate_alpha_file(alpha_num, formula, description=""):
    """生成单个alpha文件"""
    
    template = f'''"""
Alpha#{alpha_num} 因子

公式: {formula}

说明：
{description}

标签：待补充
"""

import pandas as pd
import numpy as np
from typing import Optional
from .alpha_utils import (
    ts_sum, sma, stddev, correlation, covariance,
    ts_rank, product, ts_min, ts_max, delta, delay,
    rank, scale, ts_argmax, ts_argmin, decay_linear,
    sign, abs, log, signed_power
)


def alpha{alpha_num}_factor(
    data_slice: pd.DataFrame,
    **kwargs
) -> float:
    """
    Alpha#{alpha_num} 因子计算
    
    Args:
        data_slice: 数据切片，必须包含以下列：
                   - open_price: 开盘价
                   - high_price: 最高价
                   - low_price: 最低价
                   - close_price: 收盘价
                   - volume: 成交量
                   - quote_volume: 成交额（用于计算vwap）
        **kwargs: 其他可选参数
    
    Returns:
        因子值（最后一个时间点的值）
    """
    try:
        if len(data_slice) < 2:
            return 0.0
        
        # 提取数据列
        open_price = data_slice['open_price']
        high_price = data_slice['high_price']
        low_price = data_slice['low_price']
        close_price = data_slice['close_price']
        volume = data_slice['volume']
        quote_volume = data_slice.get('quote_volume', volume * close_price)  # 如果没有quote_volume，使用volume*close_price估算
        
        # 计算收益率
        returns = close_price.pct_change().fillna(0)
        
        # 计算VWAP (Volume Weighted Average Price)
        # vwap = quote_volume / volume，如果volume为0则使用close_price
        vwap = (quote_volume / (volume + 1e-10)).fillna(close_price)
        
        # 计算adv20 (20日平均成交量)
        adv20 = sma(volume, 20)
        
        # 实现Alpha因子逻辑
        # TODO: 根据具体公式实现
        
        # 临时返回0，需要根据具体公式实现
        return 0.0
        
    except Exception as e:
        # 如果计算出错，返回0
        return 0.0
'''
    
    return template


if __name__ == "__main__":
    # 生成所有alpha文件
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    for alpha_num in range(1, 102):
        if alpha_num in ALPHA_DEFINITIONS:
            formula, _ = ALPHA_DEFINITIONS[alpha_num]
        else:
            formula = f"Alpha#{alpha_num} formula"
        
        content = generate_alpha_file(alpha_num, formula)
        
        file_path = os.path.join(base_dir, f"alpha{alpha_num}.py")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Generated alpha{alpha_num}.py")


