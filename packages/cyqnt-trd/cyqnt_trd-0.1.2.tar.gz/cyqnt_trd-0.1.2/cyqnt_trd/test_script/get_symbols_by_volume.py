import os
import logging
from typing import List, Dict

from binance_sdk_spot.spot import Spot, ConfigurationRestAPI, SPOT_REST_API_PROD_URL
from binance_sdk_derivatives_trading_usds_futures.derivatives_trading_usds_futures import (
    DerivativesTradingUsdsFutures,
    ConfigurationRestAPI as FuturesConfigurationRestAPI,
    DERIVATIVES_TRADING_USDS_FUTURES_REST_API_PROD_URL,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def get_spot_symbols_by_volume() -> List[Dict]:
    """
    获取所有现货交易对列表，并按24小时交易量排序
    
    Returns:
        按交易量降序排列的交易对列表，每个元素包含 symbol 和 volume
    """
    try:
        # 创建现货客户端配置
        spot_config = ConfigurationRestAPI(
            api_key=os.getenv("API_KEY", "yNCZdF58V32y7oL2EATCIUKlmn8wkQ8ywoQukGIR7w4nkXBLldUFgld68I2xN0fj"),
            api_secret=os.getenv("API_SECRET", "xktvKv6fcTxcgGeLrAmC3MMpX5qcDntzvBByVTPTyHEsNThg7rHoRW48qQhUpP0k"),
            base_path=os.getenv("BASE_PATH", SPOT_REST_API_PROD_URL),
        )
        
        # 初始化现货客户端
        spot_client = Spot(config_rest_api=spot_config)
        
        # 获取所有交易对的24小时交易量统计
        logging.info("正在获取现货交易对24小时交易量数据...")
        ticker_response = spot_client.rest_api.ticker24hr()
        ticker_data = ticker_response.data()
        
        # 处理响应数据：可能是列表或单个对象，可能是 Pydantic 模型或字典
        if not isinstance(ticker_data, list):
            ticker_data = [ticker_data]
        
        # 提取交易对和交易量信息
        symbols_with_volume = []
        for ticker in ticker_data:
            # 如果是 Pydantic 模型，转换为字典
            if hasattr(ticker, 'model_dump'):
                ticker_dict = ticker.model_dump(by_alias=True)
            elif hasattr(ticker, 'dict'):
                ticker_dict = ticker.dict(by_alias=True)
            elif isinstance(ticker, dict):
                ticker_dict = ticker
            else:
                # 尝试直接访问属性
                ticker_dict = {
                    'symbol': getattr(ticker, 'symbol', getattr(ticker, 'Symbol', '')),
                    'quoteVolume': getattr(ticker, 'quote_volume', getattr(ticker, 'quoteVolume', '0'))
                }
            
            symbol = ticker_dict.get('symbol', '')
            # 使用 quoteVolume (以报价货币计的交易量) 作为排序依据
            quote_volume = ticker_dict.get('quoteVolume', ticker_dict.get('quote_volume', '0'))
            volume = float(quote_volume) if quote_volume else 0.0
            symbols_with_volume.append({
                'symbol': symbol,
                'volume': volume,
                'volume_str': f"{volume:,.2f}"
            })
        
        # 按交易量降序排序
        symbols_with_volume.sort(key=lambda x: x['volume'], reverse=True)
        
        logging.info(f"成功获取 {len(symbols_with_volume)} 个现货交易对")
        return symbols_with_volume
        
    except Exception as e:
        logging.error(f"获取现货交易对列表时出错: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return []


def get_futures_symbols_by_volume() -> List[Dict]:
    """
    获取所有合约交易对列表，并按24小时交易量排序
    
    Returns:
        按交易量降序排列的交易对列表，每个元素包含 symbol 和 volume
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
        
        # 获取所有交易对的24小时交易量统计
        logging.info("正在获取合约交易对24小时交易量数据...")
        ticker_response = futures_client.rest_api.ticker24hr_price_change_statistics()
        ticker_data = ticker_response.data()
        
        # 处理响应数据：可能是列表或单个对象，可能是 Pydantic 模型或字典
        if not isinstance(ticker_data, list):
            ticker_data = [ticker_data]
        
        # 提取交易对和交易量信息
        symbols_with_volume = []
        for ticker in ticker_data:
            # 如果是 Pydantic 模型，转换为字典
            if hasattr(ticker, 'model_dump'):
                ticker_dict = ticker.model_dump(by_alias=True)
            elif hasattr(ticker, 'dict'):
                ticker_dict = ticker.dict(by_alias=True)
            elif isinstance(ticker, dict):
                ticker_dict = ticker
            else:
                # 尝试直接访问属性
                ticker_dict = {
                    'symbol': getattr(ticker, 'symbol', getattr(ticker, 'Symbol', '')),
                    'quoteVolume': getattr(ticker, 'quote_volume', getattr(ticker, 'quoteVolume', '0'))
                }
            
            symbol = ticker_dict.get('symbol', '')
            # 使用 quoteVolume (以报价货币计的交易量) 作为排序依据
            quote_volume = ticker_dict.get('quoteVolume', ticker_dict.get('quote_volume', '0'))
            volume = float(quote_volume) if quote_volume else 0.0
            symbols_with_volume.append({
                'symbol': symbol,
                'volume': volume,
                'volume_str': f"{volume:,.2f}"
            })
        
        # 按交易量降序排序
        symbols_with_volume.sort(key=lambda x: x['volume'], reverse=True)
        
        logging.info(f"成功获取 {len(symbols_with_volume)} 个合约交易对")
        return symbols_with_volume
        
    except Exception as e:
        logging.error(f"获取合约交易对列表时出错: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return []


def print_symbols_list(symbols: List[Dict], title: str, top_n: int = 20):
    """
    打印交易对列表
    
    Args:
        symbols: 交易对列表
        title: 标题
        top_n: 显示前N个
    """
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")
    print(f"总共 {len(symbols)} 个交易对，显示前 {min(top_n, len(symbols))} 个：")
    print(f"{'排名':<6} {'交易对':<20} {'24h交易量 (USDT)':>25}")
    print(f"{'-'*80}")
    
    for idx, item in enumerate(symbols[:top_n], 1):
        print(f"{idx:<6} {item['symbol']:<20} {item['volume_str']:>25}")
    
    if len(symbols) > top_n:
        print(f"\n... 还有 {len(symbols) - top_n} 个交易对未显示")


def main():
    """主函数"""
    print("\n" + "="*80)
    print("获取 Binance 交易对列表并按交易量排序")
    print("="*80)
    
    # 获取现货交易对列表
    spot_symbols = get_spot_symbols_by_volume()
    if spot_symbols:
        print_symbols_list(spot_symbols, "现货交易对列表（按24小时交易量排序）", top_n=50)
    
    # 获取合约交易对列表
    futures_symbols = get_futures_symbols_by_volume()
    if futures_symbols:
        print_symbols_list(futures_symbols, "合约交易对列表（按24小时交易量排序）", top_n=50)
    
    # 返回结果供其他脚本使用
    return {
        'spot': spot_symbols,
        'futures': futures_symbols
    }


if __name__ == "__main__":
    result = main()
    
    # 可选：保存到文件
    import json
    from datetime import datetime
    
    output_dir = "/Users/user/Desktop/repo/cyqnt_trd/tmp"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 保存现货列表
    if result['spot']:
        spot_file = os.path.join(output_dir, f"spot_symbols_by_volume_{timestamp}.json")
        with open(spot_file, 'w', encoding='utf-8') as f:
            json.dump(result['spot'], f, indent=2, ensure_ascii=False)
        print(f"\n现货交易对列表已保存到: {spot_file}")
    
    # 保存合约列表
    if result['futures']:
        futures_file = os.path.join(output_dir, f"futures_symbols_by_volume_{timestamp}.json")
        with open(futures_file, 'w', encoding='utf-8') as f:
            json.dump(result['futures'], f, indent=2, ensure_ascii=False)
        print(f"合约交易对列表已保存到: {futures_file}")

