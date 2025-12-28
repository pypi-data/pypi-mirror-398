# Test Script 使用说明

## get_symbols_by_volume.py

获取 Binance 所有合约和现货交易对列表，并按24小时交易量排序。

### 功能

- 获取所有现货交易对列表，按24小时交易量降序排序
- 获取所有合约交易对列表，按24小时交易量降序排序
- 在控制台显示前50个交易量最大的交易对
- 将结果保存为 JSON 文件到 `tmp/` 目录

### 使用方法

```bash
# 方式1: 作为模块运行（推荐）
cd /Users/user/Desktop/repo/cyqnt_trd
python -m cyqnt_trd.test_script.get_symbols_by_volume

# 方式2: 直接运行脚本
cd /Users/user/Desktop/repo/cyqnt_trd
python cyqnt_trd/test_script/get_symbols_by_volume.py
```

### 输出

脚本会在控制台显示：
- 现货交易对列表（前50个，按交易量排序）
- 合约交易对列表（前50个，按交易量排序）

同时会将完整列表保存为 JSON 文件：
- `tmp/spot_symbols_by_volume_YYYYMMDD_HHMMSS.json` - 现货交易对列表
- `tmp/futures_symbols_by_volume_YYYYMMDD_HHMMSS.json` - 合约交易对列表

### JSON 文件格式

每个 JSON 文件包含一个数组，每个元素包含：
```json
{
  "symbol": "BTCUSDT",
  "volume": 1234567890.12,
  "volume_str": "1,234,567,890.12"
}
```

### 注意事项

- 脚本使用公开 API，不需要 API Key 和 Secret（可以设置为空字符串）
- 交易量数据基于24小时滚动窗口
- 交易量以 USDT 计价（quoteVolume）

---

## test_order.py

测试 Binance 下单接口，包含现货和合约的买卖功能。

### 功能

- **现货交易测试**：
  - 市价买入/卖出
  - 限价买入/卖出
  
- **合约交易测试**：
  - 市价买入/卖出
  - 限价买入/卖出

- **撤单功能**：
  - 撤销现货订单（单个/批量）
  - 撤销合约订单
  - 查询当前挂单

### 使用方法

```bash
# 方式1: 作为模块运行（推荐）
cd /Users/user/Desktop/repo/cyqnt_trd
python -m cyqnt_trd.test_script.test_order

# 方式2: 直接运行脚本
cd /Users/user/Desktop/repo/cyqnt_trd
python cyqnt_trd/test_script/test_order.py
```

### 函数说明

#### 现货交易函数

- `test_spot_buy_market(symbol, quantity)` - 现货市价买入
- `test_spot_sell_market(symbol, quantity)` - 现货市价卖出
- `test_spot_buy_limit(symbol, quantity, price)` - 现货限价买入
- `test_spot_sell_limit(symbol, quantity, price)` - 现货限价卖出

#### 合约交易函数

- `test_futures_buy_market(symbol, quantity)` - 合约市价买入
- `test_futures_sell_market(symbol, quantity)` - 合约市价卖出
- `test_futures_buy_limit(symbol, quantity, price)` - 合约限价买入
- `test_futures_sell_limit(symbol, quantity, price)` - 合约限价卖出

#### 撤单函数

- `cancel_spot_order(symbol, order_id, orig_client_order_id)` - 撤销现货订单
- `cancel_futures_order(symbol, order_id, orig_client_order_id)` - 撤销合约订单
- `cancel_all_spot_orders(symbol)` - 撤销现货某个交易对的所有挂单
- `get_spot_open_orders(symbol)` - 获取现货当前挂单
- `get_futures_open_orders(symbol)` - 获取合约当前挂单
- `show_spot_open_orders(symbol)` - 显示现货当前挂单（格式化输出）
- `show_futures_open_orders(symbol)` - 显示合约当前挂单（格式化输出）

#### 通用函数

- `test_spot_order(symbol, side, order_type, quantity, price, time_in_force)` - 现货下单通用函数
- `test_futures_order(symbol, side, order_type, quantity, price, time_in_force, position_side, reduce_only)` - 合约下单通用函数

### 参数说明

- `symbol`: 交易对，如 "BTCUSDT"
- `side`: 买卖方向，"BUY" 或 "SELL"
- `order_type`: 订单类型，"MARKET" 或 "LIMIT"
- `quantity`: 数量（必需）
- `price`: 价格（LIMIT 订单必需）
- `time_in_force`: 有效期，"GTC", "IOC", "FOK"（默认 "GTC"）
- `position_side`: 持仓方向（仅合约），"LONG", "SHORT", "BOTH"
- `reduce_only`: 是否只减仓（仅合约），"true" 或 "false"

### 使用示例

