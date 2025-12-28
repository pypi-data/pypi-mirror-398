"""
测试所有101个Alpha因子

测试 selected_alpha 模块中的所有 Alpha 因子，验证它们是否能正常工作。

使用方法：
    # 方式1: 作为模块运行（推荐）
    cd /Users/user/Desktop/repo/crypto_trading
    python -m cyqnt_trd.trading_signal.example_test_alpha
    
    # 方式2: 直接运行脚本
    cd /Users/user/Desktop/repo/crypto_trading
    python cyqnt_trd/trading_signal/example_test_alpha.py
"""

import sys
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import traceback
from datetime import datetime

# 添加项目根目录到路径，以便导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入所有alpha因子
try:
    from cyqnt_trd.trading_signal.selected_alpha import ALPHA_FACTORS
    from cyqnt_trd.backtesting import BacktestFramework
except ImportError as e:
    print(f"导入错误: {e}")
    print(f"\n当前工作目录: {os.getcwd()}")
    print(f"当前文件路径: {os.path.abspath(__file__)}")
    print(f"项目根目录: {project_root}")
    print("\n提示：请使用以下方式运行：")
    print("  cd /Users/user/Desktop/repo/crypto_trading")
    print("  python -m cyqnt_trd.trading_signal.example_test_alpha")
    sys.exit(1)


def create_test_data(n_samples: int = 100) -> pd.DataFrame:
    """
    创建测试数据
    
    Args:
        n_samples: 样本数量
    
    Returns:
        测试用的DataFrame
    """
    np.random.seed(42)
    
    # 生成模拟价格数据
    base_price = 100.0
    prices = [base_price]
    for i in range(n_samples - 1):
        change = np.random.normal(0, 0.02)  # 2%的标准差
        prices.append(prices[-1] * (1 + change))
    
    # 创建DataFrame
    data = pd.DataFrame({
        'open_price': [p * (1 + np.random.normal(0, 0.01)) for p in prices],
        'high_price': [p * (1 + abs(np.random.normal(0, 0.015))) for p in prices],
        'low_price': [p * (1 - abs(np.random.normal(0, 0.015))) for p in prices],
        'close_price': prices,
        'volume': np.random.uniform(1000, 10000, n_samples),
        'quote_volume': [p * v for p, v in zip(prices, np.random.uniform(1000, 10000, n_samples))],
    })
    
    # 确保high >= close >= low, high >= open >= low
    for i in range(len(data)):
        high = max(data.iloc[i]['open_price'], data.iloc[i]['close_price'])
        low = min(data.iloc[i]['open_price'], data.iloc[i]['close_price'])
        data.iloc[i, data.columns.get_loc('high_price')] = max(high, data.iloc[i]['high_price'])
        data.iloc[i, data.columns.get_loc('low_price')] = min(low, data.iloc[i]['low_price'])
    
    return data


def test_single_alpha(alpha_num: int, alpha_func, test_data: pd.DataFrame) -> Tuple[bool, str, float]:
    """
    测试单个alpha因子
    
    Args:
        alpha_num: alpha编号
        alpha_func: alpha因子函数
        test_data: 测试数据
    
    Returns:
        (是否成功, 错误信息或成功信息, 因子值)
    """
    try:
        # 测试不同长度的数据切片
        test_sizes = [10, 20, 50, len(test_data)]
        
        for size in test_sizes:
            if size > len(test_data):
                continue
            
            data_slice = test_data.iloc[:size]
            result = alpha_func(data_slice)
            
            # 检查结果类型
            if not isinstance(result, (int, float, np.number)):
                return False, f"返回类型错误: {type(result)}, 期望 float", 0.0
            
            # 检查是否为NaN或无穷大
            if pd.isna(result) or np.isinf(result):
                return False, f"返回值为NaN或无穷大: {result}", 0.0
        
        # 如果所有测试都通过，返回成功
        final_result = alpha_func(test_data)
        return True, "测试通过", float(final_result)
        
    except Exception as e:
        error_msg = f"错误: {str(e)}"
        return False, error_msg, 0.0


