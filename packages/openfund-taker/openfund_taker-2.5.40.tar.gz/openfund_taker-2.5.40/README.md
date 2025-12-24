# OpenFund Taker

OpenFund Taker 是一个自动化的加密货币交易持仓管理系统，可以监控和管理多个交易所的持仓，并提供高级的止损和止盈策略。

## 功能特性

- 支持多交易所（Binance、OKX、Bitget）
- 多种交易策略：
  - **LiquidityGrabStrategy**：流动性抓取策略，结合订单块分析
  - **BestTopDownStrategy**：自顶向下多时间框架分析
  - **SMCSLAndTP**：基于智能资金概念的止损止盈
  - **TrailingSLAndTP**：移动止损止盈管理
  - **ThreeLineTrading**：三线交易策略
- 自动化持仓监控和管理
- 可配置的止损和止盈水平
- 多时间框架分析（HTF、ATF、ETF、LTF）
- 飞书 Webhook 通知
- 完善的日志记录，按日切割
- 支持单个交易对独立配置

## 环境要求

- Python 3.9+
- 依赖管理使用 Poetry

## 安装

### 使用 Poetry（推荐）

```bash
# 安装依赖
poetry install

# 激活虚拟环境
poetry shell
```

### 使用 pip

```bash
pip install openfund-taker
```

## 配置说明

在项目根目录创建 `taker_config.yaml` 文件。完整示例请参考 `taker_config.yaml`。

### 平台配置

配置交易所 API 凭证：

```yaml
platform:
  binance: 
    apiKey: "你的API密钥"
    secret: "你的密钥"
  okx:
    apiKey: "你的API密钥"
    secret: "你的密钥"
    password: "你的API密码"
  bitget: 
    apiKey: "你的API密钥"
    secret: "你的密钥"
    password: "你的API密码"
```

### 通用设置

```yaml
common:
  monitor_interval: 10  # 监控间隔（秒）
  actived_taker: "LiquidityGrabStrategyTaker"  # 激活的策略
  feishu_webhook: "https://open.feishu.cn/..."  # 通知 Webhook
  cache_ttl: 60  # 缓存时间（分钟）
  proxy: "http://localhost:7890"  # 可选代理
```

### 策略配置

#### 全局策略设置

```yaml
strategy:
  all_stop_loss_pct: 2  # 止损百分比
  all_TP_SL_ratio: 1.5  # 止盈止损比
  leverage: 1  # 杠杆倍数
  CHF: "15m"  # 当前时间框架
  HTF: "4h"   # 高时间框架
  LTF: "1m"   # 低时间框架
  ATF: "15m"  # 分析时间框架
  ETF: "1m"   # 入场时间框架
```

#### 流动性抓取策略

```yaml
liquidity_grab_strategy:
  htf: "4h"                         # 高时间框架
  atf: "15m"                        # 分析时间框架
  etf: "1m"                         # 入场时间框架
  open_body_break: false            # 是否使用实体突破
  min_profit_ratio: 1.5             # 最小盈亏比
  stop_loss_buffer_ticks: 2         # 止损缓冲点数
  liquidity_atr_offset: 0.1         # 流动性 ATR 偏移
  enable_liquidity_target_tp: true  # 启用流动性目标止盈
  enable_order_block_trailing: true # 启用订单块移动止损
  tp_structure_confirmation: true   # 止盈需要结构确认
  trailing_order_block_atr: 0.6     # 移动止损订单块 ATR 倍数
```

#### 移动止损策略

```yaml
trailing_strategy:
  open_trail_profit: false              # 是否开启追踪利润
  all_low_trail_profit_threshold: 0.5   # 第一档利润触发阈值
  all_first_trail_profit_threshold: 1   # 第二档利润触发阈值
  all_second_trail_profit_threshold: 3  # 第三档利润触发阈值
  all_low_trail_stop_loss_pct: 0.7      # 第一档最大回撤比例
  all_trail_stop_loss_pct: 0.6          # 第二档最大回撤比例
  all_higher_trail_stop_loss_pct: 0.5   # 第三档最大回撤比例
```

### 单个交易对配置

可以为特定交易对覆盖全局设置：

```yaml
tradingPairs:
  "DOGE/USDT:USDT":
    HTF: "4h"
    ATF: "15m"
    ETF: "1m"
    liquidity_grab_strategy:
      min_profit_ratio: 2.0
      # ... 其他覆盖配置
```

## 使用方法

### 命令行

安装后，运行 taker：

```bash
openfund-taker
```

或使用 Poetry：

```bash
poetry run openfund-taker
```

### 编程方式

```python
from taker.main import main

if __name__ == "__main__":
    main()
```

## 可用策略

1. **LiquidityGrabStrategyTaker**：高级策略，识别并交易流动性抓取，结合订单块分析
2. **BestTopDownStrategyTaker**：多时间框架自顶向下分析，带结构确认
3. **SMCSLAndTPTaker**：基于智能资金概念的持仓管理
4. **TrailingSLAndTPTaker**：动态移动止损止盈
5. **TrailingSLTaker**：简单移动止损管理
6. **ThreeLineTradingTaker**：基于三线指标的交易

## 日志记录

日志存储在 `log/` 目录，按日切割：
- 当前日志：`log/openfund-taker.log`
- 历史日志：`log/openfund-taker.log.YYYY-MM-DD`

在 `taker_config.yaml` 的 `Logger` 部分配置日志级别。

## 开发

### 运行测试

```bash
poetry run pytest
```

### 项目结构

```
openfund-taker/
├── src/taker/           # 主要源代码
│   ├── main.py          # 入口点
│   ├── StrategyTaker.py # 基础策略类
│   └── *Taker.py        # 策略实现
├── tests/               # 测试文件
├── example/             # 示例 notebooks
├── log/                 # 日志文件
├── taker_config.yaml    # 配置文件
└── pyproject.toml       # 项目元数据
```

## 注意事项

- 确保系统时间同步，避免 API 认证问题
- 如需代理，在 `taker_config.yaml` 中配置代理设置
- 建议先使用模拟交易或小仓位测试策略
- 定期监控日志，及时发现问题
- 不同交易所可能有不同的持仓模式要求

## 版本

当前版本：2.5.10

## 许可证

详见 LICENSE 文件。
