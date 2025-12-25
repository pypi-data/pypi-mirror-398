"""
日记账管理工具模块
"""
from typing import List
from enum import Enum
from fastmcp import FastMCP, Context
from pydantic import Field
from config import config


class DateMode(str, Enum):
    """日期模式枚举"""
    PERIOD = "period"  # 帐期模式 (YYYY-MM)
    DATE = "date"      # 日期模式 (YYYY-MM-DD)

def register_journal_entry_tools(mcp: FastMCP) -> FastMCP:
    """注册日记账管理相关的工具"""

    @mcp.tool(
        name="journal_entry_create"
     )
    def journal_entry_create_tool(
        ctx: Context,
        finance_account_id: int = Field(description="资金账户ID"),
        creation_date: str = Field(description="日期，格式：YYYY-MM-DD"),
        ab_id: int = Field(description="帐套ID"),
        actual_counterpart_account_id: int = Field(default=0,description="实际对方资金账户ID，为0表示不创建对方流水，为有效资金账户ID则创建对方流水"),
        summary: str = Field(default="", description="摘要（可选）"),
        counterpart_account_name: str = Field(default="", description="对方账户名称（可选）"),
        income: float = Field(default=0, description="收入金额（可选）"),
        original_income: float = Field(default=0, description="原币收入金额（可选）"),
        expense: float = Field(default=0, description="支出金额（可选）"),
        original_expense: float = Field(default=0, description="原币支出金额（可选）"),
        income_exchange_rate: float = Field(default=1, description="收入汇率（可选）"),
        expense_exchange_rate: float = Field(default=1, description="支出汇率（可选）"),
        voucher_id: int = Field(default=None, description="凭证ID（可选）"),
        remark: str = Field(default="", description="备注（可选）"),
        creator_id: int = Field(default=None, description="制单人ID（可选）"),
        account_counterpart_json: dict = Field(default=None, description="账户对方科目信息（可选），格式: {'accountingTitleId': 科目ID, 'accountingTitleName': 科目名称, 'auxiliaries': [{'id': 辅助ID, 'code': 辅助编码, 'name': 辅助名称, 'auxiliary_accounting_category_id': 辅助类别ID}]}"),
        serial_number: str = Field(default="", description="流水号（可选）"),
        counterpart_bank: str = Field(default="", description="对方银行（可选）"),
        counterpart_account_number: str = Field(default="", description="对方账号（可选）"),
        original_document_number: str = Field(default="", description="原单据编号（可选）"),
        counterpart_entry_id: int = Field(default=None, description="对方日记账流水ID（可选）")
    ) -> dict:
        """
        创建新的日记账记录

        Args:
            ctx: MCP上下文对象
            finance_account_id: 资金账户ID
            creation_date: 日期，格式：YYYY-MM-DD
            ab_id: 帐套ID
            actual_counterpart_account_id: 实际对方资金账户ID，为0表示不创建对方流水，为有效资金账户ID则创建对方流水
            summary: 摘要（可选）
            counterpart_account_name: 对方账户名称（可选）
            income: 收入金额（可选）
            original_income: 原币收入金额（可选）
            expense: 支出金额（可选）
            original_expense: 原币支出金额（可选）
            income_exchange_rate: 收入汇率（可选）
            expense_exchange_rate: 支出汇率（可选）
            voucher_id: 凭证ID（可选）
            remark: 备注（可选）
            creator_id: 制单人ID（可选）
            account_counterpart_json: 账户对方科目信息（可选）
            serial_number: 流水号（可选）
            counterpart_bank: 对方银行（可选）
            counterpart_account_number: 对方账号（可选）
            original_document_number: 原单据编号（可选）
            counterpart_entry_id: 对方日记账流水ID（可选）

        参数补充说明:
        1. account_counterpart_json格式示例:
           {
               "accountingTitleId": 10690,
               "accountingTitleName": "1002 银行存款",
               "auxiliaries": [
                   {
                       "id": 454,
                       "code": "B003",
                       "name": "农业银行专用户",
                       "auxiliary_accounting_category_id": 502
                   }
               ]
           }
        2. actual_counterpart_account_id说明:
           - 为0表示不创建对方日记账流水
           - 为有效资金账户ID表示创建对方日记账流水，该资金账户必须绑定account_counterpart_json对应的科目+辅助
           - 可通过find_finance_account_tool查询account_counterpart_json对应的资金账户情况
        3. counterpart_entry_id: 如果创建时已知对方日记账流水ID，可通过此参数指定
        4.创建示例：
          1）简单创建：
          {
            "ab_id": 20,
            "creation_date": "2025-10-01",
            "summary": "我的测试",
            "income": "0.00",
            "expense": "666",
            "counterpart_account_name": "",
            "finance_account_id": 35,
            "actual_counterpart_account_id": 0
         }
          2）带对方科目+辅助创建：
          {
            "ab_id": 0,
            "creation_date": "2025-10-01",
            "summary": "我的测试",
            "income": "888",
            "expense": "0.00",
            "account_counterpart_json": {
                "accountingTitleId": 12049,
                "accountingTitleName": "113 内部往来",
                "auxiliary_accountings": {
                    "555": 647
                },
                "auxiliaries": [
                    {
                        "id": 647,
                        "code": "BM003",
                        "name": "农业服务部",
                        "auxiliary_accounting_category_id": 555
                    }
                ],
                "auxiliary_accounting_category_ids": [
                    555
                ],
                "auxiliary_accounting_category_names": [
                    "部门"
                ]
            },
            "counterpart_account_name": "",
            "finance_account_id": 35,
            "actual_counterpart_account_id": 0
        }
        3） 创建对方流水

        {
            "ab_id": 20,
            "creation_date": "2025-10-01",
            "summary": "我的测试",
            "income": "0.00",
            "expense": "998",
            "account_counterpart_json": {
                "accountingTitleId": 12045,
                "accountingTitleName": "101 现金",
                "auxiliary_accountings": {},
                "auxiliaries": [],
                "auxiliary_accounting_category_ids": null,
                "auxiliary_accounting_category_names": null
            },
            "counterpart_account_name": "",
            "finance_account_id": 35,
            "actual_counterpart_account_id": 34
        }

        Returns:
            dict: 包含创建结果的字典，包含以下字段：
                - success: bool - 请求是否成功
                - message: str - 返回消息说明
                - data: dict - 创建结果数据，包含：
                    - record_id: int - 新创建的日记账记录ID
        """
        request_data = {
            "finance_account_id": finance_account_id,
            "creation_date": creation_date,
            "ab_id": ab_id,
            "summary": summary,
            "counterpart_account_name": counterpart_account_name,
            "income": income,
            "original_income": original_income,
            "expense": expense,
            "original_expense": original_expense,
            "income_exchange_rate": income_exchange_rate,
            "expense_exchange_rate": expense_exchange_rate,
            "remark": remark,
            "serial_number": serial_number,
            "counterpart_bank": counterpart_bank,
            "counterpart_account_number": counterpart_account_number,
            "original_document_number": original_document_number,
        }
        # 只添加非None的字段
        optional_fields = {
            "voucher_id": voucher_id,
            "creator_id": creator_id,
            "account_counterpart_json": account_counterpart_json,
            "counterpart_entry_id": counterpart_entry_id,
            "actual_counterpart_account_id": actual_counterpart_account_id
        }
        for key, value in optional_fields.items():
            if value is not None:
                request_data[key] = value
        
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/cashier/journal_entry_create/", request_data)

    @mcp.tool(
        name="journal_entry_update"    )
    def journal_entry_update_tool(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        id: int = Field(description="日记账记录ID（主键）"),
        actual_counterpart_account_id: int = Field(description="实际对方账户ID，为0表示不创建对方流水，为有效资金账户ID则创建对方流水"),
        finance_account_id: int = Field(default=None, description="账户ID（可选）"),
        creation_date: str = Field(default=None, description="日期，格式：YYYY-MM-DD（可选）"),
        summary: str = Field(default=None, description="摘要（可选）"),
        counterpart_account_name: str = Field(default=None, description="对方账户名称（可选）"),
        income: float = Field(default=None, description="收入金额（可选）"),
        original_income: float = Field(default=None, description="原币收入金额（可选）"),
        expense: float = Field(default=None, description="支出金额（可选）"),
        original_expense: float = Field(default=None, description="原币支出金额（可选）"),
        income_exchange_rate: float = Field(default=None, description="收入汇率（可选）"),
        expense_exchange_rate: float = Field(default=None, description="支出汇率（可选）"),
        voucher_id: int = Field(default=None, description="凭证ID（可选）"),
        remark: str = Field(default=None, description="备注（可选）"),
        creator_id: int = Field(default=None, description="制单人ID（可选）"),
        account_counterpart_json: dict = Field(default=None, description="账户对方科目信息（可选），格式: {'accountingTitleId': 科目ID, 'accountingTitleName': 科目名称, 'auxiliaries': [{'id': 辅助ID, 'code': 辅助编码, 'name': 辅助名称, 'auxiliary_accounting_category_id': 辅助类别ID}]}"),
        serial_number: str = Field(default=None, description="流水号（可选）"),
        counterpart_bank: str = Field(default=None, description="对方银行（可选）"),
        counterpart_account_number: str = Field(default=None, description="对方账号（可选）"),
        original_document_number: str = Field(default=None, description="原单据编号（可选）"),
        counterpart_entry_id: int = Field(default=None, description="对方日记账流水ID（可选）")
    ) -> dict:
        """
        更新日记账记录

        Args:
            ctx: MCP上下文对象
            id: 日记账记录ID（主键）
            actual_counterpart_account_id: 实际对方账户ID，为0表示不创建对方流水，为有效资金账户ID则创建对方流水
            finance_account_id: 账户ID（可选）
            creation_date: 日期，格式：YYYY-MM-DD（可选）
            summary: 摘要（可选）
            counterpart_account_name: 对方账户名称（可选）
            income: 收入金额（可选）
            original_income: 原币收入金额（可选）
            expense: 支出金额（可选）
            original_expense: 原币支出金额（可选）
            income_exchange_rate: 收入汇率（可选）
            expense_exchange_rate: 支出汇率（可选）
            voucher_id: 凭证ID（可选）
            remark: 备注（可选）
            creator_id: 制单人ID（可选）
            account_counterpart_json: 账户对方科目信息（可选）
            serial_number: 流水号（可选）
            counterpart_bank: 对方银行（可选）
            counterpart_account_number: 对方账号（可选）
            original_document_number: 原单据编号（可选）
            counterpart_entry_id: 对方日记账流水ID（可选）

        参数补充说明:
        1. account_counterpart_json格式示例:
           {
               "accountingTitleId": 10690,
               "accountingTitleName": "1002 银行存款",
               "auxiliaries": [
                   {
                       "id": 454,
                       "code": "B003",
                       "name": "农业银行专用户",
                       "auxiliary_accounting_category_id": 502
                   }
               ]
           }
        2. actual_counterpart_account_id说明:
           - 为0表示不创建对方日记账流水
           - 为有效资金账户ID表示创建对方日记账流水，该资金账户必须绑定account_counterpart_json对应的科目+辅助
           - 可通过find_finance_account_tool查询account_counterpart_json对应的资金账户情况
        3. counterpart_entry_id: 如果更新时已知对方日记账流水ID，可通过此参数指定

        Returns:
            dict: 包含更新结果的字典，包含以下字段：
                - success: bool - 请求是否成功
                - message: str - 返回消息说明
                - data: dict - 更新结果数据，包含：
                    - affect_rows: int - 影响的行数
        """
        request_data = {
            "id": id,
            "ab_id": ab_id,
            "actual_counterpart_account_id": actual_counterpart_account_id,
        }
        # 只添加非None的字段
        optional_fields = {
            "finance_account_id": finance_account_id,
            "creation_date": creation_date,
            "summary": summary,
            "counterpart_account_name": counterpart_account_name,
            "income": income,
            "original_income": original_income,
            "expense": expense,
            "original_expense": original_expense,
            "income_exchange_rate": income_exchange_rate,
            "expense_exchange_rate": expense_exchange_rate,
            "voucher_id": voucher_id,
            "remark": remark,
            "creator_id": creator_id,
            "account_counterpart_json": account_counterpart_json,
            "serial_number": serial_number,
            "counterpart_bank": counterpart_bank,
            "counterpart_account_number": counterpart_account_number,
            "original_document_number": original_document_number,
            "counterpart_entry_id": counterpart_entry_id
        }
        for key, value in optional_fields.items():
            if value is not None:
                request_data[key] = value
        
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/cashier/journal_entry_update/", request_data)

    @mcp.tool(
        name="journal_entry_list"
    )
    def journal_entry_list_tool(
        ctx: Context,
        finance_account_id: int = Field(description="账户ID"),
        ab_id: int = Field(description="帐套ID"),
        date_mode: DateMode = Field(description="时间模式: period(帐期模式-YYYY-MM) 或 date(日期模式-YYYY-MM-DD)"),
        start_cashier_period: str = Field(description="开始时间，格式：YYYY-MM-DD或YYYY-MM"),
        end_cashier_period: str = Field(description="结束时间，格式：YYYY-MM-DD或YYYY-MM"),
        current: int = Field(default=1, description="页码（可选，默认1）"),
        pageSize: int = Field(default=10, description="每页记录数（可选，默认10，为0则返回所有记录）"),
        sorter: dict = Field(default=None, description="排序字段（可选）"),
        params: dict = Field(default=None, description="搜索参数（可选）"),
        filters: dict = Field(default=None, description="过滤条件（可选）"),
        voucher_search: str = Field(default=None, description="凭证情况（可选）"),
        summary: str = Field(default=None, description="摘要（可选）"),
        creator: str = Field(default=None, description="制单人（可选）"),
        amount: float = Field(default=None, description="金额（可选）"),
        opposite_account_subject: str = Field(default=None, description="账户对方科目（可选）"),
        opposite_account: str = Field(default=None, description="对方账户（可选）"),
        remark: str = Field(default=None, description="备注（可选）"),
        show_daily_subtotal: bool = Field(default=None, description="是否显示日小计（可选）"),
        keyWords: str = Field(default=None, description="关键字（可选）")
    ) -> dict:
        """
        分页查询日记账记录

        Returns:
            dict: 包含查询结果的字典，包含以下字段：
                - data: List[dict] - 日记账记录列表数据
                - total: int - 总记录数
                - current: int - 当前页码
                - pageSize: int - 每页记录数
        """
        request_data = {
            "finance_account_id": finance_account_id,
            "ab_id": ab_id,
            "date_mode": date_mode,
            "start_cashier_period": start_cashier_period,
            "end_cashier_period": end_cashier_period,
            "current": current,
            "pageSize": pageSize,
        }
        # 只添加非None的字段
        optional_fields = {
            "sorter": sorter,
            "params": params,
            "filters": filters,
            "voucher_search": voucher_search,
            "summary": summary,
            "creator": creator,
            "amount": amount,
            "opposite_account_subject": opposite_account_subject,
            "opposite_account": opposite_account,
            "remark": remark,
            "show_daily_subtotal": show_daily_subtotal,
            "keyWords": keyWords
        }
        for key, value in optional_fields.items():
            if value is not None:
                request_data[key] = value
        
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/cashier/journal_entry_list/", request_data)

    @mcp.tool(
        name="journal_entry_list_summary"
    )
    def journal_entry_list_summary_tool(
        ctx: Context,
        finance_account_id: int = Field(description="账户ID"),
        ab_id: int = Field(description="帐套ID"),
        date_mode: DateMode = Field(description="时间模式: period(帐期模式-YYYY-MM) 或 date(日期模式-YYYY-MM-DD)"),
        start_cashier_period: str = Field(description="开始时间，格式：YYYY-MM-DD或YYYY-MM"),
        end_cashier_period: str = Field(description="结束时间，格式：YYYY-MM-DD或YYYY-MM"),
        current: int = Field(default=1, description="页码（可选，默认1）"),
        pageSize: int = Field(default=10, description="每页记录数（可选，默认10，为0则返回所有记录）"),
        sorter: dict = Field(default=None, description="排序字段（可选）"),
        params: dict = Field(default=None, description="搜索参数（可选）"),
        filters: dict = Field(default=None, description="过滤条件（可选）"),
        voucher_search: str = Field(default=None, description="凭证情况（可选）"),
        summary: str = Field(default=None, description="摘要（可选）"),
        creator: str = Field(default=None, description="制单人（可选）"),
        amount: float = Field(default=None, description="金额（可选）"),
        opposite_account_subject: str = Field(default=None, description="账户对方科目（可选）"),
        opposite_account: str = Field(default=None, description="对方账户（可选）"),
        remark: str = Field(default=None, description="备注（可选）"),
        show_daily_subtotal: bool = Field(default=None, description="是否显示日小计（可选）"),
        keyWords: str = Field(default=None, description="关键字（可选）")
    ) -> dict:
        """
        查询日记账汇总信息

        Returns:
            dict: 包含汇总结果的字典，包含以下字段：
                - data: List[dict] - 日记账汇总数据
                - total: int - 总记录数
                - current: int - 当前页码
                - pageSize: int - 每页记录数
        """
        request_data = {
            "finance_account_id": finance_account_id,
            "ab_id": ab_id,
            "date_mode": date_mode,
            "start_cashier_period": start_cashier_period,
            "end_cashier_period": end_cashier_period,
            "current": current,
            "pageSize": pageSize,
        }
        # 只添加非None的字段
        optional_fields = {
            "sorter": sorter,
            "params": params,
            "filters": filters,
            "voucher_search": voucher_search,
            "summary": summary,
            "creator": creator,
            "amount": amount,
            "opposite_account_subject": opposite_account_subject,
            "opposite_account": opposite_account,
            "remark": remark,
            "show_daily_subtotal": show_daily_subtotal,
            "keyWords": keyWords
        }
        for key, value in optional_fields.items():
            if value is not None:
                request_data[key] = value
        
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/cashier/journal_entry_list_summary/", request_data)

    @mcp.tool(
        name="journal_entry_batch_delete"
    )
    def journal_entry_batch_delete_tool(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        ids: List[int] = Field(description="要删除的日记账记录ID列表")
    ) -> dict:
        """
        批量删除日记账记录

        Returns:
            dict: 包含删除结果的字典，包含以下字段：
                - affect_rows: int - 影响的行数
        """
        request_data = {
            "ab_id": ab_id,
            "ids": ids
        }
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/cashier/journal_entry_batch_delete/", request_data)

    @mcp.tool(
        name="journal_entry_batch_create"
    )
    def journal_entry_batch_create_tool(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        journal_entries: List[dict] = Field(description="批量新增的日记账列表，每个日记账的数据结构参考单个新增的参数")
    ) -> dict:
        """
        批量新增日记账记录

        Args:
            ab_id: 帐套id
            journal_entries: 日记帐明细数组
                finance_account_id: 资金账户ID
                creation_date: 日期，格式：YYYY-MM-DD
                currency_id: 币别ID
                actual_counterpart_account_id: 实际对方资金账户ID，为0表示不创建对方流水，为有效资金账户ID则创建对方流水
                summary: 摘要（可选）
                counterpart_account_name: 对方账户名称（可选）
                income: 收入金额（可选）
                original_income: 原币收入金额（可选）
                expense: 支出金额（可选）
                original_expense: 原币支出金额（可选）
                income_exchange_rate: 收入汇率（可选）
                expense_exchange_rate: 支出汇率（可选）
                voucher_id: 凭证ID（可选）
                remark: 备注（可选）
                creator_id: 制单人ID（可选）
                account_counterpart_json: 账户对方科目信息（可选）
                serial_number: 流水号（可选）
                counterpart_bank: 对方银行（可选）
                counterpart_account_number: 对方账号（可选）
                original_document_number: 原单据编号（可选）
                counterpart_entry_id: 对方日记账流水ID（可选）

        Returns:
            dict: 包含成功创建的记录ID列表和错误信息的字典，包含以下字段：
                - success: bool - 请求是否成功
                - message: str - 返回消息说明
                - data: dict - 创建结果数据，包含：
                    - record_ids: List[int] - 成功创建的日记账ID列表
                    - errors: List[dict] - 创建失败的错误信息列表
        """
        request_data = {
            "ab_id":ab_id,
            "journal_entries": journal_entries,
        }

        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/cashier/journal_entry_batch_create/", request_data)

    return mcp