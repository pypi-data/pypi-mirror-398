# Time Server Package

一个提供JSON-RPC接口的时间服务器Python包，支持获取不同时区的当前时间。

## 功能特性

- 提供`tools/get_current_time` JSON-RPC方法
- 支持指定时区获取时间
- 基于FastAPI框架构建
- 包含命令行入口点

## 安装

```bash
pip install time-server-pkg
```

## 使用方法

### 作为命令行工具运行

```bash
time-server
```

### 作为Python模块导入

```python
from time_server_pkg import app, get_current_time

# 获取当前时间
print(get_current_time())

# 获取指定时区的时间
print(get_current_time("Asia/Shanghai"))
```

## API接口

服务器默认在`http://localhost:8000`启动，提供以下JSON-RPC方法：

### tools/get_current_time

获取当前时间，可选参数：

- `timezone`: 时区字符串，例如`"Asia/Shanghai"`, `"America/New_York"`等

示例请求：
```json
{
  "jsonrpc": "2.0",
  "method": "tools/get_current_time",
  "params": {"timezone": "Asia/Shanghai"},
  "id": 1
}
```

示例响应：
```json
{
  "jsonrpc": "2.0",
  "result": "2023-11-15 14:30:45 CST",
  "id": 1
}
```

## 技术栈

- Python 3.7+
- FastAPI
- Uvicorn
- pytz

## 许可证

MIT License
