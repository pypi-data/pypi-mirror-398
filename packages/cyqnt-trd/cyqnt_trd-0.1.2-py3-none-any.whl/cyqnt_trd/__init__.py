"""
Cyqnt Trading Package

一个用于加密货币交易的工具包，包含数据获取、交易信号生成和回测功能。

主要模块:
- get_data: 数据获取模块，支持从 Binance 获取期货和现货数据
- trading_signal: 交易信号模块，包含因子计算和信号策略
- backtesting: 回测框架，支持因子测试和策略回测
"""

__version__ = "0.1.0"

# 导入主要模块
from . import get_data
from . import trading_signal
from . import backtesting

__all__ = [
    'get_data',
    'trading_signal',
    'backtesting',
    'utils',
    '__version__',
]

