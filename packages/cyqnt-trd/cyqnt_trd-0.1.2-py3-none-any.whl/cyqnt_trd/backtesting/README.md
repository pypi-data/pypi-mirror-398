# 回测框架使用说明

本回测框架提供了两个主要功能：
1. **单因子胜率测试** - 测试某个因子在预测未来价格方向上的胜率
2. **策略回测** - 根据买卖信号进行回测，计算收益率和收益曲线

## 功能概述

### 1. 单因子胜率测试 (FactorTester)

用于测试某个因子在预测未来一段时间内价格方向（多/空）的胜率。

**主要功能：**
- 计算因子值（正数=看多，负数=看空，0=中性）
- 统计看多/看空信号的胜率
- 计算平均收益率
- 输出详细的测试结果

### 2. 策略回测 (StrategyBacktester)

根据买卖信号进行回测，计算收益率和收益曲线。

**主要功能：**
- 根据买卖信号模拟交易
- 计算总收益率、胜率、最大回撤、夏普比率等指标
- 绘制资金曲线、价格曲线和回撤曲线
- 记录所有交易详情

## 快速开始

### 基本使用

```python
import pandas as pd
import json
from cyqnt_trd.backtesting import BacktestFramework

# 加载数据
data_path = 'path/to/your/data.json'
framework = BacktestFramework(data_path=data_path)

# 定义因子函数
def my_factor(data: pd.DataFrame, index: int) -> float:
    """因子函数：返回因子值（正数=看多，负数=看空）"""
    current_price = data.iloc[index]['close_price']
    # 你的因子计算逻辑
    # ...
    return 1.0  # 或 -1.0, 0.0

# 测试因子
results = framework.test_factor(
    factor_func=my_factor,
    forward_periods=7,  # 未来7个周期
    min_periods=0,
    factor_name="我的因子"
)

# 打印结果
framework.print_factor_results(results)
```

### 策略回测

```python
# 定义信号函数
def my_signal(data: pd.DataFrame, index: int) -> str:
    """信号函数：返回 'buy', 'sell', 'hold' 或 None"""
    # 你的信号生成逻辑
    # ...
    return 'buy'  # 或 'sell', 'hold'

# 回测策略
results = framework.backtest_strategy(
    signal_func=my_signal,
    min_periods=0,
    position_size=0.5,  # 每次使用50%的资金
    initial_capital=10000.0,
    commission_rate=0.001  # 0.1%手续费
)

# 打印结果
framework.print_backtest_results(results)

# 绘制结果
framework.plot_backtest_results(results)
```

## 数据格式要求

数据可以是以下两种格式之一：

### 1. JSON文件格式

```json
{
  "symbol": "BTCUSDT",
  "interval": "1m",
  "data": [
    {
      "open_time": 1234567890000,
      "open_time_str": "2023-01-01 00:00:00",
      "open_price": 100.0,
      "high_price": 105.0,
      "low_price": 95.0,
      "close_price": 102.0,
      "volume": 1000.0,
      ...
    },
    ...
  ]
}
```

### 2. DataFrame格式

DataFrame必须包含以下列：
- `datetime` 或 `open_time_str` 或 `open_time`: 时间
- `close_price`: 收盘价
- 其他因子计算所需的列（如 `open_price`, `high_price`, `low_price`, `volume` 等）

## 详细示例

### 示例1: 移动平均线因子测试

```python
def ma_factor(data: pd.DataFrame, index: int) -> float:
    """MA5因子：价格高于MA5看多，低于MA5看空"""
    if index < 5:
        return 0
    
    current_price = data.iloc[index]['close_price']
    ma5 = data.iloc[index-5:index]['close_price'].mean()
    
    if current_price > ma5:
        return 1.0  # 看多
    else:
        return -1.0  # 看空

# 测试因子
framework = BacktestFramework(data_path='data.json')
results = framework.test_factor(
    factor_func=ma_factor,
    forward_periods=7,
    min_periods=5,
    factor_name="MA5因子"
)
framework.print_factor_results(results)
```

