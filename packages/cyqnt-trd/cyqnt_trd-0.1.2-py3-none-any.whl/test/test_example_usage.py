"""
测试 cyqnt_trd package 的使用示例

参考 cyqnt_trd.trading_signal.example_usage，使用 package 方式导入和使用
"""

import os
from pathlib import Path

# 使用 package 方式导入（假设已通过 pip install -e . 安装）
from cyqnt_trd.backtesting import BacktestFramework
from cyqnt_trd.trading_signal.factor import ma_factor, ma_cross_factor, rsi_factor
from cyqnt_trd.trading_signal.signal import (
    ma_signal,
    ma_cross_signal,
    factor_based_signal,
    multi_factor_signal
)
from cyqnt_trd.trading_signal.selected_alpha import alpha1_factor


def get_data_path(symbol: str = "BTCUSDT", data_type: str = "current") -> str:
    """
    获取数据文件路径
    
    Args:
        symbol: 交易对符号，例如 'BTCUSDT'
        data_type: 数据类型，'current' 或 'futures'
    
    Returns:
        数据文件路径
    """
    # 获取项目根目录（data_all）
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "tmp" / "data" / f"{symbol}_{data_type}"
    
    # 查找 JSON 文件
    json_files = list(data_dir.glob("*.json"))
    if json_files:
        # 返回最新的文件
        return str(sorted(json_files, key=lambda x: x.stat().st_mtime, reverse=True)[0])
    else:
        raise FileNotFoundError(f"未找到 {symbol}_{data_type} 的数据文件")


def test_1_use_factor():
    """
    测试1: 使用factor中的因子进行因子测试
    """
    print("=" * 60)
    print("测试1: 使用factor中的因子进行因子测试")
    print("=" * 60)
    
    try:
        data_path = get_data_path("BTCUSDT", "current")
        print(f"使用数据文件: {data_path}")
    except FileNotFoundError as e:
        print(f"错误: {e}")
        return
    
    framework = BacktestFramework(data_path=data_path)
    
    # 使用factor中的ma_factor进行测试
    def ma_factor_wrapper(data_slice):
        return ma_factor(data_slice, period=5)
    
    factor_results = framework.test_factor(
        factor_func=ma_factor_wrapper,
        forward_periods=5,
        min_periods=10,
        factor_name="MA5因子（来自factor模块）"
    )
    
    # 保存结果到 result 目录
    save_dir = str(Path(__file__).parent.parent / "result")
    os.makedirs(save_dir, exist_ok=True)
    framework.print_factor_results(
        factor_results,
        save_dir=save_dir
    )


def test_2_use_signal():
    """
    测试2: 使用signal中的信号策略进行回测
    """
    print("\n" + "=" * 60)
    print("测试2: 使用signal中的信号策略进行回测")
    print("=" * 60)
    
    try:
        data_path = get_data_path("BTCUSDT", "current")
        print(f"使用数据文件: {data_path}")
    except FileNotFoundError as e:
        print(f"错误: {e}")
        return

    framework = BacktestFramework(data_path=data_path)
    
    # 使用signal中的ma_signal进行回测
    period = 3
    def ma_signal_wrapper(data_slice, position, entry_price, entry_index, take_profit, stop_loss, check_periods):
        return ma_signal(
            data_slice, position, entry_price, entry_index,
            take_profit, stop_loss, period=period
        )
    
    backtest_results = framework.backtest_strategy(
        signal_func=ma_signal_wrapper,
        min_periods=10,
        position_size=0.2,
        initial_capital=10000.0,
        commission_rate=0.00001,
        take_profit=0.03,
        stop_loss=0.1,
        strategy_name="MA3策略（来自signal模块）"
    )
    
    framework.print_backtest_results(backtest_results)
    
    # 保存结果
    save_dir = str(Path(__file__).parent.parent / "result")
    os.makedirs(save_dir, exist_ok=True)
    framework.plot_backtest_results(
        backtest_results,
        save_dir=save_dir
    )


