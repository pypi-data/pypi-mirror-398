"""
资金账户管理工具模块
"""
from typing import List
from fastmcp import FastMCP, Context
from pydantic import Field
from config import config

def register_finance_account_tools(mcp: FastMCP) -> FastMCP:
    """注册资金账户管理相关的工具"""

    @mcp.tool(
        name="finance_account_list"
    )
    def finance_account_list_tool(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        current: int = Field(default=1, description="页码（可选，默认1）"),
        pageSize: int = Field(default=10, description="每页记录数（可选，默认10，为0则返回所有记录）"),
        sorter: dict = Field(default=None, description="排序字段（可选）"),
        params: dict = Field(default=None, description="搜索参数（可选）"),
        filters: dict = Field(default=None, description="过滤条件（可选）"),
        account_type: str = Field(default=None, description="账户类型（可选，值：'CASH'-库存现金, 'BANK'-银行存款, 'OTHER'-其他货币资金）"),
        account_code: str = Field(default=None, description="账户编码（可选）"),
        exclude_id: int = Field(default=None, description="排除的账户ID（可选）"),
        id: int = Field(default=None, description="账户ID（可选）"),
        accounting_title_id: int = Field(default=None, description="科目ID（可选，为0表示没有科目）")
    ) -> dict:
        """
        分页查询资金账户

        Args:
            ctx: MCP上下文对象
            ab_id: 帐套ID
            current: 页码（可选，默认1）
            pageSize: 每页记录数（可选，默认10，为0则返回所有记录）
            sorter: 排序字段（可选）
            params: 搜索参数（可选）
            filters: 过滤条件（可选）
            account_type: 账户类型（可选，值：'CASH'-库存现金, 'BANK'-银行存款, 'OTHER'-其他货币资金）
            account_code: 账户编码（可选）
            exclude_id: 排除的账户ID（可选）
            id: 账户ID（可选）
            accounting_title_id: 科目ID（可选，为0表示没有科目）

        Returns:
            dict: 包含查询结果的字典，包含以下字段：
                - data: List[dict] - 资金账户列表数据
                - total: int - 总记录数
                - current: int - 当前页码
                - pageSize: int - 每页记录数
        """
        request_data = {
            "ab_id": ab_id,
            "current": current,
            "pageSize": pageSize,
        }
        # 只添加非None的字段
        optional_fields = {
            "sorter": sorter,
            "params": params,
            "filters": filters,
            "account_type": account_type,
            "account_code": account_code,
            "exclude_id": exclude_id,
            "id": id,
            "accounting_title_id": accounting_title_id
        }
        for key, value in optional_fields.items():
            if value is not None:
                request_data[key] = value
        
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/cashier/finance_account_list/", request_data)

    @mcp.tool(
        name="finance_account_update"
    )
    def finance_account_update_tool(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        id: int = Field(description="资金账户ID（主键）"),
        account_code: str = Field(default=None, description="账户编码（可选）"),
        account_name: str = Field(default=None, description="账户名称（可选）"),
        currency_id: int = Field(default=None, description="币别ID（可选）"),
        accounting_title_id: int = Field(default=None, description="入账科目ID（可选）"),
        bank_account_number: str = Field(default=None, description="银行账户号（可选）"),
        bank_or_institution: str = Field(default=None, description="银行/机构（可选）"),
        remarks: str = Field(default=None, description="备注（可选）"),
        bank_integration_status: bool = Field(default=None, description="银企互联状态（可选，False-未启用, True-启用中）"),
        enabled_status: bool = Field(default=None, description="启用状态（可选，False-未启用, True-已启用）"),
        account_type: str = Field(default=None, description="账户类型（可选，值：'CASH'-库存现金, 'BANK'-银行存款, 'OTHER'-其他货币资金）"),
        auxiliary_accountings: dict = Field(default=None, description="""账号关联科目的辅助信息（可选),如果科目没关联，那么相应辅助信息也应该为None
                                            格式:{"辅助核算类别":对应类别的辅助核算}，比如:{"32":18}
                                             """)
    ) -> dict:
        """
        更新资金账户

        注意：1)currency_id 和 accounting_title_id 要么都提供，要么都不提供.2)对于开启了外币核算的科目，auxiliary_accountings必须指定。
        Returns:
            dict: 包含更新结果的字典，包含以下字段：
                - affect_rows: int - 影响的行数
        """
        request_data = {
            "id": id,
            "ab_id": ab_id,
        }
        # 只添加非None的字段
        optional_fields = {
            "account_code": account_code,
            "account_name": account_name,
            "currency_id": currency_id,
            "accounting_title_id": accounting_title_id,
            "bank_account_number": bank_account_number,
            "bank_or_institution": bank_or_institution,
            "remarks": remarks,
            "bank_integration_status": bank_integration_status,
            "enabled_status": enabled_status,
            "account_type": account_type,
            "auxiliary_accountings": auxiliary_accountings
        }
        for key, value in optional_fields.items():
            if value is not None:
                request_data[key] = value
        
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/cashier/finance_account_update/", request_data)

    @mcp.tool(
        name="finance_account_create"
    )
    def finance_account_create_tool(
        ctx: Context,
        account_code: str = Field(description="账户编码"),
        account_name: str = Field(description="账户名称"),
        currency_id: int = Field(description="币别ID"),
        ab_id: int = Field(description="帐套ID"),
        account_type: str = Field(description="账户类型，值：'CASH'-库存现金, 'BANK'-银行存款, 'OTHER'-其他货币资金"),
        accounting_title_id: int = Field(default=None, description="入账科目ID（可选）"),
        bank_account_number: str = Field(default="", description="银行账户号（可选）"),
        bank_or_institution: str = Field(default="", description="银行/机构（可选）"),
        remarks: str = Field(default="", description="备注（可选）"),
        bank_integration_status: bool = Field(default=False, description="银企互联状态（可选，False-未启用, True-启用中，默认False）"),
        enabled_status: bool = Field(default=True, description="启用状态（可选，False-未启用, True-已启用，默认True）"),
        auxiliary_accountings: dict = Field(default=None, description="""账号关联科目的辅助信息（可选),如果科目没关联，那么相应辅助信息也应该为None
                                            格式:{"辅助核算类别":对应类别的辅助核算}，比如:{"32":18}
                                             """)
    ) -> dict:
        """
        创建资金账户
        注意：1)currency_id 和 accounting_title_id 要么都提供，要么都不提供.2)对于开启了外币核算的科目，auxiliary_accountings必须指定。

        Returns:
            dict: 包含创建结果的字典，包含以下字段：
                - record_id: int - 新创建的资金账户ID
        """
        request_data = {
            "account_code": account_code,
            "account_name": account_name,
            "currency_id": currency_id,
            "ab_id": ab_id,
            "account_type": account_type,
            "bank_account_number": bank_account_number,
            "bank_or_institution": bank_or_institution,
            "remarks": remarks,
            "bank_integration_status": bank_integration_status,
            "enabled_status": enabled_status,
        }
        # 只添加非None的字段
        optional_fields = {
            "accounting_title_id": accounting_title_id,
            "auxiliary_accountings": auxiliary_accountings
        }
        for key, value in optional_fields.items():
            if value is not None:
                request_data[key] = value
        
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/cashier/finance_account_create/", request_data)

    @mcp.tool(
        name="finance_account_batch_delete",
        description="批量删除资金账户"
    )
    def finance_account_batch_delete_tool(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        ids: List[int] = Field(description="要删除的资金账户ID列表")
    ) -> dict:
        """
        批量删除资金账户

        Args:
            ctx: MCP上下文对象
            ids: 要删除的资金账户ID列表

        Returns:
            dict: 包含删除结果的字典，包含以下字段：
                - affect_rows: int - 影响的行数
        """
        request_data = {
            "ab_id": ab_id,
            "ids": ids
        }
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/cashier/finance_account_batch_delete/", request_data)
    @mcp.tool(
        name="find_finance_account"
    )
    def find_finance_account_tool(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        accounting_title_id: int = Field(description="科目ID"),
        auxiliaries_ids: List[int] = Field(description="辅助ID列表（按辅助所在辅助类别排序）")
    ) -> dict:
        """
        通过科目和辅助查找资金账户

        Args:
            ctx: MCP上下文对象
            ab_id: 帐套ID
            accounting_title_id: 科目ID
            auxiliaries_ids: 辅助ID列表（按辅助所在辅助类别排序）

        Returns:
            dict: 包含查询结果的字典，包含以下字段：
                - data: List[dict] - 匹配的资金账户列表，如果没有匹配的账户则返回空列表
        """
        request_data = {
            "ab_id": ab_id,
            "accounting_title_id": accounting_title_id,
            "auxiliaries_ids": auxiliaries_ids
        }
        
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/cashier/find_finance_account/", request_data)
    
    return mcp