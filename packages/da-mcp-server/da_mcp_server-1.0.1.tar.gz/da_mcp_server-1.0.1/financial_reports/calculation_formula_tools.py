from fastmcp import Context
from typing import List, Dict, Any
from config import config
from pydantic import Field
from config import config

def register_calculation_formula_tools(mcp):
    """注册计算公式管理相关的工具"""

    @mcp.tool()
    def calculation_formula_create(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        report_id: int = Field(description="报表ID"),
        accounting_title_id: int = Field(description="科目ID"),
        line_number: int = Field(description="行次"),
        operator: int = Field(description="运算符号(1-加,2-减)"),
        calculation_rule: int = Field(description="取数规则(1-余额,2-本级科目借方余额,3-本级科目贷方余额,4-末级科目借方余额,5-末级科目贷方余额,6-辅助核算借方余额,7-辅助核算贷方余额,8-发生额,9-借方发生额,10-贷方发生额)"),
        column_dimension: int = Field(default=None, description="列维度(1-通用,2-限定性,3-非限定性)")
    ) -> Dict[str, Any]:
        """
        新增报表计算公式

        补充说明
        1,这里的报表公式可适用于除“现金流量报表”以外全部报表,现金流量报表不适用,现金流量报表应该通过现金流量科目映射表来设置。

        Args:
            ab_id: 帐套id
            report_id: 报表ID,报表要在帐套内，属于帐套。
            accounting_title_id: 科目ID
            line_number: 行次
            operator: 运算符号(1-加,2-减)
            calculation_rule: 取数规则
                1. BALANCE (余额)
                统计方法：直接取科目的期末余额
                计算公式：ending_balance 字段值
                适用场景：资产负债表等需要期末余额的报表
                2. CURRENT_ACCOUNT_DEBIT_BALANCE (本级科目借方余额)
                统计方法：取当前科目级别的借方余额
                处理逻辑：
                如果余额 > 0，取余额值作为借方余额
                如果余额 ≤ 0，借方余额为0
                数据来源：debit_ending_balance 字段
                3. CURRENT_ACCOUNT_CREDIT_BALANCE (本级科目贷方余额)
                统计方法：取当前科目级别的贷方余额
                处理逻辑：
                如果余额 > 0，取余额值作为贷方余额
                如果余额 ≤ 0，贷方余额为0
                数据来源：credit_ending_balance 字段
                4. LAST_LEVEL_ACCOUNT_DEBIT_BALANCE (末级科目借方余额)
                统计方法：递归查找所有末级子科目的借方余额之和
                实现方式：
                遍历所有子科目
                如果是末级科目，取其借方余额
                如果不是末级科目，继续递归查找
                特点：包含所有最底层科目的借方余额汇总
                5. LAST_LEVEL_ACCOUNT_CREDIT_BALANCE (末级科目贷方余额)
                统计方法：递归查找所有末级子科目的贷方余额之和
                实现方式：与借方余额类似，但取贷方余额
                特点：包含所有最底层科目的贷方余额汇总
                6. AUXILIARY_DEBIT_BALANCE (辅助核算借方余额)
                统计方法：统计辅助核算科目的借方余额
                处理逻辑：
                如果科目启用了辅助核算：统计直接挂辅助的子科目借方余额
                如果科目未启用辅助核算：递归查找末级辅助科目或末级科目本身的借方余额
                适用场景：需要按辅助核算维度统计的报表
                7. AUXILIARY_CREDIT_BALANCE (辅助核算贷方余额)
                统计方法：统计辅助核算科目的贷方余额
                处理逻辑：与辅助核算借方余额类似，但取贷方余额
                特点：支持辅助核算维度的贷方余额统计
                8. OCCURRENCE (发生额)
                统计方法：计算科目的净发生额
                计算公式：
                借方科目：借方发生额 - 贷方发生额
                贷方科目：贷方发生额 - 借方发生额
                数据来源：损益凭证中的发生额数据
                9. DEBIT_OCCURRENCE (借方发生额)
                统计方法：直接取科目的借方发生额
                数据来源：current_period_accumulated_debit_amount 字段
                适用场景：利润表等需要发生额的报表
                10. CREDIT_OCCURRENCE (贷方发生额)
                统计方法：直接取科目的贷方发生额
                数据来源：current_period_accumulated_credit_amount 字段
                特点：纯发生额统计，不涉及余额计算
            column_dimension: 列维度(1-通用,2-限定性,3-非限定性)

        Returns:
            Dict[str, Any]: 返回新增记录ID
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "report_id": report_id,
            "line_number": line_number,
            "operator": operator,
            "calculation_rule": calculation_rule
        }

        # 添加可选参数
        if accounting_title_id is not None:
            request_data["accounting_title_id"] = accounting_title_id
        if column_dimension is not None:
            request_data["column_dimension"] = column_dimension

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/financial_reports/calculation_formula_create/",
            request_data
        )

        return response_data


    @mcp.tool()
    def balance_sheet_formula_list(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        report_id: int = Field(description="报表ID"),
        accounting_period: str = Field(description="会计期间，格式：YYYY-MM"),
        current: int = Field(default=1, ge=1, description="页码"),
        pageSize: int = Field(default=10, ge=0, description="每页记录数，为0则返回所有记录"),
        line_number: int = Field(default=None, description="行次")
    ) -> Dict[str, Any]:
        """
        分页查询资产负债表计算公式
        补充说明：
        1，改工具仅适用于以下报表类型：资产负债表
        Returns:
            Dict[str, Any]: 返回分页的资产负债表计算公式列表
          report_id: 报表ID
            accounting_title_id: 科目ID
            line_number: 行次
            operator: 运算符号(1-加,2-减)
            calculation_rule: 取数规则
                1. BALANCE (余额)
                统计方法：直接取科目的期末余额
                计算公式：ending_balance 字段值
                适用场景：资产负债表等需要期末余额的报表
                2. CURRENT_ACCOUNT_DEBIT_BALANCE (本级科目借方余额)
                统计方法：取当前科目级别的借方余额
                处理逻辑：
                如果余额 > 0，取余额值作为借方余额
                如果余额 ≤ 0，借方余额为0
                数据来源：debit_ending_balance 字段
                3. CURRENT_ACCOUNT_CREDIT_BALANCE (本级科目贷方余额)
                统计方法：取当前科目级别的贷方余额
                处理逻辑：
                如果余额 > 0，取余额值作为贷方余额
                如果余额 ≤ 0，贷方余额为0
                数据来源：credit_ending_balance 字段
                4. LAST_LEVEL_ACCOUNT_DEBIT_BALANCE (末级科目借方余额)
                统计方法：递归查找所有末级子科目的借方余额之和
                实现方式：
                遍历所有子科目
                如果是末级科目，取其借方余额
                如果不是末级科目，继续递归查找
                特点：包含所有最底层科目的借方余额汇总
                5. LAST_LEVEL_ACCOUNT_CREDIT_BALANCE (末级科目贷方余额)
                统计方法：递归查找所有末级子科目的贷方余额之和
                实现方式：与借方余额类似，但取贷方余额
                特点：包含所有最底层科目的贷方余额汇总
                6. AUXILIARY_DEBIT_BALANCE (辅助核算借方余额)
                统计方法：统计辅助核算科目的借方余额
                处理逻辑：
                如果科目启用了辅助核算：统计直接挂辅助的子科目借方余额
                如果科目未启用辅助核算：递归查找末级辅助科目或末级科目本身的借方余额
                适用场景：需要按辅助核算维度统计的报表
                7. AUXILIARY_CREDIT_BALANCE (辅助核算贷方余额)
                统计方法：统计辅助核算科目的贷方余额
                处理逻辑：与辅助核算借方余额类似，但取贷方余额
                特点：支持辅助核算维度的贷方余额统计
                8. OCCURRENCE (发生额)
                统计方法：计算科目的净发生额
                计算公式：
                借方科目：借方发生额 - 贷方发生额
                贷方科目：贷方发生额 - 借方发生额
                数据来源：损益凭证中的发生额数据
                9. DEBIT_OCCURRENCE (借方发生额)
                统计方法：直接取科目的借方发生额
                数据来源：current_period_accumulated_debit_amount 字段
                适用场景：利润表等需要发生额的报表
                10. CREDIT_OCCURRENCE (贷方发生额)
                统计方法：直接取科目的贷方发生额
                数据来源：current_period_accumulated_credit_amount 字段
                特点：纯发生额统计，不涉及余额计算
            column_dimension: 列维度(1-通用,2-限定性,3-非限定性)
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "current": current,
            "pageSize": pageSize,
            "accounting_period": accounting_period
        }

        # 添加可选参数
        if report_id is not None:
            request_data["report_id"] = report_id
        if line_number is not None:
            request_data["line_number"] = line_number

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/financial_reports/balance_sheet_formula_list/",
            request_data
        )

        return response_data

    @mcp.tool()
    def profit_statement_formula_list(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        report_id: int = Field(description="报表ID"),
        accounting_period: str = Field(description="会计期间，格式：YYYY-MM"),
        current: int = Field(default=1, ge=1, description="页码"),
        pageSize: int = Field(default=10, ge=0, description="每页记录数，为0则返回所有记录"),
        line_number: int = Field(default=None, description="行次"),
        column_dimension: int = Field(default=1, description="列维度(1-通用,2-限定性,3-非限定性)")
    ) -> Dict[str, Any]:
        """
        分页查询利润表计算公式

        补充说明:
        1,accounting_period一般取当前账期;
        2，report_id用report_list工具获取
        3,这个工具仅仅适用余额以下报表类型：利润表、收益及收益分配表、收入支出表、成本费用表、盈余及盈余分配表、业务活动表

        Returns:
            Dict[str, Any]: 返回分页的利润表计算公式列表
          report_id: 报表ID
            accounting_title_id: 科目ID
            line_number: 行次
            operator: 运算符号(1-加,2-减)
            calculation_rule: 取数规则
                1. BALANCE (余额)
                统计方法：直接取科目的期末余额
                计算公式：ending_balance 字段值
                适用场景：资产负债表等需要期末余额的报表
                2. CURRENT_ACCOUNT_DEBIT_BALANCE (本级科目借方余额)
                统计方法：取当前科目级别的借方余额
                处理逻辑：
                如果余额 > 0，取余额值作为借方余额
                如果余额 ≤ 0，借方余额为0
                数据来源：debit_ending_balance 字段
                3. CURRENT_ACCOUNT_CREDIT_BALANCE (本级科目贷方余额)
                统计方法：取当前科目级别的贷方余额
                处理逻辑：
                如果余额 > 0，取余额值作为贷方余额
                如果余额 ≤ 0，贷方余额为0
                数据来源：credit_ending_balance 字段
                4. LAST_LEVEL_ACCOUNT_DEBIT_BALANCE (末级科目借方余额)
                统计方法：递归查找所有末级子科目的借方余额之和
                实现方式：
                遍历所有子科目
                如果是末级科目，取其借方余额
                如果不是末级科目，继续递归查找
                特点：包含所有最底层科目的借方余额汇总
                5. LAST_LEVEL_ACCOUNT_CREDIT_BALANCE (末级科目贷方余额)
                统计方法：递归查找所有末级子科目的贷方余额之和
                实现方式：与借方余额类似，但取贷方余额
                特点：包含所有最底层科目的贷方余额汇总
                6. AUXILIARY_DEBIT_BALANCE (辅助核算借方余额)
                统计方法：统计辅助核算科目的借方余额
                处理逻辑：
                如果科目启用了辅助核算：统计直接挂辅助的子科目借方余额
                如果科目未启用辅助核算：递归查找末级辅助科目或末级科目本身的借方余额
                适用场景：需要按辅助核算维度统计的报表
                7. AUXILIARY_CREDIT_BALANCE (辅助核算贷方余额)
                统计方法：统计辅助核算科目的贷方余额
                处理逻辑：与辅助核算借方余额类似，但取贷方余额
                特点：支持辅助核算维度的贷方余额统计
                8. OCCURRENCE (发生额)
                统计方法：计算科目的净发生额
                计算公式：
                借方科目：借方发生额 - 贷方发生额
                贷方科目：贷方发生额 - 借方发生额
                数据来源：损益凭证中的发生额数据
                9. DEBIT_OCCURRENCE (借方发生额)
                统计方法：直接取科目的借方发生额
                数据来源：current_period_accumulated_debit_amount 字段
                适用场景：利润表等需要发生额的报表
                10. CREDIT_OCCURRENCE (贷方发生额)
                统计方法：直接取科目的贷方发生额
                数据来源：current_period_accumulated_credit_amount 字段
                特点：纯发生额统计，不涉及余额计算
                column_dimension: 列维度(1-通用,2-限定性,3-非限定性)
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "current": current,
            "pageSize": pageSize,
            "accounting_period": accounting_period
        }

        # 添加可选参数
        if report_id is not None:
            request_data["report_id"] = report_id
        if line_number is not None:
            request_data["line_number"] = line_number
        if column_dimension is not None:
            request_data["column_dimension"] = column_dimension

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/financial_reports/profit_statement_formula_list/",
            request_data
        )

        return response_data

    @mcp.tool()
    def calculation_formula_update(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        id: int = Field(description="计算公式ID"),
        report_id: int = Field(default=None, description="报表ID"),
        accounting_title_id: int = Field(default=None, description="科目ID"),
        line_number: int = Field(default=None, description="行次"),
        operator: int = Field(default=None, description="运算符号(1-加,2-减)"),
        calculation_rule: int = Field(default=None, description="取数规则(1-余额,2-本级科目借方余额,3-本级科目贷方余额,4-末级科目借方余额,5-末级科目贷方余额,6-辅助核算借方余额,7-辅助核算贷方余额,8-发生额,9-借方发生额,10-贷方发生额)")
    ) -> Dict[str, Any]:
        """
        更新报表计算公式

        Args:
            id: 计算公式ID
            report_id: 报表ID
            accounting_title_id: 科目ID
            line_number: 行次
            operator: 运算符号
            calculation_rule: 取数规则(1-余额,2-本级科目借方余额,3-本级科目贷方余额,4-末级科目借方余额,5-末级科目贷方余额,6-辅助核算借方余额,7-辅助核算贷方余额,8-发生额,9-借方发生额,10-贷方发生额)

        Returns:
            Dict[str, Any]: 返回影响的行数
        """
        # 构建请求数据
        request_data = {
            "ab_id":ab_id,
            "id": id
        }

        # 添加可选参数
        if report_id is not None:
            request_data["report_id"] = report_id
        if accounting_title_id is not None:
            request_data["accounting_title_id"] = accounting_title_id
        if line_number is not None:
            request_data["line_number"] = line_number
        if operator is not None:
            request_data["operator"] = operator
        if calculation_rule is not None:
            request_data["calculation_rule"] = calculation_rule

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/financial_reports/calculation_formula_update/",
            request_data
        )

        return response_data

    @mcp.tool()
    def calculation_formula_batch_delete(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        ids: List[int] = Field(description="要删除的计算公式ID列表")
    ) -> Dict[str, Any]:
        """
        批量删除报表计算公式

        Args:
            ids: 要删除的计算公式ID列表

        Returns:
            Dict[str, Any]: 返回删除操作的结果
        """
        # 构建请求数据
        request_data = {
            "ab_id":ab_id,
            "ids": ids
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/financial_reports/calculation_formula_batch_delete/",
            request_data
        )

        return response_data

    @mcp.tool()
    def calculation_formula_batch_create(
        ctx: Context,
        items: List[dict] = Field(description="批量新增的报表公式列表,数据结构参考单个新增的参数")
    ) -> Dict[str, Any]:
        """
        批量新增报表计算公式

        补充信息：
            每个报表公式项目的数据结构参考calculation_formula_create的参数说明

        Returns:
            Dict[str, Any]: 包含成功创建的记录ID列表和错误信息的字典，包含以下字段：
                - success: bool - 请求是否成功
                - message: str - 返回消息说明
                - data: dict - 创建结果数据，包含：
                    - created_ids: List[int] - 成功创建的公式ID列表
                    - errors: List[dict] - 创建失败的错误信息列表
        """
        request_data = {
            "formulas": items,
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/financial_reports/calculation_formula_batch_create/",
            request_data
        )

        return response_data

    return mcp