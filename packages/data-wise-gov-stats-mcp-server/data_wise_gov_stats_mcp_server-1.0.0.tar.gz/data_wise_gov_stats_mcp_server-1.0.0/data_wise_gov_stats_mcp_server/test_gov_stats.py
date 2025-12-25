"""
Gov Stats MCP Server 测试文件
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from query import GovStatsQueryEngine


def test_query_engine():
    """测试查询引擎"""
    print("🔍 测试国家统计局数据查询引擎...")
    
    engine = GovStatsQueryEngine()
    
    # 测试数据
    test_queries = [
        {
            "zbcode": "A010101",
            "datestr": "202401",
            "dbcode": "hgyd",
            "description": "全国居民消费价格分类指数"
        },
        {
            "zbcode": "A0D0101",
            "datestr": "202401",
            "dbcode": "hgyd",
            "description": "货币供应量(M2)"
        }
    ]
    
    for test in test_queries:
        try:
            print(f"\n📊 测试查询: {test['description']}")
            print(f"   指标代码: {test['zbcode']}")
            print(f"   查询日期: {test['datestr']}")
            
            result = engine.query_stats_data(
                zbcode=test['zbcode'],
                datestr=test['datestr'],
                dbcode=test['dbcode']
            )
            
            print(f"   查询结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            print("   ✅ 查询成功")
            
        except Exception as e:
            print(f"   ❌ 查询失败: {e}")
    
    print("\n✅ 查询引擎测试完成")


def main():
    """主测试函数"""
    print("🚀 开始 Gov Stats MCP Server 测试")
    print("=" * 50)
    
    test_query_engine()
    
    print("\n" + "=" * 50)
    print("🎉 所有测试完成")


if __name__ == "__main__":
    main()
