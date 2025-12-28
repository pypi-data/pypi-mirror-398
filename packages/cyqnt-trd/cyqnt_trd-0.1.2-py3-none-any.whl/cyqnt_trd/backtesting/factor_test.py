"""
单因子胜率测试模块

用于测试某个因子在预测未来价格方向上的胜率
"""

import pandas as pd
import numpy as np
from typing import Callable, Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import json
import os


class FactorTester:
    """
    单因子胜率测试器
    
    用于测试某个因子在预测未来一段时间内价格方向（多/空）的胜率
    """
    
    def __init__(self, data: pd.DataFrame):
        """
        初始化因子测试器
        
        Args:
            data: 包含K线数据的DataFrame，必须包含以下列：
                  - datetime 或 open_time_str: 时间
                  - close_price: 收盘价
                  以及其他因子计算所需的列
        """
        self.data = data.copy()
        
        # 确保有datetime列
        if 'datetime' not in self.data.columns:
            if 'open_time_str' in self.data.columns:
                self.data['datetime'] = pd.to_datetime(self.data['open_time_str'])
            elif 'open_time' in self.data.columns:
                self.data['datetime'] = pd.to_datetime(self.data['open_time'], unit='ms')
            else:
                raise ValueError("数据必须包含 'datetime', 'open_time_str' 或 'open_time' 列")
        
        # 确保有close_price列
        if 'close_price' not in self.data.columns:
            raise ValueError("数据必须包含 'close_price' 列")
        
        # 按时间排序
        self.data = self.data.sort_values('datetime').reset_index(drop=True)
    
    def test_factor(
        self,
        factor_func: Callable[[pd.DataFrame], float],
        forward_periods: int = 7,
        min_periods: int = 0,
        factor_name: str = "factor"
    ) -> Dict:
        """
        测试单因子的胜率
        
        Args:
            factor_func: 因子计算函数，接受数据切片作为参数，返回因子值
                        - data_slice: 数据切片（包含历史数据和当前数据点）
                        - 返回: 因子值（正数表示看多，负数表示看空，0表示中性）
            forward_periods: 向前看的周期数（例如：7表示未来7个周期）
            min_periods: 最小需要的周期数（用于计算因子时）
            factor_name: 因子名称，用于结果标识
        
        Returns:
            包含测试结果的字典：
            - factor_name: 因子名称
            - total_samples: 总样本数
            - long_signals: 看多信号数量
            - short_signals: 看空信号数量
            - neutral_signals: 中性信号数量
            - long_win_rate: 看多信号胜率
            - short_win_rate: 看空信号胜率
            - overall_win_rate: 总体胜率
            - long_avg_return: 看多信号平均收益率
            - short_avg_return: 看空信号平均收益率
            - details: 详细结果列表
        """
        results = {
            'factor_name': factor_name,
            'total_samples': 0,
            'long_signals': 0,
            'short_signals': 0,
            'neutral_signals': 0,
            'long_win_rate': 0.0,
            'short_win_rate': 0.0,
            'overall_win_rate': 0.0,
            'long_avg_return': 0.0,
            'short_avg_return': 0.0,
            'details': []
        }
        
        long_wins = 0
        short_wins = 0
        long_returns = []
        short_returns = []
        
        # 遍历每个时间点（确保有足够的数据向前看）
        for i in range(min_periods, len(self.data) - forward_periods):
            try:
                # 计算因子值：传递数据切片而不是整个data和index
                # 需要确定因子函数需要多少历史数据
                # 为了兼容性，传递足够的数据切片（假设最多需要50个周期）
                max_period = 50
                start_idx = max(0, i - max_period)
                data_slice = self.data.iloc[start_idx:i+1].copy()
                factor_value = factor_func(data_slice)
                
                if factor_value is None or np.isnan(factor_value):
                    continue
                
                # 获取当前价格
                current_price = self.data.iloc[i]['close_price']
                
                # 获取未来 forward_periods 个周期的价格数据
                future_start_idx = i + 1
                future_end_idx = min(i + forward_periods + 1, len(self.data))
                
                if future_end_idx <= future_start_idx:
                    continue
                
                future_prices = self.data.iloc[future_start_idx:future_end_idx]['close_price'].values
                future_prices_max = self.data.iloc[future_start_idx:future_end_idx]['high_price'].values
                future_prices_min = self.data.iloc[future_start_idx:future_end_idx]['low_price'].values
                
                # 获取最后一个周期的价格用于计算收益率
                future_idx = i + forward_periods
                if future_idx >= len(self.data):
                    future_price = self.data.iloc[-1]['close_price']
                else:
                    future_price = self.data.iloc[future_idx]['close_price']
                
                # 计算未来收益率（基于最后一个周期）
                future_return = (future_price - current_price) / current_price
                
                # 判断信号类型和是否获胜
                signal_type = None
                is_win = False
                
                if factor_value > 0:
                    # 看多信号：只要未来 n 个周期内存在任一价格高于当前价格，即认为获胜
                    signal_type = 'long'
                    results['long_signals'] += 1
                    is_win = bool(np.any(future_prices > current_price))
                    if is_win:
                        long_wins += 1
                    long_returns.append(future_return)
                    
                elif factor_value < 0:
                    # 看空信号：只要未来 n 个周期内存在任一价格低于当前价格，即认为获胜
                    signal_type = 'short'
                    results['short_signals'] += 1
                    is_win = bool(np.any(future_prices < current_price))
                    if is_win:
                        short_wins += 1
                    short_returns.append(future_return)
                    
                else:
                    # 中性信号
                    signal_type = 'neutral'
                    results['neutral_signals'] += 1
                
                # 记录详细信息
                results['details'].append({
                    'datetime': self.data.iloc[i]['datetime'],
                    'index': i,
                    'factor_value': float(factor_value),
                    'signal_type': signal_type,
                    'current_price': float(current_price),
                    'future_price': float(future_price),
                    'future_return': float(future_return),
                    'is_win': is_win
                })
                
                results['total_samples'] += 1
                
            except Exception as e:
                # 如果因子计算出错，跳过该点
                continue
        
        # 计算胜率
        if results['long_signals'] > 0:
            results['long_win_rate'] = long_wins / results['long_signals']
            results['long_avg_return'] = np.mean(long_returns) if long_returns else 0.0
        
        if results['short_signals'] > 0:
            results['short_win_rate'] = short_wins / results['short_signals']
            results['short_avg_return'] = np.mean(short_returns) if short_returns else 0.0
        
        total_wins = long_wins + short_wins
        total_signals = results['long_signals'] + results['short_signals']
        if total_signals > 0:
            results['overall_win_rate'] = total_wins / total_signals
        
        return results
    
    def print_results(
        self, 
        results: Dict,
        save_dir: Optional[str] = None,
        factor_name: Optional[str] = None,
        data_name: Optional[str] = None,
        save_json: Optional[str] = None,
        source_start_str: Optional[str] = None,
        source_end_str: Optional[str] = None
    ):
        """
        打印测试结果
        
        Args:
            results: test_factor返回的结果字典
            save_dir: 保存目录（如果提供factor_name和data_name，将在此目录下保存文件）
            factor_name: 因子名称（用于自动生成文件名，如果为None，从results中获取）
            data_name: 数据名称（用于自动生成文件名）
            save_json: JSON结果保存路径（如果提供，将保存JSON，优先级高于自动生成）
            source_start_str: 源数据的开始日期字符串（格式：YYYYMMDD），如果提供则优先使用
            source_end_str: 源数据的结束日期字符串（格式：YYYYMMDD），如果提供则优先使用
        """
        print(f"\n{'='*60}")
        print(f"因子测试结果: {results['factor_name']}")
        print(f"{'='*60}")
        print(f"总样本数: {results['total_samples']}")
        print(f"看多信号数: {results['long_signals']}")
        print(f"看空信号数: {results['short_signals']}")
        print(f"中性信号数: {results['neutral_signals']}")
        print(f"\n看多信号胜率: {results['long_win_rate']:.2%}")
        print(f"看多信号次日平均收益率: {results['long_avg_return']:.4%}")
        print(f"\n看空信号胜率: {results['short_win_rate']:.2%}")
        print(f"看空信号次日平均收益率: {results['short_avg_return']:.4%}")
        print(f"\n总体胜率: {results['overall_win_rate']:.2%}")
        print(f"{'='*60}\n")
        
        # 自动保存JSON结果
        if save_dir and (factor_name or results.get('factor_name')) and data_name:
            # 获取因子名称
            if factor_name is None:
                factor_name = results.get('factor_name', 'factor')
            
            # 清理名称，移除特殊字符，用于文件名
            clean_factor_name = factor_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            clean_data_name = data_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            
            # 优先使用源数据的时间范围，如果没有则从数据中提取测试时间段
            start_str = source_start_str or ""
            end_str = source_end_str or ""
            
            if not start_str or not end_str:
                # 从数据中提取测试时间段
                if not self.data.empty and 'datetime' in self.data.columns:
                    try:
                        start_time = self.data['datetime'].min()
                        end_time = self.data['datetime'].max()
                        
                        # 转换为datetime对象（如果还不是）
                        if not isinstance(start_time, (pd.Timestamp, datetime)):
                            start_time = pd.to_datetime(start_time)
                            end_time = pd.to_datetime(end_time)
                        
                        # 格式化时间为 YYYYMMDD
                        start_str = start_time.strftime('%Y%m%d')
                        end_str = end_time.strftime('%Y%m%d')
                    except Exception:
                        # 如果时间提取失败，使用空字符串
                        pass
            
            # 确定保存目录结构
            if start_str and end_str:
                # 子文件夹格式：{数据名称}_{开始日期}_{结束日期}
                subfolder_name = f"{clean_data_name}_{start_str}_{end_str}"
                final_save_dir = os.path.join(save_dir, subfolder_name)
            else:
                # 如果没有时间段，只使用数据名称
                final_save_dir = os.path.join(save_dir, clean_data_name)
            
            # 确保目录存在
            os.makedirs(final_save_dir, exist_ok=True)
            
            # 文件名只包含因子名称
            base_filename = f"{clean_factor_name}_factor"
            base_path = os.path.join(final_save_dir, base_filename)
            
            # 如果未明确指定路径，使用自动生成的路径
            if save_json is None:
                save_json = f"{base_path}.json"
        
        # 保存JSON结果
        if save_json:
            self.save_results(results, save_json)
    
    def save_results(self, results: Dict, filepath: str):
        """
        保存测试结果到JSON文件
        
        Args:
            results: test_factor返回的结果字典
            filepath: 保存路径
        """
        # 转换datetime为字符串以便JSON序列化
        output = results.copy()
        for detail in output['details']:
            if isinstance(detail['datetime'], (pd.Timestamp, datetime)):
                detail['datetime'] = detail['datetime'].isoformat()
            # 转换numpy类型为Python原生类型
            if 'is_win' in detail:
                detail['is_win'] = bool(detail['is_win'])
            if 'factor_value' in detail:
                detail['factor_value'] = float(detail['factor_value'])
            if 'current_price' in detail:
                detail['current_price'] = float(detail['current_price'])
            if 'future_price' in detail:
                detail['future_price'] = float(detail['future_price'])
            if 'future_return' in detail:
                detail['future_return'] = float(detail['future_return'])
        
        # 转换统计指标中的numpy类型
        for key in ['long_win_rate', 'short_win_rate', 'overall_win_rate', 
                   'long_avg_return', 'short_avg_return']:
            if key in output:
                value = output[key]
                if isinstance(value, (np.integer, np.floating)):
                    output[key] = float(value)
                elif isinstance(value, np.bool_):
                    output[key] = bool(value)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"结果已保存到: {filepath}")

