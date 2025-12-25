"""
AkShare MCP Server 测试文件
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scanner import scan_akshare_functions, get_function_info
from executor import AkShareExecutor


def test_scanner():
    """测试函数扫描"""
    print("🔍 测试 AkShare 函数扫描...")
    
    try:
        functions = scan_akshare_functions()
        
        print(f"   扫描到 {len(functions)} 个函数")
        print(f"\n   前10个函数:")
        for func in functions[:10]:
            print(f"   - {func['name']}: {func['doc'][:50]}...")
        
        print("\n   ✅ 扫描测试通过")
        
    except Exception as e:
        print(f"   ❌ 扫描测试失败: {e}")


def test_function_info():
    """测试获取函数信息"""
    print("\n🔍 测试获取函数详细信息...")
    
    test_functions = ["stock_zh_a_spot_em", "macro_china_cpi"]
    
    for func_name in test_functions:
        try:
            print(f"\n   函数: {func_name}")
            info = get_function_info(func_name)
            
            print(f"   参数数量: {len(info['params'])}")
            print(f"   参数列表:")
            for param in info['params']:
                required = "必需" if param['required'] else "可选"
                print(f"     - {param['name']} ({required})")
            
            print("   ✅ 获取成功")
            
        except Exception as e:
            print(f"   ❌ 获取失败: {e}")


def test_executor():
    """测试函数执行"""
    print("\n🔍 测试函数执行...")
    
    executor = AkShareExecutor()
    
    # 测试一个简单的函数
    try:
        print("\n   执行: stock_zh_a_spot_em")
        result = executor.execute_function("stock_zh_a_spot_em", {})
        
        print(f"   返回数据行数: {len(result)}")
        if result:
            print(f"   第一行数据: {json.dumps(result[0], ensure_ascii=False)[:100]}...")
        
        print("   ✅ 执行成功")
        
    except Exception as e:
        print(f"   ❌ 执行失败: {e}")


def main():
    """主测试函数"""
    print("🚀 开始 AkShare MCP Server 测试")
    print("=" * 50)
    
    test_scanner()
    test_function_info()
    test_executor()
    
    print("\n" + "=" * 50)
    print("🎉 所有测试完成")


if __name__ == "__main__":
    main()
