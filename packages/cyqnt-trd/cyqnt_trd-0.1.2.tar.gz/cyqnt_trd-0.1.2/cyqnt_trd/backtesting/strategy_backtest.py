"""
策略回测模块

根据买卖信号进行回测，计算收益率和收益曲线
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Callable, Optional, Dict, List, Tuple
from datetime import datetime
import json
import os


class StrategyBacktester:
    """
    策略回测器
    
    根据买卖信号进行回测，计算收益率和收益曲线
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        initial_capital: float = 10000.0,
        commission_rate: float = 0.001
    ):
        """
        初始化策略回测器
        
        Args:
            data: 包含K线数据的DataFrame，必须包含以下列：
                  - datetime 或 open_time_str: 时间
                  - close_price: 收盘价
            initial_capital: 初始资金
            commission_rate: 手续费率（默认0.1%）
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
        
        # 确保有high_price和low_price列（用于止盈止损）
        if 'high_price' not in self.data.columns:
            raise ValueError("数据必须包含 'high_price' 列（用于止盈止损）")
        if 'low_price' not in self.data.columns:
            raise ValueError("数据必须包含 'low_price' 列（用于止盈止损）")
        
        # 按时间排序
        self.data = self.data.sort_values('datetime').reset_index(drop=True)
        
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate

    def backtest(
        self,
        signal_func: Callable,
        min_periods: int = 0,
        position_size: float = 1.0,
        take_profit: Optional[float] = None,
        stop_loss: Optional[float] = None,
        check_periods: int = 1
    ) -> Dict:
        """
        执行回测

        Args:
            signal_func: 信号生成函数，必须接受以下参数：
                        (data_slice, position, entry_price, entry_index, take_profit, stop_loss, check_periods) -> str
                        - data_slice: 数据切片（包含历史数据和当前数据点）
                        - position: 当前持仓数量（如果没有持仓则为0）
                        - entry_price: 入场价格（如果没有持仓则为0）
                        - entry_index: 入场索引（如果没有持仓则为-1）
                        - take_profit: 止盈比例（例如：0.1 表示 10%）
                        - stop_loss: 止损比例（例如：0.1 表示 10%）
                        - check_periods: 检查未来多少个周期（只能为1，因为实际使用时无法看到未来数据）
                        - 返回: 'buy'（买入）, 'sell'（卖出）, 'hold'（持有）或 None
                        策略函数可以根据持仓信息自行决定是否止盈止损
            min_periods: 最小需要的周期数（用于计算信号时）
            position_size: 每次交易的仓位大小（相对于可用资金的比例，0-1之间）
            take_profit: 止盈比例（传递给策略函数，由策略决定是否使用）
            stop_loss: 止损比例（传递给策略函数，由策略决定是否使用）
            check_periods: 检查未来多少个周期（只能为1，默认1，即只检查当前周期）
                          注意：回测时只能为1，因为实际交易中无法看到今天之后的数据

        Returns:
            包含回测结果的字典：
            - initial_capital: 初始资金
            - final_capital: 最终资金
            - total_return: 总收益率
            - total_trades: 总交易次数
            - win_trades: 盈利交易次数
            - loss_trades: 亏损交易次数
            - win_rate: 胜率
            - max_drawdown: 最大回撤
            - sharpe_ratio: 夏普比率
            - equity_curve: 资金曲线（DataFrame）
            - trades: 交易记录列表
        """
        import concurrent.futures

        # 初始化
        capital = self.initial_capital
        position = 0  # 持仓数量
        entry_price = 0  # 入场价格
        entry_index = -1  # 入场索引

        equity_curve = []
        trades = []

        # 预先准备多线程需要的参数
        max_period = 50
        idx_range = range(min_periods, len(self.data))

        # 1. 并行调用信号函数
        def signal_func_runner(args):
            i, position, entry_price, entry_index = args
            try:
                start_idx = max(0, i - max_period)
                data_slice = self.data.iloc[start_idx:i+1].copy()
                signal = signal_func(
                    data_slice, position, entry_price, entry_index,
                    take_profit, stop_loss, check_periods
                )
                current_price = self.data.iloc[i]['close_price']
                current_time = self.data.iloc[i]['datetime']
                return (i, signal, current_price, current_time)
            except Exception as e:
                return (i, None, None, None)

        # 为所有时间点提前构建并行参数列表（注意，position/entry_price/entry_index变化只能串行，这里仅signal并行！）
        # 所以只能并行 signal_func 的输入，每步的仓位信息和买卖流水必须主进程顺序推进。
        # 做法：先并行计算所有点的信号，然后主进程串行执行持仓等逻辑。

        # 获取每个时间点需要的切片和并行参数（仓位参数全部为当前最新，后续再用）
        # 方案：只并行计算信号，不动持仓逻辑。
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # 注意：这里只能给signal_func实际需要的参数，其余（如position, entry_price等）在回测流程串行推演
            # 由于并行只加速技术信号（只依赖slice数据，不依赖仓位），所以先串行取决于之前的position。
            # 所有信号都需要position等，回测需要逐步推进状态，不能直接全部并发。
            #
            # 解决办法：只并行信号生成(即信号与持仓变化无关的情形，例如策略只考虑slice，不用position等参数)。如果策略要用这些参数仍必须主线程推演，信号函数并行意义有限。
            #
            # 这里我们假设信号函数主要耗时来自数据slice运算（如大量因子），用过去slice计算信号，不严重依赖实时持仓等。
            # 所以我们在持仓、entry_price、entry_index等参数为"推演至当前时刻"的主线程状态下，同步推进主循环，并行仅用于信号slice耗时运算。

            # 改进方案：主循环推演仓位，但每次 slice 调 signal_func 并行
            signals_future = [None] * len(idx_range)

            def signal_worker(i, position, entry_price, entry_index):
                try:
                    start_idx = max(0, i - max_period)
                    data_slice = self.data.iloc[start_idx:i+1].copy()
                    signal = signal_func(
                        data_slice, position, entry_price, entry_index,
                        take_profit, stop_loss, check_periods
                    )
                    current_price = self.data.iloc[i]['close_price']
                    current_time = self.data.iloc[i]['datetime']
                    return (i, signal, current_price, current_time)
                except Exception as e:
                    return (i, None, None, None)
            
            # 逐步推进账户状态，但每步并发信号计算
            with concurrent.futures.ThreadPoolExecutor() as pool:
                # 先占位，后面主循环会推进position等参数
                results_for_period = [None] * len(idx_range)
                # 记录期望并发任务
                futures = {}
                for local_idx, i in enumerate(idx_range):
                    # 提交并占位future
                    futures[local_idx] = None # 先预占
                # 下面主流程顺序推进持仓等状态，同时在每步将signal_func并发出去
                for local_idx, i in enumerate(idx_range):
                    # 提交signal_func任务（给实时position等参数）
                    futures[local_idx] = pool.submit(signal_worker, i, position, entry_price, entry_index)

                    # 取出回调结果（非阻塞等待，可以微调batch方式用于进一步加速）
                    # 由于策略必须顺序推演（因为signal_func依赖当前仓位等），无法完全乱序
                    i, signal, current_price, current_time = futures[local_idx].result()

                    # 处理信号
                    if signal == 'buy' and position == 0:
                        # 买入
                        trade_amount = capital * position_size
                        position = trade_amount / current_price
                        commission = trade_amount * self.commission_rate
                        capital = capital - trade_amount - commission
                        entry_price = current_price
                        entry_index = i

                        trades.append({
                            'type': 'buy',
                            'datetime': current_time,
                            'index': i,
                            'price': float(current_price),
                            'position': float(position),
                            'capital': float(capital)
                        })
                    elif signal == 'sell' and position > 0:
                        trade_amount = position * current_price
                        commission = trade_amount * self.commission_rate
                        capital = capital + trade_amount - commission

                        pnl = (current_price - entry_price) / entry_price if entry_price > 0 else 0
                        pnl_amount = trade_amount - (position * entry_price) - commission if entry_price > 0 else 0

                        reason = 'signal'
                        if entry_price > 0:
                            price_change = (current_price - entry_price) / entry_price
                            if take_profit is not None and price_change >= take_profit:
                                reason = 'take_profit'
                            elif stop_loss is not None and price_change <= -stop_loss:
                                reason = 'stop_loss'

                        trades.append({
                            'type': 'sell',
                            'reason': reason,
                            'datetime': current_time,
                            'index': i,
                            'price': float(current_price),
                            'entry_price': float(entry_price),
                            'pnl': float(pnl),
                            'pnl_amount': float(pnl_amount),
                            'capital': float(capital)
                        })

                        position = 0
                        entry_price = 0
                        entry_index = -1

                    # 计算当前总资产（现金 + 持仓市值）
                    current_equity = capital + (position * current_price if position > 0 else 0)
                    equity_curve.append({
                        'datetime': current_time,
                        'index': i,
                        'equity': float(current_equity),
                        'capital': float(capital),
                        'position': float(position),
                        'price': float(current_price)
                    })

        # 如果最后还有持仓，按最后价格平仓
        if position > 0:
            last_price = self.data.iloc[-1]['close_price']
            last_time = self.data.iloc[-1]['datetime']
            trade_amount = position * last_price
            commission = trade_amount * self.commission_rate
            capital = capital + trade_amount - commission

            pnl = (last_price - entry_price) / entry_price
            pnl_amount = trade_amount - (position * entry_price) - commission

            trades.append({
                'type': 'sell',
                'reason': 'close_position',
                'datetime': last_time,
                'index': len(self.data) - 1,
                'price': float(last_price),
                'entry_price': float(entry_price),
                'pnl': float(pnl),
                'pnl_amount': float(pnl_amount),
                'capital': float(capital)
            })

            # 更新最后一条资金曲线
            if equity_curve:
                equity_curve[-1]['equity'] = float(capital)
                equity_curve[-1]['capital'] = float(capital)
                equity_curve[-1]['position'] = 0.0

        # 构建资金曲线DataFrame
        equity_df = pd.DataFrame(equity_curve)

        # 计算统计指标
        final_capital = capital
        total_return = (final_capital - self.initial_capital) / self.initial_capital

        # 计算交易统计
        sell_trades = [t for t in trades if t['type'] == 'sell']
        total_trades = len(sell_trades)
        win_trades = len([t for t in sell_trades if t.get('pnl', 0) > 0])
        loss_trades = len([t for t in sell_trades if t.get('pnl', 0) < 0])
        win_rate = win_trades / total_trades if total_trades > 0 else 0.0

        # 计算最大回撤
        equity_values = equity_df['equity'].values
        peak = np.maximum.accumulate(equity_values)
        drawdown = (equity_values - peak) / peak
        max_drawdown = abs(np.min(drawdown)) if len(drawdown) > 0 else 0.0

        # 计算夏普比率（简化版，假设无风险利率为0）
        returns = equity_df['equity'].pct_change().dropna()
        if len(returns) > 0 and returns.std() > 0:
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)  # 年化
        else:
            sharpe_ratio = 0.0

        results = {
            'initial_capital': self.initial_capital,
            'final_capital': final_capital,
            'total_return': total_return,
            'total_trades': total_trades,
            'win_trades': win_trades,
            'loss_trades': loss_trades,
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'equity_curve': equity_df,
            'trades': trades
        }

        return results
    
    def plot_results(
        self, 
        results: Dict, 
        figsize: Tuple[int, int] = (14, 10),
        save_image: Optional[str] = None,
        save_json: Optional[str] = None,
        strategy_name: Optional[str] = None,
        data_name: Optional[str] = None,
        save_dir: Optional[str] = None,
        source_start_str: Optional[str] = None,
        source_end_str: Optional[str] = None
    ):
        """
        绘制回测结果
        
        Args:
            results: backtest返回的结果字典
            figsize: 图形大小
            save_image: 图片保存路径（如果提供，将保存图片，优先级高于自动生成）
            save_json: JSON结果保存路径（如果提供，将保存JSON，优先级高于自动生成）
            strategy_name: 策略名称（用于自动生成文件名）
            data_name: 数据名称（用于自动生成文件名）
            save_dir: 保存目录（如果提供strategy_name和data_name，将在此目录下保存文件）
            source_start_str: 源数据的开始日期字符串（格式：YYYYMMDD），如果提供则优先使用
            source_end_str: 源数据的结束日期字符串（格式：YYYYMMDD），如果提供则优先使用
        """
        equity_df = results['equity_curve']
        
        # 如果提供了策略名称和数据名称，自动生成文件名
        if strategy_name and data_name:
            # 清理名称，移除特殊字符，用于文件名
            clean_strategy_name = strategy_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            clean_data_name = data_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            
            # 优先使用源数据的时间范围，如果没有则从equity_curve中提取
            start_str = source_start_str or ""
            end_str = source_end_str or ""
            
            if not start_str or not end_str:
                # 从equity_curve中提取测试时间段
                if not equity_df.empty and 'datetime' in equity_df.columns:
                    try:
                        start_time = equity_df['datetime'].min()
                        end_time = equity_df['datetime'].max()
                        
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
            if save_dir:
                # 根据数据名称和开始结束日期创建子文件夹
                if start_str and end_str:
                    # 子文件夹格式：{数据名称}_{开始日期}_{结束日期}
                    subfolder_name = f"{clean_data_name}_{start_str}_{end_str}"
                    final_save_dir = os.path.join(save_dir, subfolder_name)
                else:
                    # 如果没有时间段，只使用数据名称
                    final_save_dir = os.path.join(save_dir, clean_data_name)
                
                # 确保目录存在
                os.makedirs(final_save_dir, exist_ok=True)
                
                # 文件名只包含策略名称
                base_filename = f"{clean_strategy_name}_backtest"
                base_path = os.path.join(final_save_dir, base_filename)
            else:
                # 如果没有提供保存目录，使用原来的逻辑（文件名包含所有信息）
                time_period_str = f"_{start_str}_{end_str}" if (start_str and end_str) else ""
                base_filename = f"{clean_strategy_name}_{clean_data_name}{time_period_str}_backtest"
                base_path = base_filename
            
            # 如果未明确指定路径，使用自动生成的路径
            if save_image is None:
                save_image = f"{base_path}.png"
            if save_json is None:
                save_json = f"{base_path}.json"
        elif save_dir:
            # 如果提供了save_dir但没有strategy_name或data_name，使用默认文件名
            # 确保目录存在
            os.makedirs(save_dir, exist_ok=True)
            
            # 使用默认文件名
            default_name = "backtest_result"
            if strategy_name:
                default_name = strategy_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            elif data_name:
                default_name = data_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            
            base_path = os.path.join(save_dir, default_name)
            
            if save_image is None:
                save_image = f"{base_path}.png"
            if save_json is None:
                save_json = f"{base_path}.json"
        
        # Set default font (no need for Chinese fonts)
        plt.rcParams['axes.unicode_minus'] = False
        
        fig, axes = plt.subplots(3, 1, figsize=figsize, gridspec_kw={'height_ratios': [2, 1, 1]})
        
        # 1. Equity Curve
        ax1 = axes[0]
        ax1.plot(equity_df['datetime'], equity_df['equity'], label='Equity Curve', linewidth=2, color='blue')
        ax1.axhline(y=results['initial_capital'], color='gray', linestyle='--', label='Initial Capital')
        ax1.set_title('Backtest Equity Curve', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Equity (USDT)', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Price Curve and Trading Signals
        ax2 = axes[1]
        ax2.plot(equity_df['datetime'], equity_df['price'], label='Price', linewidth=1.5, color='black', alpha=0.7)
        
        # Mark buy/sell points
        buy_trades = [t for t in results['trades'] if t['type'] == 'buy']
        sell_trades = [t for t in results['trades'] if t['type'] == 'sell']
        
        if buy_trades:
            buy_times = [t['datetime'] for t in buy_trades]
            buy_prices = [t['price'] for t in buy_trades]
            ax2.scatter(buy_times, buy_prices, color='green', marker='^', s=100, label='Buy', zorder=5)
        
        if sell_trades:
            sell_times = [t['datetime'] for t in sell_trades]
            sell_prices = [t['price'] for t in sell_trades]
            ax2.scatter(sell_times, sell_prices, color='red', marker='v', s=100, label='Sell', zorder=5)
        
        ax2.set_title('Price Curve and Trading Signals', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Price (USDT)', fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Drawdown Curve
        ax3 = axes[2]
        equity_values = equity_df['equity'].values
        peak = np.maximum.accumulate(equity_values)
        drawdown = (equity_values - peak) / peak * 100
        ax3.fill_between(equity_df['datetime'], drawdown, 0, color='red', alpha=0.3, label='Drawdown')
        ax3.plot(equity_df['datetime'], drawdown, color='red', linewidth=1)
        ax3.set_title('Drawdown Curve', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Drawdown (%)', fontsize=12)
        ax3.set_xlabel('Time', fontsize=12)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存图片
        if save_image:
            plt.savefig(save_image, dpi=300, bbox_inches='tight')
            print(f"图片已保存到: {save_image}")
        
        plt.show()
        
        # 保存JSON结果
        if save_json:
            self.save_results(results, save_json)
        
        # 打印统计信息
        # self.print_results(results)
    
    def print_results(self, results: Dict):
        """
        打印回测结果
        
        Args:
            results: backtest返回的结果字典
        """
        print(f"\n{'='*60}")
        print("回测结果统计")
        print(f"{'='*60}")
        print(f"初始资金: {results['initial_capital']:.2f} USDT")
        print(f"最终资金: {results['final_capital']:.2f} USDT")
        print(f"总收益率: {results['total_return']:.2%}")
        print(f"\n交易统计:")
        print(f"  总交易次数: {results['total_trades']}")
        print(f"  盈利交易: {results['win_trades']}")
        print(f"  亏损交易: {results['loss_trades']}")
        print(f"  胜率: {results['win_rate']:.2%}")
        print(f"\n风险指标:")
        print(f"  最大回撤: {results['max_drawdown']:.2%}")
        print(f"  夏普比率: {results['sharpe_ratio']:.2f}")
        print(f"{'='*60}\n")
    
    def save_results(self, results: Dict, filepath: str):
        """
        保存回测结果到JSON文件
        
        Args:
            results: backtest返回的结果字典
            filepath: 保存路径
        """
        output = results.copy()
        
        # 转换DataFrame为字典
        output['equity_curve'] = output['equity_curve'].to_dict('records')
        
        # 转换datetime为字符串
        for record in output['equity_curve']:
            if isinstance(record['datetime'], (pd.Timestamp, datetime)):
                record['datetime'] = record['datetime'].isoformat()
        
        for trade in output['trades']:
            if isinstance(trade['datetime'], (pd.Timestamp, datetime)):
                trade['datetime'] = trade['datetime'].isoformat()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"结果已保存到: {filepath}")

