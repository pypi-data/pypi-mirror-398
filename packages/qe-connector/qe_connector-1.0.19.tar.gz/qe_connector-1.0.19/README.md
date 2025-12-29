# Quantum Execute Python SDK

[![Python Version](https://img.shields.io/pypi/pyversions/qe-connector)](https://pypi.org/project/qe-connector/)
[![PyPI Version](https://img.shields.io/pypi/v/qe-connector)](https://pypi.org/project/qe-connector/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

这是 Quantum Execute 公共 API 的官方 Python SDK，为开发者提供了一个轻量级、易于使用的接口来访问 Quantum Execute 的交易服务。

## 功能特性

- ✅ 完整的 Quantum Execute API 支持
- ✅ 交易所 API 密钥管理
- ✅ 主订单创建与管理（TWAP、VWAP、POV 等算法）
- ✅ 订单查询和成交明细
- ✅ ListenKey 创建与管理
- ✅ 交易对信息查询
- ✅ 服务器连通性测试
- ✅ 服务器时间同步
- ✅ 安全的 HMAC-SHA256 签名认证
- ✅ 支持生产环境和测试环境
- ✅ 链式调用 API 设计
- ✅ 完整的错误处理

## 安装

```bash
pip install qe-connector
```

或者从源码安装：

```bash
git clone https://github.com/Quantum-Execute/qe-connector-python.git
cd qe-connector-python
pip install -e .
```

## 快速开始

### 初始化客户端

```python
from qe.user import User as Client
import logging

# 配置日志（可选）
logging.basicConfig(level=logging.INFO)

# 创建生产环境客户端
client = Client(
    api_key="your-api-key",
    api_secret="your-api-secret"
)

# 创建测试环境客户端
client = Client(
    api_key="your-api-key",
    api_secret="your-api-secret",
    base_url="https://testapi.quantumexecute.com"
)
```

### 使用枚举类型（推荐）

SDK 提供了枚举类型来确保类型安全和代码提示。推荐使用枚举而不是字符串：

```python
# 导入枚举类型
from qe.lib import Algorithm, Exchange, MarketType, OrderSide, StrategyType, MarginType

# 可用的枚举值
print("算法类型:", [algo.value for algo in Algorithm])           # ['TWAP', 'VWAP', 'POV']
print("交易所:", [exchange.value for exchange in Exchange])     # ['Binance', 'OKX', 'LTP', 'Deribit']
print("市场类型:", [market.value for market in MarketType])     # ['SPOT', 'PERP']
print("订单方向:", [side.value for side in OrderSide])         # ['buy', 'sell']
print("策略类型:", [strategy.value for strategy in StrategyType]) # ['TWAP_1', 'POV']
print("保证金类型:", [margin.value for margin in MarginType])   # ['U']

# 使用枚举创建订单（推荐）
response = client.create_master_order(
    algorithm=Algorithm.TWAP,        # 而不是 "TWAP"
    exchange=Exchange.BINANCE,  # 或 Exchange.OKX、Exchange.LTP、Exchange.DERIBIT       # 而不是 "Binance"（支持 Binance、OKX、LTP、Deribit）
    marketType=MarketType.SPOT,      # 而不是 "SPOT"
    side=OrderSide.BUY,             # 而不是 "buy"
    # ... 其他参数
)
```

## API 参考

### 公共接口

#### 服务器连通性测试

##### Ping 服务器

测试与 Quantum Execute 服务器的连通性。

**请求参数：**

| 参数名 | 类型 | 是否必传 | 描述 |
|--------|------|----------|------|
| 无需参数 | - | - | - |

**响应：**

成功时无返回内容，失败时返回错误信息。

**示例代码：**

```python
from qe.status import Status as StatusClient

# 创建状态客户端（无需认证）
status_client = StatusClient()

# 测试服务器连通性
try:
    status_client.ping()
    print("服务器连接正常")
except Exception as e:
    print(f"服务器连接失败: {e}")
```

#### 获取服务器时间

##### 查询服务器时间戳

获取 Quantum Execute 服务器的当前时间戳（毫秒）。

**请求参数：**

| 参数名 | 类型 | 是否必传 | 描述 |
|--------|------|----------|------|
| 无需参数 | - | - | - |

**响应字段：**

| 字段名 | 类型 | 描述 |
|--------|------|------|
| serverTimeMilli | int | 服务器时间戳（毫秒） |

**示例代码：**

```python
from qe.status import Status as StatusClient
import datetime

# 创建状态客户端
status_client = StatusClient()

# 获取服务器时间戳
try:
    timestamp = status_client.timestamp()
    print(f"服务器时间戳: {timestamp}")
    
    # 转换为可读时间格式
    readable_time = datetime.datetime.fromtimestamp(timestamp / 1000)
    print(f"服务器时间: {readable_time}")
except Exception as e:
    print(f"获取时间戳失败: {e}")
```

#### 交易对管理

##### 查询交易对列表

获取支持的交易对信息，包括现货和合约交易对。

**请求参数：**

| 参数名 | 类型 | 是否必传 | 描述 |
|--------|------|----------|------|
| page | int | 否 | 页码 |
| pageSize | int | 否 | 每页数量 |
| exchange | str | 否 | 交易所名称筛选，可选值：Binance、OKX、LTP、Deribit |
| marketType | str/TradingPairMarketType | 否 | 市场类型筛选，可选值：SPOT（现货）、FUTURES（合约） |
| isCoin | bool | 否 | 是否为币种筛选 |

**响应字段：**

| 字段名 | 类型 | 描述 |
|--------|------|------|
| items | array | 交易对列表 |
| ├─ id | int | 交易对 ID |
| ├─ symbol | string | 交易对符号（如：BTCUSDT） |
| ├─ baseAsset | string | 基础币种（如：BTC） |
| ├─ quoteAsset | string | 计价币种（如：USDT） |
| ├─ exchange | string | 交易所名称 |
| ├─ marketType | string | 市场类型（SPOT/FUTURES） |
| ├─ contractType | string | 合约类型（仅合约交易对） |
| ├─ deliveryDate | string | 交割日期（仅合约交易对） |
| ├─ status | string | 交易对状态 |
| ├─ createdAt | string | 创建时间 |
| ├─ updatedAt | string | 更新时间 |
| page | int | 当前页码 |
| pageSize | int | 每页数量 |
| total | string | 总数 |

**示例代码：**

```python
from qe.pub import Pub as PubClient
from qe.lib import TradingPairMarketType

# 创建公共客户端（无需认证）
pub_client = PubClient()

# 获取所有交易对
try:
    pairs = pub_client.trading_pairs()
    print(f"总交易对数量: {pairs.get('total', 0)}")
    
    # 打印前几个交易对信息
    for pair in pairs.get('items', [])[:5]:
        print(f"""
交易对信息：
    符号: {pair['symbol']}
    基础币种: {pair['baseAsset']}
    计价币种: {pair['quoteAsset']}
    交易所: {pair['exchange']}
    市场类型: {pair['marketType']}
    状态: {pair['status']}
    创建时间: {pair['createdAt']}
        """)
        
        # 如果是合约交易对，显示额外信息
        if pair['marketType'] == 'FUTURES':
            print(f"    合约类型: {pair.get('contractType', 'N/A')}")
            if pair.get('deliveryDate'):
                print(f"    交割日期: {pair['deliveryDate']}")
                
except Exception as e:
    print(f"获取交易对失败: {e}")

# 使用枚举类型筛选（推荐）
try:
    # 获取币安现货交易对
    spot_pairs = pub_client.trading_pairs(
        exchange=Exchange.BINANCE,  # 或 Exchange.OKX、Exchange.LTP
        marketType=TradingPairMarketType.SPOT,  # 使用枚举
        page=1,
        pageSize=10
    )
    print(f"币安现货交易对数量: {len(spot_pairs.get('items', []))}")
    
    # 获取合约交易对
    futures_pairs = pub_client.trading_pairs(
        marketType=TradingPairMarketType.FUTURES,  # 使用枚举
        page=1,
        pageSize=20
    )
    print(f"合约交易对数量: {len(futures_pairs.get('items', []))}")
    
    # 获取币种交易对
    coin_pairs = pub_client.trading_pairs(isCoin=True)
    print(f"币种交易对数量: {len(coin_pairs.get('items', []))}")
    
except Exception as e:
    print(f"筛选交易对失败: {e}")

# 使用字符串筛选（向后兼容）
try:
    # 使用字符串参数
    spot_pairs = pub_client.trading_pairs(
        exchange="Binance",  # 或 "OKX"、"LTP"
        marketType="SPOT",  # 使用字符串
        page=1,
        pageSize=5
    )
    print(f"现货交易对数量: {len(spot_pairs.get('items', []))}")
    
except Exception as e:
    print(f"获取现货交易对失败: {e}")
```

### 交易所 API 管理

#### 查询交易所 API 列表

查询当前用户绑定的所有交易所 API 账户。

**请求参数：**

| 参数名 | 类型 | 是否必传 | 描述 |
|--------|------|----------|------|
| page | int | 否 | 页码 |
| pageSize | int | 否 | 每页数量 |
| exchange | str | 否 | 交易所名称筛选，可选值：Binance、OKX、LTP、Deribit |

**响应字段：**

| 字段名 | 类型 | 描述 |
|--------|------|------|
| items | array | API 列表 |
| ├─ id | string | API 记录的唯一标识 |
| ├─ createdAt | string | API 添加时间 |
| ├─ accountName | string | 账户名称（如：账户1、账户2） |
| ├─ exchange | string | 交易所名称（如：Binance、OKX、LTP、Deribit） |
| ├─ apiKey | string | 交易所 API Key（部分隐藏） |
| ├─ verificationMethod | string | API 验证方式（如：OAuth、API） |
| ├─ status | string | API 状态：正常、异常（不可用） |
| ├─ isValid | bool | API 是否有效 |
| ├─ isTradingEnabled | bool | 是否开启交易权限 |
| ├─ isDefault | bool | 是否为该交易所的默认账户 |
| ├─ isPm | bool | 是否为 Pm 账户 |
| total | int | API 总数 |
| page | int | 当前页码 |
| pageSize | int | 每页显示数量 |

**示例代码：**

```python
# 获取所有交易所 API 密钥
apis = client.list_exchange_apis()
print(f"共有 {apis['total']} 个 API 密钥")

# 打印每个 API 的详细信息
for api in apis['items']:
    print(f"""
API 信息：
    账户: {api['accountName']}
    交易所: {api['exchange']}
    状态: {api['status']}
    交易权限: {'开启' if api['isTradingEnabled'] else '关闭'}
    是否默认: {'是' if api['isDefault'] else '否'}
    是否PM账户: {'是' if api['isPm'] else '否'}
    添加时间: {api['createdAt']}
    """)

# 带分页和过滤
apis = client.list_exchange_apis(
    page=1,
    pageSize=10,
    exchange="binance"  # 或 "okx"、"ltp"
)
```

### 交易订单管理

#### 创建主订单

创建新的主订单并提交到算法侧执行。

**请求参数：**

| 参数名 | 类型 | 是否必传 | 描述 |
|--------|------|------|------|
| **基础参数** |
| strategyType | string/StrategyType | 是    | 策略类型，可选值：TWAP-1、POV |
| algorithm | string/Algorithm | 是    | 交易算法。strategyType=TWAP-1时，可选值：TWAP、VWAP、BoostVWAP、BoostTWAP；strategyType=POV时，可选值：POV |
| exchange | string/Exchange | 是    | 交易所名称，可选值：Binance、OKX、LTP、Deribit |
| symbol | string | 是    | 交易对符号（如：BTCUSDT）（可用交易对查询） |
| marketType | string/MarketType | 是    | 可选值：SPOT（现货）、PERP（永续合约） |
| side | string/OrderSide | 是    | 1.如果isTargetPosition=False：side代表交易方向，可选值：buy（买入）、sell（卖出）；合约交易时可与reduceOnly组合，reduceOnly=True时：buy代表买入平空，sell代表卖出平多。2.如果isTargetPosition=True：side代表仓位方向，可选值：buy（多头）、sell（空头）。【仅合约交易时需传入】 |
| apiKeyId | string | 是    | 指定使用的 API Key ID，这将决定您本次下单使用哪个交易所账户执行 |
| **数量参数（二选一）** |
| totalQuantity | float | 否*   | 要交易的总数量，与 orderNotional 二选一，输入范围：>0 |
| orderNotional | float | 否*   | 按价值下单时的金额，以计价币种为单位（如ETHUSDT为USDT数量），与 totalQuantity 二选一，输入范围：>0 |
| **下单模式参数** |
| isTargetPosition | bool | 否    | 是否为目标仓位下单，默认为 false |
| **时间参数** |
| startTime | string | 否    | 交易执行的启动时间，传入格式：ISO 8601(2025-09-03T01:30:00+08:00)，若不传入，则立即执行 |
| executionDuration | int | 否    | 订单最大执行时长，分钟，范围>=1 |
| **TWAP/VWAP 算法参数** |
| mustComplete | bool | 否    | 是否一定要在executionDuration之内执行完毕，选false则不会追赶进度，默认：true |
| makerRateLimit | float | 否    | 要求maker占比超过该值，范围：0-1（包含0和1。输入0.1代表10%），默认：-1(算法智能计算推荐值执行) |
| povLimit | string | 否    | 占市场成交量比例上限，优先级低于mustComplete，范围：0-1（包含0和1。输入0.1代表10%），默认：0.8 |
| limitPrice | float | 否    | 最高/低允许交易的价格，买入时该字段象征最高买入价，卖出时该字段象征最低卖出价，若市价超出范围则停止交易，范围：>0，默认：-1，代表无限制 |
| upTolerance | string | 否    | 允许超出目标进度的最大容忍度，范围：0-1（不包含0和1，最小输入0.0001，最大输入0.9999。输入0.1代表可以超前目标进度10%），默认：-1（即无容忍） |
| lowTolerance | string | 否    | 允许落后目标进度的最大容忍度，范围：0-1（不包含0和1，最小输入0.0001，最大输入0.9999。输入0.1代表可落后目标进度10%），默认：-1（即无容忍） |
| strictUpBound | bool | 否    | 是否严格小于uptolerance，开启后会更加严格贴近交易进度执行，同时可能会把母单拆很细；如需严格控制交易进度则建议开启，其他场景建议不开启，默认：false |
| tailOrderProtection | bool | 否    | 订单余量小于交易所最小发单量时，是否必须taker扫完，如果false，则订单余量小于交易所最小发单量时，订单结束执行；如果true，则订单余量随最近一笔下单全额执行（可能会提高Taker率），默认：true |
| **POV 算法参数** |
| makerRateLimit | float | 否    | 要求maker占比超过该值（包含0和1，输入0.1代表10%），输入范围：0-1（输入0.1代表10%），默认：-1(算法智能计算推荐值执行) |
| povLimit | string | 否    | 占市场成交量比例上限（包含0和0.5，一般建议小于0.15），输入范围：0-0.5（povMinLimit < max(povLimit-0.01,0)），默认：0 |
| povMinLimit | float | 否    | 占市场成交量比例下限，范围：小于max(POVLimit-0.01,0)，默认：0（即无下限） |
| limitPrice | float | 否    | 最高/低允许交易的价格，买入时该字段象征最高买入价，卖出时该字段象征最低卖出价，若市价超出范围则停止交易，范围：>0，默认：-1，代表无限制 |
| strictUpBound | bool | 否    | 是否追求严格小于povLimit，开启后可能会把很小的母单也拆的很细，比如50u拆成10个5u，不建议开启，算法的每个order会权衡盘口流动性，默认：false |
| tailOrderProtection | bool | 否    | 订单余量小于交易所最小发单量时，是否必须taker扫完，如果false，则订单余量小于交易所最小发单量时，订单结束执行；如果true，则订单余量随最近一笔下单全额执行（可能会提高Taker率），默认：true |
| **其他参数** |
| reduceOnly | bool | 否    | 合约交易时是否仅减仓，默认值：false |
| marginType | string/MarginType | 否*   | **永续合约必传参数** - 合约交易保证金类型，可选值：U（U本位），默认：U（暂时只支持U本位永续合约）。当marketType为PERP（永续合约）时必传 |
| isMargin | bool | 否    | 是否使用现货杠杆。- 默认为false - 仅现货可使用该字段 |
| notes | string | 否    | 订单备注 |

*注：totalQuantity 和 orderNotional 必须传其中一个，但当 isTargetPosition 为 true 时，totalQuantity 必填代表目标仓位数量且 orderNotional 不可填  
*注：当使用 Deribit 账户下单 BTCUSD 或 ETHUSD 合约时，只能使用 totalQuantity 作为数量输入字段，且数量单位为 USD；orderNotional 当前不可用。  
*注：使用BoostVWAP、BoostTWAP时，代表使用高频alpha发单。仅Binance交易所永续合约BTCUSDT、ETHUSDT交易对可用，不适用于其他交易所、交易对。

**响应字段：**

| 字段名 | 类型 | 描述 |
|--------|------|------|
| masterOrderId | string | 创建成功的主订单 ID |
| success | bool | 创建是否成功 |
| message | string | 创建结果消息 |

**示例代码：**

```python
# 导入枚举类型（推荐方式）
from qe.lib import Algorithm, Exchange, MarketType, OrderSide, StrategyType, MarginType

# TWAP 订单示例 - 使用枚举创建订单（推荐）
response = client.create_master_order(
    algorithm=Algorithm.TWAP,                      # 使用算法枚举
    exchange=Exchange.BINANCE,  # 或 Exchange.OKX、Exchange.LTP、Exchange.DERIBIT                     # 使用交易所枚举（Binance、OKX、LTP 或 Deribit）
    symbol="BTCUSDT",
    marketType=MarketType.SPOT,                    # 使用市场类型枚举
    side=OrderSide.BUY,                           # 使用订单方向枚举
    apiKeyId="your-api-key-id",                   # 从 list_exchange_apis 获取
    orderNotional=200,                            # $200 名义价值
    strategyType=StrategyType.TWAP_1,             # 使用策略类型枚举
    startTime="2025-09-02T19:54:34+08:00",
    executionDuration=5,                           # 5 分钟
    mustComplete=True,                            # 必须完成全部订单
    worstPrice=-1,                               # -1 表示无价格限制
    upTolerance="-1",                            # 允许超出容忍度
    lowTolerance="-1",                           # 允许落后容忍度
    strictUpBound=False,                         # 不追求严格小于uptolerance
    tailOrderProtection=True,                    # 尾单保护
    notes="测试 TWAP 订单"                       # 订单备注
)

if response.get('success'):
    print(f"主订单创建成功，ID: {response['masterOrderId']}")
else:
    print(f"创建失败：{response.get('message')}")
```

**目标仓位下单示例：**

```python
# 目标仓位下单示例 - 买入 1.5 BTC 到目标仓位
response = client.create_master_order(
    algorithm=Algorithm.TWAP,                      # 使用算法枚举
    exchange=Exchange.BINANCE,  # 或 Exchange.OKX、Exchange.LTP、Exchange.DERIBIT                     # 使用交易所枚举（Binance、OKX、LTP 或 Deribit）
    symbol="BTCUSDT",
    marketType=MarketType.SPOT,                    # 使用市场类型枚举
    side=OrderSide.BUY,                           # 使用订单方向枚举
    apiKeyId="your-api-key-id",                   # 从 list_exchange_apis 获取
    totalQuantity=1.5,                            # 目标数量 1.5 BTC
    isTargetPosition=True,                        # 启用目标仓位模式
    strategyType=StrategyType.TWAP_1,             # 使用策略类型枚举
    startTime="2025-09-02T19:54:34+08:00",
    executionDuration=60,                         # 60 分钟
    mustComplete=True,                            # 必须完成全部订单
    limitPrice="65000",                           # 最高价格 $65,000
    upTolerance="0.1",                            # 允许超出 10%
    lowTolerance="0.1",                           # 允许落后 10%
    strictUpBound=False,                          # 不追求严格小于uptolerance
    tailOrderProtection=True,                     # 尾单保护
    notes="目标仓位订单示例"                      # 订单备注
)

if response.get('success'):
    print(f"目标仓位订单创建成功，ID: {response['masterOrderId']}")
else:
    print(f"创建失败：{response.get('message')}")
```

**POV 算法示例：**

```python
# POV 订单示例 - 按市场成交量比例买入 BTC
response = client.create_master_order(
    algorithm=Algorithm.POV,                       # POV 算法
    exchange=Exchange.BINANCE,  # 或 Exchange.OKX、Exchange.LTP、Exchange.DERIBIT
    symbol="BTCUSDT",
    marketType=MarketType.SPOT,                    # 现货市场
    side=OrderSide.BUY,                           # 买入
    apiKeyId="your-api-key-id",
    totalQuantity=1.5,                            # 买入 1.5 BTC
    executionDuration=60,                         # 60 分钟
    povLimit=0.1,                                 # 占市场成交量 10%
    povMinLimit=0.05,                             # 最低占市场成交量 5%
    strictUpBound=False,                          # 不追求严格小于povLimit
    limitPrice=65000,                             # 最高价格 $65,000
    tailOrderProtection=True,
    strategyType=StrategyType.TWAP_1,             # 使用策略类型枚举
    notes="POV 订单示例"
)

if response.get('success'):
    print(f"POV 订单创建成功，ID: {response['masterOrderId']}")
```

#### 查询主订单列表

获取用户的主订单列表。

**请求参数：**

| 参数名 | 类型 | 是否必传 | 描述 |
|--------|------|----------|------|
| page | int | 否 | 页码 |           
| pageSize | int | 否 | 每页数量 |
| status | string | 否 | 订单状态筛选，可选值：NEW（执行中）、COMPLETED（已完成） |
| exchange | string | 否 | 交易所名称筛选，可选值：Binance、OKX、LTP、Deribit |
| symbol | string | 否 | 交易对筛选 |
| startTime | string | 否 | 开始时间筛选 |
| endTime | string | 否 | 结束时间筛选 |

**响应字段：**

| 字段名 | 类型 | 描述 |
|--------|------|------|
| items | array | 主订单列表 |
| ├─ masterOrderId | string | 主订单 ID |
| ├─ algorithm | string | 算法 |
| ├─ algorithmType | string | 算法类型 |
| ├─ exchange | string | 交易所 |
| ├─ symbol | string | 交易对 |
| ├─ marketType | string | 市场类型 |
| ├─ side | string | 买卖方向 |
| ├─ totalQuantity | float | 总数量 |        
| ├─ filledQuantity | float | 1.按币数下单时，该字段代表已成交币数。2.按金额下单时，该字段值代表已成交金额 |   
| ├─ averagePrice | float | 平均成交价 |
| ├─ status | string | 状态：NEW（创建，未执行）、WAITING（等待中）、PROCESSING（执行中，且未完成）、PAUSED（已暂停）、CANCEL（取消中）、CANCELLED（已取消）、COMPLETED（已完成）、REJECTED（已拒绝）、EXPIRED（已过期）、CANCEL_REJECT（取消被拒绝） |
| ├─ executionDuration | int | 执行时长（分钟） |
| ├─ priceLimit | float | 价格限制 |
| ├─ startTime | string | 开始时间 |
| ├─ endTime | string | 结束时间 |
| ├─ createdAt | string | 创建时间 |
| ├─ updatedAt | string | 更新时间 |
| ├─ notes | string | 备注 |
| ├─ marginType | string | 保证金类型（U:U本位） |
| ├─ reduceOnly | bool | 是否仅减仓 |
| ├─ strategyType | string | 策略类型 |
| ├─ orderNotional | string | 订单金额（按成交额提交的下单数量） |
| ├─ mustComplete | bool | 是否必须完成 |
| ├─ makerRateLimit | string | 最低 Maker 率 |
| ├─ povLimit | string | 最大市场成交量占比 |
| ├─ clientId | string | 客户端 ID |
| ├─ date | string | 发单日期（格式：YYYYMMDD） |
| ├─ ticktimeInt | string | 发单时间（格式：093000000 表示 9:30:00.000） |
| ├─ limitPriceString | string | 限价（字符串） |
| ├─ upTolerance | string | 上容忍度 |
| ├─ lowTolerance | string | 下容忍度 |
| ├─ strictUpBound | bool | 严格上界 |
| ├─ ticktimeMs | int64 | 发单时间戳（epoch 毫秒） |
| ├─ category | string | 交易品种（spot 或 perp） |
| ├─ filledAmount | float | 成交币数 |
| ├─ totalValue | float | 成交总值 |
| ├─ base | string | 基础币种 |
| ├─ quote | string | 计价币种 |
| ├─ completionProgress | float | 完成进度（0-100）返回50代表50%  |
| ├─ reason | string | 原因（如取消原因） |
| total | int | 总数 |
| page | int | 当前页码 |
| pageSize | int | 每页数量 |

**示例代码：**

```python
# 查询所有主订单
orders = client.get_master_orders()

# 带过滤条件查询
orders = client.get_master_orders(
    page=1,
    pageSize=20,
    status="NEW",              # 执行中的订单
    symbol="BTCUSDT",
    startTime="2024-01-01T00:00:00Z",
    endTime="2024-01-31T23:59:59Z"
)

# 打印订单详细信息
for order in orders['items']:
    print(f"""
订单信息：
    ID: {order['masterOrderId']}
    算法: {order['algorithm']} ({order.get('strategyType', 'N/A')})
    交易对: {order['symbol']} {order['marketType']}
    方向: {order['side']}
    状态: {order['status']}
    完成度: {order['completionProgress'] * 100:.2f}%
    平均价格: ${order.get('averagePrice', 0):.2f}
    已成交: {order['filledQuantity']} / {order['totalQuantity']}
    成交金额: ${order.get('filledAmount', 0):.2f}
    Maker率: {order.get('takerMakerRate', 0) * 100:.2f}%
    创建时间: {order['createdAt']}
    发单日期: {order.get('date', 'N/A')}
    上容忍度: {order.get('upTolerance', 'N/A')}
    下容忍度: {order.get('lowTolerance', 'N/A')}
    """)
```

#### 查询成交记录

获取用户的成交记录。

**请求参数：**

| 参数名 | 类型 | 是否必传 | 描述 |
|--------|------|----------|------|
| page | int | 否 | 页码 |
| pageSize | int | 否 | 每页数量 |
| masterOrderId | string | 否 | 主订单 ID 筛选 |
| subOrderId | string | 否 | 子订单 ID 筛选 |
| symbol | string | 否 | 交易对筛选 |
| status | string | 否 | 订单状态筛选，多个状态用逗号分隔，如：PLACED,FILLED。支持的状态：PLACED（已下单）、REJECTED（已拒单）、CANCELLED（算法已撤单）、FILLED（完全成交）、Cancelack（交易已撤单）、CANCEL_REJECTED（拒绝撤单） |
| startTime | string | 否 | 开始时间筛选 |
| endTime | string | 否 | 结束时间筛选 |

**响应字段：**

| 字段名 | 类型 | 描述 |
|--------|------|------|
| items | array | 成交记录列表 |
| ├─ id | string | 记录 ID |
| ├─ orderCreatedTime | string | 订单创建时间 |
| ├─ masterOrderId | string | 主订单 ID |
| ├─ exchange | string | 交易所 |
| ├─ category | string | 市场类型 |
| ├─ symbol | string | 交易对 |
| ├─ side | string | 方向 |
| ├─ filledValue | float | 成交价值 |
| ├─ filledQuantity | string | 成交数量 |
| ├─ avgPrice | float | 平均价格 |
| ├─ price | float | 成交价格 |
| ├─ fee | float | 手续费 |
| ├─ tradingAccount | string | 交易账户 |
| ├─ status | string | 状态 |
| ├─ rejectReason | string | 拒绝原因 |
| ├─ base | string | 基础币种 |
| ├─ quote | string | 计价币种 |
| ├─ type | string | 订单类型 |
| total | int | 总数 |
| page | int | 当前页码 |
| pageSize | int | 每页数量 |

**示例代码：**

```python
# 查询特定主订单的成交明细
fills = client.get_order_fills(
    masterOrderId="your-master-order-id",
    page=1,
    pageSize=50
)

# 查询所有成交
fills = client.get_order_fills(
    symbol="BTCUSDT",
    startTime="2024-01-01T00:00:00Z",
    endTime="2024-01-01T23:59:59Z"
)

# 查询特定状态的成交记录
fills = client.get_order_fills(
    status="FILLED,CANCELLED",  # 查询已成交和已撤单的记录
    symbol="BTCUSDT",
    page=1,
    pageSize=50
)

# 查询被拒绝的订单
fills = client.get_order_fills(
    status="REJECTED",
    startTime="2024-01-01T00:00:00Z",
    endTime="2024-01-31T23:59:59Z",
    page=1,
    pageSize=100
)

# 统计成交信息
total_value = 0
total_fee = 0
for fill in fills['items']:
    print(f"""
成交详情：
    时间: {fill['orderCreatedTime']}
    交易对: {fill['symbol']}
    方向: {fill['side']}
    成交价格: ${fill['price']:.2f}
    成交数量: {fill['filledQuantity']}
    成交金额: ${fill['filledValue']:.2f}
    手续费: ${fill['fee']:.4f}
    账户: {fill['tradingAccount']}
    类型: {fill.get('type', 'N/A')}
    """)
    total_value += fill['filledValue']
    total_fee += fill['fee']

print(f"总成交额: ${total_value:.2f}, 总手续费: ${total_fee:.2f}")
```

#### 查询TCA分析数据

获取TCA分析数据列表（strategy-api：APIKEY签名鉴权）。

**请求参数：**

| 参数名 | 类型 | 是否必传 | 描述 |
|--------|------|----------|------|
| symbol | str | 否 | 交易对筛选 |
| category | str | 否 | 策略类别筛选 |
| apikey | str | 否 | ApiKey id 列表，逗号分隔 |
| startTime | int | 否 | 开始时间戳（毫秒） |
| endTime | int | 否 | 结束时间戳（毫秒） |

**响应：**

成功时返回后端 `message` 字段原样（通常为 `list[dict]`）。

**示例代码：**

```python
# 查询TCA分析数据
items = client.get_tca_analysis(
    symbol="BTCUSDT",
    category="spot",
    apikey="your-apikey-id",
    startTime=1735689600000,
    endTime=1735776000000
)

print(f"items数量: {len(items)}")
if items:
    first = items[0]
    print("示例字段:")
    print("  master_order_id:", first.get("master_order_id"))
    print("  side:", first.get("side"))
    print("  symbol:", first.get("symbol"))
    print("  twap_slippage_bps:", first.get("twap_slippage_bps"))
    print("  make_fill_rate:", first.get("make_fill_rate"))
```

#### 取消主订单

取消指定的主订单。

**请求参数：**

| 参数名 | 类型 | 是否必传 | 描述 |
|--------|------|----------|------|
| masterOrderId | string | 是 | 要取消的主订单 ID |
| reason | string | 否 | 取消原因 |

**响应字段：**

| 字段名 | 类型 | 描述 |
|--------|------|------|
| success | bool | 取消是否成功 |
| message | string | 取消结果消息 |

**示例代码：**

```python
# 取消订单
response = client.cancel_master_order(
    masterOrderId="your-master-order-id",
    reason="用户手动取消"  # 可选的取消原因
)

if response.get('success'):
    print("订单取消成功")
else:
    print(f"订单取消失败: {response.get('message')}")

# 批量取消示例
def cancel_all_active_orders(client):
    """取消所有活跃订单"""
    orders = client.get_master_orders(status="ACTIVE")
    cancelled_count = 0
    
    for order in orders['items']:
        try:
            response = client.cancel_master_order(
                masterOrderId=order['masterOrderId'],
                reason="批量取消活跃订单"
            )
            if response.get('success'):
                cancelled_count += 1
                print(f"已取消订单: {order['masterOrderId']}")
            else:
                print(f"取消失败: {order['masterOrderId']} - {response.get('message')}")
        except Exception as e:
            print(f"取消异常: {order['masterOrderId']} - {str(e)}")
    
    print(f"\n总计取消 {cancelled_count} 个订单")
    return cancelled_count
```

#### 创建 ListenKey

创建一个随机的UUID作为ListenKey，绑定当前用户信息，有效期24小时。ListenKey用于WebSocket连接，可以实时接收用户相关的交易数据推送。

**请求参数：**

| 参数名 | 类型 | 是否必传 | 描述 |
|--------|------|----------|------|
| 无需参数 | - | - | - |

**响应字段：**

| 字段名 | 类型 | 描述 |
|--------|------|------|
| listenKey | string | 生成的ListenKey |
| expireAt | string | ListenKey过期时间戳（秒） |
| success | bool | 创建是否成功 |
| message | string | 创建结果消息 |

**示例代码：**

```python
# 创建 ListenKey
result = client.create_listen_key()

if result.get('success'):
    print(f"ListenKey创建成功:")
    print(f"ListenKey: {result['listenKey']}")
    print(f"过期时间: {result['expireAt']}")
    
    # 使用 ListenKey 建立 WebSocket 连接
    # ws_url = f"wss://api.quantumexecute.com/ws/{result['listenKey']}"
else:
    print(f"ListenKey创建失败：{result.get('message')}")
```

**注意事项：**
- ListenKey 有效期为 24 小时，过期后需要重新创建
- 每个用户同时只能有一个有效的 ListenKey
- ListenKey 用于 WebSocket 连接，可以实时接收交易数据推送
- 建议在应用启动时创建 ListenKey，并在接近过期时重新创建

## 错误处理

SDK 提供了详细的错误信息，包括 API 错误和网络错误：

```python
from qe.error import ClientError, APIError

response = client.create_master_order(
    # ... 设置参数
)

if 'error' in response:
    # 检查是否为 API 错误
    error = response['error']
    if isinstance(error, dict) and 'code' in error:
        print(f"API 错误 - 代码: {error['code']}, 原因: {error.get('reason')}, 消息: {error.get('message')}")
        print(f"TraceID: {error.get('trace_id')}")
        
        # 根据错误代码处理
        if error['code'] == 400:
            print("请求参数错误")
        elif error['code'] == 401:
            print("认证失败")
        elif error['code'] == 403:
            print("权限不足")
        elif error['code'] == 429:
            print("请求过于频繁")
        else:
            print(f"其他错误: {error}")
    else:
        print(f"网络或其他错误: {error}")
```

## 高级配置

### 自定义 HTTP 客户端

```python
import requests
import time

# 创建自定义 HTTP 客户端 注意：覆盖headers时必须添加请求头 X-MBX-APIKEY 值为api_key
session = requests.Session()
session.timeout = 30  # 30 秒超时
session.headers.update({
    "Content-Type": "application/json;charset=utf-8",
    "X-MBX-APIKEY": "your-api-key",
})

client = Client("your-api-key", "your-api-secret")
client.session = session
```

### 使用代理

```python
import requests

proxies = {
    'https': 'http://proxy.example.com:8080'
}

client = Client("your-api-key", "your-api-secret")
client.session.proxies.update(proxies)
```

### 时间偏移调整

如果遇到时间戳错误，可以调整客户端的时间偏移：

```python
# 设置时间偏移（毫秒）
client.time_offset = 1000  # 客户端时间比服务器快 1 秒
```

### 请求重试

```python
import time
import math

# 实现简单的重试逻辑
def retry_request(func, max_retries=3):
    """重试请求函数"""
    for i in range(max_retries):
        try:
            return func()
        except Exception as e:
            if i == max_retries - 1:
                raise e
            
            # 检查是否应该重试
            if hasattr(e, 'code') and 400 <= e.code < 500:
                raise e  # 不重试客户端错误
            
            # 指数退避
            wait_time = math.pow(2, i)
            print(f"请求失败，{wait_time}秒后重试...")
            time.sleep(wait_time)

# 使用重试
def create_order_with_retry():
    return client.create_master_order(
        # ... 设置参数
    )

result = retry_request(create_order_with_retry, max_retries=3)
```

## 最佳实践

### 1. API 密钥管理

```python
# 定期检查 API 密钥状态
def check_api_key_status(client):
    apis = client.list_exchange_apis()
    if not apis.get('items'):
        print("获取 API 列表失败")
        return
    
    for api in apis['items']:
        if not api['isValid']:
            print(f"警告: API {api['id']} ({api['accountName']}) 状态异常")
```

### 2. 订单监控

```python
# 监控订单执行状态
def monitor_order(client, master_order_id):
    import time
    
    while True:
        orders = client.get_master_orders(page=1, pageSize=1)
        
        if not orders['items']:
            print("订单不存在")
            return
        
        order = orders['items'][0]
        print(f"订单进度: {order['completionProgress']*100:.2f}%, 状态: {order['status']}")
        
        if order['status'] == "COMPLETED":
            print(f"订单已结束，最终状态: {order['status']}")
            return
        
        time.sleep(10)  # 每 10 秒检查一次
```

### 3. 批量处理

```python
# 批量获取所有订单
def get_all_orders(client):
    all_orders = []
    page = 1
    page_size = 100
    
    while True:
        result = client.get_master_orders(page=page, pageSize=page_size)
        all_orders.extend(result['items'])
        
        # 检查是否还有更多数据
        if len(result['items']) < page_size:
            break
        page += 1
    
    return all_orders
```

### 4. ListenKey 管理

```python
import time
from datetime import datetime

# ListenKey 管理器
class ListenKeyManager:
    def __init__(self, client):
        self.client = client
        self.listen_key = None
        self.expire_at = None
    
    def create_listen_key(self):
        """创建或刷新 ListenKey"""
        result = self.client.create_listen_key()
        
        if not result.get('success'):
            raise Exception(f"创建 ListenKey 失败: {result.get('message')}")
        
        self.listen_key = result['listenKey']
        self.expire_at = int(result['expireAt'])
        
        print(f"ListenKey 创建成功: {self.listen_key}, 过期时间: {self.expire_at}")
        return self.listen_key
    
    def is_expired(self):
        """检查 ListenKey 是否即将过期"""
        if not self.expire_at:
            return True
        # 提前1小时刷新
        return time.time() > self.expire_at - 3600
    
    def auto_refresh(self):
        """自动刷新 ListenKey"""
        if self.is_expired():
            print("ListenKey 即将过期，开始刷新...")
            self.create_listen_key()

# 使用示例
manager = ListenKeyManager(client)
listen_key = manager.create_listen_key()

# 定期检查并刷新
while True:
    manager.auto_refresh()
    time.sleep(1800)  # 每30分钟检查一次
```

### 5. WebSocket 实时数据推送

SDK 提供了完整的 WebSocket 服务，可以实时接收交易数据推送，包括主订单状态更新、子订单变化、成交明细等。

#### 创建 WebSocket 服务

```python
import logging
import time
from qe import API, WebSocketService, WebSocketEventHandlers, MasterOrderMessage, OrderMessage, FillMessage
from qe.user import User as Client

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def on_connected():
    """连接成功回调"""
    logger.info("WebSocket连接成功")

def on_disconnected():
    """断开连接回调"""
    logger.info("WebSocket连接断开")

def on_error(error):
    """错误回调"""
    logger.error(f"WebSocket错误: {error}")

def on_status(data):
    """状态消息回调"""
    logger.info(f"收到状态消息: {data}")

def on_master_order(message: MasterOrderMessage):
    """主订单消息回调"""
    logger.info(f"收到主订单消息:")
    logger.info(f"  主订单ID: {message.master_order_id}")
    logger.info(f"  客户端ID: {message.client_id}")
    logger.info(f"  策略: {message.strategy}")
    logger.info(f"  交易对: {message.symbol}")
    logger.info(f"  方向: {message.side}")
    logger.info(f"  数量: {message.qty}")
    logger.info(f"  状态: {message.status}")
    logger.info(f"  时间戳: {message.timestamp}")

def on_order(message: OrderMessage):
    """订单消息回调"""
    logger.info(f"收到订单消息:")
    logger.info(f"  主订单ID: {message.master_order_id}")
    logger.info(f"  订单ID: {message.order_id}")
    logger.info(f"  交易对: {message.symbol}")
    logger.info(f"  方向: {message.side}")
    logger.info(f"  价格: {message.price}")
    logger.info(f"  数量: {message.quantity}")
    logger.info(f"  状态: {message.status}")
    logger.info(f"  已成交数量: {message.fill_qty}")
    logger.info(f"  剩余数量: {message.quantity_remaining}")

def on_fill(message: FillMessage):
    """成交消息回调"""
    logger.info(f"收到成交消息:")
    logger.info(f"  主订单ID: {message.master_order_id}")
    logger.info(f"  订单ID: {message.order_id}")
    logger.info(f"  交易对: {message.symbol}")
    logger.info(f"  方向: {message.side}")
    logger.info(f"  成交价格: {message.fill_price}")
    logger.info(f"  成交数量: {message.filled_qty}")
    logger.info(f"  成交时间: {message.fill_time}")

def on_raw_message(message):
    """原始消息回调"""
    logger.debug(f"收到原始消息: {message.type} - {message.data}")

def main():
    """主函数"""
    # 创建API客户端
    api = Client(   #这里应该要换成Client才能运行
        api_key="your_api_key",
        api_secret="your_api_secret",
        base_url="https://test.quantumexecute.com"
    )
    
    # 创建WebSocket事件处理器
    handlers = WebSocketEventHandlers(
        on_connected=on_connected,
        on_disconnected=on_disconnected,
        on_error=on_error,
        on_status=on_status,
        on_master_order=on_master_order,
        on_order=on_order,
        on_fill=on_fill,
        on_raw_message=on_raw_message
    )
    
    # 创建WebSocket服务
    ws_service = WebSocketService(api)
    ws_service.set_handlers(handlers)
    
    # 设置连接参数
    ws_service.set_reconnect_delay(5.0)  # 重连延迟5秒
    ws_service.set_ping_interval(30.0)   # 心跳间隔30秒
    ws_service.set_pong_timeout(10.0)    # Pong超时10秒
    
    try:
        # 获取listen_key
        listen_key_result = api.create_listen_key()
        if not listen_key_result.get('success'):
            logger.error(f"创建ListenKey失败: {listen_key_result.get('message')}")
            return
        
        listen_key = listen_key_result['listenKey']
        
        # 连接WebSocket
        logger.info("正在连接WebSocket...")
        ws_service.connect(listen_key)
        
        # 等待连接建立
        time.sleep(2)
        
        if ws_service.is_connected():
            logger.info("WebSocket连接已建立，开始接收消息...")
            
            # 保持连接运行
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("收到中断信号，正在关闭连接...")
        else:
            logger.error("WebSocket连接失败")
    
    except Exception as e:
        logger.error(f"发生错误: {e}")
    
    finally:
        # 关闭WebSocket连接
        ws_service.close()
        logger.info("WebSocket连接已关闭")

if __name__ == "__main__":
    main()
```

#### 消息类型说明

**客户端推送消息类型：**

| 消息类型 | 描述 |
|----------|------|
| data | 数据消息 |
| status | 状态消息 |
| error | 错误消息 |
| master_data | 主订单数据 |
| order_data | 订单数据 |

**第三方消息类型：**

| 消息类型 | 描述 |
|----------|------|
| master_order | 主订单消息 |
| order | 子订单消息 |
| fill | 成交消息 |

#### 配置选项

```python
# 设置重连延迟
ws_service.set_reconnect_delay(10.0)  # 10秒

# 设置心跳间隔
ws_service.set_ping_interval(2.0)     # 2秒

# 设置Pong超时时间
ws_service.set_pong_timeout(15.0)     # 15秒

# 设置日志记录器
import logging
logger = logging.getLogger("websocket")
ws_service.set_logger(logger)
```

#### 连接状态管理

```python
# 检查连接状态
if ws_service.is_connected():
    print("WebSocket 已连接")
else:
    print("WebSocket 未连接")

# 手动重连
if not ws_service.is_connected():
    listen_key = "your-listen-key"
    ws_service.connect(listen_key)
```

#### 错误处理

```python
def on_error(error):
    """错误回调"""
    logger.error(f"WebSocket 错误: {error}")
    
    # 根据错误类型进行处理
    if "connection refused" in str(error).lower():
        logger.error("连接被拒绝，可能是服务器不可用")
    elif "authentication failed" in str(error).lower():
        logger.error("认证失败，请检查 ListenKey 是否有效")
    elif "timeout" in str(error).lower():
        logger.error("连接超时，请检查网络连接")
```

#### 生产环境使用建议

1. **自动重连机制**：SDK 已内置自动重连功能，无需手动实现
2. **ListenKey 管理**：定期检查 ListenKey 有效性，接近过期时主动刷新
3. **错误监控**：实现完善的错误日志记录和监控
4. **负载均衡**：考虑使用多个 WebSocket 连接分散负载
5. **消息去重**：根据 `messageId` 实现消息去重处理

#### 高级用法示例

```python
class TradingBot:
    def __init__(self, api_key, api_secret):
        self.api = API(api_key, api_secret)
        self.ws_service = None
        self.listen_key = None
        
    def start_websocket(self):
        """启动WebSocket连接"""
        # 创建ListenKey
        result = self.api.create_listen_key()
        if not result.get('success'):
            raise Exception(f"创建ListenKey失败: {result.get('message')}")
        
        self.listen_key = result['listenKey']
        
        # 创建事件处理器
        handlers = WebSocketEventHandlers(
            on_connected=self._on_connected,
            on_disconnected=self._on_disconnected,
            on_error=self._on_error,
            on_master_order=self._on_master_order,
            on_order=self._on_order,
            on_fill=self._on_fill
        )
        
        # 创建WebSocket服务
        self.ws_service = WebSocketService(self.api)
        self.ws_service.set_handlers(handlers)
        
        # 连接
        self.ws_service.connect(self.listen_key)
        
    def _on_connected(self):
        print("交易机器人已连接")
        
    def _on_disconnected(self):
        print("交易机器人连接断开")
        
    def _on_error(self, error):
        print(f"交易机器人错误: {error}")
        
    def _on_master_order(self, message):
        print(f"主订单更新: {message.master_order_id} - {message.status}")
        
    def _on_order(self, message):
        print(f"子订单更新: {message.order_id} - {message.status}")
        
    def _on_fill(self, message):
        print(f"成交通知: {message.order_id} - {message.filled_qty} @ {message.fill_price}")
        
    def stop(self):
        """停止WebSocket连接"""
        if self.ws_service:
            self.ws_service.close()

# 使用示例
bot = TradingBot("your-api-key", "your-api-secret")
bot.start_websocket()

# 保持运行
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("正在停止...")
    bot.stop()
```

## 常见问题

### 1. 如何获取 API 密钥？

请登录 Quantum Execute 平台，在用户设置中创建 API 密钥。

### 2. 如何处理时间格式？

时间格式使用 ISO 8601 标准，例如：
- UTC 时间：`2024-01-01T10:00:00Z`
- 带时区：`2024-01-01T18:00:00+08:00`

### 3. 订单类型说明

- **TWAP (Time Weighted Average Price)**：时间加权平均价格算法，在指定时间段内平均分配订单
- **VWAP (Volume Weighted Average Price)**：成交量加权平均价格算法，根据市场成交量分布执行订单
- **POV (Percentage of Volume)**：成交量百分比算法，保持占市场成交量的固定比例

### 4. 枚举值说明

**算法类型 (Algorithm)：**

| 枚举值 | 描述 |
|--------|------|
| TWAP | TWAP算法 |
| VWAP | VWAP算法 |
| POV | POV算法 |
| BoostVWAP | BoostVWAP算法（高频alpha发单） |
| BoostTWAP | BoostTWAP算法（高频alpha发单） |

**市场类型 (MarketType)：**

| 枚举值 | 描述 |
|--------|------|
| SPOT | 现货市场 |
| PERP | 合约市场 |

**订单方向 (OrderSide)：**

| 枚举值 | 描述 |
|--------|------|
| buy | 买入 |
| sell | 卖出 |

**交易所 (Exchange)：**

| 枚举值 | 描述 |
|--------|------|
| Binance | 币安 |
| OKX | OKX |
| LTP | LTP |
| Deribit | Deribit |

**保证金类型 (MarginType)：**

| 枚举值 | 描述 |
|--------|------|
| U | U本位 |

**母单状态 (MasterOrderStatus)：**

| 枚举值 | 描述 |
|--------|------|
| NEW | 执行中 |
| COMPLETED | 已完成 |

**交易对市场类型 (TradingPairMarketType)：**

| 枚举值 | 描述 |
|--------|------|
| SPOT | 现货品种 |
| FUTURES | 期货品种 |

### 5. 公共接口使用说明

**Status 接口（无需认证）：**
- `ping()`: 测试服务器连通性
- `timestamp()`: 获取服务器时间戳

**Pub 接口（无需认证）：**
- `trading_pairs()`: 获取交易对列表，支持各种筛选条件

**User 接口（需要认证）：**
- 所有交易相关功能都需要有效的 API 密钥

### 6. 枚举类型使用建议

推荐使用枚举类型而不是字符串，这样可以获得：
- 类型安全：编译时检查参数正确性
- 代码提示：IDE 可以提供自动补全
- 避免拼写错误：减少因字符串拼写错误导致的错误

```python
# 推荐使用枚举
from qe.lib import TradingPairMarketType

# 使用枚举
pairs = pub_client.trading_pairs(marketType=TradingPairMarketType.SPOT)

# 不推荐使用字符串
pairs = pub_client.trading_pairs(marketType="SPOT")
```

### 7. WebSocket 相关说明

**WebSocket 连接地址：**
- `wss://test.quantumexecute.com/api/ws?listen_key={listenKey}`

**支持的消息类型：**
- 主订单状态更新（`master_order`）
- 子订单变化（`order`）
- 成交明细（`fill`）
- 系统状态消息（`status`）
- 错误消息（`error`）

**连接管理：**
- SDK 自动处理心跳检测和重连
- 支持自定义重连延迟、心跳间隔等参数
- 提供连接状态查询接口

**消息处理：**
- 支持结构化消息解析
- 提供原始消息访问接口
- 支持自定义错误处理逻辑

**性能优化建议：**
- 避免在消息处理器中执行耗时操作
- 使用异步处理消息，避免阻塞主连接
- 合理设置心跳参数，平衡实时性和资源消耗

**WebSocket 使用示例：**

```python
from qe import API, WebSocketService, WebSocketEventHandlers

# 创建API客户端
api = API("your-api-key", "your-api-secret")

# 创建WebSocket服务
ws_service = WebSocketService(api)

# 设置事件处理器
handlers = WebSocketEventHandlers(
    on_connected=lambda: print("连接成功"),
    on_disconnected=lambda: print("连接断开"),
    on_error=lambda e: print(f"错误: {e}"),
    on_master_order=lambda msg: print(f"主订单: {msg.master_order_id}"),
    on_order=lambda msg: print(f"子订单: {msg.order_id}"),
    on_fill=lambda msg: print(f"成交: {msg.filled_qty}")
)

ws_service.set_handlers(handlers)

# 获取ListenKey并连接
listen_key = api.create_listen_key()['listenKey']
ws_service.connect(listen_key)

# 保持连接
import time
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ws_service.close()
```

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 联系我们

- 官网：[https://test.quantumexecute.com](https://test.quantumexecute.com)
- 邮箱：support@quantumexecute.com
- GitHub：[https://github.com/Quantum-Execute/qe-connector-python](https://github.com/Quantum-Execute/qe-connector-python)