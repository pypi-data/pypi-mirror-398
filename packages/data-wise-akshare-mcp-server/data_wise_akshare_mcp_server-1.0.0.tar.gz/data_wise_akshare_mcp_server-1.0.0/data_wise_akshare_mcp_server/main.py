"""
AkShare MCP Server
提供 AkShare 金融数据接口的 MCP 服务
"""

from __future__ import annotations

import json
from typing import Any, Dict
from fastmcp import FastMCP
from pydantic import BaseModel, Field

# 导入扫描器和执行器
try:
    from .scanner import scan_akshare_functions, get_function_info
    from .executor import AkShareExecutor
except ImportError:
    from scanner import scan_akshare_functions, get_function_info
    from executor import AkShareExecutor


# 创建 FastMCP 实例
mcp = FastMCP("AkShare MCP Server")


class FunctionListRequest(BaseModel):
    """函数列表查询请求"""
    keyword: str = Field(default=None, description="关键词过滤（可选）")
    limit: int = Field(default=100, description="返回数量限制，默认100")


class FunctionInfoRequest(BaseModel):
    """函数信息查询请求"""
    function_name: str = Field(..., description="函数名")


class ExecuteFunctionRequest(BaseModel):
    """执行函数请求"""
    function_name: str = Field(..., description="函数名")
    params: Dict[str, Any] = Field(default_factory=dict, description="函数参数")


# 初始化执行器
executor = AkShareExecutor()


@mcp.tool()
def list_functions(request: FunctionListRequest) -> str:
    """
    获取 AkShare 可用函数列表
    
    返回所有可用的 AkShare 函数及其参数信息。
    可以通过 keyword 参数过滤函数名。
    
    常见函数示例：
    - stock_zh_a_spot_em: A股实时行情
    - stock_zh_a_hist: A股历史行情
    - fund_open_fund_info_em: 开放式基金信息
    - macro_china_cpi: 中国CPI数据
    - futures_main_sina: 期货主力合约
    
    Args:
        request: 查询请求
        
    Returns:
        JSON格式的函数列表
    """
    try:
        functions = scan_akshare_functions()
        
        # 关键词过滤
        if request.keyword:
            keyword_lower = request.keyword.lower()
            functions = [
                f for f in functions 
                if keyword_lower in f['name'].lower() or keyword_lower in f['doc'].lower()
            ]
        
        # 限制返回数量
        if request.limit:
            functions = functions[:request.limit]
        
        response = {
            "success": True,
            "functions": functions,
            "total": len(functions),
            "keyword": request.keyword
        }
        return json.dumps(response, ensure_ascii=False, indent=2)
    except Exception as e:
        error_response = {
            "success": False,
            "error": str(e),
            "data": None
        }
        return json.dumps(error_response, ensure_ascii=False, indent=2)


@mcp.tool()
def get_function_detail(request: FunctionInfoRequest) -> str:
    """
    获取指定函数的详细信息
    
    返回函数的完整文档、参数列表、参数类型等详细信息。
    
    Args:
        request: 包含函数名的请求
        
    Returns:
        JSON格式的函数详细信息
    """
    try:
        info = get_function_info(request.function_name)
        
        response = {
            "success": True,
            "function_info": info
        }
        return json.dumps(response, ensure_ascii=False, indent=2)
    except Exception as e:
        error_response = {
            "success": False,
            "error": str(e),
            "data": None
        }
        return json.dumps(error_response, ensure_ascii=False, indent=2)


@mcp.tool()
def execute_function(request: ExecuteFunctionRequest) -> str:
    """
    执行 AkShare 函数
    
    调用指定的 AkShare 函数并返回结果。
    
    使用步骤：
    1. 使用 list_functions 查找需要的函数
    2. 使用 get_function_detail 查看函数参数
    3. 使用 execute_function 执行函数获取数据
    
    示例：
    - 获取A股实时行情：function_name="stock_zh_a_spot_em", params={}
    - 获取股票历史：function_name="stock_zh_a_hist", params={"symbol": "000001", "period": "daily"}
    
    Args:
        request: 包含函数名和参数的请求
        
    Returns:
        JSON格式的执行结果
    """
    try:
        result = executor.execute_function(
            function_name=request.function_name,
            params=request.params
        )
        
        response = {
            "success": True,
            "data": result,
            "count": len(result),
            "function": request.function_name,
            "params": request.params
        }
        return json.dumps(response, ensure_ascii=False, indent=2)
    except Exception as e:
        error_response = {
            "success": False,
            "error": str(e),
            "data": None
        }
        return json.dumps(error_response, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run()


def main():
    """命令行入口点函数"""
    mcp.run()
