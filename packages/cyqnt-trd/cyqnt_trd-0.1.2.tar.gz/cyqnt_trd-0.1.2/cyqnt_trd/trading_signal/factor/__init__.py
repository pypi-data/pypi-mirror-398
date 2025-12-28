"""
交易因子模块

定义各种交易因子，用于预测价格方向
因子函数签名: factor_func(data: pd.DataFrame, index: int) -> float
- 正数表示看多，负数表示看空，0表示中性
"""

# 导入所有因子
from .ma_factor import ma_factor, ma_cross_factor
from .rsi_factor import rsi_factor

__all__ = [
    'ma_factor',
    'ma_cross_factor',
    'rsi_factor',
]

