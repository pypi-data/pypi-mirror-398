# MCP时间服务器

一个基于MCP（Model Context Protocol）协议的时间服务器，提供获取当前时间的工具。

## 功能特性

- 支持多种传输协议：stdio、streamable-http、sse
- 支持时区参数，可获取不同时区的当前时间
- 提供命令行接口，方便配置和启动
- 基于MCP协议，可与AI模型无缝集成

## 安装

使用pip安装：

```bash
pip install mcp_time_server
```

## 使用方法

### 启动服务器

#### 1. 使用stdio传输方式

```bash
mcp-time-server --transport stdio
```

#### 2. 使用streamable-http传输方式

```bash
mcp-time-server --transport streamable-http --port 8000
```

#### 3. 使用sse传输方式

```bash
mcp-time-server --transport sse --port 8000
```

### 使用工具

服务器提供`get_current_time`工具，可通过MCP协议调用。

#### 参数

- `timezone` (可选)：时区字符串，例如 "Asia/Shanghai"、"America/New_York"

#### 示例请求

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "call_tool",
  "params": {
    "name": "get_current_time",
    "params": {
      "timezone": "Asia/Shanghai"
    }
  }
}
```

#### 示例响应

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": "2025-12-28 12:30:45.123456 CST"
}
```

## 开发

### 克隆仓库

```bash
git clone https://github.com/bdc/mcp_time_server.git
cd mcp_time_server
```

### 安装依赖

```bash
pip install -e .
```

### 运行测试

```bash
python -m pytest
```

## 许可证

MIT License
