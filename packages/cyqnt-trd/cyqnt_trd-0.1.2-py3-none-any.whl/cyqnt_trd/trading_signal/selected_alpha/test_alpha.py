"""
Alpha因子测试脚本

测试 selected_alpha 模块中的 Alpha 因子

这个文件是 test_script/test_alpha.py 的快捷方式，可以直接在 selected_alpha 目录下运行测试。

使用方法：
    # 方式1: 作为模块运行（推荐）
    cd /Users/user/Desktop/repo/cyqnt_trd
    python -m cyqnt_trd.trading_signal.selected_alpha.test_alpha
    
    # 方式2: 直接运行脚本
    cd /Users/user/Desktop/repo/cyqnt_trd
    python cyqnt_trd/trading_signal/selected_alpha/test_alpha.py
"""

import sys
import os

# 添加项目根目录到路径，以便导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录（cyqnt_trd 的父目录）
# test_alpha.py 位于: cyqnt_trd/cyqnt_trd/trading_signal/selected_alpha/test_alpha.py
# 需要向上4级到达: cyqnt_trd/
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入回测框架和Alpha因子模块
try:
    from cyqnt_trd.backtesting import BacktestFramework
    from cyqnt_trd.trading_signal.selected_alpha import alpha1_factor
    from cyqnt_trd.trading_signal.signal import factor_based_signal
except ImportError as e:
    print(f"导入错误: {e}")
    print(f"\n当前工作目录: {os.getcwd()}")
    print(f"当前文件路径: {os.path.abspath(__file__)}")
    print(f"项目根目录: {project_root}")
    print(f"Python路径: {sys.path[:3]}")
    print("\n提示：请使用以下方式运行：")
    print("  cd /Users/user/Desktop/repo/cyqnt_trd")
    print("  python -m cyqnt_trd.trading_signal.selected_alpha.test_alpha")
    print("\n或者直接运行脚本：")
    print("  cd /Users/user/Desktop/repo/cyqnt_trd")
    print("  python cyqnt_trd/trading_signal/selected_alpha/test_alpha.py")
    sys.exit(1)


def test_alpha1_factor():
    """
    测试 Alpha#1 因子
    
    测试因子在预测未来价格方向上的胜率
    """
    print("=" * 60)
    print("测试 Alpha#1 因子")
    print("=" * 60)
    print("\n因子说明：")
    print("  - 公式: rank(Ts_ArgMax(SignedPower(((returns<0)?stddev(returns,20):close),2.),5))-0.5)")
    print("  - 策略逻辑：对过去5天按照收盘价最高或下行波动率最高进行排名")
    print("  - 下行波动率最高的一天离计算时间越近，越可以投资")
    print("  - 收盘价最高离计算时间越近，越可以投资")
    print("  - 标签：mean-reversion+momentum")
    print()
    
    # 加载数据
    # 可以使用不同的数据文件进行测试
    data_path = '/Users/user/Desktop/repo/cyqnt_trd/tmp/data/BTCUSDT_futures/BTCUSDT_3m_158879_20250101_000000_20251127_235959_20251128_145101.json'
    
    # 如果数据文件不存在，尝试其他路径
    if not os.path.exists(data_path):
        # 尝试查找其他可用的数据文件
        data_dir = '/Users/user/Desktop/repo/cyqnt_trd/tmp/data'
        if os.path.exists(data_dir):
            # 查找第一个可用的JSON文件
            for root, dirs, files in os.walk(data_dir):
                for file in files:
                    if file.endswith('.json'):
                        data_path = os.path.join(root, file)
                        print(f"使用数据文件: {data_path}")
                        break
                if data_path and os.path.exists(data_path):
                    break
    
    if not os.path.exists(data_path):
        print(f"错误：找不到数据文件: {data_path}")
        print("请确保数据文件存在，或修改 data_path 变量指向正确的数据文件")
        return
    
    framework = BacktestFramework(data_path=data_path)
    
    # 创建因子包装函数
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
    save_dir = '/Users/user/Desktop/repo/cyqnt_trd/result'
    framework.print_factor_results(
        factor_results,
        save_dir=save_dir
    )


def test_alpha1_with_different_params():
    """
    测试 Alpha#1 因子的不同参数组合
    """
    print("\n" + "=" * 60)
    print("测试 Alpha#1 因子的不同参数组合")
    print("=" * 60)
    
    # 加载数据
    data_path = '/Users/user/Desktop/repo/cyqnt_trd/tmp/data/BTCUSDT_futures/BTCUSDT_1d_1095_20251127_113603.json'
    
    if not os.path.exists(data_path):
        print(f"错误：找不到数据文件: {data_path}")
        return
    
    framework = BacktestFramework(data_path=data_path)
    
    # 测试不同的参数组合
    param_combinations = [
        {"lookback_days": 3, "stddev_period": 10, "power": 2.0, "name": "Alpha#1 (lookback=3, stddev=10)"},
        {"lookback_days": 5, "stddev_period": 20, "power": 2.0, "name": "Alpha#1 (lookback=5, stddev=20)"},
        {"lookback_days": 7, "stddev_period": 30, "power": 2.0, "name": "Alpha#1 (lookback=7, stddev=30)"},
    ]
    
    for params in param_combinations:
        print(f"\n测试参数组合: {params['name']}")
        print(f"  lookback_days={params['lookback_days']}, stddev_period={params['stddev_period']}, power={params['power']}")
        
        def alpha1_wrapper(data_slice):
            return alpha1_factor(
                data_slice,
                lookback_days=params['lookback_days'],
                stddev_period=params['stddev_period'],
                power=params['power']
            )
        
        min_periods = params['lookback_days'] + params['stddev_period'] + 5
        
        factor_results = framework.test_factor(
            factor_func=alpha1_wrapper,
            forward_periods=7,
            min_periods=min_periods,
            factor_name=params['name']
        )
        
        # 只打印简要结果
        print(f"  总样本数: {factor_results['total_samples']}")
        print(f"  看多信号数: {factor_results['long_signals']}")
        print(f"  看空信号数: {factor_results['short_signals']}")
        print(f"  看多胜率: {factor_results['long_win_rate']:.2%}")
        print(f"  看空胜率: {factor_results['short_win_rate']:.2%}")
        print(f"  总体胜率: {factor_results['overall_win_rate']:.2%}")


def test_alpha1_in_signal():
    """
    测试在信号策略中使用 Alpha#1 因子
    """
    print("\n" + "=" * 60)
    print("测试在信号策略中使用 Alpha#1 因子")
    print("=" * 60)
    
    # 加载数据
    data_path = '/Users/user/Desktop/repo/cyqnt_trd/tmp/data/BTCUSDT_futures/BTCUSDT_1d_1095_20251127_113603.json'
    
    if not os.path.exists(data_path):
        print(f"错误：找不到数据文件: {data_path}")
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
    save_dir = '/Users/user/Desktop/repo/cyqnt_trd/result'
    framework.plot_backtest_results(
        backtest_results,
        save_dir=save_dir
    )


def main():
    """
    主函数：运行所有测试
    """
    # 测试 Alpha#1 因子
    # test_alpha1_factor()
    
    # 测试不同参数组合（可选，取消注释以运行）
    # test_alpha1_with_different_params()
    
    # 测试在信号策略中使用 Alpha#1 因子（可选，取消注释以运行）
    test_alpha1_in_signal()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("\n提示：")
    print("  - 取消注释 main() 函数中的其他测试函数来运行更多测试")
    print("  - 推荐使用模块方式运行: python3 -m cyqnt_trd.trading_signal.selected_alpha.test_alpha")


if __name__ == "__main__":
    main()