import os
from binance_sdk_derivatives_trading_usds_futures.derivatives_trading_usds_futures import (
    ConfigurationRestAPI,
    DERIVATIVES_TRADING_USDS_FUTURES_REST_API_PROD_URL,
)


def set_user(
    api_key: str = "",
    api_secret: str = "",
    base_path: str = DERIVATIVES_TRADING_USDS_FUTURES_REST_API_PROD_URL
) -> ConfigurationRestAPI:
    """
    设置 API 配置，将 API_KEY、API_SECRET 和 BASE_PATH 写入环境变量，并返回配置对象

    Args:
        api_key (str, optional): API Key. 默认值为内置测试Key。
        api_secret (str, optional): API Secret. 默认值为内置测试Secret。
        base_path (str, optional): API Base路径。默认生产环境。

    Returns:
        ConfigurationRestAPI: Binance REST API 配置对象
    """
    os.environ["API_KEY"] = api_key
    os.environ["API_SECRET"] = api_secret
    os.environ["BASE_PATH"] = base_path

    configuration_rest_api = ConfigurationRestAPI(
        api_key=os.getenv("API_KEY"),
        api_secret=os.getenv("API_SECRET"),
        base_path=os.getenv("BASE_PATH"),
    )
    return configuration_rest_api
