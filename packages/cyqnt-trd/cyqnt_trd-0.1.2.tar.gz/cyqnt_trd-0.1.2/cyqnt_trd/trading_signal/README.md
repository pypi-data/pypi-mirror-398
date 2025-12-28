# 交易因子和信号策略模块

本模块提供了交易因子（factor）和交易信号策略（signal）的框架，支持在信号策略中使用因子。

## 目录结构

```
trading_signal/
├── factor/              # 交易因子模块
│   ├── __init__.py      # 因子模块导出
│   ├── ma_factor.py     # 移动平均线因子
│   └── rsi_factor.py    # RSI因子
├── signal/              # 交易信号策略模块
│   ├── __init__.py      # 信号模块导出
│   ├── ma_signal.py     # 基于移动平均线的信号策略
│   └── factor_based_signal.py  # 基于因子的信号策略（可在signal中使用factor）
└── example_usage.py     # 使用示例
```

## 因子（Factor）

因子用于预测价格方向，函数签名：
```python
factor_func(data: pd.DataFrame, index: int) -> float
```

- **返回值**：
  - 正数：看多
  - 负数：看空
  - 0：中性或数据不足

### 已实现的因子

1. **ma_factor**: 简单移动平均线因子
   ```python
   from cyqnt_trd.trading_signal.factor import ma_factor
   
   # 使用MA5因子
   factor_value = ma_factor(data, index, period=5)
   ```

2. **ma_cross_factor**: 移动平均线交叉因子
   ```python
   from cyqnt_trd.trading_signal.factor import ma_cross_factor
   
   # 使用短期5日、长期20日均线交叉因子
   factor_value = ma_cross_factor(data, index, short_period=5, long_period=20)
   ```

3. **rsi_factor**: RSI因子
   ```python
   from cyqnt_trd.trading_signal.factor import rsi_factor
   
   # 使用RSI因子
   factor_value = rsi_factor(data, index, period=14, oversold=30.0, overbought=70.0)
   ```

## 信号策略（Signal）

信号策略用于生成买卖信号，函数签名：
```python
signal_func(
    data: pd.DataFrame, 
    index: int, 
    position: float, 
    entry_price: float, 
    entry_index: int,
    take_profit: float,
    stop_loss: float,
    check_periods: int
) -> str
```

- **参数说明**：
  - `check_periods`: 检查未来多少个周期（**只能为1**，因为实际使用时无法看到今天之后的数据）
- **返回值**：
  - `'buy'`: 买入信号
  - `'sell'`: 卖出信号
  - `'hold'`: 持有（不操作）

### 已实现的信号策略

1. **ma_signal**: 基于移动平均线的交易信号
   ```python
   from cyqnt_trd.trading_signal.signal import ma_signal
   
   # 需要包装成符合框架要求的函数
   def ma_signal_wrapper(data, index, position, entry_price, entry_index, 
                        take_profit, stop_loss, check_periods):
       return ma_signal(data, index, position, entry_price, entry_index,
                       take_profit, stop_loss, check_periods, period=5)
   ```

2. **ma_cross_signal**: 基于移动平均线交叉的交易信号
   ```python
   from cyqnt_trd.trading_signal.signal import ma_cross_signal
   ```

3. **factor_based_signal**: 基于因子的交易信号（可在signal中使用factor）
   ```python
   from cyqnt_trd.trading_signal.signal import factor_based_signal
   from cyqnt_trd.trading_signal.factor import ma_factor
   
   # 使用factor中的ma_factor
   def factor_signal_wrapper(data, index, position, entry_price, entry_index,
                            take_profit, stop_loss, check_periods):
       factor_func = lambda d, i: ma_factor(d, i, period=5)
       return factor_based_signal(
           data, index, position, entry_price, entry_index,
           take_profit, stop_loss, check_periods,
           factor_func=factor_func
       )
   ```

4. **multi_factor_signal**: 多因子组合策略
   ```python
   from cyqnt_trd.trading_signal.signal import multi_factor_signal
   from cyqnt_trd.trading_signal.factor import ma_factor, rsi_factor
   
   # 组合多个因子
   def multi_factor_wrapper(data, index, position, entry_price, entry_index,
                           take_profit, stop_loss, check_periods):
       factor_funcs = [
           lambda d, i: ma_factor(d, i, period=5),
           lambda d, i: rsi_factor(d, i, period=14)
       ]
       weights = [0.6, 0.4]
       return multi_factor_signal(
           data, index, position, entry_price, entry_index,
           take_profit, stop_loss, check_periods,
           factor_funcs=factor_funcs,
           weights=weights
       )
   ```

