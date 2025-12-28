# AICP Helper SDK

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

AICP Helper SDK 是 AI Cloud Platform (AICP) 的公共 Python SDK，用于简化微服务项目的开发。该库提供了统一的配置管理、监控和其他公共工具功能，旨在减少冗余代码，提高开发效率。

## ✨ 功能特性

- **🔧 统一配置管理**: 从中央配置服务器获取配置，并通过 Redis pub/sub 机制监听配置变更
- **⚡ 实时配置更新**: 自动监听配置变更并实时更新应用配置
- **🔄 重试机制**: 内置配置获取失败重试逻辑，提高系统稳定性
- **🎨 自定义配置支持**: 支持合并自定义配置与远程配置
- **🔔 回调通知**: 配置更新时支持自定义回调函数
- **🏗️ 建造者模式**: 提供流畅的API设计，简化配置过程

## 📦 安装

### 从源码安装

```bash
git clone <repository-url>
cd aicp-helper
pip install -r requirements.txt
pip install .
```

### 开发模式安装

```bash
pip install -e .
```

### 使用 pip 直接安装

```bash
pip install aicp-helper
```

## 🚀 快速开始

### 基本用法

```python
from aicp_helper.helper import HelperConfigBuilder

# 使用建造者模式创建 helper
helper = HelperConfigBuilder().svc("model").config_server("http://your-server:8000").create_helper()

# 初始化并监听配置变更（可选自定义配置和回调函数）
config = helper.init_and_watch_config(
    custom_config={"key": "value"},
    callback=lambda new_config: print("配置已更新:", new_config)
)

# 使用配置
print(config.get('database_host'))
```

### 高级用法

```python
import logging
from aicp_helper.helper import HelperConfigBuilder

# 配置日志器
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 创建带完整配置的 helper
helper = HelperConfigBuilder()
    .svc("maas")
    .config_server("http://config-server:8000")
    .logger(logger)
    .create_helper()


# 自定义配置更新回调
def on_config_update(new_config):
    logger.info(f"配置已更新: {new_config}")
    # 在这里处理配置更新逻辑


# 初始化配置
config = helper.init_and_watch_config(
    custom_config={"app_name": "my-service"},
    callback=on_config_update
)

# 使用配置
db_host = config.get('database_host')
api_key = config.get('api_key')
```

## 📚 支持的服务类型

| 服务类型 | 描述 |
|---------|------|
| `aicp` | AICP 核心服务 |
| `maas` | 模型即服务 |
| `model` | 模型服务 |
| `docker` | Docker 服务 |
| `epfs` | 弹性文件系统服务 |

## 🏛️ 项目结构

```
aicp-helper/
├── src/
│   ├── __init__.py
│   ├── const.py              # 常量定义
│   ├── helper.py             # 核心辅助类和建造者模式
│   └── aicp_config/
│       ├── __init__.py       # 配置管理实现
├── test/                     # 测试文件
├── requirements.txt          # 依赖包列表
├── setup.py                 # 包安装配置
└── README.md                # 项目文档
```

## 🔧 核心模块

### HelperConfigBuilder
使用建造者模式创建 HelperConfig：

```python
from aicp_helper.helper import HelperConfigBuilder

config = (HelperConfigBuilder()
          .svc("maas")  # 设置服务类型
          .config_server("http://server:8000")  # 设置配置服务器
          .logger(logger)  # 设置日志器
          .create_helper())  # 创建 Helper 实例
```

### AicpConfig
配置管理核心类，负责：
- 从 HTTP 端点获取配置
- 通过 Redis 监听配置变更
- 处理配置合并和缓存
- 支持重试逻辑和错误处理

## 🔑 环境变量

| 变量名 | 必需 | 描述 |
|--------|------|------|
| `Authorization` | 是 | 授权头，用于访问配置服务器 |

## 📋 依赖项

- `httpx~=0.27.0` - HTTP 客户端，用于获取配置
- `redis~=5.0.1` - Redis 客户端，用于 pub/sub 通知
- `cachetools~=5.3.2` - 缓存工具
- `pydash~=8.0.3` - 实用工具函数

## 🧪 开发

### 运行测试

```bash
python -m unittest test/aicp_config.py
```

### 安装开发依赖

```bash
pip install -r requirements.txt
```

### 代码规范

该项目遵循 PEP 8 代码规范，建议使用以下工具：

```bash
# 代码格式化
black aicp_helper/ test/

# 代码检查
flake8 aicp_helper/ test/

# 类型检查
mypy aicp_helper/
```

## 🔧 配置服务器

SDK 默认期望：
- 配置服务器 URL: `http://config-server-service.aicp-system:8000`
- Redis 连接信息从配置服务器获取
- 授权头通过环境变量 `Authorization` 设置

## 🤝 贡献指南

我们欢迎所有形式的贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## ❓ 常见问题

### Q: 如何处理配置服务器连接失败？
**A**: SDK 内置了重试机制，默认重试 10 次，每次间隔 2 秒。如果仍然失败，会抛出异常。

### Q: 配置更新是实时的吗？
**A**: 是的，通过 Redis pub/sub 机制实现实时配置更新。当配置服务器发布更新通知时，所有连接的服务都会立即收到并更新配置。

### Q: 如何调试配置加载问题？
**A**: 可以设置日志级别为 DEBUG 或 INFO，SDK 会输出详细的配置加载和监听日志。

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Q: 支持哪些配置格式？
**A**: SDK 支持 JSON 格式的配置，并可以与 Python 字典无缝集成。

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系我们

- **维护者**: syw@coreshub.cn
- **团队**: AICP Team
- **邮箱**: aicp-team@coreshub.cn

## 🗺️ 路线图

- [ ] 添加更多服务类型支持
- [ ] 支持配置版本管理
- [ ] 添加配置变更历史记录
- [ ] 支持配置模板和继承
- [ ] 添加配置验证机制

---

**AICP Helper SDK** - 让 AICP 微服务开发更简单！ 🚀