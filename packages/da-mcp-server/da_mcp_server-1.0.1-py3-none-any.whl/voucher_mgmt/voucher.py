from fastmcp import Context
from typing import List, Dict, Any, Optional, Union
from pydantic import Field
from config import config
from datetime import date
from config import config

def register_voucher_tools(mcp):
    """注册凭证管理相关的工具"""

    @mcp.tool()
    def voucher_create(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        voucher_prefix_id: int = Field(description="凭证字ID"),
        voucher_number: int = Field(description="凭证序号"),
        creation_time: str = Field(description="制单时间，格式：YYYY-MM-DD"),
        voucher_sheet_count: int = Field(description="单据张数"),
        source_module: int = Field(description="来源模块枚举值: 1-手工录入, 2-电子档案, 3-发票管理, 4-业务凭证, 5-资产, 6-期末结转, 7-工资"),
        voucher_details: List[Dict[str, Any]] = Field(description="""凭证详情列表，至少2条，每条包含以下字段：
            - accounting_title_id: int (必填) - 会计科目ID,,必须是明细科目
            - summary: str (必填) - 摘要
            - debit_amount: Decimal  - 借方金额，最大精度19位，小数2位
            - credit_amount: Decimal  - 贷方金额，最大精度19位，小数2位
            - currency_id: int(必填)  - 币别ID,没有开启外币核算和指定的情况下，一般为本位币ids
            - exchange_rate: Decimal - 汇率，最大精度19位，小数6位
            - original_currency_amount: Decimal  - 原币金额，最大精度19位，小数2位
            - quantity: Decimal  - 数量，最大精度19位，小数6位
            - unit_price: Decimal  - 单价，最大精度19位，小数6位
            - auxiliary_accountings: Dict (可选) - 辅助会计ID映射，格式：{'辅助类别id': '辅助id'}，允许为null
            """),
        remarks: str = Field(default=None, description="备注"),
        electronic_file_ids: List[int] = Field(default=None, description="附件清单IDs"),
        param_type: int = Field(default=None, description="参数类型枚举值: 0-编辑凭证, 1-日记账批量推凭, 2-日记账单个推凭, 3-固定资产新增推凭, 4-固定资产清理推凭, 5-减值准备凭证, 6-原值变动推凭, 7-累计折旧变动推凭, 8-计提折旧, 9-结转本期损益推凭, 10-会计电子档案推凭, 11-期末结转自定义模板推凭"),
        param: Dict[str, Any] = Field(default=None, description="额外参数"),
        push_batch: str = Field(default=None, description="推凭批次号")
    ) -> Dict[str, Any]:
        """
        新增凭证
        
        重要说明：
        1. 凭证详情(voucher_details)必须包含至少2条记录，且借贷金额必须平衡
        2. 每条凭证分录必须指定借方金额或贷方金额，不能同时为空或同时有值
        3. 金额字段精度：借贷金额和原币金额为2位小数，汇率/数量/单价为6位小数
        创建示例：
            {
            "ab_id": 80,
            "voucher_prefix_id": 718,
            "voucher_number": 9,
            "creation_time": "2025-10-02",
            "voucher_sheet_count": 1,
            "source_module": 1,
            "voucher_details": [
                {
                "accounting_title_id": 11347,
                "summary": "美元银行存款增加-建设银行",
                "debit_amount": 7200,
                "credit_amount": 0,
                "currency_id": 209,
                "exchange_rate": 7.2,
                "original_currency_amount": 1000,
                "quantity": 0,
                "unit_price": 0,
                "auxiliary_accountings": {
                    "526": 622
                }
                },
                {
                "accounting_title_id": 11347,
                "summary": "人民币银行存款减少-建设银行",
                "debit_amount": 0,
                "credit_amount": 7200,
                "currency_id": 207,
                "exchange_rate": 1,
                "original_currency_amount": 7200,
                "quantity": 1,
                "unit_price": 7200,
                "auxiliary_accountings": {
                    "526": 622
                }
                }
            ],
            "remarks": "美元兑换人民币"
            }
            
        Returns:
            Dict[str, Any]: 返回新增凭证的记录ID，格式：{"record_id": 123}
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "voucher_prefix_id": voucher_prefix_id,
            "voucher_number": voucher_number,
            "creation_time": creation_time,
            "voucher_sheet_count": voucher_sheet_count,
            "source_module": source_module,
            "voucher_details": voucher_details
        }

        # 添加可选参数
        if remarks is not None:
            request_data["remarks"] = remarks
        if electronic_file_ids is not None:
            request_data["electronic_file_ids"] = electronic_file_ids
        if param_type is not None:
            request_data["param_type"] = param_type
        if param is not None:
            request_data["param"] = param
        if push_batch is not None:
            request_data["push_batch"] = push_batch

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/voucher_create/",
            request_data
        )

        return response_data

    @mcp.tool()
    def voucher_update(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        id: int = Field(description="凭证ID"),
        voucher_prefix_id: int = Field(default=None, description="凭证字ID"),
        voucher_number: int = Field(default=None, description="凭证序号"),
        creation_time: str = Field(default=None, description="制单时间，格式：YYYY-MM-DD"),
        creator_id: int = Field(default=None, description="制单人ID"),
        approval_time: str = Field(default=None, description="审核时间，格式：YYYY-MM-DD"),
        approver_id: int = Field(default=None, description="审核人ID"),
        remarks: str = Field(default=None, description="备注"),
        voucher_sheet_count: int = Field(default=None, description="单据张数"),
        electronic_file_ids: List[int] = Field(default=None, description="附件清单IDs"),
        voucher_details: List[Dict[str, Any]] = Field(default=None, description="""凭证详情列表，会完全替换原有明细，每条包含以下字段：
            - id: int (可选) - 凭证明细ID，更新时传入，新增时不传
            - voucher_id: int (可选) - 凭证ID
            - accounting_title_id: int (可选) - 会计科目ID,必须是明细科目
            - summary: str (可选) - 摘要
            - debit_amount: Decimal - 借方金额，最大精度19位，小数2位，允许为null
            - credit_amount: Decimal - 贷方金额，最大精度19位，小数2位，允许为null
            - currency_id: int (可选) - 币别ID，允许为null
            - exchange_rate: Decimal - 汇率，最大精度19位，小数6位
            - original_currency_amount: Decimal - 原币金额，最大精度19位，小数2位
            - quantity: Decimal - 数量，最大精度19位，小数6位
            - unit_price: Decimal - 单价，最大精度19位，小数6位
            - auxiliary_code: str (可选) - 辅助代码，最大长度255，允许为空和null
            - auxiliary_name: str (可选) - 辅助名称，最大长度255，允许为空和null
            - auxiliary_accountings: Dict (可选) - 辅助会计ID映射，格式：{'辅助类别id': '辅助id'}，允许为null
            - auxiliary_voucher_details: List (可选) - 辅助凭证详情列表，每个元素包含：
                * id: int (可选) - 辅助凭证明细ID
                * auxiliary_accounting_category_id: int (必填) - 辅助核算类别ID
                * auxiliary_accounting_id: int (必填) - 辅助核算项目ID
                * auxiliary_accounting_category_name: str (可选) - 辅助核算类别名称
                * auxiliary_accounting_code: str (可选) - 辅助核算项目代码
                * auxiliary_accounting_name: str (可选) - 辅助核算项目名称
                * voucher_detail_id: int (可选) - 凭证明细ID
                * creation_time: str (可选) - 创建时间
                * creator_id: int (可选) - 创建人ID
            - line_number: int (可选) - 凭证明细的行次，允许为null
            - cash_flow_item_line_number: int (可选) - 现金流量项目行次，允许为null
            - accounting_title: Dict (可选) - 科目必要详情，包含：
                * is_foreign_currency_accounting_enabled: bool (可选) - 是否启用外币核算
                * is_quantity_accounting_enabled: bool (可选) - 是否启用数量核算
                * is_auxiliary_accounting_enabled: bool (可选) - 是否启用辅助核算
                * at_code: str (可选) - 科目代码
                * at_name: str (可选) - 科目名称
                * at_name_path: str (可选) - 科目层级名称路径
                * measurement_unit: str (可选) - 计量单位
                * parent_at_code: str (可选) - 父级科目代码
                * level: int (可选) - 科目层级
            """)
    ) -> Dict[str, Any]:
        """
        更新凭证
        
        重要说明：
        1. 只有id字段是必填的，其他字段均为可选，只更新传入的字段
        2. 如果提供了voucher_details，会完全替换原有的凭证明细
        3. 更新凭证明细时，需要保持借贷平衡
        4. 金额字段精度：借贷金额和原币金额为2位小数，汇率/数量/单价为6位小数
        5. 辅助核算配置方式（三选一，推荐使用 auxiliary_voucher_details）：
        - auxiliary_accountings: 简化格式，系统会自动创建辅助凭证明细
        - auxiliary_voucher_details: 详细格式，可精确控制每个辅助核算项目
        - auxiliary_code/auxiliary_name: 传统格式，适用于已有辅助组合
        6. accounting_title 字段主要用于提供科目核算属性，系统会根据实际科目配置进行验证
        
        Args:
            id: 凭证ID（必填）
            voucher_prefix_id: 凭证字ID
            voucher_number: 凭证序号
            creation_time: 制单时间
            creator_id: 制单人ID
            approval_time: 审核时间
            approver_id: 审核人ID
            remarks: 备注信息
            voucher_sheet_count: 单据张数
            electronic_file_ids: 电子档案附件ID列表
            voucher_details: 凭证详情列表，会完全替换原有明细
            
        Returns:
            Dict[str, Any]: 返回影响的行数，格式：{"affect_rows": 1}
        """
        # 构建请求数据
        request_data = {
            "id": id,
            "ab_id": ab_id
        }

        # 添加可选参数
        if voucher_prefix_id is not None:
            request_data["voucher_prefix_id"] = voucher_prefix_id
        if voucher_number is not None:
            request_data["voucher_number"] = voucher_number
        if creation_time is not None:
            request_data["creation_time"] = creation_time
        if creator_id is not None:
            request_data["creator_id"] = creator_id
        if approval_time is not None:
            request_data["approval_time"] = approval_time
        if approver_id is not None:
            request_data["approver_id"] = approver_id
        if remarks is not None:
            request_data["remarks"] = remarks
        if voucher_sheet_count is not None:
            request_data["voucher_sheet_count"] = voucher_sheet_count
        if electronic_file_ids is not None:
            request_data["electronic_file_ids"] = electronic_file_ids
        if voucher_details is not None:
            request_data["voucher_details"] = voucher_details

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/voucher_update/",
            request_data
        )

        return response_data
    @mcp.tool()
    def get_voucher_list(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        fields: List[str] = Field(description="选择返回的凭证字段，可选值：['id', 'ab_id', 'voucher_prefix_id', 'voucher_number', 'voucher_prefix_number', 'voucher_prefix_code', 'creation_time', 'creator_id', 'creator_name', 'creator_signature', 'approval_time', 'approver_id', 'approver_name', 'approver_signature', 'remarks', 'voucher_sheet_count', 'voucher_details', 'electronic_files_array', 'electronic_file_ids', 'is_accounting_closed']。如果为空，则返回所有字段。"),
        voucher_details_fields: List[str] = Field(default=None, description="选择返回的凭证详情字段，仅在fields包含'voucher_details'时有效。可选值：['id', 'voucher_id', 'accounting_title_id', 'accounting_title', 'currency_id', 'currency_code', 'auxiliary_code', 'auxiliary_name', 'quantity', 'unit_price', 'summary', 'debit_amount', 'credit_amount', 'exchange_rate', 'original_currency_amount', 'auxiliary_voucher_details', 'auxiliary_accountings', 'accounting_title_display_name', 'summary_display_name', 'at_code', 'at_names', 'line_number', 'cash_flow_item_line_number']。如果为空，则返回所有详情字段。"),
        current: int = Field(default=1, ge=1, description="页码"),
        pageSize: int = Field(default=10, ge=0, description="每页记录数，为0则返回所有记录"),
        sorter: Dict[str, str] = Field(default=None, description="排序字段，格式：{'字段名': 'ascend'|'descend'}"),
        params: Dict[str, Any] = Field(default=None, description="参数搜索条件"),
        filters: Dict[str, List[Any]] = Field(default=None, description="过滤条件"),
        id: int = Field(default=None, description="凭证ID"),
        enableNewVoucherQuerySort: bool = Field(default=None, description="启用新增凭证查询排序"),
        start_accounting_period: str = Field(default=None, description="开始会计期间，格式：YYYY-MM"),
        end_accounting_period: str = Field(default=None, description="结束会计期间，格式：YYYY-MM"),
        voucher_prefix_id: int = Field(default=None, description="凭证字ID"),
        voucher_number: str = Field(default=None, description="凭证号"),
        accounting_titles: str = Field(default=None, description="科目编码"),
        summary: str = Field(default=None, description="摘要"),
        voucher_audit_status: int = Field(default=None, description="审核状态"),
        source_module: int = Field(default=None, description="来源模块枚举值: 1-手工录入, 2-电子档案, 3-发票管理, 4-业务凭证, 5-资产, 6-期末结转, 7-工资"),
        auxiliary_accounting_category_id: int = Field(default=None, description="辅助类别ID"),
        auxiliary_accounting_id: int = Field(default=None, description="辅助ID"),
        amount_range: Dict[str, float] = Field(default=None, description="金额范围，格式：{'amount_from': 0, 'amount_to': 1000}"),
        original_amount_range: Dict[str, float] = Field(default=None, description="原币金额范围"),
        currency_id: int = Field(default=None, description="币别ID"),
        creator: str = Field(default=None, description="制单人"),
        foreign_currency_type: str = Field(default=None, description="外币核算类型"),
        quantity_accounting: str = Field(default=None, description="数量核算"),
        approval_person: str = Field(default=None, description="审核人"),
        remark_type: str = Field(default=None, description="备注类型"),
        remarks: str = Field(default=None, description="备注内容"),
        subject_and_auxiliary_separate: bool = Field(default=None, description="科目与辅助分开显示"),
        push_batch: str = Field(default=None, description="推凭唯一码"),
        keyword: str = Field(default=None, description="关键字"),
        voucher_prefix_number: str = Field(default=None, description="凭证字号")
    ) -> Dict[str, Any]:
        """
        分页查询凭证列表
        调用该工具的请一定选择必要的字段,尽量默认返回全部字段信息。
        Args:
            ab_id: 帐套ID（必填）
            其他参数均为可选的查询条件
            fields: 选择返回的凭证字段，可选值：['id', 'ab_id', 'voucher_prefix_id', 'voucher_number', 'voucher_prefix_number', 'voucher_prefix_code', 'creation_time', 'creator_id', 'creator_name', 'creator_signature', 'approval_time', 'approver_id', 'approver_name', 'approver_signature', 'remarks', 'voucher_sheet_count', 'voucher_details', 'electronic_files_array', 'electronic_file_ids', 'is_accounting_closed']。如果为空，则返回所有字段。
            voucher_details_fields: 选择返回的凭证详情字段，仅在fields包含'voucher_details'时有效。可选值：['id', 'voucher_id', 'accounting_title_id', 'accounting_title', 'currency_id', 'currency_code', 'auxiliary_code', 'auxiliary_name', 'quantity', 'unit_price', 'summary', 'debit_amount', 'credit_amount', 'exchange_rate', 'original_currency_amount', 'auxiliary_voucher_details', 'auxiliary_accountings', 'accounting_title_display_name', 'summary_display_name', 'at_code', 'at_names', 'line_number', 'cash_flow_item_line_number']。如果为空，则返回所有详情字段。

        Returns:
            Dict[str, Any]: 返回分页的凭证列表，根据fields参数过滤字段
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
        if id is not None:
            request_data["id"] = id
        if enableNewVoucherQuerySort is not None:
            request_data["enableNewVoucherQuerySort"] = enableNewVoucherQuerySort
        if start_accounting_period is not None:
            request_data["start_accounting_period"] = start_accounting_period
        if end_accounting_period is not None:
            request_data["end_accounting_period"] = end_accounting_period
        if voucher_prefix_id is not None:
            request_data["voucher_prefix_id"] = voucher_prefix_id
        if voucher_number is not None:
            request_data["voucher_number"] = voucher_number
        if accounting_titles is not None:
            request_data["accounting_titles"] = accounting_titles
        if summary is not None:
            request_data["summary"] = summary
        if voucher_audit_status is not None:
            request_data["voucher_audit_status"] = voucher_audit_status
        if source_module is not None:
            request_data["source_module"] = source_module
        if auxiliary_accounting_category_id is not None:
            request_data["auxiliary_accounting_category_id"] = auxiliary_accounting_category_id
        if auxiliary_accounting_id is not None:
            request_data["auxiliary_accounting_id"] = auxiliary_accounting_id
        if amount_range is not None:
            request_data["amount_range"] = amount_range
        if original_amount_range is not None:
            request_data["original_amount_range"] = original_amount_range
        if currency_id is not None:
            request_data["currency_id"] = currency_id
        if creator is not None:
            request_data["creator"] = creator
        if foreign_currency_type is not None:
            request_data["foreign_currency_type"] = foreign_currency_type
        if quantity_accounting is not None:
            request_data["quantity_accounting"] = quantity_accounting
        if approval_person is not None:
            request_data["approval_person"] = approval_person
        if remark_type is not None:
            request_data["remark_type"] = remark_type
        if remarks is not None:
            request_data["remarks"] = remarks
        if subject_and_auxiliary_separate is not None:
            request_data["subject_and_auxiliary_separate"] = subject_and_auxiliary_separate
        if push_batch is not None:
            request_data["push_batch"] = push_batch
        if keyword is not None:
            request_data["keyword"] = keyword
        if voucher_prefix_number is not None:
            request_data["voucher_prefix_number"] = voucher_prefix_number

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/get_voucher_list/",
            request_data
        )

        # 如果指定了字段过滤，则处理返回数据
        if fields is not None and response_data.get("success") and "data" in response_data and "data" in response_data["data"]:
            filtered_data = []
            for item in response_data["data"]["data"]:
                filtered_item = {}
                # 处理凭证字段过滤
                for field in fields:
                    if field in item:
                        if field == "voucher_details" and voucher_details_fields is not None:
                            # 处理凭证详情字段过滤
                            if item["voucher_details"] is not None:
                                filtered_details = []
                                for detail in item["voucher_details"]:
                                    filtered_detail = {}
                                    for detail_field in voucher_details_fields:
                                        if detail_field in detail:
                                            filtered_detail[detail_field] = detail[detail_field]
                                    filtered_details.append(filtered_detail)
                                filtered_item[field] = filtered_details
                            else:
                                filtered_item[field] = item[field]
                        else:
                            filtered_item[field] = item[field]
                filtered_data.append(filtered_item)
            # 更新返回数据中的数据列表
            response_data["data"]["data"] = filtered_data

        return response_data

    @mcp.tool()
    def voucher_batch_delete(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        ids: List[int] = Field(description="要删除的凭证ID列表")
    ) -> Dict[str, Any]:
        """
        批量删除凭证
        
        Args:
            ids: 要删除的凭证ID列表
            
        Returns:
            Dict[str, Any]: 返回删除操作的结果
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "ids": ids
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/voucher_batch_delete/",
            request_data
        )

        return response_data

    @mcp.tool()
    def voucher_audit(
        ctx: Context,
        id: int = Field(description="凭证ID"),
        ab_id: int = Field(description="帐套ID")
    ) -> Dict[str, Any]:
        """
        审核凭证
        
        Args:
            id: 凭证ID
            ab_id: 帐套ID
            
        Returns:
            Dict[str, Any]: 返回审核操作的结果
        """
        # 构建请求数据
        request_data = {
            "id": id,
            "ab_id": ab_id
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/voucher_audit/",
            request_data
        )

        return response_data

    @mcp.tool()
    def voucher_un_audit(
        ctx: Context,
        id: int = Field(description="凭证ID"),
        ab_id: int = Field(description="帐套ID")
    ) -> Dict[str, Any]:
        """
        反审核凭证
        
        Args:
            id: 凭证ID
            ab_id: 帐套ID
            
        Returns:
            Dict[str, Any]: 返回反审核操作的结果
        """
        # 构建请求数据
        request_data = {
            "id": id,
            "ab_id": ab_id
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/voucher_un_audit/",
            request_data
        )

        return response_data

    @mcp.tool()
    def generate_voucher_number(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        voucher_prefix_id: int = Field(description="凭证字ID"),
        period: str = Field(description="期号，格式：YYYY-MM 或 YYYY-MM-DD")
    ) -> Dict[str, Any]:
        """
        自动生成凭证序号
        
        Args:
            ab_id: 帐套ID
            voucher_prefix_id: 凭证字ID
            period: 期号
            
        Returns:
            Dict[str, Any]: 返回生成的凭证序号
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "voucher_prefix_id": voucher_prefix_id,
            "period": period
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/generate_voucher_number/",
            request_data
        )

        return response_data

    @mcp.tool()
    def voucher_batch_create(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        vouchers: List[dict] = Field(description="批量新增的凭证列表,数据结构参考单个新增的参数")
    ) -> Dict[str, Any]:
        """
        批量新增凭证

        补充信息：
            每个凭证项目的数据结构参考voucher_create的参数说明
        请求示例：
        {
            "ab_id":80,
        vouchers:[{
            "ab_id": 80,
            "voucher_prefix_id": 718,
            "voucher_number": 9,
            "creation_time": "2025-10-02",
            "voucher_sheet_count": 1,
            "source_module": 1,
            "voucher_details": [
                {
                "accounting_title_id": 11347,
                "summary": "美元银行存款增加-建设银行",
                "debit_amount": 7200,
                "credit_amount": 0,
                "currency_id": 209,
                "exchange_rate": 7.2,
                "original_currency_amount": 1000,
                "quantity": null,
                "unit_price": null,
                "auxiliary_accountings": {
                    "526": 622
                }
                },
                {
                "accounting_title_id": 11347,
                "summary": "人民币银行存款减少-建设银行",
                "debit_amount": 0,
                "credit_amount": 7200,
                "currency_id": 207,
                "exchange_rate": 1,
                "original_currency_amount": 7200,
                "quantity": 1,
                "unit_price": 7200,
                "auxiliary_accountings": {
                    "526": 622
                }
                }
            ],
            "remarks": "美元兑换人民币"
            }]
        }

        Returns:
            Dict[str, Any]: 包含成功创建的记录ID列表和错误信息的字典，包含以下字段：
                - success: bool - 请求是否成功
                - message: str - 返回消息说明
                - data: dict - 创建结果数据，包含：
                    - record_ids: List[int] - 成功创建的凭证ID列表
                    - errors: List[dict] - 创建失败的错误信息列表
        """
        request_data = {
            "vouchers": vouchers,
            "ab_id": ab_id
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/voucher_batch_create/",
            request_data
        )

        return response_data

    return mcp