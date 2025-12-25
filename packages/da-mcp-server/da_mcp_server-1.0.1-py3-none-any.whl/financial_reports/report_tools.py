import json
import io
import requests
from fastmcp import Context
from typing import List, Dict, Any, Optional
from config import config
from pydantic import Field

def register_financial_report_tools(mcp):
    """注册财务报表相关的工具"""

    @mcp.tool()
    def report_list(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        current: int = Field(default=1, ge=1, description="页码"),
        pageSize: int = Field(default=10, ge=0, description="每页记录数，为0则返回所有记录"),
        sorter: Dict[str, str] = Field(default=None, description="排序字段，格式：{'字段名': 'ascend'|'descend'}"),
        params: Dict[str, Any] = Field(default=None, description="参数搜索条件"),
        filters: Dict[str, List[Any]] = Field(default=None, description="过滤条件"),
        report_type: int = Field(default=None, description="报表类型(1-资产负债表,2-利润表,3-现金流量表,4-收益及收益分配表,5-收入支出表,6-成本费用表,7-盈余及盈余分配表,8-业务活动表)"),
    ) -> Dict[str, Any]:
        """
        获取财务报表列表,获取报表ID

       Returns:
            Dict[str, Any]: 包含分页信息和报表数据的字典，结构如下：
            {
                "success": bool,           # 操作是否成功
                "message": str,            # 响应消息
                "data": {
                    "total": int,          # 总记录数
                    "current": int,        # 当前页码
                    "pageSize": int,       # 每页记录数
                    "data": [             # 报表数据列表
                        {
                            "id": int,                    # 报表主键ID
                            "ab_id": int,                 # 帐套ID
                            "report_type": int,           # 报表类型
                            "name": str,                  # 报表名称
                            "column_settings": str,       # 报表列设置(JSON字符串,可以获得表头设置)
                            "row_settings": str           # 报表行设置(JSON字符串，可以获得报表行设置)
                        },
                        # ... 更多报表记录
                    ]
                }
            }
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "current": current,
            "pageSize": pageSize
        }

        # 添加可选参数
        if sorter is not None:
            request_data["sorter"] = sorter
        if params is not None:
            request_data["params"] = params
        if filters is not None:
            request_data["filters"] = filters
        if report_type is not None:
            request_data["report_type"] = report_type

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/financial_reports/report_list/",
            request_data
        )

        report_data = response_data['data']['data']
        if report_data:
            # 处理报表列表中的每个项目
            for report_item in report_data:
                if 'column_settings' in report_item and report_item['column_settings']:
                    try:
                        report_item['column_settings'] = json.loads(report_item['column_settings'])
                    except (json.JSONDecodeError, TypeError):                        
                        pass
                if 'row_settings' in report_item and report_item['row_settings']:
                    try:
                        report_item['row_settings'] = json.loads(report_item['row_settings'])
                    except (json.JSONDecodeError, TypeError):
                        pass
        return response_data
 
    return mcp