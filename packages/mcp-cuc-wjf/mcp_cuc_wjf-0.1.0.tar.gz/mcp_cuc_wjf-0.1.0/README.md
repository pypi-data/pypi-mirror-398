# MCP Time Server

基于 Model Context Protocol (MCP) 的时间服务，提供获取当前时间的工具函数，支持时区参数。

## 功能特性

- 提供获取当前时间的工具函数
- 支持时区参数（如 "Asia/Shanghai"、"America/New_York"）
- 符合 MCP 协议规范
- 简单易用的 API
- 支持多种传输方式

## 安装

使用 pip 安装：

```bash
pip install mcp-time-server
```

## 使用方法

### 作为 MCP 服务器运行

可以直接运行模块：

```bash
python -m mcp_time_server
```

或者使用命令行脚本：

```bash
mcp-time-server
```

### 在代码中使用

```python
from mcp_time_server import run_server

# 启动 MCP 服务器
run_server(transport="sse")
```

## API 文档

### 工具函数

#### get_current_time(timezone: Optional[str] = None) -> str

获取当前时间的工具函数

- **参数**: `timezone` - 可选，时区字符串，例如 "Asia/Shanghai"、"America/New_York"
- **返回**: 格式化的当前时间字符串（格式：YYYY-MM-DD HH:MM:SS.SSSSSS 时区名称）
- **示例**:
  ```python
  # 获取当前时间（系统默认时区）
  get_current_time()  # 返回类似 "2025-12-26 19:30:45.123456 CST"
  
  # 获取上海时区的当前时间
  get_current_time(timezone="Asia/Shanghai")  # 返回类似 "2025-12-26 19:30:45.123456 CST"
  
  # 获取纽约时区的当前时间
  get_current_time(timezone="America/New_York")  # 返回类似 "2025-12-26 06:30:45.123456 EST"
  ```

### 服务器函数

#### run_server(transport: str = "sse") -> None

启动 MCP 服务器

- **参数**: `transport` - 可选，传输方式，默认为 "sse" (Server-Sent Events)
- **支持的传输方式**:
  - "sse": Server-Sent Events
  - "stdio": 标准输入输出（适用于本地进程间通信）
  - "websocket": WebSocket

## 依赖项

- `fastmcp`: 用于实现 MCP 协议
- `pytz`: 用于时区处理

## 许可证

MIT License

## 贡献

欢迎提交 Issues 和 Pull Requests！

## 联系方式

- 作者: Your Name
- 邮箱: your.email@example.com
- GitHub: [https://github.com/yourusername/mcp-time-server](https://github.com/yourusername/mcp-time-server)
