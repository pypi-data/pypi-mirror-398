# Rocket Logger

生产级 Python 日志库，开箱即用，支持多环境配置和灵活的自定义覆盖。

## 特性

- 🚀 **开箱即用**：预配置 dev/test/prod 三个环境
- 🎯 **零配置启动**：安装后直接 `get_logger(env="prod")`
- 🔧 **灵活覆盖**：支持自定义配置文件增量覆盖
- 📦 **配置内置**：配置文件打包在库中，无需用户准备
- 🎨 **彩色输出**：开发环境支持彩色日志
- 🔄 **自动轮转**：支持按时间和按大小轮转
- ✅ **类型安全**：基于 Pydantic 的配置验证

## 快速开始

### 安装

```bash
pip install jsrocket
```

### 基础使用

```python
from rocket.logger import get_logger

# 开发环境（DEBUG 级别，彩色输出）
logger = get_logger(env="dev")
logger.debug("调试信息")
logger.info("信息日志")

# 测试环境（INFO 级别）
logger = get_logger(env="test")
logger.info("测试执行")

# 生产环境（ERROR 级别，无控制台输出）
logger = get_logger(env="prod")
logger.error("生产错误")
logger.critical("严重问题")
```

## 环境配置

### Dev 环境（开发）
- 日志级别：DEBUG
- 控制台输出：彩色日志
- 文件路径：`logs/dev/app.log`
- 日志轮转：每天午夜，保留 7 天

### Test 环境（测试）
- 日志级别：INFO
- 控制台输出：启用
- 文件路径：`logs/test/app.log`
- 日志轮转：每天午夜，保留 3 天

### Production 环境（生产）
- 日志级别：ERROR
- 控制台输出：关闭
- 文件路径：`logs/prod/app.log`
- 日志轮转：每天午夜，保留 30 天

## 自定义配置

创建自定义配置文件，只需包含要覆盖的字段：

```yaml
# my_config.yaml
logger:
  level: "WARNING"  # 只改日志级别
  handlers:
    file_path: "/var/log/myapp/app.log"  # 只改路径
  # 其他字段保持环境默认值
```

使用自定义配置：

```python
logger = get_logger(
    env="prod",
    config_file="/etc/myapp/logging.yaml"
)
```

## 高级用法

### 环境变量控制

```python
import os

env = os.getenv("APP_ENV", "dev")
logger = get_logger(env=env)
```

### Docker 部署

```dockerfile
# Dockerfile
ENV APP_ENV=prod
COPY logging.yaml /etc/myapp/logging.yaml
```

```python
# 应用代码
import os
logger = get_logger(
    env=os.getenv("APP_ENV", "prod"),
    config_file="/etc/myapp/logging.yaml"
)
```

### Kubernetes ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-logging
data:
  logging.yaml: |
    logger:
      handlers:
        file_path: "/var/log/app/app.log"
      rotation:
        backup_count: 90
```

```python
# 应用代码
logger = get_logger(
    env="prod",
    config_file="/etc/config/logging.yaml"
)
```

## 配置选项

### 完整配置示例

```yaml
logger:
  name: "my-app"
  level: "INFO"  # DEBUG/INFO/WARNING/ERROR/CRITICAL
  encoding: "utf-8"
  
  handlers:
    console: true
    file: true
    file_path: "logs/app.log"
  
  rotation:
    type: "time"  # time 或 size
    when: "midnight"  # 时间轮转触发时机
    interval: 1
    backup_count: 30
    max_size: "100MB"  # 按大小轮转时的上限
  
  format:
    console: "%(asctime)s - %(levelname)s - %(message)s"
    file: "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    json: false  # JSON 格式输出
```

### 按大小轮转

```yaml
logger:
  rotation:
    type: "size"
    max_size: "500MB"
    backup_count: 50
```

### JSON 格式输出

```yaml
logger:
  format:
    json: true
```

## 最佳实践

### 1. 开发环境
```python
# 本地开发使用 dev 环境
logger = get_logger(env="dev")
```

### 2. 测试环境
```python
# CI/CD 中使用 test 环境
logger = get_logger(env="test")
```

### 3. 生产环境
```python
# 生产部署使用 prod + 自定义配置
logger = get_logger(
    env="prod",
    config_file="/etc/myapp/logging.yaml"
)
```

### 4. 最小化自定义配置
只包含需要修改的字段，其他使用环境默认值：

```yaml
# 最小配置示例
logger:
  handlers:
    file_path: "/custom/path/app.log"
```

## 文档

详细配置说明请参考：[CONFIG_USAGE.md](docs/CONFIG_USAGE.md)

## 依赖

- Python >= 3.13
- PyYAML >= 6.0.0
- Pydantic >= 2.0.0

## 许可

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
