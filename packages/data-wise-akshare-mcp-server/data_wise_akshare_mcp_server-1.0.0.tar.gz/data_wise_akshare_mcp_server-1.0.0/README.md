# AkShare MCP Server

提供 AkShare 金融数据接口的 MCP 服务。

## 功能特性

- 🔍 获取所有可用的 AkShare 函数列表
- 📖 查看函数详细信息（参数、文档等）
- 🚀 通用函数执行接口
- 💰 支持股票、基金、期货、宏观经济等数据

## 安装

```bash
pip install data-wise-akshare-mcp-server
```

## 使用方法

### 作为 MCP 服务器运行

```bash
uvx data-wise-akshare-mcp-server
```

### 在 Kiro 中配置

在 `.kiro/settings/mcp.json` 中添加：

```json
{
  "mcpServers": {
    "akshare": {
      "command": "uvx",
      "args": ["data-wise-akshare-mcp-server"]
    }
  }
}
```

## 可用工具

### 1. list_functions - 获取函数列表

获取所有可用的 AkShare 函数及其参数信息。

**参数：**
- `keyword` (可选): 关键词过滤
- `limit` (可选): 返回数量限制，默认100

**示例：**
```json
{
  "keyword": "stock",
  "limit": 50
}
```

### 2. get_function_detail - 获取函数详情

获取指定函数的详细信息，包括完整文档和参数列表。

**参数：**
- `function_name` (必需): 函数名

**示例：**
```json
{
  "function_name": "stock_zh_a_hist"
}
```

### 3. execute_function - 执行函数

执行指定的 AkShare 函数并返回数据。

**参数：**
- `function_name` (必需): 函数名
- `params` (可选): 函数参数字典

**示例：**
```json
{
  "function_name": "stock_zh_a_hist",
  "params": {
    "symbol": "000001",
    "period": "daily",
    "start_date": "20240101",
    "end_date": "20241231"
  }
}
```

## 使用流程

1. 使用 `list_functions` 查找需要的函数
2. 使用 `get_function_detail` 查看函数参数
3. 使用 `execute_function` 执行函数获取数据

## 常用函数示例

### 股票数据
- `stock_zh_a_spot_em`: A股实时行情
- `stock_zh_a_hist`: A股历史行情
- `stock_zh_a_daily`: A股日线数据

### 基金数据
- `fund_open_fund_info_em`: 开放式基金信息
- `fund_etf_spot_em`: ETF实时行情

### 期货数据
- `futures_main_sina`: 期货主力合约
- `futures_zh_spot`: 期货实时行情

### 宏观经济
- `macro_china_cpi`: 中国CPI数据
- `macro_china_ppi`: 中国PPI数据
- `macro_china_gdp`: 中国GDP数据

## 依赖

- fastmcp >= 2.14.1
- akshare >= 1.14.0

## 许可证

MIT License
