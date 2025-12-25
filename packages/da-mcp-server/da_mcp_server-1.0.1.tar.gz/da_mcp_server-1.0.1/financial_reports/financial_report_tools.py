from fastmcp import Context
from typing import List, Dict, Any, Optional
from config import config
from pydantic import Field

def register_financial_report_query_tools(mcp):
    """注册财务报表查询相关的工具"""

    @mcp.tool()
    def get_balance_sheet(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        accounting_period: str = Field(description="会计期间，格式：YYYY-MM"),
        report_id: int = Field(description="报表ID"),
        max_line_number: int = Field(description="最大行次,最大行次可以从row_settings中可以获取")
    ) -> Dict[str, Any]:
        """
        获取资产负债表数据
        补充说明：
        1,调用示例：
        {
            "accounting_period": "2025-10",
            "ab_id": 81,
            "report_id": 268,//可以通过report_list工具获得
            "max_line_number": 130
        }

        Returns:
            Dict[str, Any]: 返回资产负债表数据
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "accounting_period": accounting_period,
            "report_id": report_id,
            "max_line_number": max_line_number
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/financial_reports/get_balance_sheet/",
            request_data
        )

        return response_data

    @mcp.tool()
    def get_income_statement(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        accounting_period: str = Field(description="会计期间，格式：YYYY-MM"),
        report_id: int = Field(description="报表ID"),
        max_line_number: int = Field(description="最大行次")
    ) -> Dict[str, Any]:
        """
        获取利润表数据
        {
            "accounting_period": "2025-10",
            "ab_id": 81,
            "report_id": 269,
            "max_line_number": 40
        }

        Returns:
            Dict[str, Any]: 返回利润表数据
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "accounting_period": accounting_period,
            "report_id": report_id,
            "max_line_number": max_line_number
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/financial_reports/get_income_statement/",
            request_data
        )

        return response_data

    @mcp.tool()
    def get_unified_financial_report_one(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        accounting_period: str = Field(description="会计期间，格式：YYYY-MM"),
        report_id: int = Field(description="报表ID"),
        max_line_number: int = Field(description="最大行次")
    ) -> Dict[str, Any]:
        """
        获取统一财务报表一数据
        包含：收入支出表、成本费用表、收益及收益分配表

        Args:
            ab_id: 帐套ID
            accounting_period: 会计期间，格式：YYYY-MM
            report_id: 报表ID
            max_line_number: 最大行次(可以从report_list工具获取的row_settings中获取)

        Returns:
            Dict[str, Any]: 返回统一财务报表一数据
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "accounting_period": accounting_period,
            "report_id": report_id,
            "max_line_number": max_line_number
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/financial_reports/get_unified_financial_report_one/",
            request_data
        )

        return response_data

    @mcp.tool()
    def get_unified_financial_report_two(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        accounting_period: str = Field(description="会计期间，格式：YYYY-MM"),
        report_id: int = Field(description="报表ID"),
        max_line_number: int = Field(description="最大行次")
    ) -> Dict[str, Any]:
        """
        获取统一财务报表二数据
        包含：业务活动表（细化限定性和非限定性维度）

        Args:
            ab_id: 帐套ID
            accounting_period: 会计期间，格式：YYYY-MM
            report_id: 报表ID
            max_line_number: 最大行次(可以从report_list工具获取的row_settings中获取)

        Returns:
            Dict[str, Any]: 返回统一财务报表二数据
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "accounting_period": accounting_period,
            "report_id": report_id,
            "max_line_number": max_line_number
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/financial_reports/get_unified_financial_report_two/",
            request_data
        )

        return response_data

    return mcp