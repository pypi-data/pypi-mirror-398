"""
测试 cyqnt_trd 包中的 get_and_save_futures_klines 和 get_and_save_klines_direct 函数

使用方法：
    python test_get_data.py
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径（如果需要）
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入 cyqnt_trd 包中的函数
from cyqnt_trd.get_data import get_and_save_futures_klines, get_and_save_klines_direct


def test_get_and_save_futures_klines():
    """
    测试1: 测试 get_and_save_futures_klines 函数
    """
    print("=" * 80)
    print("测试1: get_and_save_futures_klines - 获取期货合约K线数据")
    print("=" * 80)
    
    # 测试1.1: 获取最近的数据（单次请求）
    print("\n测试1.1: 获取 BTCUSDT 期货最近30条1小时K线数据")
    try:
        output_dir = str(project_root / "tmp" / "data" / "test_futures")
        result = get_and_save_futures_klines(
            symbol="BTCUSDT",
            interval="1h",
            limit=24*365,
            output_dir=output_dir,
            save_json=True,
            save_csv=False
        )
        if result:
            print(f"✓ 成功获取 {len(result)} 条数据")
            print(f"  数据已保存到: {output_dir}")
        else:
            print("✗ 获取数据失败")
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试1.2: 获取指定时间范围的数据（自动分页）
    print("\n测试1.2: 获取 ETHUSDT 期货指定时间范围的日线数据（自动分页）")
    try:
        output_dir = str(project_root / "tmp" / "data" / "test_futures")
        result = get_and_save_futures_klines(
            symbol="ETHUSDT",
            interval="1d",
            start_time="2024-01-01 00:00:00",
            end_time="2024-01-31 23:59:59",
            limit=1000,  # 每次请求的limit，实际会分页获取所有数据
            output_dir=output_dir,
            save_json=True,
            save_csv=False
        )
        if result:
            print(f"✓ 成功获取 {len(result)} 条数据")
            print(f"  数据已保存到: {output_dir}")
        else:
            print("✗ 获取数据失败")
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试1.3: 使用 datetime 对象指定时间范围
    print("\n测试1.3: 使用 datetime 对象获取 SOLUSDT 期货数据")
    try:
        from datetime import datetime
        output_dir = str(project_root / "tmp" / "data" / "test_futures")
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 10)
        result = get_and_save_futures_klines(
            symbol="SOLUSDT",
            interval="3m",
            start_time=start,
            end_time=end,
            limit=1000,
            output_dir=output_dir,
            save_json=True,
            save_csv=False
        )
        if result:
            print(f"✓ 成功获取 {len(result)} 条数据")
            print(f"  数据已保存到: {output_dir}")
        else:
            print("✗ 获取数据失败")
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_get_and_save_klines_direct():
    """
    测试2: 测试 get_and_save_klines_direct 函数
    """
    print("\n" + "=" * 80)
    print("测试2: get_and_save_klines_direct - 直接HTTP请求获取现货K线数据")
    print("=" * 80)
    
    # 测试2.1: 获取最近的数据（单次请求）
    print("\n测试2.1: 获取 BTCUSDT 现货最近30条1小时K线数据")
    try:
        output_dir = str(project_root / "tmp" / "data" / "test_spot")
        result = get_and_save_klines_direct(
            symbol="BTCUSDT",
            interval="1h",
            limit=1000,
            output_dir=output_dir,
            save_json=True,
            save_csv=False
        )
        if result:
            print(f"✓ 成功获取 {len(result)} 条数据")
            print(f"  数据已保存到: {output_dir}")
        else:
            print("✗ 获取数据失败")
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试2.2: 获取指定时间范围的数据（自动分页）
    print("\n测试2.2: 获取 ETHUSDT 现货指定时间范围的3分钟K线数据（自动分页）")
    try:
        output_dir = str(project_root / "tmp" / "data" / "test_spot")
        result = get_and_save_klines_direct(
            symbol="ETHUSDT",
            interval="3m",
            start_time="2024-12-01 00:00:00",
            end_time="2024-12-07 23:59:59",
            limit=1000,  # 每次请求的limit，实际会分页获取所有数据
            output_dir=output_dir,
            save_json=True,
            save_csv=False
        )
        if result:
            print(f"✓ 成功获取 {len(result)} 条数据")
            print(f"  数据已保存到: {output_dir}")
        else:
            print("✗ 获取数据失败")
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试2.3: 使用字符串日期格式（简化格式）
    print("\n测试2.3: 使用简化日期格式获取 SOLUSDT 现货数据")
    try:
        output_dir = str(project_root / "tmp" / "data" / "test_spot")
        result = get_and_save_klines_direct(
            symbol="SOLUSDT",
            interval="1d",
            start_time="2024-01-01",
            end_time="2024-01-31",
            limit=1000,
            output_dir=output_dir,
            save_json=True,
            save_csv=False
        )
        if result:
            print(f"✓ 成功获取 {len(result)} 条数据")
            print(f"  数据已保存到: {output_dir}")
        else:
            print("✗ 获取数据失败")
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试2.4: 测试不同时间间隔
    print("\n测试2.4: 获取 XRPUSDT 现货不同时间间隔的数据")
    try:
        output_dir = str(project_root / "tmp" / "data" / "test_spot")
        intervals = ["1h", "4h", "1d"]
        for interval in intervals:
            print(f"  测试间隔: {interval}")
            result = get_and_save_klines_direct(
                symbol="XRPUSDT",
                interval=interval,
                limit=10,
                output_dir=output_dir,
                save_json=False,  # 不保存，只测试获取
                save_csv=False
            )
            if result:
                print(f"    ✓ 成功获取 {len(result)} 条数据")
            else:
                print(f"    ✗ 获取数据失败")
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_data_validation():
    """
    测试3: 验证获取的数据格式
    """
    print("\n" + "=" * 80)
    print("测试3: 验证获取的数据格式")
    print("=" * 80)
    
    try:
        output_dir = str(project_root / "tmp" / "data" / "test_validation")
        
        # 获取少量数据进行验证
        print("\n获取 BTCUSDT 期货数据用于验证...")
        result = get_and_save_futures_klines(
            symbol="BTCUSDT",
            interval="1h",
            limit=5,
            output_dir=output_dir,
            save_json=True,
            save_csv=False
        )
        
        if result and len(result) > 0:
            print(f"✓ 获取到 {len(result)} 条数据")
            
            # 验证数据格式
            first_kline = result[0]
            print(f"\n数据格式验证:")
            print(f"  数据类型: {type(first_kline)}")
            print(f"  数据长度: {len(first_kline)}")
            print(f"  第一条数据示例: {first_kline[:6]}...")  # 显示前6个字段
            
            # 验证必需字段
            required_fields = [0, 1, 2, 3, 4, 5, 6]  # 时间、价格、成交量等
            all_present = all(i < len(first_kline) for i in required_fields)
            if all_present:
                print(f"  ✓ 必需字段完整")
            else:
                print(f"  ✗ 必需字段缺失")
            
            # 验证保存的JSON文件
            json_files = list(Path(output_dir).glob("*.json"))
            if json_files:
                import json
                latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
                print(f"\n验证保存的JSON文件: {latest_file.name}")
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'symbol' in data and 'data' in data:
                        print(f"  ✓ JSON文件格式正确")
                        print(f"  交易对: {data['symbol']}")
                        print(f"  数据条数: {data.get('data_count', len(data.get('data', [])))}")
                    else:
                        print(f"  ✗ JSON文件格式不正确")
        else:
            print("✗ 未获取到数据，无法验证")
            
    except Exception as e:
        print(f"✗ 验证失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """
    主函数：运行所有测试
    """
    print("=" * 80)
    print("cyqnt_trd 数据获取函数测试脚本")
    print("=" * 80)
    print("\n注意：")
    print("  1. 确保已安装 cyqnt_trd package: pip install -e /path/to/crypto_trading")
    print("  2. 测试数据将保存到 tmp/data/ 目录")
    print("  3. 部分测试需要网络连接访问 Binance API")
    print()
    
    # 运行测试
    try:
        # 测试1: get_and_save_futures_klines
        test_get_and_save_futures_klines()
        
        # 测试2: get_and_save_klines_direct
        test_get_and_save_klines_direct()
        
        # 测试3: 数据验证
        test_data_validation()
        
        print("\n" + "=" * 80)
        print("所有测试完成！")
        print("=" * 80)
        print("\n提示：")
        print("  - 可以查看 tmp/data/ 目录下的测试数据文件")
        print("  - JSON文件包含完整的元数据和格式化后的K线数据")
        print("  - 可以通过修改测试函数中的参数来测试不同的场景")
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