## 使用示例

### 示例1: 使用因子进行因子测试

```python
from cyqnt_trd.backtesting import BacktestFramework
from cyqnt_trd.trading_signal.factor import ma_factor

# 加载数据
framework = BacktestFramework(data_path='path/to/data.json')

# 创建因子包装函数
def ma_factor_wrapper(data, index):
    return ma_factor(data, index, period=5)

# 测试因子
factor_results = framework.test_factor(
    factor_func=ma_factor_wrapper,
    forward_periods=2,
    min_periods=10,
    factor_name="MA5因子"
)

framework.print_factor_results(factor_results, save_dir='result')
```

### 示例2: 使用信号策略进行回测

```python
from cyqnt_trd.backtesting import BacktestFramework
from cyqnt_trd.trading_signal.signal import ma_signal

# 加载数据
framework = BacktestFramework(data_path='path/to/data.json')

# 创建信号包装函数
def ma_signal_wrapper(data, index, position, entry_price, entry_index,
                     take_profit, stop_loss, check_periods):
    return ma_signal(data, index, position, entry_price, entry_index,
                    take_profit, stop_loss, check_periods, period=5)

# 回测策略
backtest_results = framework.backtest_strategy(
    signal_func=ma_signal_wrapper,
    min_periods=10,
    position_size=0.2,
    initial_capital=10000.0,
    commission_rate=0.00001,
    take_profit=0.1,
    stop_loss=0.5,
    check_periods=1,  # 只能为1，因为实际使用时无法看到未来数据
    strategy_name="MA5策略"
)

framework.print_backtest_results(backtest_results)
framework.plot_backtest_results(backtest_results, save_dir='result')
```

### 示例3: 在信号策略中使用因子

```python
from cyqnt_trd.backtesting import BacktestFramework
from cyqnt_trd.trading_signal.signal import factor_based_signal
from cyqnt_trd.trading_signal.factor import ma_factor

# 加载数据
framework = BacktestFramework(data_path='path/to/data.json')

# 创建基于因子的信号函数
def factor_signal_wrapper(data, index, position, entry_price, entry_index,
                         take_profit, stop_loss, check_periods):
    factor_func = lambda d, i: ma_factor(d, i, period=5)
    return factor_based_signal(
        data, index, position, entry_price, entry_index,
        take_profit, stop_loss, check_periods,
        factor_func=factor_func
    )

# 回测策略
backtest_results = framework.backtest_strategy(
    signal_func=factor_signal_wrapper,
    min_periods=10,
    position_size=0.2,
    initial_capital=10000.0,
    commission_rate=0.00001,
    take_profit=0.1,
    stop_loss=0.5,
    check_periods=1,  # 只能为1，因为实际使用时无法看到未来数据
    strategy_name="基于MA因子的策略"
)

framework.print_backtest_results(backtest_results)
framework.plot_backtest_results(backtest_results, save_dir='result')
```

## 扩展指南

### 添加新因子

1. 在 `factor/` 目录下创建新的因子文件（如 `macd_factor.py`）
2. 实现因子函数，符合签名：`factor_func(data: pd.DataFrame, index: int) -> float`
3. 在 `factor/__init__.py` 中导入并导出新因子

### 添加新信号策略

1. 在 `signal/` 目录下创建新的信号文件（如 `macd_signal.py`）
2. 实现信号函数，符合签名：`signal_func(data, index, position, entry_price, entry_index, take_profit, stop_loss, check_periods) -> str`
3. 如果需要使用factor中的因子，可以从 `cyqnt_trd.trading_signal.factor` 导入
4. 在 `signal/__init__.py` 中导入并导出新信号

### 在信号中使用因子

信号策略可以直接导入并使用factor中的因子：

```python
# 在signal模块的文件中
from ..factor.ma_factor import ma_factor
from ..factor.rsi_factor import rsi_factor

def my_signal(data, index, position, entry_price, entry_index,
              take_profit, stop_loss, check_periods):
    # 使用factor中的因子
    ma_value = ma_factor(data, index, period=5)
    rsi_value = rsi_factor(data, index, period=14)
    
    # 基于因子值生成交易信号
    if ma_value > 0 and rsi_value > 0:
        return 'buy'
    elif ma_value < 0 and rsi_value < 0:
        return 'sell'
    else:
        return 'hold'
```

## 注意事项

1. 因子函数和信号函数都需要处理数据不足的情况（返回0或'hold'）
2. 信号函数需要检查止盈止损条件
3. 使用因子或信号时，通常需要创建包装函数来适配框架的参数要求
4. 多因子组合时，注意权重的归一化

