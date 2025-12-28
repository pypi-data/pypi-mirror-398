# import logging
# from binance_common.configuration import ConfigurationRestAPI
# from binance_common.constants import ALGO_REST_API_PROD_URL
# from binance_common.errors import (
#     ClientError,
#     UnauthorizedError,
#     ForbiddenError,
#     TooManyRequestsError,
#     RequiredError,
#     RateLimitBanError,
#     ServerError,
#     NetworkError,
#     NotFoundError,
#     BadRequestError,
# )
# from binance_sdk_algo.algo import Algo

# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s'
# )

# # Configuration
# configuration = ConfigurationRestAPI(
#     api_key="yNCZdF58V32y7oL2EATCIUKlmn8wkQ8ywoQukGIR7w4nkXBLldUFgld68I2xN0fj",
#     api_secret="xktvKv6fcTxcgGeLrAmC3MMpX5qcDntzvBByVTPTyHEsNThg7rHoRW48qQhUpP0k",
#     base_path=ALGO_REST_API_PROD_URL
# )

# client = Algo(config_rest_api=configuration)

# try:
#     logging.info("Attempting to query historical algo orders...")
#     response = client.rest_api.query_historical_algo_orders_spot_algo()

#     data = response.data()
#     logging.info(f"query_historical_algo_orders_spot_algo() response: {data}")
# except UnauthorizedError as e:
#     logging.error("=" * 60)
#     logging.error("UNAUTHORIZED ERROR - Invalid API credentials")
#     logging.error("=" * 60)
#     logging.error(f"Error details: {e}")
#     logging.error("\nTroubleshooting steps:")
#     logging.error("1. Verify your API key is correct")
#     logging.error("2. Verify your API secret is correct")
#     logging.error("3. Check if the API key is enabled in your Binance account")
#     logging.error("4. Ensure the API key hasn't been deleted or revoked")
# except ForbiddenError as e:
#     logging.error("=" * 60)
#     logging.error("FORBIDDEN ERROR - API key permissions or IP restrictions")
#     logging.error("=" * 60)
#     logging.error(f"Error details: {e}")
#     logging.error("\nTroubleshooting steps:")
#     logging.error("1. Check if your API key has 'Enable Reading' permission")
#     logging.error("2. Check if your API key has 'Enable Spot & Margin Trading' permission (if needed)")
#     logging.error("3. Verify your IP address is whitelisted (if IP restrictions are enabled)")
#     logging.error("4. Go to Binance API Management and check:")
#     logging.error("   - API key permissions")
#     logging.error("   - IP access restrictions (if enabled, add your current IP)")
# except TooManyRequestsError as e:
#     logging.error("=" * 60)
#     logging.error("RATE LIMIT EXCEEDED")
#     logging.error("=" * 60)
#     logging.error(f"Error details: {e}")
#     logging.error("\nPlease wait before making another request")
# except RateLimitBanError as e:
#     logging.error("=" * 60)
#     logging.error("IP ADDRESS BANNED - Excessive rate limit violations")
#     logging.error("=" * 60)
#     logging.error(f"Error details: {e}")
#     logging.error("\nYour IP has been temporarily banned. Please wait before retrying.")
# except BadRequestError as e:
#     logging.error("=" * 60)
#     logging.error("BAD REQUEST - Invalid request parameters")
#     logging.error("=" * 60)
#     logging.error(f"Error details: {e}")
# except ServerError as e:
#     logging.error("=" * 60)
#     logging.error("SERVER ERROR - Binance server issue")
#     logging.error("=" * 60)
#     logging.error(f"Error details: {e}")
#     logging.error("\nThis is a server-side issue. Please try again later.")
# except NetworkError as e:
#     logging.error("=" * 60)
#     logging.error("NETWORK ERROR - Connection issue")
#     logging.error("=" * 60)
#     logging.error(f"Error details: {e}")
#     logging.error("\nCheck your internet connection and try again.")
# except Exception as e:
#     logging.error("=" * 60)
#     logging.error("UNEXPECTED ERROR")
#     logging.error("=" * 60)
#     logging.error(f"Error type: {type(e).__name__}")
#     logging.error(f"Error details: {e}")
#     logging.error(f"Full error: {str(e)}")
    
#     # Try to get more details if available
#     if hasattr(e, 'response'):
#         logging.error(f"Response: {e.response}")
#     if hasattr(e, 'status_code'):
#         logging.error(f"Status code: {e.status_code}")

from binance_common.configuration import ConfigurationRestAPI
from binance_common.constants import ALGO_REST_API_PROD_URL
from binance_sdk_algo.algo import Algo
import logging

logging.basicConfig(level=logging.INFO)
configuration = ConfigurationRestAPI(api_key="yNCZdF58V32y7oL2EATCIUKlmn8wkQ8ywoQukGIR7w4nkXBLldUFgld68I2xN0fj", api_secret="xktvKv6fcTxcgGeLrAmC3MMpX5qcDntzvBByVTPTyHEsNThg7rHoRW48qQhUpP0k", base_path=ALGO_REST_API_PROD_URL)

client = Algo(config_rest_api=configuration)

try:
    response = client.rest_api.query_historical_algo_orders_spot_algo()

    data = response.data()
    logging.info(f"query_historical_algo_orders_spot_algo() response: {data}")
except Exception as e:
    logging.error(f"query_historical_algo_orders_spot_algo() error: {e}")