def test_3_factor_in_signal():
    """
    测试3: 在signal中使用factor中的因子
    """
    print("\n" + "=" * 60)
    print("测试3: 在signal中使用factor中的因子")
    print("=" * 60)
    
    try:
        data_path = get_data_path("BTCUSDT", "current")
        print(f"使用数据文件: {data_path}")
    except FileNotFoundError as e:
        print(f"错误: {e}")
        return

    framework = BacktestFramework(data_path=data_path)
    
    # 使用factor_based_signal，它内部会使用factor中的因子
    def factor_signal_wrapper(data_slice, position, entry_price, entry_index, take_profit, stop_loss, check_periods):
        # 使用factor中的ma_factor
        factor_func = lambda d: ma_factor(d, period=5)
        return factor_based_signal(
            data_slice, position, entry_price, entry_index,
            take_profit, stop_loss, check_periods,
            factor_func=factor_func
        )
    
    backtest_results = framework.backtest_strategy(
        signal_func=factor_signal_wrapper,
        min_periods=35,  # 至少需要35个周期
        position_size=0.2,
        initial_capital=10000.0,
        commission_rate=0.00001,
        take_profit=0.1,
        stop_loss=0.5,
        check_periods=1,
        strategy_name="基于MA因子的策略"
    )
    
    framework.print_backtest_results(backtest_results)
    
    # 保存结果
    save_dir = str(Path(__file__).parent.parent / "result")
    os.makedirs(save_dir, exist_ok=True)
    framework.plot_backtest_results(
        backtest_results,
        save_dir=save_dir
    )


def test_4_multi_factor():
    """
    测试4: 使用多因子组合策略
    """
    print("\n" + "=" * 60)
    print("测试4: 使用多因子组合策略")
    print("=" * 60)
    
    try:
        data_path = get_data_path("BTCUSDT", "current")
        print(f"使用数据文件: {data_path}")
    except FileNotFoundError as e:
        print(f"错误: {e}")
        return

    framework = BacktestFramework(data_path=data_path)
    
    # 使用multi_factor_signal，组合多个因子
    def multi_factor_signal_wrapper(data_slice, position, entry_price, entry_index, take_profit, stop_loss, check_periods):
        # 组合ma_factor和rsi_factor
        factor_funcs = [
            lambda d: ma_factor(d, period=5),
            lambda d: rsi_factor(d, period=14)
        ]
        weights = [0.6, 0.4]  # MA因子权重0.6，RSI因子权重0.4
        
        return multi_factor_signal(
            data_slice, position, entry_price, entry_index,
            take_profit, stop_loss, check_periods,
            factor_funcs=factor_funcs,
            weights=weights
        )
    
    backtest_results = framework.backtest_strategy(
        signal_func=multi_factor_signal_wrapper,
        min_periods=20,  # 需要更多周期因为RSI需要14个周期
        position_size=0.2,
        initial_capital=10000.0,
        commission_rate=0.00001,
        take_profit=0.1,
        stop_loss=0.5,
        check_periods=1,
        strategy_name="多因子组合策略（MA+RSI）"
    )
    
    framework.print_backtest_results(backtest_results)
    
    # 保存结果
    save_dir = str(Path(__file__).parent.parent / "result")
    os.makedirs(save_dir, exist_ok=True)
    framework.plot_backtest_results(
        backtest_results,
        save_dir=save_dir
    )


