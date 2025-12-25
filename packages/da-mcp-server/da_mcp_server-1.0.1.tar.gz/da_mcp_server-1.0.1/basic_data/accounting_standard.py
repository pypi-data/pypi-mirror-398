"""
会计准则管理工具
"""
from fastmcp import Context, FastMCP
from typing import Dict, Any, List
from pydantic import Field
from config import config

def register_accounting_standard_tools(mcp: FastMCP) -> FastMCP:
    """注册会计准则管理相关的工具"""

    @mcp.tool()
    def accounting_standard_all(
        ctx: Context
    ) -> Dict[str, Any]:
        """
        获取所有会计准则，不分页

        Args:
            ctx: MCP上下文对象

        Returns:
            包含所有会计准则的字典
        """
        return config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/prj_setting/accounting_standard_all/",
            {}
        )

    return mcp

def register_accounting_title_template_tools(mcp: FastMCP) -> FastMCP:
    """注册会计科目模板管理相关的工具"""

    @mcp.tool()
    def accounting_title_template_list(
        ctx: Context,
        current: int = Field(default=1, description="页码，默认为1"),
        pageSize: int = Field(default=10, description="每页记录数，默认为10，为0则返回所有记录"),
        ast_id: int = Field(default=None, description="会计准则ID（可选）"),
        at_code: str = Field(default=None, description="科目代码（可选）"),
        at_name: str = Field(default=None, description="科目名称（可选）"),
        accounting_title_category_template_id: int = Field(default=None, description="科目分类ID（可选）")
    ) -> Dict[str, Any]:
        """
        分页查询相关准则的会计科目模板

        Args:
            ctx: MCP上下文对象
            current: 页码，默认为1
            pageSize: 每页记录数，默认为10，为0则返回所有记录
            ast_id: 会计准则ID（可选）
            at_code: 科目代码（可选）
            at_name: 科目名称（可选）
            accounting_title_category_template_id: 科目分类ID（可选）

        Returns:
            包含分页信息和会计科目模板列表的字典
        """
        data = {
            "current": current,
            "pageSize": pageSize
        }
        if ast_id is not None:
            data["ast_id"] = ast_id
        if at_code is not None:
            data["at_code"] = at_code
        if at_name is not None:
            data["at_name"] = at_name
        if accounting_title_category_template_id is not None:
            data["accounting_title_category_template_id"] = accounting_title_category_template_id

        return config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/prj_setting/accounting_title_template_list/",
            data
        )

    return mcp

def register_accounting_title_category_template_tools(mcp: FastMCP) -> FastMCP:
    """注册科目分类模板管理相关的工具"""

    @mcp.tool()
    def accounting_title_category_template_list(
        ctx: Context,
        ast_id: int = Field(description="会计准则ID"),
        current: int = Field(default=1, description="页码，默认为1"),
        pageSize: int = Field(default=10, description="每页记录数，默认为10，为0则返回所有记录"),
    ) -> Dict[str, Any]:
        """
        分页查询相关准则的科目分类模板

        Args:
            ctx: MCP上下文对象
            current: 页码，默认为1
            pageSize: 每页记录数，默认为10，为0则返回所有记录
            sorter: 排序字段
            params: 搜索参数
            filters: 过滤条件

        Returns:
            包含分页信息和科目分类模板列表的字典
        """
        data = {
            "current": current,
            "pageSize": pageSize,
            "ast_id": ast_id
        }

        return config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/prj_setting/accounting_title_category_template_list/",
            data
        )
 
    return mcp

def register_report_setting_tools(mcp: FastMCP) -> FastMCP:
    """注册报表设置管理相关的工具"""

    @mcp.tool()
    def report_setting_list(
        ctx: Context,
        current: int = Field(default=1, description="页码，默认为1"),
        pageSize: int = Field(default=10, description="每页记录数，默认为10，为0则返回所有记录"),
        asd_id: int = Field(default=None, description="会计准则ID（可选）"),
        report_type: int = Field(default=None, description="报表类型(1-资产负债表,2-利润表,3-现金流量表,4-收益及收益分配表,5-收入支出表,6-成本费用表,7-盈余及盈余分配表,8-业务活动表)")
    ) -> Dict[str, Any]:
        """
        分页查询报表设置

        Args:
            ctx: MCP上下文对象
            current: 页码，默认为1
            pageSize: 每页记录数，默认为10，为0则返回所有记录
            asd_id: 会计准则ID（可选）
            report_type: 报表类型（可选）

        Returns:
            包含分页信息和报表设置列表的字典
        """
        data = {
            "current": current,
            "pageSize": pageSize
        }
        if asd_id is not None:
            data["asd_id"] = asd_id
        if report_type is not None:
            data["report_type"] = report_type

        return config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/prj_setting/report_setting_list/",
            data
        )

    return mcp

def register_calculation_formula_setting_tools(mcp: FastMCP) -> FastMCP:
    """注册报表计算公式管理相关的工具"""

    @mcp.tool()
    def calculation_formula_setting_list(
        ctx: Context,
        current: int = Field(default=1, description="页码，默认为1"),
        pageSize: int = Field(default=10, description="每页记录数，默认为10，为0则返回所有记录"),
        sorter: Dict[str, str] = Field(default=None, description="排序字段"),
        params: Dict[str, str] = Field(default=None, description="搜索参数"),
        filters: Dict[str, List[str]] = Field(default=None, description="过滤条件"),
        asd_id: int = Field(default=None, description="会计准则ID（可选）"),
        report_type: int = Field(default=None, description="报表类型(1-资产负债表,2-利润表,4-收益及收益分配表,5-收入支出表,6-成本费用表,7-盈余及盈余分配表,8-业务活动表)"),
        line_number: int = Field(default=None, description="行次（可选）")
    ) -> Dict[str, Any]:
        """
        分页查询相关准则的报表初始化计算公式

        补充说明：
            1，该工具不适用于:3-现金流量表.
        Returns:
            包含分页信息和报表计算公式列表的字典
        """
        data = {
            "current": current,
            "pageSize": pageSize
        }
        if sorter:
            data["sorter"] = sorter
        if params:
            data["params"] = params
        if filters:
            data["filters"] = filters
        if asd_id is not None:
            data["asd_id"] = asd_id
        if report_type is not None:
            data["report_type"] = report_type
        if line_number is not None:
            data["line_number"] = line_number

        return config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/prj_setting/calculation_formula_setting_list/",
            data
        )


    return mcp