```python
from cyqnt_trd.test_script.test_order import (
    test_spot_buy_market,
    test_spot_sell_market,
    test_futures_buy_market,
    test_futures_sell_market
)

# 现货市价买入 0.001 BTC
result = test_spot_buy_market("BTCUSDT", 0.001)

# 现货市价卖出 0.001 BTC
result = test_spot_sell_market("BTCUSDT", 0.001)

# 合约市价买入 0.001 BTC
result = test_futures_buy_market("BTCUSDT", 0.001)

# 合约市价卖出 0.001 BTC
result = test_futures_sell_market("BTCUSDT", 0.001)

# 查看当前挂单
from cyqnt_trd.test_script.test_order import (
    show_spot_open_orders,
    show_futures_open_orders
)

show_spot_open_orders("BTCUSDT")  # 查看现货 BTCUSDT 的挂单
show_futures_open_orders()  # 查看合约所有交易对的挂单

# 撤销订单
from cyqnt_trd.test_script.test_order import (
    cancel_spot_order,
    cancel_futures_order,
    cancel_all_spot_orders
)

# 通过订单ID撤销现货订单
cancel_spot_order("BTCUSDT", order_id=12345678)

# 通过客户端订单ID撤销合约订单
cancel_futures_order("BTCUSDT", orig_client_order_id="my_order_123")

# 撤销现货某个交易对的所有挂单
cancel_all_spot_orders("BTCUSDT")
```

### 环境变量

脚本支持通过环境变量配置 API 密钥：

```bash
export API_KEY="your_api_key"
export API_SECRET="your_api_secret"
export BASE_PATH="https://api.binance.com"  # 可选，默认使用生产环境
```

### 注意事项

⚠️ **重要警告**：

1. **实际下单风险**：此脚本会进行真实交易，请谨慎使用！
2. **测试环境**：建议先在测试网络或使用小额资金测试
3. **API 密钥安全**：不要将 API 密钥提交到版本控制系统
4. **默认参数**：脚本中的测试函数默认已注释，避免意外下单
5. **余额检查**：下单前请确保账户有足够的余额
6. **交易对验证**：确保交易对符号正确且可交易
7. **价格精度**：注意交易对的价格和数量精度要求

### 返回格式

函数返回字典，包含：

```python
{
    "success": True,  # 是否成功
    "rate_limits": {...},  # API 限流信息
    "order": {...}  # 订单详情
}
```

如果失败：

```python
{
    "success": False,
    "error": "错误信息",
    "traceback": "错误堆栈"
}
```

---

## realtime_price_tracker.py

实时价格跟踪脚本，通过 WebSocket 实时跟踪当前价格数据，并向前追溯 n 个周期，为实时计算 signal 和计算 strategy 做准备。

### 功能

- **实时价格跟踪**：通过 WebSocket 实时接收 K 线数据
- **历史数据加载**：自动加载历史 n 个周期的数据
- **数据管理**：维护一个包含历史数据的 DataFrame，格式与回测框架兼容
- **回调机制**：支持注册回调函数，在新 K 线到达或数据更新时触发
- **自动数据更新**：当新的 K 线关闭时，自动更新 DataFrame

### 使用方法

```bash
# 方式1: 作为模块运行（推荐）
cd /Users/user/Desktop/repo/cyqnt_trd
python -m cyqnt_trd.test_script.realtime_price_tracker

# 方式2: 直接运行脚本
cd /Users/user/Desktop/repo/cyqnt_trd
python cyqnt_trd/test_script/realtime_price_tracker.py
```

### 基本用法

```python
import asyncio
from cyqnt_trd.test_script.realtime_price_tracker import RealtimePriceTracker

async def main():
    # 创建跟踪器
    tracker = RealtimePriceTracker(
        symbol="BTCUSDT",
        interval="1m",  # 1分钟K线
        lookback_periods=100  # 向前追溯100个周期
    )
    
    # 注册回调函数
    def on_new_kline(kline_dict, data_df):
        print(f"新 K 线: {kline_dict['open_time_str']}, 价格: {kline_dict['close_price']}")
        print(f"当前数据量: {len(data_df)} 条")
    
    tracker.register_on_new_kline(on_new_kline)
    
    # 运行跟踪器
    await tracker.run_forever()

asyncio.run(main())
```

### 高级用法：结合 Signal 和 Strategy 计算

