"""
实盘交易脚本

结合 RealtimePriceTracker 和订单执行功能，实现基于实时数据的自动交易。

⚠️ 警告：此脚本会执行真实交易，请谨慎使用！
建议：
1. 先在测试网络或使用小额资金测试
2. 仔细检查所有参数
3. 确保策略已经过充分回测
4. 设置合理的止盈止损

使用方法：
    python real_time_trade.py
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from cyqnt_trd.utils import set_user

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入 cyqnt_trd 包
try:
    from cyqnt_trd.online_trading.realtime_price_tracker import RealtimePriceTracker
    from cyqnt_trd.test_script.test_order import (
        test_futures_order,
        test_spot_order,
        get_futures_balance,
        get_spot_balance,
        show_futures_balances,
        show_spot_balances,
        get_futures_open_orders,
        cancel_futures_order
    )
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
logger = logging.getLogger(__name__)


class RealTimeTradingBot:
    """
    实盘交易机器人
    
    使用 RealtimePriceTracker 获取实时数据，根据交易信号执行真实订单
    """
    
    def __init__(
        self,
        symbol: str,
        interval: str = "1m",
        lookback_periods: int = 100,
        market_type: str = "futures",  # "futures" 或 "spot"
        position_size_pct: float = 0.01,  # 每次使用资金的百分比
        take_profit: float = 0.1,  # 止盈10%
        stop_loss: float = 0.05,  # 止损5%
        strategy: str = "ma5",  # 策略类型
        min_order_quantity: float = 0.001,  # 最小下单数量
        ssl_verify: bool = False,
        dry_run: bool = True  # 是否为模拟模式（不实际下单）
    ):
        """
        初始化实盘交易机器人
        
        Args:
            symbol: 交易对符号
            interval: 时间间隔
            lookback_periods: 历史数据周期数
            market_type: 市场类型，"futures" 或 "spot"
            position_size_pct: 每次交易使用的资金比例（0-1）
            take_profit: 止盈比例（0-1）
            stop_loss: 止损比例（0-1）
            strategy: 策略类型
            min_order_quantity: 最小下单数量
            ssl_verify: SSL证书验证
            dry_run: 是否为模拟模式（True=不实际下单，False=真实下单）
        """
        self.symbol = symbol.upper()
        self.interval = interval
        self.market_type = market_type
        self.position_size_pct = position_size_pct
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.strategy = strategy
        self.min_order_quantity = min_order_quantity
        self.dry_run = dry_run
        
        # 创建价格跟踪器
        self.tracker = RealtimePriceTracker(
            symbol=symbol,
            interval=interval,
            lookback_periods=lookback_periods,
            market_type=market_type,
            ssl_verify=ssl_verify
        )
        
        # 交易状态
        self.position = 0.0  # 当前持仓数量
        self.entry_price = 0.0  # 入场价格
        self.entry_index = -1  # 入场索引
        self.entry_time = None  # 入场时间
        self.entry_order_id = None  # 入场订单ID
        
        # 交易记录
        self.completed_trades = []  # 已完成的交易
        self.total_trades = 0
        self.win_trades = 0
        self.loss_trades = 0
        self.total_profit = 0.0
        
        # 统计信息
        self.start_time = datetime.now()
        self.last_signal = None
        self.last_signal_time = None
        
        # 注册回调
        self.tracker.register_on_new_kline(self._on_new_kline)
        
        # 显示初始状态
        if dry_run:
            logger.warning("="*80)
            logger.warning("⚠️  模拟模式：不会执行真实订单")
            logger.warning("="*80)
        else:
            logger.warning("="*80)
            logger.warning("⚠️  实盘模式：将执行真实订单！")
            logger.warning("="*80)
    
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
            logger.debug(f"计算信号时出错: {e}")
            return None
        
        return None
    
    def _get_available_balance(self) -> float:
        """
        获取可用余额
        
        Returns:
            可用余额
        """
        try:
            if self.market_type == "futures":
                result = get_futures_balance("USDT")
                if result.get("success"):
                    balance_info = result.get("balances", {})
                    return balance_info.get("available", 0.0)
            else:
                # 从交易对中提取报价货币
                quote_asset = "USDT"  # 默认
                if self.symbol.endswith("USDT"):
                    quote_asset = "USDT"
                elif self.symbol.endswith("BUSD"):
                    quote_asset = "BUSD"
                elif self.symbol.endswith("USDC"):
                    quote_asset = "USDC"
                
                result = get_spot_balance(quote_asset)
                if result.get("success"):
                    balance_info = result.get("balances", {})
                    return balance_info.get("free", 0.0)
        except Exception as e:
            logger.error(f"获取余额失败: {e}")
        
        return 0.0
    
    def _calculate_order_quantity(self, price: float, side: str) -> float:
        """
        计算订单数量
        
        Args:
            price: 当前价格
            side: 买卖方向，"BUY" 或 "SELL"
            
        Returns:
            订单数量
        """
        if side == "BUY":
            # 买入：使用可用余额的百分比
            available = self._get_available_balance()
            order_value = available * self.position_size_pct
            quantity = order_value / price
            
            # 确保不小于最小下单数量
            if quantity < self.min_order_quantity:
                return 0.0
            
            return quantity
        else:
            # 卖出：使用当前持仓
            return self.position
    
    def _execute_buy_order(self, price: float, time_str: str) -> bool:
        """
        执行买入订单
        
        Args:
            price: 买入价格
            time_str: 时间字符串
            
        Returns:
            是否成功
        """
        quantity = self._calculate_order_quantity(price, "BUY")
        
        if quantity < self.min_order_quantity:
            logger.warning(f"计算出的数量 {quantity} 小于最小下单数量 {self.min_order_quantity}")
            return False
        
        logger.info(f"准备买入: {self.symbol}, 数量: {quantity:.6f}, 价格: {price:.2f}")
        
        if self.dry_run:
            logger.info("🔵 [模拟] 执行买入订单")
            logger.info(f"  时间: {time_str}")
            logger.info(f"  价格: {price:.2f}")
            logger.info(f"  数量: {quantity:.6f}")
            logger.info(f"  金额: {quantity * price:.2f}")
            
            # 模拟更新状态
            self.position = quantity
            self.entry_price = price
            self.entry_time = time_str
            return True
        else:
            # 真实下单
            try:
                if self.market_type == "futures":
                    result = test_futures_order(
                        symbol=self.symbol,
                        side="BUY",
                        order_type="MARKET",
                        quantity=quantity
                    )
                else:
                    result = test_spot_order(
                        symbol=self.symbol,
                        side="BUY",
                        order_type="MARKET",
                        quantity=quantity
                    )
                
                if result.get("success"):
                    order_data = result.get("order", {})
                    executed_qty = float(order_data.get("executedQty", order_data.get("executed_qty", quantity)))
                    avg_price = float(order_data.get("avgPrice", order_data.get("avg_price", price)))
                    order_id = order_data.get("orderId", order_data.get("order_id"))
                    
                    logger.info(f"✅ 买入订单成功")
                    logger.info(f"  订单ID: {order_id}")
                    logger.info(f"  成交数量: {executed_qty:.6f}")
                    logger.info(f"  成交均价: {avg_price:.2f}")
                    
                    # 更新状态
                    self.position = executed_qty
                    self.entry_price = avg_price
                    self.entry_time = time_str
                    self.entry_order_id = order_id
                    
                    return True
                else:
                    logger.error(f"买入订单失败: {result.get('error')}")
                    return False
            except Exception as e:
                logger.error(f"执行买入订单时出错: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return False
    
    def _execute_sell_order(self, price: float, time_str: str) -> bool:
        """
        执行卖出订单
        
        Args:
            price: 卖出价格
            time_str: 时间字符串
            
        Returns:
            是否成功
        """
        quantity = self._calculate_order_quantity(price, "SELL")
        
        if quantity < self.min_order_quantity:
            logger.warning(f"持仓数量 {quantity} 小于最小下单数量 {self.min_order_quantity}")
            return False
        
        logger.info(f"准备卖出: {self.symbol}, 数量: {quantity:.6f}, 价格: {price:.2f}")
        
        if self.dry_run:
            # 计算盈亏
            profit_amount = (price - self.entry_price) * quantity
            profit_pct = (price - self.entry_price) / self.entry_price * 100
            
            logger.info("🔴 [模拟] 执行卖出订单")
            logger.info(f"  时间: {time_str}")
            logger.info(f"  价格: {price:.2f}")
            logger.info(f"  入场价: {self.entry_price:.2f}")
            logger.info(f"  数量: {quantity:.6f}")
            logger.info(f"  盈亏金额: {profit_amount:+.2f}")
            logger.info(f"  盈亏比例: {profit_pct:+.2f}%")
            
            # 记录交易
            trade_record = {
                'entry_time': self.entry_time,
                'exit_time': time_str,
                'entry_price': self.entry_price,
                'exit_price': price,
                'quantity': quantity,
                'profit_amount': profit_amount,
                'profit_pct': profit_pct
            }
            self.completed_trades.append(trade_record)
            
            # 更新统计
            self.total_trades += 1
            self.total_profit += profit_amount
            if profit_amount > 0:
                self.win_trades += 1
            else:
                self.loss_trades += 1
            
            # 重置持仓
            self.position = 0.0
            self.entry_price = 0.0
            self.entry_time = None
            self.entry_order_id = None
            
            return True
        else:
            # 真实下单
            try:
                if self.market_type == "futures":
                    result = test_futures_order(
                        symbol=self.symbol,
                        side="SELL",
                        order_type="MARKET",
                        quantity=quantity,
                        reduce_only="true"  # 只减仓
                    )
                else:
                    result = test_spot_order(
                        symbol=self.symbol,
                        side="SELL",
                        order_type="MARKET",
                        quantity=quantity
                    )
                
                if result.get("success"):
                    order_data = result.get("order", {})
                    executed_qty = float(order_data.get("executedQty", order_data.get("executed_qty", quantity)))
                    avg_price = float(order_data.get("avgPrice", order_data.get("avg_price", price)))
                    order_id = order_data.get("orderId", order_data.get("order_id"))
                    
                    # 计算盈亏
                    profit_amount = (avg_price - self.entry_price) * executed_qty
                    profit_pct = (avg_price - self.entry_price) / self.entry_price * 100
                    
                    logger.info(f"✅ 卖出订单成功")
                    logger.info(f"  订单ID: {order_id}")
                    logger.info(f"  成交数量: {executed_qty:.6f}")
                    logger.info(f"  成交均价: {avg_price:.2f}")
                    logger.info(f"  盈亏金额: {profit_amount:+.2f}")
                    logger.info(f"  盈亏比例: {profit_pct:+.2f}%")
                    
                    # 记录交易
                    trade_record = {
                        'entry_time': self.entry_time,
                        'exit_time': time_str,
                        'entry_price': self.entry_price,
                        'exit_price': avg_price,
                        'quantity': executed_qty,
                        'profit_amount': profit_amount,
                        'profit_pct': profit_pct,
                        'entry_order_id': self.entry_order_id,
                        'exit_order_id': order_id
                    }
                    self.completed_trades.append(trade_record)
                    
                    # 更新统计
                    self.total_trades += 1
                    self.total_profit += profit_amount
                    if profit_amount > 0:
                        self.win_trades += 1
                    else:
                        self.loss_trades += 1
                    
                    # 重置持仓
                    self.position = 0.0
                    self.entry_price = 0.0
                    self.entry_time = None
                    self.entry_order_id = None
                    
                    return True
                else:
                    logger.error(f"卖出订单失败: {result.get('error')}")
                    return False
            except Exception as e:
                logger.error(f"执行卖出订单时出错: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return False
    
    def _on_new_kline(self, kline_dict: Dict[str, Any], data_df):
        """
        新K线数据回调函数
        
        Args:
            kline_dict: 新K线数据字典
            data_df: 历史数据DataFrame
        """
        current_price = kline_dict['close_price']
        current_time = kline_dict['open_time_str']
        
        # 计算交易信号
        signal = self._calculate_signal(data_df)
        
        # 显示状态
        self._display_status(current_time, current_price, signal)
        
        # 检查止盈止损（如果有持仓）
        if self.position > 0:
            profit_pct = (current_price - self.entry_price) / self.entry_price
            if profit_pct >= self.take_profit:
                logger.info(f"触发止盈: {profit_pct*100:.2f}% >= {self.take_profit*100:.2f}%")
                self._execute_sell_order(current_price, current_time)
                return
            elif profit_pct <= -self.stop_loss:
                logger.info(f"触发止损: {profit_pct*100:.2f}% <= -{self.stop_loss*100:.2f}%")
                self._execute_sell_order(current_price, current_time)
                return
        
        # 执行交易
        if signal == 'buy' and self.position == 0:
            # 避免频繁交易：检查上次信号时间
            if self.last_signal == 'buy' and self.last_signal_time:
                time_diff = (datetime.now() - self.last_signal_time).total_seconds()
                if time_diff < 60:  # 至少间隔60秒
                    logger.debug("买入信号过于频繁，跳过")
                    return
            
            self._execute_buy_order(current_price, current_time)
            self.last_signal = 'buy'
            self.last_signal_time = datetime.now()
            
        elif signal == 'sell' and self.position > 0:
            self._execute_sell_order(current_price, current_time)
            self.last_signal = 'sell'
            self.last_signal_time = datetime.now()
    
    def _display_status(self, time_str: str, price: float, signal: Optional[str]):
        """
        显示当前状态
        
        Args:
            time_str: 时间字符串
            price: 当前价格
            signal: 交易信号
        """
        # 计算统计信息
        runtime = datetime.now() - self.start_time
        runtime_str = f"{runtime.days}天 {runtime.seconds // 3600}小时 {(runtime.seconds % 3600) // 60}分钟"
        win_rate = (self.win_trades / self.total_trades * 100) if self.total_trades > 0 else 0.0
        
        # 获取余额
        available_balance = self._get_available_balance()
        
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
            profit_pct = (price - self.entry_price) / self.entry_price * 100
            print(f"持仓: {self.position:.6f} | 入场价: {self.entry_price:.2f} | 浮动盈亏: {profit_pct:+.2f}%")
        else:
            print(f"持仓: 无")
        print(f"{'='*80}")
        print(f"💰 账户信息:")
        print(f"  可用余额: {available_balance:.2f}")
        print(f"  累计盈亏: {self.total_profit:+.2f}")
        print(f"  运行时间: {runtime_str}")
        print(f"  总交易次数: {self.total_trades} | 盈利: {self.win_trades} | 亏损: {self.loss_trades} | 胜率: {win_rate:.2f}%")
        print(f"{'='*80}\n")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取交易统计信息
        
        Returns:
            统计信息字典
        """
        runtime = datetime.now() - self.start_time
        win_rate = (self.win_trades / self.total_trades * 100) if self.total_trades > 0 else 0.0
        avg_profit = self.total_profit / self.total_trades if self.total_trades > 0 else 0.0
        
        return {
            'total_trades': self.total_trades,
            'win_trades': self.win_trades,
            'loss_trades': self.loss_trades,
            'win_rate': win_rate,
            'total_profit': self.total_profit,
            'avg_profit': avg_profit,
            'runtime': str(runtime),
            'completed_trades': self.completed_trades
        }
    
    def print_final_report(self):
        """
        打印最终报告
        """
        stats = self.get_statistics()
        
        print("\n" + "="*80)
        print("📊 最终交易报告")
        print("="*80)
        print(f"交易对: {self.symbol}")
        print(f"市场类型: {self.market_type}")
        print(f"策略: {self.strategy}")
        print(f"运行时间: {stats['runtime']}")
        print(f"\n📈 交易统计:")
        print(f"  总交易次数: {stats['total_trades']}")
        print(f"  盈利次数: {stats['win_trades']}")
        print(f"  亏损次数: {stats['loss_trades']}")
        print(f"  胜率: {stats['win_rate']:.2f}%")
        print(f"  总盈亏: {stats['total_profit']:+.2f}")
        print(f"  平均盈亏: {stats['avg_profit']:.2f}")
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
    
    async def start(self):
        """
        启动实盘交易
        """
        print("="*80)
        print("🚀 实盘交易机器人启动")
        print("="*80)
        print(f"交易对: {self.symbol}")
        print(f"市场类型: {self.market_type}")
        print(f"时间间隔: {self.interval}")
        print(f"策略: {self.strategy}")
        print(f"仓位大小: {self.position_size_pct * 100:.0f}%")
        print(f"止盈: {self.take_profit * 100:.0f}%")
        print(f"止损: {self.stop_loss * 100:.0f}%")
        print(f"模式: {'模拟模式' if self.dry_run else '实盘模式'}")
        print("="*80)
        
        # 显示账户余额
        print("\n账户余额:")
        if self.market_type == "futures":
            show_futures_balances()
        else:
            show_spot_balances()
        
        print("\n等待实时数据...\n")
        
        await self.tracker.run_forever()


