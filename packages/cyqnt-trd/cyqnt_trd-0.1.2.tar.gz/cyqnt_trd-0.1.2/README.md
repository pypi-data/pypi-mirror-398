# cyqnt_trd

一个用于加密货币交易的工具包，包含数据获取、交易信号生成和回测功能。

## 功能特性

- **数据获取**: 从 Binance 获取期货和现货K线数据
- **交易信号**: 提供多种技术指标因子和信号策略
- **回测框架**: 支持因子测试和策略回测

## 安装

### 方式1: 作为可编辑包安装（推荐用于开发）

```bash
cd /path/to/cyqnt_trd
pip install -e .
```

### 方式2: 直接安装

```bash
cd /path/to/cyqnt_trd
pip install .
```

### 方式3: 从源码安装

```bash
cd /path/to/cyqnt_trd
python setup.py install
```

## 依赖

主要依赖包：
- pandas >= 1.5.0
- numpy >= 1.23.0
- matplotlib >= 3.5.0
- requests >= 2.28.0

Binance SDK 依赖（需要单独安装）：
- binance-sdk-spot
- binance-sdk-derivatives-trading-usds-futures
- binance-sdk-algo
- binance-common

安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

### 作为 Python Package 使用

安装后，可以直接导入使用：

```python
# 导入数据获取模块
from cyqnt_trd.get_data import get_and_save_futures_klines, get_and_save_klines

# 导入交易信号模块
from cyqnt_trd.trading_signal.factor import ma_factor, rsi_factor
from cyqnt_trd.trading_signal.signal import ma_signal, factor_based_signal

# 导入回测框架
from cyqnt_trd.backtesting import BacktestFramework, FactorTester, StrategyBacktester

# 使用示例
data = get_and_save_futures_klines("BTCUSDT", interval="1h", limit=100)
framework = BacktestFramework(data_path="data/BTCUSDT_1h.json")
result = framework.test_factor(ma_factor, short_window=5, long_window=20)
```

### 运行示例脚本

```bash
# 作为模块运行
python -m cyqnt_trd.trading_signal.example_usage

# 运行测试脚本
python -m cyqnt_trd.test_script.realtime_price_tracker
```

## 项目结构

```
cyqnt_trd/
├── cyqnt_trd/          # 主包目录
│   ├── __init__.py         # 包初始化文件
│   ├── get_data/           # 数据获取模块
│   │   ├── __init__.py
│   │   ├── get_futures_data.py
│   │   └── get_trending_data.py
│   ├── trading_signal/     # 交易信号模块
│   │   ├── __init__.py
│   │   ├── factor/         # 因子模块
│   │   ├── signal/         # 信号策略模块
│   │   └── selected_alpha/ # Alpha因子模块
│   ├── backtesting/        # 回测框架
│   │   ├── __init__.py
│   │   ├── framework.py
│   │   ├── factor_test.py
│   │   └── strategy_backtest.py
│   └── test_script/        # 测试脚本
├── pyproject.toml          # 包配置文件
├── requirements.txt        # 依赖列表
└── README.md              # 说明文档
```

## 许可证

MIT License

Copyright (c) 2025 Haowen Wang