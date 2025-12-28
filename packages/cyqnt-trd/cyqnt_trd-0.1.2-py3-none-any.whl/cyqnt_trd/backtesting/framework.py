"""
回测框架主模块

提供统一的回测框架接口
"""

import pandas as pd
import json
import os
import re
from typing import Callable, Optional, Dict, Tuple
from .factor_test import FactorTester
from .strategy_backtest import StrategyBacktester


class BacktestFramework:
    """
    回测框架主类
    
    提供统一的接口来使用因子测试和策略回测功能
    """
    
    def __init__(self, data_path: Optional[str] = None, data: Optional[pd.DataFrame] = None):
        """
        初始化回测框架
        
        Args:
            data_path: JSON数据文件路径（可选）
            data: 直接提供DataFrame数据（可选）
        
        注意: data_path 和 data 必须提供其中一个
        """
        self.data_path = data_path
        self.source_start_time = None
        self.source_end_time = None
        
        if data_path:
            # 从JSON文件加载数据
            with open(data_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            if isinstance(json_data, dict) and 'data' in json_data:
                self.data = pd.DataFrame(json_data['data'])
                # 从源数据中提取时间范围
                if len(json_data['data']) > 0:
                    first_item = json_data['data'][0]
                    last_item = json_data['data'][-1]
                    
                    # 提取开始时间（使用第一个数据的open_time_str）
                    if 'open_time_str' in first_item:
                        try:
                            self.source_start_time = pd.to_datetime(first_item['open_time_str'])
                        except Exception:
                            pass
                    
                    # 提取结束时间（使用最后一个数据的close_time_str）
                    if 'close_time_str' in last_item:
                        try:
                            self.source_end_time = pd.to_datetime(last_item['close_time_str'])
                        except Exception:
                            pass
            else:
                self.data = pd.DataFrame(json_data)
        
        elif data is not None:
            self.data = data.copy()
        else:
            raise ValueError("必须提供 data_path 或 data 参数")
        
        # 初始化测试器
        self.factor_tester = FactorTester(self.data)
        self.strategy_backtester = StrategyBacktester(self.data)
    
    def _get_source_time_range(self) -> Tuple[Optional[str], Optional[str]]:
        """
        获取源数据的时间范围
        
        Returns:
            (start_str, end_str): 开始日期和结束日期的字符串（格式：YYYYMMDD），如果无法获取则返回 (None, None)
        """
        if self.source_start_time is not None and self.source_end_time is not None:
            try:
                start_str = self.source_start_time.strftime('%Y%m%d %H%M%S')
                end_str = self.source_end_time.strftime('%Y%m%d %H%M%S')
                return start_str, end_str
            except Exception:
                pass
        return None, None
    
    def _extract_data_name(self, data_path: Optional[str] = None) -> Optional[str]:
        """
        从数据路径中提取数据名称
        
        Args:
            data_path: 数据文件路径（如果为None，使用self.data_path）
        
        Returns:
            数据名称（如 ETHUSDT），如果无法提取则返回None
        """
        path = data_path or self.data_path
        if not path:
            return None
        
        # 从文件名中提取，例如：ETHUSDT_1d_1095_20251127_114210.json -> ETHUSDT
        filename = os.path.basename(path)
        # 匹配交易对名称（通常是大写字母+数字的组合，如 BTCUSDT, ETHUSDT）
        match = re.match(r'^([A-Z0-9]+)', filename)
        if match:
            return match.group(1)
        
        # 如果文件名不匹配，尝试从路径中提取
        # 例如：.../ETHUSDT_futures/... -> ETHUSDT
        path_parts = path.split(os.sep)
        for part in path_parts:
            if '_' in part:
                # 尝试提取交易对名称
                match = re.match(r'^([A-Z0-9]+)', part)
                if match:
                    return match.group(1)
        
        return None
    
    def test_factor(
        self,
        factor_func: Callable[[pd.DataFrame, int], float],
        forward_periods: int = 7,
        min_periods: int = 0,
        factor_name: str = "factor"
    ) -> Dict:
        """
        测试单因子胜率
        
        Args:
            factor_func: 因子计算函数，接受数据切片作为参数
                        (data_slice: pd.DataFrame) -> float
            forward_periods: 向前看的周期数
            min_periods: 最小需要的周期数
            factor_name: 因子名称
        
        Returns:
            测试结果字典
        """
        return self.factor_tester.test_factor(
            factor_func=factor_func,
            forward_periods=forward_periods,
            min_periods=min_periods,
            factor_name=factor_name
        )
    
    def backtest_strategy(
        self,
        signal_func: Callable,
        min_periods: int = 0,
        position_size: float = 1.0,
        initial_capital: float = 10000.0,
        commission_rate: float = 0.001,
        take_profit: Optional[float] = None,
        stop_loss: Optional[float] = None,
        check_periods: int = 1,
        strategy_name: Optional[str] = None
    ) -> Dict:
        """
        回测策略
        
        Args:
            signal_func: 信号生成函数，必须接受以下参数：
                        (data_slice, position, entry_price, entry_index, take_profit, stop_loss, check_periods) -> str
                        - data_slice: 数据切片（包含历史数据和当前数据点）
                        - position: 当前持仓数量
                        - entry_price: 入场价格
                        - entry_index: 入场索引
                        - take_profit: 止盈比例
                        - stop_loss: 止损比例
                        - check_periods: 检查未来多少个周期（只能为1，因为实际使用时无法看到未来数据）
                        策略函数可以根据持仓信息自行决定是否止盈止损
            min_periods: 最小需要的周期数
            position_size: 每次交易的仓位大小
            initial_capital: 初始资金
            commission_rate: 手续费率
            take_profit: 止盈比例（例如：0.1 表示 10%），传递给策略函数，由策略决定是否使用
            stop_loss: 止损比例（例如：0.1 表示 10%），传递给策略函数，由策略决定是否使用
            check_periods: 检查未来多少个周期（只能为1，默认1，即只检查当前周期）
                          注意：回测时只能为1，因为实际交易中无法看到今天之后的数据
            strategy_name: 策略名称（用于保存结果时的文件命名）
        
        Returns:
            回测结果字典（包含 strategy_name 字段）
        
        Raises:
            ValueError: 如果 check_periods 不等于 1
        """
        # 验证 check_periods 只能为 1
        if check_periods != 1:
            raise ValueError(
                f"回测策略时 check_periods 只能为 1，因为实际使用时无法看到今天之后的数据。"
                f"当前值: {check_periods}"
            )
        
        # 更新初始资金和手续费率
        self.strategy_backtester.initial_capital = initial_capital
        self.strategy_backtester.commission_rate = commission_rate
        
        results = self.strategy_backtester.backtest(
            signal_func=signal_func,
            min_periods=min_periods,
            position_size=position_size,
            take_profit=take_profit,
            stop_loss=stop_loss,
            check_periods=check_periods
        )
        
        # 将策略名称添加到结果中
        if strategy_name:
            results['strategy_name'] = strategy_name
        
        return results
    
    def plot_backtest_results(
        self, 
        results: Dict, 
        figsize: tuple = (14, 10),
        save_dir: Optional[str] = None,
        strategy_name: Optional[str] = None,
        data_name: Optional[str] = None
    ):
        """
        绘制回测结果
        
        Args:
            results: backtest_strategy返回的结果字典
            figsize: 图形大小
            save_dir: 保存目录（如果提供，将自动保存图片和JSON）
            strategy_name: 策略名称（如果为None，尝试从results中获取）
            data_name: 数据名称（如果为None，尝试从数据路径中提取）
        """
        # 获取策略名称
        if strategy_name is None:
            strategy_name = results.get('strategy_name')
        
        # 获取数据名称
        if data_name is None:
            data_name = self._extract_data_name()
        
        # 如果提供了save_dir但没有strategy_name或data_name，打印警告
        if save_dir and (not strategy_name or not data_name):
            if not strategy_name:
                print(f"警告: 无法获取策略名称，将使用默认名称保存图片")
            if not data_name:
                print(f"警告: 无法从数据路径中提取数据名称，将使用默认名称保存图片")
                print(f"  数据路径: {self.data_path}")
        
        # 获取源数据的时间范围
        source_start_str, source_end_str = self._get_source_time_range()
        
        # 调用plot_results，如果提供了策略名称和数据名称，将自动保存
        self.strategy_backtester.plot_results(
            results=results,
            figsize=figsize,
            strategy_name=strategy_name,
            data_name=data_name,
            save_dir=save_dir,
            source_start_str=source_start_str,
            source_end_str=source_end_str
        )
    
    def print_factor_results(
        self, 
        results: Dict,
        save_dir: Optional[str] = None,
        factor_name: Optional[str] = None,
        data_name: Optional[str] = None
    ):
        """
        打印因子测试结果
        
        Args:
            results: test_factor返回的结果字典
            save_dir: 保存目录（如果提供，将自动保存JSON）
            factor_name: 因子名称（如果为None，尝试从results中获取）
            data_name: 数据名称（如果为None，尝试从数据路径中提取）
        """
        # 获取因子名称
        if factor_name is None:
            factor_name = results.get('factor_name')
        
        # 获取数据名称
        if data_name is None:
            data_name = self._extract_data_name()
        
        # 获取源数据的时间范围
        source_start_str, source_end_str = self._get_source_time_range()
        
        # 调用print_results，如果提供了保存目录，将自动保存
        self.factor_tester.print_results(
            results=results,
            save_dir=save_dir,
            factor_name=factor_name,
            data_name=data_name,
            source_start_str=source_start_str,
            source_end_str=source_end_str
        )
    
    def print_backtest_results(self, results: Dict):
        """
        打印回测结果
        
        Args:
            results: backtest_strategy返回的结果字典
        """
        self.strategy_backtester.print_results(results)