```python
import asyncio
from cyqnt_trd.test_script.realtime_price_tracker import RealtimePriceTracker
from cyqnt_trd.trading_signal.signal.ma_signal import ma_signal

async def main():
    tracker = RealtimePriceTracker(
        symbol="BTCUSDT",
        interval="1m",
        lookback_periods=100
    )
    
    def calculate_signal(kline_dict, data_df):
        """在新 K 线到达时计算交易信号"""
        if len(data_df) < 10:  # 确保有足够的数据
            return
        
        # 使用最后一行作为当前数据点
        current_slice = data_df.iloc[-10:]  # 使用最近10条数据
        
        # 计算信号（假设没有持仓）
        signal = ma_signal(
            data_slice=current_slice,
            position=0.0,  # 当前持仓
            entry_price=0.0,  # 入场价格
            entry_index=-1,  # 入场索引
            take_profit=0.1,  # 止盈10%
            stop_loss=0.05,  # 止损5%
            period=5  # MA周期
        )
        
        print(f"时间: {kline_dict['open_time_str']}, 价格: {kline_dict['close_price']}, 信号: {signal}")
    
    tracker.register_on_new_kline(calculate_signal)
    await tracker.run_forever()

asyncio.run(main())
```

### API 说明

#### RealtimePriceTracker 类

**初始化参数：**

- `symbol` (str): 交易对符号，例如 'BTCUSDT', 'ETHUSDT'
- `interval` (str): 时间间隔，例如 '1m', '5m', '1h', '1d'
  - 可选值: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
- `lookback_periods` (int): 向前追溯的周期数（默认100）
- `market_type` (str): 市场类型，'futures' 或 'spot'（默认 'futures'，目前只支持期货）

**主要方法：**

- `load_historical_data()`: 加载历史数据（异步）
- `start()`: 启动实时跟踪（异步）
- `stop()`: 停止实时跟踪（异步）
- `run_forever()`: 运行实时跟踪直到中断（异步）
- `get_data()`: 获取当前的数据 DataFrame
- `get_latest_price()`: 获取最新价格
- `register_on_new_kline(callback)`: 注册新 K 线回调函数
- `register_on_data_updated(callback)`: 注册数据更新回调函数

**回调函数签名：**

- `on_new_kline(kline_dict: Dict[str, Any], data_df: pd.DataFrame) -> None`
  - 当新的 K 线关闭时调用
  - `kline_dict`: 新 K 线的字典数据
  - `data_df`: 更新后的完整数据 DataFrame

- `on_data_updated(data_df: pd.DataFrame) -> None`
  - 当数据更新时调用
  - `data_df`: 更新后的完整数据 DataFrame

### 数据格式

跟踪器维护的 DataFrame 包含以下列：

- `datetime`: 时间（pandas Timestamp）
- `open_time`: 开盘时间（毫秒时间戳）
- `open_time_str`: 开盘时间（字符串格式）
- `open_price`: 开盘价
- `high_price`: 最高价
- `low_price`: 最低价
- `close_price`: 收盘价
- `volume`: 成交量
- `close_time`: 收盘时间（毫秒时间戳）
- `close_time_str`: 收盘时间（字符串格式）
- `quote_volume`: 成交额
- `trades`: 成交笔数
- `taker_buy_base_volume`: 主动买入成交量
- `taker_buy_quote_volume`: 主动买入成交额
- `ignore`: 忽略字段

该格式与回测框架兼容，可以直接用于 signal 和 strategy 计算。

### 注意事项

1. **数据量限制**：`lookback_periods` 参数控制维护的历史数据量，数据会自动滚动更新
2. **K 线关闭**：只有关闭的 K 线（`is_closed = True`）才会添加到 DataFrame，未关闭的 K 线只更新 `latest_kline`
3. **异步操作**：所有网络操作都是异步的，需要使用 `asyncio` 运行
4. **错误处理**：脚本包含错误处理和日志记录，便于调试
5. **API 密钥**：WebSocket streams 不需要 API 密钥，但 REST API 可能需要（用于加载历史数据）
6. **SSL 证书验证**：如果遇到 SSL 证书验证错误（如 `CERTIFICATE_VERIFY_FAILED`），可以在初始化时设置 `ssl_verify=False`（仅用于开发/测试环境）

### 处理 SSL 证书验证错误

如果遇到 SSL 证书验证错误，可以按以下方式处理：

```python
# 方式1: 在初始化时禁用 SSL 验证（仅用于开发/测试）
tracker = RealtimePriceTracker(
    symbol="BTCUSDT",
    interval="1m",
    lookback_periods=100,
    ssl_verify=False  # 禁用 SSL 证书验证
)

# 方式2: 修复系统 SSL 证书（推荐用于生产环境）
# macOS: 运行以下命令安装证书
# /Applications/Python\ 3.x/Install\ Certificates.command
# 或者手动安装证书到系统
```

**警告**：禁用 SSL 验证会降低安全性，仅应在开发/测试环境中使用。生产环境应修复 SSL 证书问题。

### 环境变量

脚本支持通过环境变量配置：

```bash
export API_KEY="your_api_key"  # 可选，用于 REST API
export API_SECRET="your_api_secret"  # 可选，用于 REST API
export BASE_PATH="https://fapi.binance.com"  # 可选，默认使用生产环境
export STREAM_URL="wss://fstream.binance.com"  # 可选，默认使用生产环境
```


