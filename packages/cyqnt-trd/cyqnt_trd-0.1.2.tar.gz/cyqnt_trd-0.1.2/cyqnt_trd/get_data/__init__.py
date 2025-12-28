"""
数据获取模块

提供从 Binance 获取期货和现货K线数据的功能
"""

from .get_futures_data import get_and_save_futures_klines
from .get_trending_data import get_and_save_klines, get_and_save_klines_direct

__all__ = [
    'get_and_save_futures_klines',
    'get_and_save_klines',
    'get_and_save_klines_direct',
]

