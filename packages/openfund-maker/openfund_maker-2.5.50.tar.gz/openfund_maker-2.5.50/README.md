# OpenFund Maker - 加密货币量化交易系统

OpenFund Maker 是一个专业的加密货币量化交易系统，集成了多种交易策略和智能风控机制。系统支持 Binance、OKX、Bitget 等主流交易所，提供自动化交易、分档移动止盈、AI 辅助决策等功能。

## 项目概述

**版本**: 2.5.11  
**Python 版本**: 3.9+  
**核心依赖**: ccxt 4.4.26, pandas, openfund-core

### 核心特性

- **多策略支持**: 流动性抓取、SMC、MACD、Top-Down、三线反转等多种交易策略
- **智能风控**: 分档移动止盈、自适应目标位、动态止损机制
- **AI 辅助决策**: 集成 AI 形态验证系统，提高交易准确率
- **多交易所支持**: Binance、OKX、Bitget
- **实时监控**: 飞书 Webhook 通知、详细日志记录
- **灵活配置**: YAML 配置文件，支持交易对级别的个性化参数


## 项目架构

### 目录结构
```
openfund-maker/
├── src/maker/                    # 核心代码目录
│   ├── ai_validation/           # AI 验证模块
│   │   ├── ai_client.py        # AI 服务客户端
│   │   ├── coordinator.py      # 验证协调器
│   │   ├── data_collector.py   # 数据收集器
│   │   ├── pattern_recognizer.py # 形态识别器
│   │   └── decision_engine.py  # 决策引擎
│   ├── StrategyMaker.py        # 策略基类
│   ├── LiquidityGrabStrategyMaker.py  # 流动性抓取策略
│   ├── SMCStrategyMaker.py     # Smart Money Concept 策略
│   ├── MACDStrategyMaker.py    # MACD 策略
│   ├── BestTopDownStrategyMaker.py # Top-Down 策略
│   ├── ThreeLineStrategyMaker.py   # 三线反转策略
│   ├── AdaptiveTargetFinder.py     # 自适应目标位查找器
│   ├── TechnicalAnalysisIntegrator.py # 技术分析集成器
│   └── main.py                 # 主程序入口
├── maker_config.yaml           # 主配置文件
├── pyproject.toml             # 项目依赖配置
├── tests/                     # 测试目录
└── log/                       # 日志目录
```

### 技术栈

- **交易接口**: CCXT 4.4.26 (统一交易所 API)
- **数据处理**: Pandas 2.2.3
- **任务调度**: APScheduler 3.11.0
- **AI 服务**: Moonshot API (Kimi-K2 模型)
- **配置管理**: PyYAML 6.0.2
- **缓存**: CacheTools 5.3.2

## 交易所配置要求

**重要**: CCXT 版本不一致可能导致 bug，请严格按照 requirements.txt 安装

- **Binance**: 需设置**单向持仓**
- **OKX**: **单向持仓和双向持仓都支持**
- **Bitget**: 需设置**双向持仓**

## 相关视频教程

