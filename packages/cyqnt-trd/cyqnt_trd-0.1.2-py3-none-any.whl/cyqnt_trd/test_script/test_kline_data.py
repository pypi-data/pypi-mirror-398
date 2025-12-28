"""
K线数据查询测试脚本

测试查询 Binance 现货和期货合约的K线数据

使用方法：
    # 方式1: 作为模块运行（推荐）
    cd /Users/user/Desktop/repo/cyqnt_trd
    python -m cyqnt_trd.test_script.test_kline_data
    
    # 方式2: 直接运行脚本
    cd /Users/user/Desktop/repo/cyqnt_trd
    python cyqnt_trd/test_script/test_kline_data.py
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional, Union

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入 Binance SDK
try:
    from binance_sdk_spot.spot import Spot, ConfigurationRestAPI, SPOT_REST_API_PROD_URL
    from binance_sdk_spot.rest_api.models import KlinesIntervalEnum
    from binance_sdk_derivatives_trading_usds_futures.derivatives_trading_usds_futures import (
        DerivativesTradingUsdsFutures,
        ConfigurationRestAPI as FuturesConfigurationRestAPI,
        DERIVATIVES_TRADING_USDS_FUTURES_REST_API_PROD_URL,
    )
    from binance_sdk_derivatives_trading_usds_futures.rest_api.models import (
        KlineCandlestickDataIntervalEnum,
    )
except ImportError as e:
    print(f"导入错误: {e}")
    print("\n提示：请确保已安装 binance-connector-python")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def _convert_to_timestamp_ms(time_input: Union[datetime, str, int, None]) -> Optional[int]:
    """
    将各种时间格式转换为毫秒时间戳
    
    Args:
        time_input: 时间输入，可以是：
                   - datetime 对象
                   - 字符串格式的时间，例如 '2023-01-01 00:00:00' 或 '2023-01-01'
                   - 整数时间戳（秒或毫秒，自动判断）
                   - None
    
    Returns:
        毫秒时间戳，如果输入为 None 则返回 None
    """
    if time_input is None:
        return None
    
    if isinstance(time_input, datetime):
        return int(time_input.timestamp() * 1000)
    
    if isinstance(time_input, str):
        try:
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d', '%Y/%m/%d %H:%M:%S', '%Y/%m/%d']:
                try:
                    dt = datetime.strptime(time_input, fmt)
                    return int(dt.timestamp() * 1000)
                except ValueError:
                    continue
            raise ValueError(f"无法解析时间字符串: {time_input}")
        except Exception as e:
            logging.error(f"时间字符串解析失败: {e}")
            raise
    
    if isinstance(time_input, int):
        if time_input > 1e10:
            return time_input
        else:
            return time_input * 1000
    
    raise TypeError(f"不支持的时间类型: {type(time_input)}")


def query_spot_klines(
    symbol: str,
    interval: str = "1h",
    limit: int = 100,
    start_time: Optional[Union[datetime, str, int]] = None,
    end_time: Optional[Union[datetime, str, int]] = None,
) -> Optional[list]:
    """
    查询现货K线数据
    
    Args:
        symbol: 交易对符号，例如 'BTCUSDT', 'ETHUSDT'
        interval: 时间间隔，例如 '1d', '1h', '1m'
                 可选值: 1s, 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
        limit: 返回的数据条数，默认100，最大1000
        start_time: 开始时间，可以是 datetime、字符串或时间戳
        end_time: 结束时间，可以是 datetime、字符串或时间戳
    
    Returns:
        返回查询到的K线数据列表，如果出错返回 None
    """
    try:
        # 创建现货客户端配置
        spot_config = ConfigurationRestAPI(
            api_key=os.getenv("API_KEY", ""),
            api_secret=os.getenv("API_SECRET", ""),
            base_path=os.getenv("BASE_PATH", SPOT_REST_API_PROD_URL),
        )
        
        # 初始化现货客户端
        spot_client = Spot(config_rest_api=spot_config)
        
        # 将字符串间隔转换为枚举值
        interval_map = {
            "1s": KlinesIntervalEnum.INTERVAL_1s,
            "1m": KlinesIntervalEnum.INTERVAL_1m,
            "3m": KlinesIntervalEnum.INTERVAL_3m,
            "5m": KlinesIntervalEnum.INTERVAL_5m,
            "15m": KlinesIntervalEnum.INTERVAL_15m,
            "30m": KlinesIntervalEnum.INTERVAL_30m,
            "1h": KlinesIntervalEnum.INTERVAL_1h,
            "2h": KlinesIntervalEnum.INTERVAL_2h,
            "4h": KlinesIntervalEnum.INTERVAL_4h,
            "6h": KlinesIntervalEnum.INTERVAL_6h,
            "8h": KlinesIntervalEnum.INTERVAL_8h,
            "12h": KlinesIntervalEnum.INTERVAL_12h,
            "1d": KlinesIntervalEnum.INTERVAL_1d,
            "3d": KlinesIntervalEnum.INTERVAL_3d,
            "1w": KlinesIntervalEnum.INTERVAL_1w,
            "1M": KlinesIntervalEnum.INTERVAL_1M,
        }
        
        if interval not in interval_map:
            logging.error(f"不支持的间隔: {interval}")
            return None
        
        interval_enum = interval_map[interval]
        
        # 转换时间参数为毫秒时间戳
        start_time_ms = _convert_to_timestamp_ms(start_time) if start_time is not None else None
        end_time_ms = _convert_to_timestamp_ms(end_time) if end_time is not None else None
        
        # 构建查询日志信息
        time_info = []
        if start_time_ms:
            start_str = datetime.fromtimestamp(start_time_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')
            time_info.append(f"开始时间: {start_str}")
        if end_time_ms:
            end_str = datetime.fromtimestamp(end_time_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')
            time_info.append(f"结束时间: {end_str}")
        time_info_str = ", ".join(time_info) if time_info else "最近数据"
        
        logging.info(f"正在查询现货 {symbol} 的K线数据，间隔: {interval}, 数量: {limit}, {time_info_str}")
        
        # 查询K线数据
        response = spot_client.rest_api.klines(
            symbol=symbol,
            interval=interval_enum,
            start_time=start_time_ms,
            end_time=end_time_ms,
            limit=limit
        )
        
        # 获取数据
        klines_data = response.data()
        
        if not klines_data:
            logging.warning("未获取到数据")
            return None
        
        logging.info(f"成功获取 {len(klines_data)} 条数据")
        return klines_data
        
    except Exception as e:
        logging.error(f"查询现货K线数据时出错: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return None


def query_futures_klines(
    symbol: str,
    interval: str = "1h",
    limit: int = 100,
    start_time: Optional[Union[datetime, str, int]] = None,
    end_time: Optional[Union[datetime, str, int]] = None,
) -> Optional[list]:
    """
    查询期货合约K线数据
    
    Args:
        symbol: 交易对符号，例如 'BTCUSDT', 'ETHUSDT'
        interval: 时间间隔，例如 '1d', '1h', '1m'
                 可选值: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
        limit: 返回的数据条数，默认100，最大1000
        start_time: 开始时间，可以是 datetime、字符串或时间戳
        end_time: 结束时间，可以是 datetime、字符串或时间戳
    
    Returns:
        返回查询到的K线数据列表，如果出错返回 None
    """
    try:
        # 创建合约客户端配置
        futures_config = FuturesConfigurationRestAPI(
            api_key=os.getenv("API_KEY", ""),
            api_secret=os.getenv("API_SECRET", ""),
            base_path=os.getenv(
                "BASE_PATH", DERIVATIVES_TRADING_USDS_FUTURES_REST_API_PROD_URL
            ),
        )
        
        # 初始化合约客户端
        futures_client = DerivativesTradingUsdsFutures(config_rest_api=futures_config)
        
        # 将字符串间隔转换为枚举值
        interval_map = {
            "1m": KlineCandlestickDataIntervalEnum.INTERVAL_1m,
            "3m": KlineCandlestickDataIntervalEnum.INTERVAL_3m,
            "5m": KlineCandlestickDataIntervalEnum.INTERVAL_5m,
            "15m": KlineCandlestickDataIntervalEnum.INTERVAL_15m,
            "30m": KlineCandlestickDataIntervalEnum.INTERVAL_30m,
            "1h": KlineCandlestickDataIntervalEnum.INTERVAL_1h,
            "2h": KlineCandlestickDataIntervalEnum.INTERVAL_2h,
            "4h": KlineCandlestickDataIntervalEnum.INTERVAL_4h,
            "6h": KlineCandlestickDataIntervalEnum.INTERVAL_6h,
            "8h": KlineCandlestickDataIntervalEnum.INTERVAL_8h,
            "12h": KlineCandlestickDataIntervalEnum.INTERVAL_12h,
            "1d": KlineCandlestickDataIntervalEnum.INTERVAL_1d,
            "3d": KlineCandlestickDataIntervalEnum.INTERVAL_3d,
            "1w": KlineCandlestickDataIntervalEnum.INTERVAL_1w,
            "1M": KlineCandlestickDataIntervalEnum.INTERVAL_1M,
        }
        
        if interval not in interval_map:
            logging.error(f"不支持的间隔: {interval}")
            return None
        
        interval_enum = interval_map[interval]
        
        # 转换时间参数为毫秒时间戳
        start_time_ms = _convert_to_timestamp_ms(start_time) if start_time is not None else None
        end_time_ms = _convert_to_timestamp_ms(end_time) if end_time is not None else None
        
        # 构建查询日志信息
        time_info = []
        if start_time_ms:
            start_str = datetime.fromtimestamp(start_time_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')
            time_info.append(f"开始时间: {start_str}")
        if end_time_ms:
            end_str = datetime.fromtimestamp(end_time_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')
            time_info.append(f"结束时间: {end_str}")
        time_info_str = ", ".join(time_info) if time_info else "最近数据"
        
        logging.info(f"正在查询期货 {symbol} 的K线数据，间隔: {interval}, 数量: {limit}, {time_info_str}")
        
        # 查询K线数据
        response = futures_client.rest_api.kline_candlestick_data(
            symbol=symbol,
            interval=interval_enum,
            start_time=start_time_ms,
            end_time=end_time_ms,
            limit=limit
        )
        
        # 获取数据
        klines_data = response.data()
        
        if not klines_data:
            logging.warning("未获取到数据")
            return None
        
        logging.info(f"成功获取 {len(klines_data)} 条数据")
        return klines_data
        
    except Exception as e:
        logging.error(f"查询期货K线数据时出错: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return None


def print_klines_summary(klines_data: list, symbol: str, market_type: str = "现货"):
    """
    打印K线数据摘要
    
    Args:
        klines_data: K线数据列表
        symbol: 交易对符号
        market_type: 市场类型（现货/期货）
    """
    if not klines_data:
        print("无数据可显示")
        return
    
    print(f"\n{'='*80}")
    print(f"{market_type} {symbol} K线数据摘要")
    print(f"{'='*80}")
    print(f"总数据条数: {len(klines_data)}")
    
    # 解析第一条和最后一条数据
    first_kline = klines_data[0]
    last_kline = klines_data[-1]
    
    # K线数据格式: [开盘时间, 开盘价, 最高价, 最低价, 收盘价, 成交量, 收盘时间, 成交额, 成交笔数, ...]
    first_open_time = int(first_kline[0]) if isinstance(first_kline[0], str) else first_kline[0]
    first_close_time = int(first_kline[6]) if isinstance(first_kline[6], str) else first_kline[6]
    last_open_time = int(last_kline[0]) if isinstance(last_kline[0], str) else last_kline[0]
    last_close_time = int(last_kline[6]) if isinstance(last_kline[6], str) else last_kline[6]
    
    print(f"时间范围: {datetime.fromtimestamp(first_open_time / 1000).strftime('%Y-%m-%d %H:%M:%S')} "
          f"至 {datetime.fromtimestamp(last_close_time / 1000).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 显示前3条和后3条数据
    print(f"\n前3条数据:")
    print(f"{'时间':<20} {'开盘':>12} {'最高':>12} {'最低':>12} {'收盘':>12} {'成交量':>15}")
    print(f"{'-'*80}")
    for kline in klines_data[:3]:
        open_time = int(kline[0]) if isinstance(kline[0], str) else kline[0]
        time_str = datetime.fromtimestamp(open_time / 1000).strftime('%Y-%m-%d %H:%M:%S')
        open_price = float(kline[1])
        high_price = float(kline[2])
        low_price = float(kline[3])
        close_price = float(kline[4])
        volume = float(kline[5])
        print(f"{time_str:<20} {open_price:>12.2f} {high_price:>12.2f} {low_price:>12.2f} "
              f"{close_price:>12.2f} {volume:>15.2f}")
    
    if len(klines_data) > 6:
        print(f"\n... (省略 {len(klines_data) - 6} 条数据) ...\n")
        print(f"后3条数据:")
        print(f"{'时间':<20} {'开盘':>12} {'最高':>12} {'最低':>12} {'收盘':>12} {'成交量':>15}")
        print(f"{'-'*80}")
        for kline in klines_data[-3:]:
            open_time = int(kline[0]) if isinstance(kline[0], str) else kline[0]
            time_str = datetime.fromtimestamp(open_time / 1000).strftime('%Y-%m-%d %H:%M:%S')
            open_price = float(kline[1])
            high_price = float(kline[2])
            low_price = float(kline[3])
            close_price = float(kline[4])
            volume = float(kline[5])
            print(f"{time_str:<20} {open_price:>12.2f} {high_price:>12.2f} {low_price:>12.2f} "
                  f"{close_price:>12.2f} {volume:>15.2f}")
    elif len(klines_data) > 3:
        print(f"\n后3条数据:")
        print(f"{'时间':<20} {'开盘':>12} {'最高':>12} {'最低':>12} {'收盘':>12} {'成交量':>15}")
        print(f"{'-'*80}")
        for kline in klines_data[3:]:
            open_time = int(kline[0]) if isinstance(kline[0], str) else kline[0]
            time_str = datetime.fromtimestamp(open_time / 1000).strftime('%Y-%m-%d %H:%M:%S')
            open_price = float(kline[1])
            high_price = float(kline[2])
            low_price = float(kline[3])
            close_price = float(kline[4])
            volume = float(kline[5])
            print(f"{time_str:<20} {open_price:>12.2f} {high_price:>12.2f} {low_price:>12.2f} "
                  f"{close_price:>12.2f} {volume:>15.2f}")
    
    print(f"{'='*80}\n")


def test_spot_klines():
    """测试查询现货K线数据"""
    print("\n" + "="*80)
    print("测试1: 查询现货K线数据")
    print("="*80)
    
    # 示例1: 查询最近的数据
    print("\n示例1: 查询 BTCUSDT 最近100条1小时K线数据")
    klines = query_spot_klines(
        symbol="BTCUSDT",
        interval="1h",
        limit=100
    )
    if klines:
        print_klines_summary(klines, "BTCUSDT", "现货")
    
    # 示例2: 查询指定时间范围的数据
    print("\n示例2: 查询 ETHUSDT 最近7天的日线数据")
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    klines = query_spot_klines(
        symbol="ETHUSDT",
        interval="1d",
        limit=10,
        start_time=start_time,
        end_time=end_time
    )
    if klines:
        print_klines_summary(klines, "ETHUSDT", "现货")
    
    # 示例3: 使用字符串格式的时间
    print("\n示例3: 查询 SOLUSDT 指定时间范围的4小时K线数据")
    klines = query_spot_klines(
        symbol="SOLUSDT",
        interval="4h",
        limit=50,
        start_time="2024-01-01 00:00:00",
        end_time="2024-01-10 23:59:59"
    )
    if klines:
        print_klines_summary(klines, "SOLUSDT", "现货")


def test_futures_klines():
    """测试查询期货K线数据"""
    print("\n" + "="*80)
    print("测试2: 查询期货合约K线数据")
    print("="*80)
    
    # 示例1: 查询最近的数据
    print("\n示例1: 查询 BTCUSDT 期货最近100条1小时K线数据")
    klines = query_futures_klines(
        symbol="BTCUSDT",
        interval="1h",
        limit=100
    )
    if klines:
        print_klines_summary(klines, "BTCUSDT", "期货")
    
    # 示例2: 查询指定时间范围的数据
    print("\n示例2: 查询 ETHUSDT 期货最近7天的日线数据")
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    klines = query_futures_klines(
        symbol="ETHUSDT",
        interval="1d",
        limit=10,
        start_time=start_time,
        end_time=end_time
    )
    if klines:
        print_klines_summary(klines, "ETHUSDT", "期货")
    
    # 示例3: 使用字符串格式的时间
    print("\n示例3: 查询 SOLUSDT 期货指定时间范围的4小时K线数据")
    klines = query_futures_klines(
        symbol="SOLUSDT",
        interval="4h",
        limit=50,
        start_time="2024-01-01 00:00:00",
        end_time="2024-01-10 23:59:59"
    )
    if klines:
        print_klines_summary(klines, "SOLUSDT", "期货")


def main():
    """主函数"""
    print("\n" + "="*80)
    print("Binance K线数据查询测试")
    print("="*80)
    
    # 测试现货K线数据查询
    test_spot_klines()
    
    # 测试期货K线数据查询
    test_futures_klines()
    
    print("\n" + "="*80)
    print("测试完成")
    print("="*80)


if __name__ == "__main__":
    main()

