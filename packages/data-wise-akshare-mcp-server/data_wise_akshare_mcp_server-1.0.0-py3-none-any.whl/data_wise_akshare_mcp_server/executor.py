"""
AkShare 函数执行器
"""

from __future__ import annotations

from typing import Dict, Any, List


class AkShareExecutor:
    """AkShare 函数执行器"""
    
    def execute_function(
        self,
        function_name: str,
        params: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        执行 AkShare 函数
        
        Args:
            function_name: 函数名
            params: 函数参数字典
            
        Returns:
            执行结果
        """
        try:
            import akshare as ak
        except ImportError:
            raise ImportError("请先安装 akshare: pip install akshare")
        
        # 检查函数是否存在
        if not hasattr(ak, function_name):
            raise ValueError(f"函数不存在: {function_name}")
        
        func = getattr(ak, function_name)
        
        if not callable(func):
            raise ValueError(f"{function_name} 不是可调用函数")
        
        try:
            # 执行函数
            call_params = params or {}
            result = func(**call_params)
            
            # 转换结果为字典列表
            if hasattr(result, 'to_dict'):
                # pandas DataFrame
                data = result.to_dict('records')
            elif isinstance(result, (dict, list)):
                data = result if isinstance(result, list) else [result]
            else:
                # 其他类型转换为字符串
                data = [{"value": str(result)}]
            
            return data
            
        except Exception as e:
            raise Exception(f"执行函数失败: {str(e)}")
