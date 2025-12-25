"""
AkShare 接口扫描器
"""

from __future__ import annotations

import inspect
from typing import Dict, Any, List


def scan_akshare_functions() -> List[Dict[str, Any]]:
    """
    扫描 AkShare 所有可用的函数接口
    
    Returns:
        函数列表，每个包含函数名、参数、文档等信息
    """
    try:
        import akshare as ak
    except ImportError:
        raise ImportError("请先安装 akshare: pip install akshare")
    
    functions = []
    
    for name in dir(ak):
        # 跳过私有方法和特殊属性
        if name.startswith('_'):
            continue
        
        obj = getattr(ak, name)
        
        # 只处理可调用对象
        if not callable(obj):
            continue
        
        try:
            # 获取函数签名
            sig = inspect.signature(obj)
            
            # 解析参数
            params = []
            for param_name, param in sig.parameters.items():
                if param_name in ('self', 'cls'):
                    continue
                
                param_info = {
                    "name": param_name,
                    "required": param.default is inspect.Parameter.empty,
                    "default": None if param.default is inspect.Parameter.empty else str(param.default)
                }
                params.append(param_info)
            
            # 获取文档字符串
            doc = inspect.getdoc(obj) or ""
            
            functions.append({
                "name": name,
                "params": params,
                "doc": doc[:200] if doc else "无文档说明"  # 限制文档长度
            })
            
        except Exception:
            # 跳过无法解析的函数
            continue
    
    return functions


def get_function_info(function_name: str) -> Dict[str, Any]:
    """
    获取指定函数的详细信息
    
    Args:
        function_name: 函数名
        
    Returns:
        函数详细信息
    """
    try:
        import akshare as ak
    except ImportError:
        raise ImportError("请先安装 akshare: pip install akshare")
    
    if not hasattr(ak, function_name):
        raise ValueError(f"函数不存在: {function_name}")
    
    func = getattr(ak, function_name)
    
    if not callable(func):
        raise ValueError(f"{function_name} 不是可调用函数")
    
    try:
        sig = inspect.signature(func)
        
        params = []
        for param_name, param in sig.parameters.items():
            if param_name in ('self', 'cls'):
                continue
            
            param_info = {
                "name": param_name,
                "required": param.default is inspect.Parameter.empty,
                "default": None if param.default is inspect.Parameter.empty else str(param.default),
                "annotation": str(param.annotation) if param.annotation is not inspect.Parameter.empty else None
            }
            params.append(param_info)
        
        doc = inspect.getdoc(func) or "无文档说明"
        
        return {
            "name": function_name,
            "params": params,
            "doc": doc,
            "module": func.__module__
        }
        
    except Exception as e:
        raise Exception(f"获取函数信息失败: {str(e)}")
