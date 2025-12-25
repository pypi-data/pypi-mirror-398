# ctplite

Python SDK for CTPLite. 提供 gRPC 和 REST 两种客户端接口，方便开发人员在其他 Python 项目中使用。

## 安装

```bash
pip install ctplite
```

## 包结构设计

```text
sdk/
├── ctplite/
│   ├── __init__.py              # 包初始化，导出主要类
│   ├── config.py                # 配置管理（从 examples/python/config.py 重构）
│   ├── grpc_client.py           # gRPC 客户端（从 examples/python/grpc_client.py 重构）
│   ├── rest_client.py           # REST 客户端（从 examples/python/rest_client.py 重构）
│   └── proto/                   # protobuf 生成的代码
│       ├── __init__.py
│       ├── common_pb2.py
│       ├── common_pb2_grpc.py
│       ├── auth_pb2.py
│       ├── auth_pb2_grpc.py
│       ├── market_data_pb2.py
│       ├── market_data_pb2_grpc.py
│       ├── trading_pb2.py
│       └── trading_pb2_grpc.py
├── setup.py                      # 包安装配置（使用 setuptools）
├── pyproject.toml                # 现代 Python 包配置
├── MANIFEST.in                   # 包含额外文件
├── README.md                     # 包说明文档
├── LICENSE                       # 许可证文件
└── requirements.txt              # 依赖列表（用于开发）
```

## 快速开始

### 使用 gRPC 客户端

```python
from ctplite import GrpcClient, config

# 配置（通过环境变量或直接设置）
config.CTP_BROKER_ID = "9999"
config.CTP_USER_ID = "your_user_id"
config.CTP_PASSWORD = "your_password"

# 创建客户端并连接
client = GrpcClient()
client.connect()

# 登录（可选，如果使用token认证）
client.login()

# 订阅行情
for stream_msg in client.subscribe_market_data(['IF2512', 'IF2601']):
    if stream_msg.error_code == 0:
        tick = stream_msg.tick
        print(f"{tick.symbol}: {tick.last_price}")

# 查询持仓
position_resp = client.query_position()
print(f"持仓数量: {len(position_resp.positions)}")

# 关闭连接
client.close()
```

### 使用 REST 客户端

```python
from ctplite import RestClient, config

# 配置
config.CTP_BROKER_ID = "9999"
config.CTP_USER_ID = "your_user_id"
config.CTP_PASSWORD = "your_password"

# 创建客户端
client = RestClient()

# 登录
result = client.login()
print(f"登录成功: {result['success']}")

# 订阅行情
result = client.subscribe_market_data(['IF2512', 'IF2601'])
print(f"订阅成功: {result['success']}")

# 查询持仓
result = client.query_position()
print(f"持仓: {result['data']}")

# 登出
client.logout()
```

## 配置

### 环境变量配置

可以通过环境变量配置连接信息和认证信息：

```bash
export CTPLITE_GRPC_HOST=localhost
export CTPLITE_GRPC_PORT=50051
export CTPLITE_REST_HOST=localhost
export CTPLITE_REST_PORT=8080
export CTP_BROKER_ID=9999
export CTP_USER_ID=your_user_id
export CTP_PASSWORD=your_password
export CTPLITE_TOKEN=your_token  # 如果使用token认证
```

### 代码配置

```python
from ctplite import config

# gRPC 配置
config.GRPC_HOST = "localhost"
config.GRPC_PORT = 50051

# REST 配置
config.REST_HOST = "localhost"
config.REST_PORT = 8080

# CTP 认证信息
config.CTP_BROKER_ID = "9999"
config.CTP_USER_ID = "your_user_id"
config.CTP_PASSWORD = "your_password"
config.CTP_APP_ID = "simnow_client_test"  # 可选
config.CTP_AUTH_CODE = "0000000000000000"  # 可选
config.CTP_INVESTOR_ID = "244753"  # 可选

# Token 认证（如果已登录）
config.TOKEN = "your_token"
```

## 功能特性

### gRPC 客户端

- 认证服务：登录、登出、刷新token
- 行情服务：订阅/取消订阅行情数据（流式）
- 交易服务：
  - 下单、撤单
  - 查询持仓、资金账户、订单、成交
  - 流式接收订单状态更新
  - 查询合约信息、保证金率、手续费率
  - 结算确认、查询结算信息
  - 查询交易所、投资者信息
  - 查询最大报单量

### REST 客户端

- 认证服务：登录、登出
- 行情服务：订阅/取消订阅行情数据（支持Kafka topic）
- 交易服务：与 gRPC 客户端相同的功能，通过 REST API 调用

## API 文档

详细的 API 文档请参考：

- [gRPC 客户端 API](docs/grpc_client.md)
- [REST 客户端 API](docs/rest_client.md)

## 依赖

- Python >= 3.8
- grpcio >= 1.70.0
- grpcio-tools >= 1.70.0
- protobuf >= 5.29.5
- requests >= 2.31.0

## 许可证

MIT License

## 打包和发布

### 前置准备

1. **安装构建工具**：

```bash
pip install build twine
```

2. **注册 PyPI 账户**：
   - 访问 [PyPI](https://pypi.org/) 注册账户
   - 如需发布到测试仓库，访问 [TestPyPI](https://test.pypi.org/) 注册账户

3. **配置认证信息**（可选）：
   - 创建 `~/.pypirc` 文件配置 PyPI 凭证
   - 或使用环境变量 `TWINE_USERNAME` 和 `TWINE_PASSWORD`

### 本地开发安装

在开发过程中，可以使用可编辑模式安装包：

```bash
cd sdk
pip install -e .
```

### 构建分发包

在 `sdk/` 目录下执行：

```bash
# 清理之前的构建文件
rm -rf dist/ build/ *.egg-info

# 构建源码分发包和 wheel 包
python setup.py sdist build
```

构建完成后，会在 `dist/` 目录下生成：

- `ctplite-x.x.x.tar.gz` - 源码分发包
- `ctplite-x.x.x-py3-none-any.whl` - wheel 分发包


### 发布到 PyPI
发布到正式 PyPI：

```bash
# 上传到 PyPI
twine upload dist/*.tar.gz
```

### 版本管理

发布新版本前，需要更新版本号：

1. **更新 `setup.py` 或 `pyproject.toml` 中的版本号**
2. **更新 `ctplite/__init__.py` 中的 `__version__`**
3. **提交版本变更**：

```bash
git add .
git commit -m "Bump version to x.x.x"
git tag vx.x.x
git push origin main --tags
```

### 发布检查清单

- [ ] 更新版本号
- [ ] 更新 CHANGELOG（如有）
- [ ] 构建分发包并本地测试安装
- [ ] 发布到正式 PyPI

## 贡献

欢迎提交 Issue 和 Pull Request。

## 联系方式

如有问题，请通过 GitHub Issues 联系。
