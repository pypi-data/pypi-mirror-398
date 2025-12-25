"""
现金流量映射管理工具
包含现金流量映射、现金流量明细、现金流量汇总等工具
"""

from fastmcp import Context
from typing import List, Dict, Any, Optional
from config import config
from pydantic import Field
from config import config

def register_cash_flow_mapping_tools(mcp):
    """注册现金流量映射相关的工具"""

    @mcp.tool()
    def cash_flow_mapping_list(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        accounting_title_category_id: int = Field(description="科目分类ID"),
        current: int = Field(default=1, ge=1, description="页码"),
        pageSize: int = Field(default=10, ge=0, description="每页记录数，为0则返回所有记录")
    ) -> Dict[str, Any]:
        """
        分页查询现金流量映射
        根据科目分类ID分页查询现金流量映射

        补充说明：
        1，请求示例：
        {
                "current": 1,
                "pageSize": 120,
                "accounting_title_category_id": 1119,
                "ab_id": 20
        }
        2，返回的现金流量行次对应的现金流量项目需要通过report_list工具查询报表配置。
        Args:
            ab_id: 帐套ID
            accounting_title_category_id: 科目分类ID
            current: 页码
            pageSize: 每页记录数

        Returns:
            Dict[str, Any]: 返回现金流量映射列表
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "accounting_title_category_id": accounting_title_category_id,
            "current": current,
            "pageSize": pageSize
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/financial_reports/cash_flow_mapping_list/",
            request_data
        )

        return response_data

    @mcp.tool()
    def cash_flow_mapping_update(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        accounting_title_id: int = Field(description="科目ID"),
        inflow_line_number: Optional[int] = Field(default=None, description="流入行次编号"),
        outflow_line_number: Optional[int] = Field(default=None, description="流出行次编号")
    ) -> Dict[str, Any]:
        """
        更新或创建现金流量映射
        根据科目ID更新或创建现金流量映射记录

        Args:
            ab_id: 帐套ID
            accounting_title_id: 科目ID
            inflow_line_number: 流入行次编号
            outflow_line_number: 流出行次编号

        Returns:
            Dict[str, Any]: 返回操作结果
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "accounting_title_id": accounting_title_id
        }

        # 添加可选参数
        if inflow_line_number is not None:
            request_data["inflow_line_number"] = inflow_line_number
        if outflow_line_number is not None:
            request_data["outflow_line_number"] = outflow_line_number

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/financial_reports/cash_flow_mapping_update/",
            request_data
        )

        return response_data

    @mcp.tool()
    def cash_flow_mapping_batch_update(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        items: List[Dict[str, Any]] = Field(description="批量更新项目列表，每个项目包含：accounting_title_id, inflow_line_number, outflow_line_number")
    ) -> Dict[str, Any]:
        """
        批量更新现金流量映射
        批量更新或创建现金流量映射记录

        Args:
            ab_id: 帐套ID
            items: 批量更新项目列表，每个项目包含：
                - accounting_title_id: 科目ID (必填)
                - inflow_line_number: 流入行次编号 (可选)
                - outflow_line_number: 流出行次编号 (可选)

        Returns:
            Dict[str, Any]: 返回批量更新操作结果，包含：
                - affect_rows: 成功更新的记录数
                - errors: 错误信息列表
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "items": items
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/financial_reports/cash_flow_mapping_batch_update/",
            request_data
        )

        return response_data

    @mcp.tool()
    def cash_flow_mapping_nullify(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        accounting_title_id: int = Field(description="科目ID"),
        field_to_nullify: str = Field(description="要置为null的字段")
    ) -> Dict[str, Any]:
        """
        将现金流量映射字段置为null
        根据科目ID将指定的现金流量映射字段置为null

        Args:
            ab_id: 帐套ID
            accounting_title_id: 科目ID
            field_to_nullify: 要置为null的字段

        Returns:
            Dict[str, Any]: 返回操作结果
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "accounting_title_id": accounting_title_id,
            "field_to_nullify": field_to_nullify
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/financial_reports/cash_flow_mapping_nullify/",
            request_data
        )

        return response_data

    @mcp.tool()
    def cash_flow_detail(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        accounting_period: str = Field(description="会计期间，格式：YYYY-MM"),
        current_line: Optional[int] = Field(default=None, description="选择的行次"),
        current: int = Field(default=1, ge=1, description="页码"),
        pageSize: int = Field(default=10, ge=0, description="每页记录数，为0则返回所有记录"),
        show_unassigned_only: bool = Field(default=False, description="是否只显示未指定现金流量项目的记录")
    ) -> Dict[str, Any]:
        """
        获取现金流量明细账
        根据账套ID和会计期间获取现金流量明细账

        Args:
            ab_id: 帐套ID
            accounting_period: 会计期间
            current_line: 选择的行次
            current: 页码
            pageSize: 每页记录数
            show_unassigned_only: 是否只显示未指定现金流量项目的记录

        Returns:
            Dict[str, Any]: 返回现金流量明细账数据
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "accounting_period": accounting_period,
            "current": current,
            "pageSize": pageSize,
            "show_unassigned_only": show_unassigned_only
        }

        # 添加可选参数
        if current_line is not None:
            request_data["current_line"] = current_line

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/financial_reports/cash_flow_detail/",
            request_data
        )

        return response_data

    @mcp.tool()
    def cash_flow_detail_by_voucher(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        voucher_id: int = Field(description="凭证ID")
    ) -> Dict[str, Any]:
        """
        获取指定凭证的现金流量明细
        根据账套ID和凭证ID获取现金流量明细（不分页）

        Args:
            ab_id: 帐套ID
            voucher_id: 凭证ID

        Returns:
            Dict[str, Any]: 返回指定凭证的现金流量明细
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "voucher_id": voucher_id
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/financial_reports/cash_flow_detail_by_voucher/",
            request_data
        )

        return response_data

    @mcp.tool()
    def cash_flow_detail_update(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        id: int = Field(description="现金流量明细ID"),
        cash_flow_item_line_number: int = Field(description="现金流量项目行次")
    ) -> Dict[str, Any]:
        """
        更新现金流量明细的现金流量项目
        根据现金流量明细ID更新现金流量项目行次

        Args:
            id: 现金流量明细ID
            cash_flow_item_line_number: 现金流量项目行次

        Returns:
            Dict[str, Any]: 返回操作结果
        """
        # 构建请求数据
        request_data = {
            "ab_id":ab_id,
            "id": id,
            "cash_flow_item_line_number": cash_flow_item_line_number
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/financial_reports/cash_flow_detail_update/",
            request_data
        )

        return response_data

    @mcp.tool()
    def cash_flow_detail_nullify(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        id: int = Field(description="现金流量明细ID")
    ) -> Dict[str, Any]:
        """
        置空现金流量明细的现金流量项目
        根据现金流量明细ID将现金流量项目行次置为null

        Args:
            id: 现金流量明细ID

        Returns:
            Dict[str, Any]: 返回操作结果
        """
        # 构建请求数据
        request_data = {
            "ab_id":ab_id,
            "id": id
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/financial_reports/cash_flow_detail_nullify/",
            request_data
        )

        return response_data

    @mcp.tool()
    def cash_flow_summary(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        accounting_period: str = Field(description="会计期间，格式：YYYY-MM")
    ) -> Dict[str, Any]:
        """
        获取现金流量项目汇总,也就是是现金流量报表数据
        根据账套ID和会计期间获取现金流量项目本期和本年累计的流入流出金额
        补充说明，现金流量报表的格式和开项请通过，report_list工具获得。
        Args:
            ab_id: 帐套ID
            accounting_period: 会计期间

        Returns:
            Dict[str, Any]: 返回现金流量项目汇总数据
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "accounting_period": accounting_period
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/financial_reports/cash_flow_summary/",
            request_data
        )

        return response_data

    @mcp.tool()
    def cash_flow_initialization_add(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        line_number: int = Field(description="报表行次"),
        initial_balance: float = Field(description="期初余额")
    ) -> Dict[str, Any]:
        """
        添加现金流量初始化数据
        根据账套ID和行次添加现金流量初始化数据

        Args:
            ab_id: 帐套ID
            line_number: 报表行次
            initial_balance: 期初余额

        Returns:
            Dict[str, Any]: 返回操作结果
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "line_number": line_number,
            "initial_balance": initial_balance
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/financial_reports/cash_flow_initialization_add/",
            request_data
        )

        return response_data

    @mcp.tool()
    def cash_flow_initialization_get(
        ctx: Context,
        ab_id: int = Field(description="帐套ID")
    ) -> Dict[str, Any]:
        """
        获取现金流量初始化数据
        根据账套ID获取现金流量初始化数据

        Args:
            ab_id: 帐套ID

        Returns:
            Dict[str, Any]: 返回现金流量初始化数据
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/financial_reports/cash_flow_initialization_get/",
            request_data
        )

        return response_data

    return mcp