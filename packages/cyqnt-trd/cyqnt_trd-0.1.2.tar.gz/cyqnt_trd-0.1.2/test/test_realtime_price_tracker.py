"""
模拟实盘测试脚本

参考 cyqnt_trd.online_trading.realtime_price_tracker 中的 RealtimePriceTracker 类，
创建模拟实盘交易测试环境。

使用方法：
    python test_realtime_price_tracker.py
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入 cyqnt_trd 包
try:
    from cyqnt_trd.online_trading.realtime_price_tracker import RealtimePriceTracker
    from cyqnt_trd.trading_signal.signal.ma_signal import ma_signal, ma_cross_signal
    from cyqnt_trd.trading_signal.signal.factor_based_signal import factor_based_signal
    from cyqnt_trd.trading_signal.factor.ma_factor import ma_factor
    from cyqnt_trd.trading_signal.factor.rsi_factor import rsi_factor
    from cyqnt_trd.trading_signal.selected_alpha.alpha1 import alpha1_factor
except ImportError as e:
    print(f"导入错误: {e}")
    print("\n提示：请确保已安装 cyqnt_trd package: pip install -e /path/to/crypto_trading")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class SimulatedTradingBot:
    """
    模拟交易机器人
    
    使用 RealtimePriceTracker 获取实时数据，并根据交易信号执行模拟交易
    """
    
    def __init__(
        self,
        symbol: str,
        interval: str = "3m",
        lookback_periods: int = 100,
        initial_capital: float = 10000.0,
        position_size: float = 0.01,  # 每次使用90%的资金
        take_profit: float = 0.1,  # 止盈10%
        stop_loss: float = 0.05,  # 止损5%
        commission_rate: float = 0.0001,  # 手续费0.01%
        strategy: str = "ma5",  # 策略类型: ma5, ma_cross, ma_factor, rsi_factor, alpha1
        ssl_verify: bool = False
    ):
        """
        初始化模拟交易机器人
        
        Args:
            symbol: 交易对符号
            interval: 时间间隔
            lookback_periods: 历史数据周期数
            initial_capital: 初始资金
            position_size: 每次交易使用的资金比例（0-1）
            take_profit: 止盈比例（0-1）
            stop_loss: 止损比例（0-1）
            commission_rate: 手续费率（0-1）
            strategy: 策略类型
            ssl_verify: SSL证书验证
        """
        self.symbol = symbol
        self.interval = interval
        self.initial_capital = initial_capital
        self.position_size = position_size
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.commission_rate = commission_rate
        self.strategy = strategy
        
        # 创建价格跟踪器
        self.tracker = RealtimePriceTracker(
            symbol=symbol,
            interval=interval,
            lookback_periods=lookback_periods,
            ssl_verify=ssl_verify
        )
        
        # 交易状态
        self.position = 0.0  # 当前持仓数量
        self.entry_price = 0.0  # 入场价格
        self.entry_index = -1  # 入场索引
        self.entry_time = None  # 入场时间
        
        # 账户状态
        self.current_capital = initial_capital  # 当前可用资金
        self.total_assets = initial_capital  # 总资产（包括持仓价值）
        
        # 交易记录
        self.completed_trades = []  # 已完成的交易
        self.total_trades = 0
        self.win_trades = 0
        self.loss_trades = 0
        self.total_profit = 0.0
        self.max_drawdown = 0.0
        self.peak_assets = initial_capital  # 资产峰值
        
        # 统计信息
        self.start_time = datetime.now()
        self.last_update_time = None
        
        # 注册回调
        self.tracker.register_on_new_kline(self._on_new_kline)
    
    def _calculate_signal(self, data_df) -> Optional[str]:
        """
        根据策略计算交易信号
        
        Args:
            data_df: 历史数据DataFrame
            
        Returns:
            交易信号: 'buy', 'sell', 'hold' 或 None
        """
        if len(data_df) < 10:
            return None
        
        # 使用足够的数据切片
        data_slice = data_df.iloc[-30:].copy() if len(data_df) >= 30 else data_df.copy()
        
        try:
            if self.strategy == "ma5":
                if len(data_slice) >= 6:
                    return ma_signal(
                        data_slice=data_slice,
                        position=self.position,
                        entry_price=self.entry_price,
                        entry_index=self.entry_index,
                        take_profit=self.take_profit,
                        stop_loss=self.stop_loss,
                        period=5
                    )
            
            elif self.strategy == "ma_cross":
                if len(data_slice) >= 22:
                    return ma_cross_signal(
                        data_slice=data_slice,
                        position=self.position,
                        entry_price=self.entry_price,
                        entry_index=self.entry_index,
                        take_profit=self.take_profit,
                        stop_loss=self.stop_loss,
                        check_periods=1,
                        short_period=5,
                        long_period=20
                    )
            
            elif self.strategy == "ma_factor":
                if len(data_slice) >= 6:
                    return factor_based_signal(
                        data_slice=data_slice,
                        position=self.position,
                        entry_price=self.entry_price,
                        entry_index=self.entry_index,
                        take_profit=self.take_profit,
                        stop_loss=self.stop_loss,
                        check_periods=1,
                        factor_func=lambda d: ma_factor(d, period=5),
                        factor_period=5
                    )
            
            elif self.strategy == "rsi_factor":
                if len(data_slice) >= 16:
                    return factor_based_signal(
                        data_slice=data_slice,
                        position=self.position,
                        entry_price=self.entry_price,
                        entry_index=self.entry_index,
                        take_profit=self.take_profit,
                        stop_loss=self.stop_loss,
                        check_periods=1,
                        factor_func=lambda d: rsi_factor(d, period=14),
                        factor_period=14
                    )
            
            elif self.strategy == "alpha1":
                if len(data_slice) >= 26:
                    return factor_based_signal(
                        data_slice=data_slice,
                        position=self.position,
                        entry_price=self.entry_price,
                        entry_index=self.entry_index,
                        take_profit=self.take_profit,
                        stop_loss=self.stop_loss,
                        check_periods=1,
                        factor_func=lambda d: alpha1_factor(d, lookback_days=5, stddev_period=20, power=2.0),
                        factor_period=25
                    )
        except Exception as e:
            logging.debug(f"计算信号时出错: {e}")
            return None
        
        return None
    
    def _on_new_kline(self, kline_dict: Dict[str, Any], data_df):
        """
        新K线数据回调函数
        
        Args:
            kline_dict: 新K线数据字典
            data_df: 历史数据DataFrame
        """
        current_price = kline_dict['close_price']
        current_time = kline_dict['open_time_str']
        
        # 更新总资产
        if self.position > 0:
            position_value = self.position * current_price
            self.total_assets = self.current_capital + position_value
            floating_profit_pct = (current_price - self.entry_price) / self.entry_price * 100
        else:
            self.total_assets = self.current_capital
            floating_profit_pct = 0.0
        
        # 更新最大回撤
        if self.total_assets > self.peak_assets:
            self.peak_assets = self.total_assets
        drawdown = (self.peak_assets - self.total_assets) / self.peak_assets
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
        
        # 计算交易信号
        signal = self._calculate_signal(data_df)
        
        # 显示状态
        self._display_status(current_time, current_price, signal, floating_profit_pct)
        
        # 执行交易
        if signal == 'buy' and self.position == 0:
            self._execute_buy(current_price, current_time, len(data_df) - 1)
        elif signal == 'sell' and self.position > 0:
            self._execute_sell(current_price, current_time)
        
        self.last_update_time = datetime.now()
    
    def _execute_buy(self, price: float, time_str: str, index: int):
        """
        执行买入操作
        
        Args:
            price: 买入价格
            time_str: 时间字符串
            index: 数据索引
        """
        # 计算买入金额（扣除手续费）
        buy_amount = self.current_capital * self.position_size
        commission = buy_amount * self.commission_rate
        net_buy_amount = buy_amount - commission
        
        # 计算买入数量
        self.position = net_buy_amount / price
        self.entry_price = price
        self.entry_index = index
        self.entry_time = time_str
        
        # 更新资金
        self.current_capital -= buy_amount
        
        print(f"\n{'='*80}")
        print(f"✅ 执行买入")
        print(f"  时间: {time_str}")
        print(f"  价格: {price:.2f}")
        print(f"  数量: {self.position:.6f}")
        print(f"  金额: {buy_amount:.2f}")
        print(f"  手续费: {commission:.2f}")
        print(f"  剩余资金: {self.current_capital:.2f}")
        print(f"{'='*80}\n")
    
    def _execute_sell(self, price: float, time_str: str):
        """
        执行卖出操作
        
        Args:
            price: 卖出价格
            time_str: 时间字符串
        """
        # 计算卖出金额
        sell_amount = self.position * price
        commission = sell_amount * self.commission_rate
        net_sell_amount = sell_amount - commission
        
        # 计算盈亏
        cost_basis = self.position * self.entry_price
        profit_amount = net_sell_amount - cost_basis
        profit_pct = (price - self.entry_price) / self.entry_price * 100
        
        # 更新资金
        self.current_capital += net_sell_amount
        
        # 记录交易
        trade_record = {
            'entry_time': self.entry_time,
            'exit_time': time_str,
            'entry_price': self.entry_price,
            'exit_price': price,
            'quantity': self.position,
            'profit_amount': profit_amount,
            'profit_pct': profit_pct,
            'commission': commission * 2  # 买入和卖出手续费
        }
        self.completed_trades.append(trade_record)
        
        # 更新统计
        self.total_trades += 1
        self.total_profit += profit_amount
        if profit_amount > 0:
            self.win_trades += 1
        else:
            self.loss_trades += 1
        
        print(f"\n{'='*80}")
        print(f"✅ 执行卖出")
        print(f"  时间: {time_str}")
        print(f"  价格: {price:.2f}")
        print(f"  入场价: {self.entry_price:.2f}")
        print(f"  数量: {self.position:.6f}")
        print(f"  盈亏金额: {profit_amount:+.2f}")
        print(f"  盈亏比例: {profit_pct:+.2f}%")
        print(f"  手续费: {commission:.2f}")
        print(f"  当前资金: {self.current_capital:.2f}")
        print(f"{'='*80}\n")
        
        # 重置持仓
        self.position = 0.0
        self.entry_price = 0.0
        self.entry_index = -1
        self.entry_time = None
    
    def _display_status(self, time_str: str, price: float, signal: Optional[str], floating_profit_pct: float):
        """
        显示当前状态
        
        Args:
            time_str: 时间字符串
            price: 当前价格
            signal: 交易信号
            floating_profit_pct: 浮动盈亏百分比
        """
        # 计算统计信息
        total_return_pct = (self.total_assets - self.initial_capital) / self.initial_capital * 100
        runtime = datetime.now() - self.start_time
        runtime_str = f"{runtime.days}天 {runtime.seconds // 3600}小时 {(runtime.seconds % 3600) // 60}分钟"
        win_rate = (self.win_trades / self.total_trades * 100) if self.total_trades > 0 else 0.0
        
        # 信号显示
        if signal:
            signal_emoji = "🟢" if signal == 'buy' else "🔴" if signal == 'sell' else "⚪"
            signal_text = f"{signal_emoji} {signal.upper()}"
        else:
            signal_text = "⚪ HOLD"
        
        print(f"\n{'='*80}")
        print(f"📊 实时状态更新")
        print(f"{'='*80}")
        print(f"时间: {time_str}")
        print(f"价格: {price:.2f}")
        print(f"信号: {signal_text}")
        if self.position > 0:
            print(f"持仓: {self.position:.6f} | 入场价: {self.entry_price:.2f} | 浮动盈亏: {floating_profit_pct:+.2f}%")
        else:
            print(f"持仓: 无")
        print(f"{'='*80}")
        print(f"💰 账户统计:")
        print(f"  初始资金: {self.initial_capital:.2f}")
        print(f"  当前资金: {self.current_capital:.2f}")
        if self.position > 0:
            print(f"  持仓价值: {self.position * price:.2f}")
        print(f"  总资产: {self.total_assets:.2f}")
        print(f"  累计盈亏: {self.total_profit:+.2f} ({total_return_pct:+.2f}%)")
        print(f"  最大回撤: {self.max_drawdown * 100:.2f}%")
        print(f"  运行时间: {runtime_str}")
        print(f"  总交易次数: {self.total_trades} | 盈利: {self.win_trades} | 亏损: {self.loss_trades} | 胜率: {win_rate:.2f}%")
        print(f"{'='*80}\n")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取交易统计信息
        
        Returns:
            统计信息字典
        """
        total_return_pct = (self.total_assets - self.initial_capital) / self.initial_capital * 100
        runtime = datetime.now() - self.start_time
        win_rate = (self.win_trades / self.total_trades * 100) if self.total_trades > 0 else 0.0
        
        # 计算平均盈亏
        avg_profit = self.total_profit / self.total_trades if self.total_trades > 0 else 0.0
        
        # 计算夏普比率（简化版）
        if len(self.completed_trades) > 0:
            returns = [t['profit_pct'] / 100 for t in self.completed_trades]
            import numpy as np
            if len(returns) > 1:
                sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0.0
            else:
                sharpe_ratio = 0.0
        else:
            sharpe_ratio = 0.0
        
        return {
            'initial_capital': self.initial_capital,
            'final_capital': self.total_assets,
            'total_return': self.total_profit,
            'total_return_pct': total_return_pct,
            'total_trades': self.total_trades,
            'win_trades': self.win_trades,
            'loss_trades': self.loss_trades,
            'win_rate': win_rate,
            'max_drawdown': self.max_drawdown * 100,
            'avg_profit': avg_profit,
            'sharpe_ratio': sharpe_ratio,
            'runtime': str(runtime),
            'completed_trades': self.completed_trades
        }
    
    async def start(self):
        """
        启动模拟交易
        """
        print("="*80)
        print("🚀 模拟实盘交易测试启动")
        print("="*80)
        print(f"交易对: {self.symbol}")
        print(f"时间间隔: {self.interval}")
        print(f"策略: {self.strategy}")
        print(f"初始资金: {self.initial_capital:.2f}")
        print(f"仓位大小: {self.position_size * 100:.0f}%")
        print(f"止盈: {self.take_profit * 100:.0f}%")
        print(f"止损: {self.stop_loss * 100:.0f}%")
        print(f"手续费率: {self.commission_rate * 100:.4f}%")
        print("="*80)
        print("\n等待实时数据...\n")
        
        await self.tracker.run_forever()
    
    def print_final_report(self):
        """
        打印最终报告
        """
        stats = self.get_statistics()
        
        print("\n" + "="*80)
        print("📊 最终交易报告")
        print("="*80)
        print(f"交易对: {self.symbol}")
        print(f"策略: {self.strategy}")
        print(f"运行时间: {stats['runtime']}")
        print(f"\n💰 资金统计:")
        print(f"  初始资金: {stats['initial_capital']:.2f}")
        print(f"  最终资产: {stats['final_capital']:.2f}")
        print(f"  总盈亏: {stats['total_return']:+.2f}")
        print(f"  总收益率: {stats['total_return_pct']:+.2f}%")
        print(f"\n📈 交易统计:")
        print(f"  总交易次数: {stats['total_trades']}")
        print(f"  盈利次数: {stats['win_trades']}")
        print(f"  亏损次数: {stats['loss_trades']}")
        print(f"  胜率: {stats['win_rate']:.2f}%")
        print(f"  平均盈亏: {stats['avg_profit']:.2f}")
        print(f"\n📉 风险指标:")
        print(f"  最大回撤: {stats['max_drawdown']:.2f}%")
        print(f"  夏普比率: {stats['sharpe_ratio']:.2f}")
        print("="*80)
        
        # 显示最近10笔交易
        if len(self.completed_trades) > 0:
            print(f"\n最近10笔交易记录:")
            print("-"*80)
            for i, trade in enumerate(self.completed_trades[-10:], 1):
                print(f"{i}. {trade['entry_time']} -> {trade['exit_time']}")
                print(f"   入场: {trade['entry_price']:.2f} | 出场: {trade['exit_price']:.2f}")
                print(f"   盈亏: {trade['profit_amount']:+.2f} ({trade['profit_pct']:+.2f}%)")
            print("="*80)


async def test_simulated_trading():
    """
    测试模拟交易
    """
    # 创建模拟交易机器人
    bot = SimulatedTradingBot(
        symbol="BTCUSDT",
        interval="1m",
        lookback_periods=100,
        initial_capital=10000.0,
        position_size=0.01,
        take_profit=0.1,
        stop_loss=0.05,
        commission_rate=0.0001,
        strategy="ma5",  # 可选: ma5, ma_cross, ma_factor, rsi_factor, alpha1
        ssl_verify=False
    )
    
    try:
        # 启动交易
        await bot.start()
    except KeyboardInterrupt:
        print("\n\n收到中断信号，正在停止...")
    finally:
        # 打印最终报告
        bot.print_final_report()


def main():
    """
    主函数
    """
    print("="*80)
    print("模拟实盘交易测试脚本")
    print("="*80)
    print("\n注意：")
    print("  1. 确保已安装 cyqnt_trd package")
    print("  2. 需要网络连接访问 Binance WebSocket")
    print("  3. 按 Ctrl+C 停止测试")
    print("  4. 测试结果将显示在控制台")
    print()
    
    try:
        asyncio.run(test_simulated_trading())
    except KeyboardInterrupt:
        print("\n测试已停止")
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

