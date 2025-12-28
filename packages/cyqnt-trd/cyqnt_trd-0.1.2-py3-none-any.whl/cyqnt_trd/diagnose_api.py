import os
import logging
from binance_common.configuration import ConfigurationRestAPI
from binance_common.constants import ALGO_REST_API_PROD_URL
from binance_sdk_algo.algo import Algo

logging.basicConfig(level=logging.INFO)

# API credentials - can be set via environment variables or use defaults below
API_KEY = os.getenv("API_KEY", "yNCZdF58V32y7oL2EATCIUKlmn8wkQ8ywoQukGIR7w4nkXBLldUFgld68I2xN0fj")
API_SECRET = os.getenv("API_SECRET", "xktvKv6fcTxcgGeLrAmC3MMpX5qcDntzvBByVTPTyHEsNThg7rHoRW48qQhUpP0k")

# Create configuration for the REST API
configuration_rest_api = ConfigurationRestAPI(
    api_key=API_KEY,
    api_secret=API_SECRET,
    base_path=os.getenv("BASE_PATH", ALGO_REST_API_PROD_URL),
)

client = Algo(config_rest_api=configuration_rest_api)

try:
    response = client.rest_api.query_historical_algo_orders_spot_algo()

    data = response.data()
    logging.info(f"query_historical_algo_orders_spot_algo() response: {data}")
except Exception as e:
    logging.error(f"query_historical_algo_orders_spot_algo() error: {e}")