- [基础使用教程](https://www.youtube.com/watch?v=1ujgGsMQbqA)
- [策略配置详解](https://www.youtube.com/watch?v=f4T0tKZTVrM)
- [高级功能演示](https://www.youtube.com/watch?v=S8ICwu9u-dk)
- [OKX 策略信号监控](https://youtu.be/ugyQDrIw8-I)
- [浮盈加仓功能](https://youtu.be/GOYzgskAjvs)
- [OKX 全仓统一监控](https://www.youtube.com/watch?v=99mCa_UiHiE)

## 快速开始

### 环境要求

- **Python**: 3.9+ (推荐 3.9)
- **操作系统**: Linux/macOS/Windows
- **网络**: 稳定的网络连接，建议配置代理

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd openfund-maker
```

2. **安装依赖**
```bash
# 使用 Poetry (推荐)
poetry install

# 或使用 pip
pip install -r requirements.txt
```

3. **配置文件**
编辑 `maker_config.yaml`，配置交易所 API 密钥和策略参数

4. **运行程序**
```bash
# 使用 Poetry
poetry run openfund-maker

# 或直接运行
python src/maker/main.py
```

### 常见问题

**Windows 用户注意事项**:
- 确保系统时间同步（很多报错源于此）
- 如有代理，在配置文件中设置 `proxy: "http://localhost:7890"`

**服务器部署建议**:
- 推荐使用阿里云轻量级服务器（月费约 34 元）
- 确保服务器时区正确
- 建议使用 systemd 或 supervisor 管理进程

**技术支持**:
- Telegram: [联系作者](https://t.me/)

## 核心功能模块

### 1. 交易策略系统

#### 流动性抓取策略 (LiquidityGrabStrategyMaker)
- 基于流动性区域的交易策略
- 支持多时间框架分析 (HTF/ATF/LTF)
- 自适应目标位查找
- 订单块 (Order Block) 识别
- 最小盈亏比和利润空间控制

#### SMC 策略 (Smart Money Concept)
- 市场结构分析 (SMS/CHoCH/BMS)
- FVG (Fair Value Gap) 识别
- Swing Points 计算
- 多时间框架确认

#### MACD 策略
- 经典 MACD 指标交易
- 支持严格模式和宽松模式
- 金叉死叉信号识别

#### Top-Down 策略
- 自顶向下分析方法
- 流动性区域检查
- 动态趋势线和通道
- 利润空间验证

#### 三线反转策略
- EMA 波动范围分析
- 振幅限制控制
- K 线形态识别

### 2. AI 辅助决策系统

集成 Moonshot AI (Kimi-K2 模型) 进行形态验证：

- **数据收集器**: 收集多时间框架 K 线数据
- **形态识别器**: 识别等高/等低形态
- **决策引擎**: 基于 AI 分析结果做出交易决策
- **降级策略**: AI 服务不可用时的备用方案
- **性能监控**: 实时监控 AI 验证性能

配置参数：
- 置信度阈值: 0.6
- 超时时间: 20 秒
- 缓存 TTL: 300 秒
- 降级模式: skip/execute

### 3. 风险管理系统

#### 分档移动止盈
- **低档保护止盈**: 0.4% 触发，0.3% 固定平仓
- **第一档移动止盈**: 1.0% 触发，20% 回撤平仓
- **第二档移动止盈**: 3.0% 触发，25% 回撤平仓

#### 止损机制
- 固定止损百分比 (默认 2%)
- 止损缓冲点数设置
- 动态止损调整

#### 自适应目标位
- 最大价格偏移: 5.0%
- 最小利润空间: 2.0%
- 最小盈亏比: 1.5
- 技术分析权重: 0.7
- 流动性权重: 0.3

### 4. 监控与通知

- **飞书 Webhook**: 实时交易通知
- **日志系统**: 按日切割，详细记录
- **定时任务**: APScheduler 调度
- **缓存机制**: 60 分钟 TTL

## 更新日志

### 2024年11月
- **11-12**: OKX 新增全仓统一监控
- **11-08**: OKX/Bitget 支持浮盈加仓
- **11-06**: OKX 统一支持单向/双向持仓
- **11-05**: 新增 Bitget 支持，OKX 策略信号监控，按日切割日志

### 2024年10月
- **10-29**: 新增黑名单功能，重新整理变量参数
- **10-28**: 修复平仓 bug，修复全仓模式反向开单问题 

## 配置说明

配置文件: `maker_config.yaml`

### 平台配置 (platform)

#### Binance 配置

```yaml
platform:
  binance:
    apiKey: "your_api_key"
    secret: "your_secret"
```

- **apiKey**: Binance API 密钥
- **secret**: Binance API 密钥密文

#### OKX 配置

```yaml
platform:
  okx:
    apiKey: "your_api_key"
    secret: "your_secret"
    password: "your_password"
```

- **apiKey**: OKX API 密钥
- **secret**: OKX API 密钥密文
- **password**: OKX API 密码

#### Bitget 配置

```yaml
platform:
  bitget:
    apiKey: "your_api_key"
    secret: "your_secret"
    password: "your_password"
```

### 通用配置 (common)

```yaml
common:
  actived_maker: "LiquidityGrabStrategyMaker"  # 激活的策略
  is_demo_trading: 0                           # 是否模拟交易
  cache_ttl: 60                                # 缓存时间(分钟)
  feishu_webhook: "https://..."                # 飞书通知
  proxy: "http://localhost:7890"               # 代理设置
  schedule:
    enabled: true
    monitor_interval: 1                        # 监控间隔(分钟)
```

### 策略配置 (strategy)

```yaml
strategy:
  leverage: 20                    # 杠杆倍数
  long_amount_usdt: 1            # 做多金额
  short_amount_usdt: 1           # 做空金额
  CHF: "1m"                      # 当前时间框架
  HTF: "4h"                      # 高时间框架
  LTF: "1m"                      # 低时间框架
  ATF: "15m"                     # 分析时间框架
  ETF: "1m"                      # 入场时间框架
```

#### 流动性抓取策略配置

```yaml
liquidity_grab_strategy:
  range_of_the_ob: 0.6                    # 订单块范围
  liquidity_atr_offset: 0.1               # 流动性 ATR 偏移
  min_profit_ratio: 1.5                   # 最小盈亏比
  min_profit_percent: 4                   # 最小利润空间%
  stop_loss_buffer_ticks: 2               # 止损缓冲点数
  enable_htf_atf_confluence: true         # 启用时间框架重合验证
  enable_check_htf_side: false            # 是否校验 HTF 方向
  max_candle_interval: 200                # 流动性有效间隔
  
  adaptive_target:
    enabled: true                         # 启用自适应目标位
    max_price_deviation_percent: 5.0     # 最大价格偏移%
    min_profit_percent: 2.0              # 最小利润空间%
    min_profit_ratio: 1.5                # 最小盈亏比
    search_step_percent: 0.5             # 搜索步长%
    technical_priority_weight: 0.7       # 技术分析权重
    liquidity_priority_weight: 0.3       # 流动性权重
```

### AI 验证配置 (ai_validation)

```yaml
ai_validation:
  enabled: true                    # 启用 AI 验证
  confidence_threshold: 0.6        # 置信度阈值
  timeout_seconds: 20              # 超时时间
  max_retries: 3                   # 最大重试次数
  fallback_mode: 'skip'            # 降级模式: skip/execute
  data_collection_candles: 200     # 数据收集 K 线数量
  enable_caching: true             # 启用缓存
  cache_ttl_seconds: 300           # 缓存 TTL

ai_service:
  endpoint_url: "https://api.moonshot.cn/v1/chat/completions"
  api_key: "your_api_key"
  model_version: "kimi-k2-0905-preview"
  timeout: 20
  max_retries: 3
```

### 交易对配置 (tradingPairs)

支持为每个交易对单独配置参数：

```yaml
tradingPairs:
  "DOGE/USDT:USDT":
    long_amount_usdt: 2
    short_amount_usdt: 2
    CHF: "1m"
    HTF: "4h"
    LTF: "1m"
    ATF: "15m"
    # ... 其他策略参数
```

## 使用示例

### 启动交易系统

```bash
# 使用 Poetry
poetry run openfund-maker

# 或直接运行
python src/maker/main.py
```

### 查看日志

```bash
# 主日志
tail -f log/openfund-maker.log

# AI 验证日志
tail -f log/openfund-ai_validation.log
```

### 运行测试

```bash
# 运行所有测试
poetry run pytest

# 运行特定测试
poetry run pytest tests/test_specific.py

# 查看覆盖率
poetry run pytest --cov=maker --cov-report=html
```

## 性能优化建议

1. **缓存配置**: 根据交易频率调整 `cache_ttl`
2. **监控间隔**: 高频交易可设置为 1 分钟，低频可设置为 5 分钟
3. **AI 验证**: 如不需要可关闭以提升性能
4. **日志级别**: 生产环境建议设置为 INFO 或 WARNING

## 安全建议

1. **API 密钥**: 使用只读+交易权限，禁用提现权限
2. **IP 白名单**: 在交易所设置 IP 白名单
3. **资金管理**: 建议单次交易金额不超过总资金的 5%
4. **止损设置**: 务必设置合理的止损百分比
5. **配置文件**: 不要将包含 API 密钥的配置文件提交到版本控制

## 故障排查

### 常见错误

1. **时间同步错误**: 确保系统时间准确
2. **网络连接失败**: 检查代理设置和网络连接
3. **API 权限不足**: 确认 API 密钥权限
4. **CCXT 版本问题**: 严格使用 4.4.26 版本
5. **持仓模式错误**: 检查交易所持仓模式设置

### 调试模式

在配置文件中设置日志级别为 DEBUG：

```yaml
Logger:
  loggers:
    openfund-maker:
      level: DEBUG
```

## 项目依赖

- **openfund-core**: 核心交易逻辑库
- **ccxt**: 统一交易所 API 接口
- **pandas**: 数据处理和分析
- **APScheduler**: 定时任务调度
- **PyYAML**: 配置文件解析
- **CacheTools**: 缓存管理

## 贡献指南

欢迎提交 Issue 和 Pull Request。

## 许可证

请查看 LICENSE 文件了解详情。

## 联系方式

- **Telegram**: [联系作者](https://t.me/buouqukuairiji)
- **打赏地址 (TRC20)**: `TUunBuqQ1ZDYt9WrA3ZarndFPQgefXqZAM`

---

**免责声明**: 本软件仅供学习和研究使用，使用本软件进行实盘交易的风险由使用者自行承担。加密货币交易存在高风险，请谨慎投资。
