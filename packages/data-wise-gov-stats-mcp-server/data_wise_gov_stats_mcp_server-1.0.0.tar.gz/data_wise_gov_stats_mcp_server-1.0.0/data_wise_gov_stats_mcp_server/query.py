"""
国家统计局数据查询引擎
"""

from __future__ import annotations

from typing import Dict, Any, List


class GovStatsQueryEngine:
    """国家统计局数据查询引擎"""
    
    def query_stats_data(
        self,
        zbcode: str,
        datestr: str,
        dbcode: str = "hgyd",
        regcode: str = None
    ) -> List[Dict[str, Any]]:
        """
        查询国家统计局数据
        
        Args:
            zbcode: 指标代码
            datestr: 查询日期，格式: YYYYMM (月度), YYYYQ1-4 (季度), YYYY (年度)
            dbcode: 数据库代码，默认 hgyd (宏观月度数据)
            regcode: 地区代码（可选）
            
        Returns:
            查询结果列表
        """
        try:
            from cnstats.stats import stats
            
            # 构建查询参数
            params = {
                "zbcode": zbcode,
                "datestr": datestr,
                "dbcode": dbcode
            }
            
            if regcode:
                params["regcode"] = regcode
            
            # 执行查询
            result = stats(**params)
            
            # 转换结果为字典列表
            if hasattr(result, 'to_dict'):
                # pandas DataFrame
                data = result.to_dict('records')
            elif isinstance(result, (dict, list)):
                data = result if isinstance(result, list) else [result]
            else:
                data = [{"value": str(result)}]
            
            return data
            
        except Exception as e:
            raise Exception(f"查询国家统计局数据失败: {str(e)}")

