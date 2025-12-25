"""
财务结账前检查工具
"""

from typing import Dict, Any, Optional
from fastmcp import FastMCP,Context
from config import config
from pydantic import Field

def register_financial_closing_precheck_tools(mcp: FastMCP) -> FastMCP:
    """注册财务结账前检查工具"""

    @mcp.tool(
        name="financial_closing_precheck",
        description="执行结账前全面检查，包括资产类科目余额检查、期末结转检查、往来挂帐检查及其他异常检查"
    )
    async def financial_closing_precheck(
        ctx: Context,
        ab_id: int = Field(description='帐套ID'),
        accounting_period: str = Field(description="账期，格式为 'YYYY-MM'")
    ) -> Dict[str, Any]:
        """
        执行结账前全面检查

        Args:
            ab_id: 帐套ID
            accounting_period: 账期，格式为 'YYYY-MM'

        Returns:
            Dict: 检查结果，包含总体结果和详细检查项目
        """
        request_data = {
            "ab_id": ab_id,
            "accounting_period": accounting_period
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/financial_closing_precheck/",
            request_data
        )

        return response_data

    return mcp