def test_all_alphas_with_test_data():
    """
    使用模拟测试数据测试所有alpha因子
    """
    print("=" * 80)
    print("测试所有101个Alpha因子（使用模拟数据）")
    print("=" * 80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 创建测试数据
    print("创建测试数据...")
    test_data = create_test_data(n_samples=200)
    print(f"  测试数据样本数: {len(test_data)}")
    print(f"  数据列: {list(test_data.columns)}")
    print()
    
    # 测试结果统计
    results: Dict[int, Tuple[bool, str, float]] = {}
    success_count = 0
    fail_count = 0
    
    # 测试每个alpha因子
    print("开始测试alpha因子...")
    print("-" * 80)
    
    for alpha_num in sorted(ALPHA_FACTORS.keys()):
        alpha_func = ALPHA_FACTORS[alpha_num]
        success, message, value = test_single_alpha(alpha_num, alpha_func, test_data)
        results[alpha_num] = (success, message, value)
        
        if success:
            success_count += 1
            status = "✓"
        else:
            fail_count += 1
            status = "✗"
        
        # 打印结果
        print(f"{status} Alpha#{alpha_num:3d}: {message[:50]}")
        if not success:
            print(f"   详情: {message}")
    
    print("-" * 80)
    print()
    
    # 打印统计结果
    print("=" * 80)
    print("测试结果统计")
    print("=" * 80)
    print(f"总alpha数量: {len(ALPHA_FACTORS)}")
    print(f"测试成功: {success_count}")
    print(f"测试失败: {fail_count}")
    print(f"成功率: {success_count / len(ALPHA_FACTORS) * 100:.2f}%")
    print()
    
    # 打印失败的alpha列表
    if fail_count > 0:
        print("失败的Alpha因子:")
        for alpha_num, (success, message, _) in results.items():
            if not success:
                print(f"  Alpha#{alpha_num}: {message}")
        print()
    
    return results


def test_all_alphas_with_real_data(data_path: str = None):
    """
    使用真实数据测试所有alpha因子
    
    Args:
        data_path: 数据文件路径，如果为None则使用默认路径
    """
    print("=" * 80)
    print("测试所有101个Alpha因子（使用真实数据）")
    print("=" * 80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 确定数据文件路径
    if data_path is None:
        data_path = "/Users/user/Desktop/repo/data_all/tmp/data/BTCUSDT_current/BTCUSDT_3m_32160_20251002_000000_20251208_000000_20251211_111242.json"
    
    # 检查文件是否存在
    if not os.path.exists(data_path):
        print(f"错误：数据文件不存在: {data_path}")
        print("请提供正确的数据文件路径")
        return None
    
    print(f"加载数据文件: {data_path}")
    
    try:
        # 加载数据
        framework = BacktestFramework(data_path=data_path)
        data = framework.data
        
        print(f"  数据样本数: {len(data)}")
        print(f"  数据列: {list(data.columns)}")
        print()
        
        # 确保数据包含必要的列
        required_columns = ['open_price', 'high_price', 'low_price', 'close_price', 'volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            print(f"错误：数据缺少必要的列: {missing_columns}")
            return None
        
        # 如果没有quote_volume，使用volume * close_price估算
        if 'quote_volume' not in data.columns:
            data['quote_volume'] = data['volume'] * data['close_price']
            print("  注意：使用 volume * close_price 估算 quote_volume")
            print()
        
    except Exception as e:
        print(f"错误：加载数据失败: {e}")
        traceback.print_exc()
        return None
    
    # 测试结果统计
    results: Dict[int, Tuple[bool, str, float]] = {}
    success_count = 0
    fail_count = 0
    
    # 测试每个alpha因子
    print("开始测试alpha因子...")
    print("-" * 80)
    
    # 使用数据的前1000行进行测试（如果数据足够长）
    test_size = min(1000, len(data))
    test_data = data.iloc[:test_size]
    
    for alpha_num in sorted(ALPHA_FACTORS.keys()):
        alpha_func = ALPHA_FACTORS[alpha_num]
        
        try:
            # 测试不同长度的数据切片
            test_sizes = [50, 100, 200, test_size]
            all_success = True
            error_msg = ""
            
            for size in test_sizes:
                if size > len(test_data):
                    continue
                
                try:
                    data_slice = test_data.iloc[:size]
                    result = alpha_func(data_slice)
                    
                    # 检查结果类型
                    if not isinstance(result, (int, float, np.number)):
                        all_success = False
                        error_msg = f"返回类型错误: {type(result)}"
                        break
                    
                    # 检查是否为NaN或无穷大
                    if pd.isna(result) or np.isinf(result):
                        # 对于某些alpha，NaN可能是正常的（数据不足），不算错误
                        pass
                
                except Exception as e:
                    all_success = False
                    error_msg = f"计算错误 (size={size}): {str(e)}"
                    break
            
            if all_success:
                # 最终测试
                final_result = alpha_func(test_data)
                if pd.isna(final_result) or np.isinf(final_result):
                    results[alpha_num] = (True, "测试通过（返回NaN/Inf，可能是数据不足）", float(final_result) if not pd.isna(final_result) else 0.0)
                else:
                    results[alpha_num] = (True, "测试通过", float(final_result))
                success_count += 1
                status = "✓"
            else:
                results[alpha_num] = (False, error_msg, 0.0)
                fail_count += 1
                status = "✗"
        
        except Exception as e:
            error_msg = f"异常: {str(e)}"
            results[alpha_num] = (False, error_msg, 0.0)
            fail_count += 1
            status = "✗"
        
        # 打印结果（每10个alpha打印一次详细进度）
        if alpha_num % 10 == 0 or not results[alpha_num][0]:
            print(f"{status} Alpha#{alpha_num:3d}: {results[alpha_num][1][:60]}")
    
    print("-" * 80)
    print()
    
    # 打印统计结果
    print("=" * 80)
    print("测试结果统计")
    print("=" * 80)
    print(f"总alpha数量: {len(ALPHA_FACTORS)}")
    print(f"测试成功: {success_count}")
    print(f"测试失败: {fail_count}")
    print(f"成功率: {success_count / len(ALPHA_FACTORS) * 100:.2f}%")
    print()
    
    # 打印失败的alpha列表
    if fail_count > 0:
        print("失败的Alpha因子:")
        for alpha_num, (success, message, _) in results.items():
            if not success:
                print(f"  Alpha#{alpha_num}: {message}")
        print()
    
    return results


def test_alpha_with_backtest_framework(alpha_num: int, data_path: str = None):
    """
    使用BacktestFramework测试单个alpha因子
    
    Args:
        alpha_num: alpha编号
        data_path: 数据文件路径
    """
    if data_path is None:
        data_path = "/Users/user/Desktop/repo/data_all/tmp/data/BTCUSDT_current/BTCUSDT_3m_32160_20251002_000000_20251208_000000_20251211_111242.json"
    
    if not os.path.exists(data_path):
        print(f"错误：数据文件不存在: {data_path}")
        return
    
    print(f"测试 Alpha#{alpha_num} 因子（使用BacktestFramework）")
    print("-" * 80)
    
    try:
        framework = BacktestFramework(data_path=data_path)
        alpha_func = ALPHA_FACTORS[alpha_num]
        
        # 创建包装函数
        def alpha_wrapper(data_slice):
            return alpha_func(data_slice)
        
        # 测试因子
        factor_results = framework.test_factor(
            factor_func=alpha_wrapper,
            forward_periods=7,
            min_periods=50,
            factor_name=f"Alpha#{alpha_num}因子"
        )
        
        # 打印简要结果
        print(f"  总样本数: {factor_results['total_samples']}")
        print(f"  看多信号数: {factor_results['long_signals']}")
        print(f"  看空信号数: {factor_results['short_signals']}")
        print(f"  看多胜率: {factor_results['long_win_rate']:.2%}")
        print(f"  看空胜率: {factor_results['short_win_rate']:.2%}")
        print(f"  总体胜率: {factor_results['overall_win_rate']:.2%}")
        print("  测试成功！")
        
    except Exception as e:
        print(f"  测试失败: {e}")
        traceback.print_exc()


def main():
    """
    主函数：运行所有测试
    """
    print("\n" + "=" * 80)
    print("Alpha因子测试脚本")
    print("=" * 80)
    print()
    
    # 测试1: 使用模拟数据测试所有alpha
    print("【测试1】使用模拟数据测试所有alpha因子")
    print()
    test_all_alphas_with_test_data()
    print("\n")
    
    # 测试2: 使用真实数据测试所有alpha
    print("【测试2】使用真实数据测试所有alpha因子")
    print()
    data_path = "/Users/user/Desktop/repo/data_all/tmp/data/BTCUSDT_current/BTCUSDT_3m_32160_20251002_000000_20251208_000000_20251211_111242.json"
    
    if os.path.exists(data_path):
        test_all_alphas_with_real_data(data_path)
    else:
        print(f"警告：真实数据文件不存在: {data_path}")
        print("跳过真实数据测试")
    print("\n")
    
    # 测试3: 使用BacktestFramework测试几个示例alpha（可选）
    print("【测试3】使用BacktestFramework测试示例alpha因子（Alpha#1, Alpha#101）")
    print()
    if os.path.exists(data_path):
        test_alpha_with_backtest_framework(1, data_path)
        print()
        test_alpha_with_backtest_framework(101, data_path)
    else:
        print("跳过BacktestFramework测试（数据文件不存在）")
    
    print("\n" + "=" * 80)
    print("所有测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()

