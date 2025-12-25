"""
Gov Stats MCP Server
提供中国国家统计局数据查询的 MCP 服务
"""

from __future__ import annotations

import json
from fastmcp import FastMCP
from pydantic import BaseModel, Field

# 导入查询引擎和常量
try:
    from .query import GovStatsQueryEngine
    from .constants import INDICATOR_DESCRIPTIONS
except ImportError:
    from query import GovStatsQueryEngine
    from constants import INDICATOR_DESCRIPTIONS


# 创建 FastMCP 实例
mcp = FastMCP("Gov Stats MCP Server")


class StatsQueryRequest(BaseModel):
    """国家统计局数据查询请求"""
    zbcode: str = Field(..., description="指标代码")
    datestr: str = Field(..., description="查询日期，格式: YYYYMM (月度), YYYYQ1-4 (季度), YYYY (年度)")
    dbcode: str = Field(default="hgyd", description="数据库代码，默认 hgyd (宏观月度数据)")
    regcode: str = Field(default=None, description="地区代码（可选）")


# 初始化查询引擎
query_engine = GovStatsQueryEngine()


@mcp.tool()
def query_stats(request: StatsQueryRequest) -> str:
    """
    查询国家统计局数据
    
    支持的指标代码示例：
    - A010101: 全国居民消费价格分类指数(上年同月=100)
    - A010801: 工业生产者出厂价格指数(上年同月=100)
    - A0D0101: 货币供应量(M2)
    - A020101: 工业增加值增长速度
    
    数据库代码：
    - hgyd: 宏观月度数据（默认）
    - hgjd: 宏观季度数据
    - hgnd: 宏观年度数据
    - fsyd: 分省月度数据
    - fsnd: 分省年度数据
    
    日期格式：
    - 月度: YYYYMM (如 202401)
    - 季度: YYYYQ1-4 (如 2024Q1)
    - 年度: YYYY (如 2024)
    
    Args:
        request: 包含查询参数的请求
        
    Returns:
        JSON格式的查询结果
    """
    try:
        result = query_engine.query_stats_data(
            zbcode=request.zbcode,
            datestr=request.datestr,
            dbcode=request.dbcode,
            regcode=request.regcode
        )
        
        response = {
            "success": True,
            "data": result,
            "count": len(result),
            "query": {
                "zbcode": request.zbcode,
                "datestr": request.datestr,
                "dbcode": request.dbcode,
                "regcode": request.regcode
            }
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
def list_indicators() -> str:
    """
    获取所有可用的指标代码清单
    
    返回所有支持的指标代码及其描述，包括：
    - 价格指数（居民消费价格、工业生产者价格等）
    - 工业数据（工业增加值、工业出口等）
    - 宏观经济（货币供应量等）
    
    Returns:
        JSON格式的指标清单
    """
    indicators = [
        {"code": code, "description": desc}
        for code, desc in INDICATOR_DESCRIPTIONS.items()
    ]
    
    response = {
        "success": True,
        "indicators": indicators,
        "total": len(indicators),
        "categories": {
            "price_index": "价格指数 (A0101xx-A0108xx)",
            "industry": "工业数据 (A020xxx)",
            "macro": "宏观经济 (A0D0xxx)"
        }
    }
    return json.dumps(response, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run()


def main():
    """命令行入口点函数"""
    mcp.run()