### 示例2: 移动平均线交叉策略

```python
def ma_cross_signal(data: pd.DataFrame, index: int) -> str:
    """MA交叉策略：价格上穿MA5买入，下穿MA5卖出"""
    if index < 5:
        return 'hold'
    
    current_price = data.iloc[index]['close_price']
    ma5 = data.iloc[index-5:index]['close_price'].mean()
    prev_price = data.iloc[index-1]['close_price']
    prev_ma5 = data.iloc[index-6:index-1]['close_price'].mean()
    
    # 上穿
    if prev_price <= prev_ma5 and current_price > ma5:
        return 'buy'
    # 下穿
    elif prev_price >= prev_ma5 and current_price < ma5:
        return 'sell'
    else:
        return 'hold'

# 回测策略
results = framework.backtest_strategy(
    signal_func=ma_cross_signal,
    min_periods=5,
    position_size=0.5,
    initial_capital=10000.0,
    commission_rate=0.001
)
framework.plot_backtest_results(results)
```

## API参考

### BacktestFramework

主回测框架类，提供统一的接口。

#### 方法

- `test_factor(factor_func, forward_periods=7, min_periods=0, factor_name="factor")` - 测试因子胜率
- `backtest_strategy(signal_func, min_periods=0, position_size=1.0, initial_capital=10000.0, commission_rate=0.001)` - 回测策略
- `plot_backtest_results(results, figsize=(14, 10))` - 绘制回测结果
- `print_factor_results(results)` - 打印因子测试结果
- `print_backtest_results(results)` - 打印回测结果

### FactorTester

单因子胜率测试器。

#### 方法

- `test_factor(factor_func, forward_periods=7, min_periods=0, factor_name="factor")` - 测试因子
- `print_results(results)` - 打印结果
- `save_results(results, filepath)` - 保存结果到JSON文件

### StrategyBacktester

策略回测器。

#### 方法

- `backtest(signal_func, min_periods=0, position_size=1.0)` - 执行回测
- `plot_results(results, figsize=(14, 10))` - 绘制结果
- `print_results(results)` - 打印结果
- `save_results(results, filepath)` - 保存结果到JSON文件

## 注意事项

1. **因子函数** (`factor_func`): 
   - 接受 `(data: pd.DataFrame, index: int)` 作为参数
   - 返回 `float`: 正数表示看多，负数表示看空，0表示中性

2. **信号函数** (`signal_func`):
   - 接受 `(data: pd.DataFrame, index: int)` 作为参数
   - 返回 `str`: `'buy'`（买入）、`'sell'`（卖出）、`'hold'`（持有）或 `None`

3. **数据要求**:
   - 数据必须按时间排序
   - 必须包含 `close_price` 列
   - 必须包含时间列（`datetime`, `open_time_str` 或 `open_time`）

4. **性能考虑**:
   - 对于大量数据，建议使用适当的数据切片
   - 因子和信号函数应该尽可能高效

## 输出结果说明

### 因子测试结果

- `total_samples`: 总样本数
- `long_signals`: 看多信号数量
- `short_signals`: 看空信号数量
- `long_win_rate`: 看多信号胜率
- `short_win_rate`: 看空信号胜率
- `overall_win_rate`: 总体胜率
- `long_avg_return`: 看多信号平均收益率
- `short_avg_return`: 看空信号平均收益率
- `details`: 详细结果列表

### 策略回测结果

- `initial_capital`: 初始资金
- `final_capital`: 最终资金
- `total_return`: 总收益率
- `total_trades`: 总交易次数
- `win_trades`: 盈利交易次数
- `loss_trades`: 亏损交易次数
- `win_rate`: 胜率
- `max_drawdown`: 最大回撤
- `sharpe_ratio`: 夏普比率
- `equity_curve`: 资金曲线（DataFrame）
- `trades`: 交易记录列表