async def test_real_time_trading():
    """
    测试实盘交易
    """
    # 创建实盘交易机器人
    # ⚠️ 警告：设置 dry_run=False 将执行真实交易！
    bot = RealTimeTradingBot(
        symbol="BNBUSDT",
        interval="3m",
        lookback_periods=1000,
        market_type="futures",  # 或 "spot"
        position_size_pct=0.01,
        take_profit=0.1,
        stop_loss=0.1,
        strategy="ma5",  # 可选: ma5, ma_cross, ma_factor, rsi_factor, alpha1
        min_order_quantity=0.00001,
        ssl_verify=False,
        dry_run=False  # ⚠️ 设置为 False 将执行真实交易！
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
    set_user()
    print("="*80)
    print("实盘交易脚本")
    print("="*80)
    print("\n⚠️  重要提示：")
    print("  1. 此脚本会执行真实交易（当 dry_run=False 时）")
    print("  2. 建议先在模拟模式下测试（dry_run=True）")
    print("  3. 确保策略已经过充分回测")
    print("  4. 设置合理的止盈止损")
    print("  5. 确保账户有足够的余额")
    print("  6. 按 Ctrl+C 停止交易")
    print()
    
    # 确认是否继续
    if not os.getenv("AUTO_CONFIRM"):
        response = input("是否继续？(yes/no): ")
        if response.lower() != "yes":
            print("已取消")
            return
    
    try:
        asyncio.run(test_real_time_trading())
    except KeyboardInterrupt:
        print("\n交易已停止")
    except Exception as e:
        print(f"\n交易过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