def test_5_alpha1_factor():
    """
    测试5: 使用Alpha#1因子进行因子测试
    """
    print("\n" + "=" * 60)
    print("测试5: 使用Alpha#1因子进行因子测试")
    print("=" * 60)
    print("\n因子说明：")
    print("  - 公式: rank(Ts_ArgMax(SignedPower(((returns<0)?stddev(returns,20):close),2.),5))-0.5)")
    print("  - 策略逻辑：对过去5天按照收盘价最高或下行波动率最高进行排名")
    print("  - 下行波动率最高的一天离计算时间越近，越可以投资")
    print("  - 收盘价最高离计算时间越近，越可以投资")
    print("  - 标签：mean-reversion+momentum")
    print()
    
    try:
        data_path = get_data_path("BTCUSDT", "futures")
        print(f"使用数据文件: {data_path}")
    except FileNotFoundError as e:
        print(f"错误: {e}")
        return

    framework = BacktestFramework(data_path=data_path)
    
    # 使用Alpha#1因子进行测试
    def alpha1_wrapper(data_slice):
        """
        Alpha#1 因子包装函数
        
        使用默认参数：lookback_days=5, stddev_period=20, power=2.0
        """
        return alpha1_factor(
            data_slice,
            lookback_days=5,
            stddev_period=20,
            power=2.0
        )
    
    # 测试因子
    print("开始测试 Alpha#1 因子...")
    print(f"  回看天数: 5")
    print(f"  标准差周期: 20")
    print(f"  幂次: 2.0")
    print(f"  向前看周期: 7")
    print()
    
    factor_results = framework.test_factor(
        factor_func=alpha1_wrapper,
        forward_periods=7,  # 未来7个周期
        min_periods=30,  # 至少需要30个周期（5+20+一些缓冲）
        factor_name="Alpha#1因子"
    )
    
    # 打印结果并保存
    save_dir = str(Path(__file__).parent.parent / "result")
    os.makedirs(save_dir, exist_ok=True)
    framework.print_factor_results(
        factor_results,
        save_dir=save_dir
    )


def test_6_alpha1_signal():
    """
    测试6: 使用基于Alpha#1因子的信号策略进行回测
    """
    print("\n" + "=" * 60)
    print("测试6: 使用基于Alpha#1因子的信号策略进行回测")
    print("=" * 60)
    
    try:
        data_path = get_data_path("BTCUSDT", "futures")
        print(f"使用数据文件: {data_path}")
    except FileNotFoundError as e:
        print(f"错误: {e}")
        return

    framework = BacktestFramework(data_path=data_path)
    
    # 创建使用 Alpha#1 因子的信号策略
    def alpha1_signal_wrapper(data_slice, position, entry_price, entry_index, take_profit, stop_loss, check_periods):
        """
        使用 Alpha#1 因子的信号策略
        """
        # 使用 Alpha#1 因子
        factor_func = lambda d: alpha1_factor(d, lookback_days=5, stddev_period=20, power=2.0)
        return factor_based_signal(
            data_slice, position, entry_price, entry_index,
            take_profit, stop_loss, check_periods,
            factor_func=factor_func
        )
    
    # 回测策略
    print("开始回测基于 Alpha#1 因子的策略...")
    backtest_results = framework.backtest_strategy(
        signal_func=alpha1_signal_wrapper,
        min_periods=30,  # 至少需要30个周期
        position_size=0.2,  # 每次使用20%的资金
        initial_capital=10000.0,
        commission_rate=0.00001,  # 0.001%手续费
        take_profit=0.1,  # 止盈10%
        stop_loss=0.5,  # 止损50%
        check_periods=1,  # 只能为1，因为实际使用时无法看到未来数据
        strategy_name="基于Alpha#1因子的策略"
    )
    
    # 打印结果
    framework.print_backtest_results(backtest_results)
    
    # 绘制结果并保存
    save_dir = str(Path(__file__).parent.parent / "result")
    os.makedirs(save_dir, exist_ok=True)
    framework.plot_backtest_results(
        backtest_results,
        save_dir=save_dir
    )


def main():
    """
    主函数：运行所有测试
    """
    print("=" * 60)
    print("cyqnt_trd Package 测试脚本")
    print("=" * 60)
    print("\n注意：")
    print("  1. 确保已安装 cyqnt_trd package: pip install -e /path/to/cyqnt_trd")
    print("  2. 确保数据文件存在于 tmp/data/ 目录下")
    print("  3. 测试结果将保存到 result/ 目录")
    print()
    
    # 运行测试（可以根据需要取消注释）
    test_1_use_factor()
    test_2_use_signal()
    # test_3_factor_in_signal()
    # test_4_multi_factor()
    # test_5_alpha1_factor()
    # test_6_alpha1_signal()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
