from fastmcp import Context
from typing import List, Dict, Any, Optional, Union
from pydantic import Field
from config import config

def register_ledger_mgmt_tools(mcp):
    """注册账簿管理相关的工具"""

    @mcp.tool()
    def query_ledger_details(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        fields: List[str] = Field(description="选择返回的字段，可选值：['accounting_title_id', 'at_code', 'at_name', 'at_code_path', 'at_name_path', 'auxiliary_code', 'auxiliary_name', 'at_direction', 'period', 'debit_amount', 'credit_amount', 'account_balance', 'original_debit_amount', 'original_credit_amount', 'original_account_balance', 'fc_code', 'direction_str']。"),
        start_accounting_period: str = Field(description="开始会计期间，格式：YYYY-MM"),
        end_accounting_period: str = Field(description="结束会计期间，格式：YYYY-MM"),
        accounting_title_level_type: int = Field(description="科目级次类型(1: 至最末级,2: 仅显示一级,3: 仅显示最末级,4: 自定义范围)"),
        current: int = Field(default=1, ge=1, description="页码"),
        pageSize: int = Field(default=10, ge=0, description="每页记录数，为0则返回所有记录"),
        sorter: Dict[str, str] = Field(default=None, description="排序字段，格式：{'字段名': 'ascend'|'descend'}"),
        params: Dict[str, Any] = Field(default=None, description="参数搜索条件"),
        filters: Dict[str, List[Any]] = Field(default=None, description="过滤条件"),
        currency_id: str = Field(default='functional', description="币别(functional:综合本位币,allCurrencies:所有币种,allCurrenciesMultiColumn:所有币种多栏式,或者传递币别的id)"),
        start_accounting_title: str = Field(default=None, description="开始科目"),
        end_accounting_title: str = Field(default=None, description="结束科目"),
        accounting_title_level: Dict[str, int] = Field(default=None, description='科目级次范围(示例:{"startLevel": 2, "endLevel": 8})'),
        show_auxiliary_accounting: bool = Field(default=False, description="显示辅助核算"),
        hide_zero_balance: bool = Field(default=False, description="余额为零不显示"),
        hide_zero_balance_and_occurrence: bool = Field(default=False, description="无发生额且余额为0不显示"),
        hide_current_total_and_yearly_total: bool = Field(default=False, description="无发生额不显示本期合计、本年累计")
    ) -> Dict[str, Any]:
        """
        查询明细账

        Returns:
            Dict[str, Any]: 返回明细账数据,返回值中account_balance是转换为本位币后的余额,一个币种的原币余额是original_account_balance.
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "current": current,
            "pageSize": pageSize,
            "start_accounting_period": start_accounting_period,
            "end_accounting_period": end_accounting_period,
            "accounting_title_level_type": accounting_title_level_type
        }

        # 添加可选参数
        if sorter is not None:
            request_data["sorter"] = sorter
        if params is not None:
            request_data["params"] = params
        if filters is not None:
            request_data["filters"] = filters
        if currency_id is not None:
            request_data["currency_id"] = currency_id
        if start_accounting_title is not None:
            request_data["start_accounting_title"] = start_accounting_title
        if end_accounting_title is not None:
            request_data["end_accounting_title"] = end_accounting_title
        if accounting_title_level is not None:
            request_data["accounting_title_level"] = accounting_title_level
        if show_auxiliary_accounting is not None:
            request_data["show_auxiliary_accounting"] = show_auxiliary_accounting
        if hide_zero_balance is not None:
            request_data["hide_zero_balance"] = hide_zero_balance
        if hide_zero_balance_and_occurrence is not None:
            request_data["hide_zero_balance_and_occurrence"] = hide_zero_balance_and_occurrence
        if hide_current_total_and_yearly_total is not None:
            request_data["hide_current_total_and_yearly_total"] = hide_current_total_and_yearly_total

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/query_ledger_details/",
            request_data
        )

        # 处理字段过滤
        if response_data.get("success") and "data" in response_data and "data" in response_data["data"]:
            filtered_data = []
            for item in response_data["data"]["data"]:
                filtered_item = {}
                for field in fields:
                    if field in item:
                        filtered_item[field] = item[field]
                filtered_data.append(filtered_item)
            # 更新返回数据中的数据列表
            response_data["data"]["data"] = filtered_data

        return response_data

    @mcp.tool()
    def get_general_ldg(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        fields: List[str] = Field(description="选择返回的字段，可选值：['accounting_title_id', 'at_code', 'at_name', 'at_code_path', 'at_name_path', 'auxiliary_code', 'auxiliary_name', 'at_direction', 'period', 'debit_amount', 'credit_amount', 'account_balance', 'original_debit_amount', 'original_credit_amount', 'original_account_balance', 'fc_code', 'direction_str']。"),
        start_accounting_period: str = Field(description="开始会计期间，格式：YYYY-MM"),
        end_accounting_period: str = Field(description="结束会计期间，格式：YYYY-MM"),
        accounting_title_level_type: int = Field(description="科目级次类型(1: 至最末级,2: 仅显示一级,3: 仅显示最末级,4: 自定义范围)"),
        current: int = Field(default=1, ge=1, description="页码"),
        pageSize: int = Field(default=10, ge=0, description="每页记录数，为0则返回所有记录"),
        sorter: Dict[str, str] = Field(default=None, description="排序字段，格式：{'字段名': 'ascend'|'descend'}"),
        params: Dict[str, Any] = Field(default=None, description="参数搜索条件"),
        filters: Dict[str, List[Any]] = Field(default=None, description="过滤条件"),
        currency_id: str = Field(default='functional', description="币别(functional:综合本位币,allCurrencies:所有币种,allCurrenciesMultiColumn:所有币种多栏式,或者传递币别的id)"),
        start_accounting_title: str = Field(default=None, description="开始科目"),
        end_accounting_title: str = Field(default=None, description="结束科目"),
        accounting_title_level: Dict[str, int] = Field(default=None, description='科目级次范围(示例:{"startLevel": 2, "endLevel": 8})'),
        show_auxiliary_accounting: bool = Field(default=False, description="显示辅助核算"),
        hide_zero_balance: bool = Field(default=False, description="余额为零不显示"),
        hide_zero_balance_and_occurrence: bool = Field(default=False, description="无发生额且余额为0不显示"),
        hide_current_total_and_yearly_total: bool = Field(default=False, description="无发生额不显示本期合计、本年累计")
    ) -> Dict[str, Any]:
        """
        获得总帐

        Args:
            ab_id: 帐套ID
            start_accounting_period: 开始会计期间
            end_accounting_period: 结束会计期间
            currency_id: 币别
            start_accounting_title: 开始科目
            end_accounting_title: 结束科目
            accounting_title_level_type: 科目级次类型
            accounting_title_level: 科目级次范围
            show_auxiliary_accounting: 显示辅助核算
            hide_zero_balance: 余额为零不显示
            hide_zero_balance_and_occurrence: 无发生额且余额为0不显示
            hide_current_total_and_yearly_total: 无发生额不显示本期合计、本年累计

        Returns:
            Dict[str, Any]: 返回总账数据,返回值中account_balance是转换为本位币后的余额,一个币种的原币余额是original_account_balance.
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "current": current,
            "pageSize": pageSize,
            "start_accounting_period": start_accounting_period,
            "end_accounting_period": end_accounting_period,
            "accounting_title_level_type": accounting_title_level_type
        }

        # 添加可选参数
        if sorter is not None:
            request_data["sorter"] = sorter
        if params is not None:
            request_data["params"] = params
        if filters is not None:
            request_data["filters"] = filters
        if currency_id is not None:
            request_data["currency_id"] = currency_id
        if start_accounting_title is not None:
            request_data["start_accounting_title"] = start_accounting_title
        if end_accounting_title is not None:
            request_data["end_accounting_title"] = end_accounting_title
        if accounting_title_level is not None:
            request_data["accounting_title_level"] = accounting_title_level
        if show_auxiliary_accounting is not None:
            request_data["show_auxiliary_accounting"] = show_auxiliary_accounting
        if hide_zero_balance is not None:
            request_data["hide_zero_balance"] = hide_zero_balance
        if hide_zero_balance_and_occurrence is not None:
            request_data["hide_zero_balance_and_occurrence"] = hide_zero_balance_and_occurrence
        if hide_current_total_and_yearly_total is not None:
            request_data["hide_current_total_and_yearly_total"] = hide_current_total_and_yearly_total

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/get_general_ldg/",
            request_data
        )

        # 处理字段过滤
        if response_data.get("success") and "data" in response_data and "data" in response_data["data"]:
            filtered_data = []
            for item in response_data["data"]["data"]:
                filtered_item = {}
                for field in fields:
                    if field in item:
                        filtered_item[field] = item[field]
                filtered_data.append(filtered_item)
            # 更新返回数据中的数据列表
            response_data["data"]["data"] = filtered_data

        return response_data

    @mcp.tool()
    def get_trial_bal(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        fields: List[str] = Field(description="选择返回的字段，可选值：['accounting_title_id', 'at_code', 'at_name', 'at_code_path', 'at_name_path', 'auxiliary_code', 'auxiliary_name', 'auxiliary_category_id', 'auxiliary_category_name', 'at_direction', 'initial_balance', 'debit_initial_balance', 'credit_initial_balance', 'original_initial_balance', 'original_debit_initial_balance', 'original_credit_initial_balance', 'debit_current_period_amount', 'credit_current_period_amount', 'original_debit_current_period_amount', 'original_credit_current_period_amount', 'debit_annual_cumulative_amount', 'credit_annual_cumulative_amount', 'original_debit_annual_cumulative_amount', 'original_credit_annual_cumulative_amount', 'ending_balance', 'debit_ending_balance', 'credit_ending_balance', 'original_ending_balance', 'original_debit_ending_balance', 'original_credit_ending_balance', 'fc_code', 'fc_name', 'exchange_rate', 'currency_id']。"),
        start_accounting_period: str = Field(description="开始会计期间，格式：YYYY-MM"),
        end_accounting_period: str = Field(description="结束会计期间，格式：YYYY-MM"),
        accounting_title_level_type: int = Field(description="科目级次类型(1: 至最末级,2: 仅显示一级,3: 仅显示最末级,4: 自定义范围)"),
        current: int = Field(default=1, ge=1, description="页码"),
        pageSize: int = Field(default=10, ge=0, description="每页记录数，为0则返回所有记录"),
        sorter: Dict[str, str] = Field(default=None, description="排序字段，格式：{'字段名': 'ascend'|'descend'}"),
        params: Dict[str, Any] = Field(default=None, description="参数搜索条件"),
        filters: Dict[str, List[Any]] = Field(default=None, description="过滤条件"),
        auxiliary_accounting_category_id: int = Field(default=None, description="辅助类别id"),
        auxiliary_accounting_id: int = Field(default=None, description="辅助id"),
        show_auxiliary_accounting: bool = Field(default=False, description="显示辅助核算"),
        hide_zero_balance: bool = Field(default=False, description="隐藏无余额"),
        hide_zero_balance_and_occurrence: bool = Field(default=False, description="隐藏无余额且无发生额"),
        show_detailed_account_full_name: bool = Field(default=False, description="显示明细科目全称"),
        show_account_category_subtotal: bool = Field(default=False, description="显示科目类别小计"),
        hide_disabled_accounts: bool = Field(default=False, description="隐藏停用科目"),
        show_all_accounts: bool = Field(default=False, description="显示全部科目"),
        start_accounting_title: str = Field(default=None, description="开始科目"),
        end_accounting_title: str = Field(default=None, description="结束科目"),
        accounting_title_level: Dict[str, int] = Field(default=None, description='科目级次范围(示例:{"startLevel": 2, "endLevel": 8})'),
        currency_id: str = Field(default='functional', description="币别(functional:综合本位币,allCurrencies:所有币种,allCurrenciesMultiColumn:所有币种多栏式,或者传递币别的id)"),
        enable_currency_subtotal: bool = Field(default=False, description="是否开启小计区分币别"),
        accounting_titles: str = Field(default=None, description="科目代码集"),
        auxiliary_accounting_ids: List[int] = Field(default=None, description="辅助项目id集合"),
        accounting_title_category_id: int = Field(default=None, description="科目分类"),
        accounting_title_ids: List[int] = Field(default=None, description="科目id集合"),
        only_show_detail_account_auxiliary_combination: bool = Field(default=False, description="是否只显示明细科目的辅助组合")
    ) -> Dict[str, Any]:
        """
        获得科目余额

        Returns:
            Dict[str, Any]: 返回科目余额数据,返回值中account_balance是转换为本位币后的余额,一个币种的原币余额是original_account_balance.
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "current": current,
            "pageSize": pageSize,
            "start_accounting_period": start_accounting_period,
            "end_accounting_period": end_accounting_period,
            "accounting_title_level_type": accounting_title_level_type
        }

        # 添加可选参数
        if sorter is not None:
            request_data["sorter"] = sorter
        if params is not None:
            request_data["params"] = params
        if filters is not None:
            request_data["filters"] = filters
        if auxiliary_accounting_category_id is not None:
            request_data["auxiliary_accounting_category_id"] = auxiliary_accounting_category_id
        if auxiliary_accounting_id is not None:
            request_data["auxiliary_accounting_id"] = auxiliary_accounting_id
        if show_auxiliary_accounting is not None:
            request_data["show_auxiliary_accounting"] = show_auxiliary_accounting
        if hide_zero_balance is not None:
            request_data["hide_zero_balance"] = hide_zero_balance
        if hide_zero_balance_and_occurrence is not None:
            request_data["hide_zero_balance_and_occurrence"] = hide_zero_balance_and_occurrence
        if show_detailed_account_full_name is not None:
            request_data["show_detailed_account_full_name"] = show_detailed_account_full_name
        if show_account_category_subtotal is not None:
            request_data["show_account_category_subtotal"] = show_account_category_subtotal
        if hide_disabled_accounts is not None:
            request_data["hide_disabled_accounts"] = hide_disabled_accounts
        if show_all_accounts is not None:
            request_data["show_all_accounts"] = show_all_accounts
        if start_accounting_title is not None:
            request_data["start_accounting_title"] = start_accounting_title
        if end_accounting_title is not None:
            request_data["end_accounting_title"] = end_accounting_title
        if accounting_title_level is not None:
            request_data["accounting_title_level"] = accounting_title_level
        if currency_id is not None:
            request_data["currency_id"] = currency_id
        if enable_currency_subtotal is not None:
            request_data["enable_currency_subtotal"] = enable_currency_subtotal
        if accounting_titles is not None:
            request_data["accounting_titles"] = accounting_titles
        if auxiliary_accounting_ids is not None:
            request_data["auxiliary_accounting_ids"] = auxiliary_accounting_ids
        if accounting_title_category_id is not None:
            request_data["accounting_title_category_id"] = accounting_title_category_id
        if accounting_title_ids is not None:
            request_data["accounting_title_ids"] = accounting_title_ids
        if only_show_detail_account_auxiliary_combination is not None:
            request_data["only_show_detail_account_auxiliary_combination"] = only_show_detail_account_auxiliary_combination

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/get_trial_bal/",
            request_data
        )

        # 处理字段过滤
        if response_data.get("success") and "data" in response_data and "data" in response_data["data"]:
            filtered_data = []
            for item in response_data["data"]["data"]:
                filtered_item = {}
                for field in fields:
                    if field in item:
                        filtered_item[field] = item[field]
                filtered_data.append(filtered_item)
            # 更新返回数据中的数据列表
            response_data["data"]["data"] = filtered_data

        return response_data

    @mcp.tool()
    def get_trial_bal_summary(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        fields: List[str] = Field(description="选择返回的字段，可选值：['accounting_title_id', 'at_code', 'at_name', 'at_code_path', 'at_name_path', 'auxiliary_code', 'auxiliary_name', 'auxiliary_category_id', 'auxiliary_category_name', 'at_direction', 'initial_balance', 'debit_initial_balance', 'credit_initial_balance', 'original_initial_balance', 'original_debit_initial_balance', 'original_credit_initial_balance', 'debit_current_period_amount', 'credit_current_period_amount', 'original_debit_current_period_amount', 'original_credit_current_period_amount', 'debit_annual_cumulative_amount', 'credit_annual_cumulative_amount', 'original_debit_annual_cumulative_amount', 'original_credit_annual_cumulative_amount', 'ending_balance', 'debit_ending_balance', 'credit_ending_balance', 'original_ending_balance', 'original_debit_ending_balance', 'original_credit_ending_balance', 'fc_code', 'fc_name', 'exchange_rate', 'currency_id']。"),
        start_accounting_period: str = Field(description="开始会计期间，格式：YYYY-MM"),
        end_accounting_period: str = Field(description="结束会计期间，格式：YYYY-MM"),
        accounting_title_level_type: int = Field(description="科目级次类型(1: 至最末级,2: 仅显示一级,3: 仅显示最末级,4: 自定义范围)"),
        sorter: Dict[str, str] = Field(default=None, description="排序字段，格式：{'字段名': 'ascend'|'descend'}"),
        params: Dict[str, Any] = Field(default=None, description="参数搜索条件"),
        filters: Dict[str, List[Any]] = Field(default=None, description="过滤条件"),
        auxiliary_accounting_category_id: int = Field(default=None, description="辅助类别id"),
        auxiliary_accounting_id: int = Field(default=None, description="辅助id"),
        show_auxiliary_accounting: bool = Field(default=False, description="显示辅助核算"),
        hide_zero_balance: bool = Field(default=False, description="隐藏无余额"),
        hide_zero_balance_and_occurrence: bool = Field(default=False, description="隐藏无余额且无发生额"),
        show_detailed_account_full_name: bool = Field(default=False, description="显示明细科目全称"),
        show_account_category_subtotal: bool = Field(default=False, description="显示科目类别小计"),
        hide_disabled_accounts: bool = Field(default=False, description="隐藏停用科目"),
        show_all_accounts: bool = Field(default=False, description="显示全部科目"),
        start_accounting_title: str = Field(default=None, description="开始科目"),
        end_accounting_title: str = Field(default=None, description="结束科目"),
        accounting_title_level: Dict[str, int] = Field(default=None, description='科目级次范围(示例:{"startLevel": 2, "endLevel": 8})'),
        currency_id: str = Field(default='functional', description="币别(functional:综合本位币,allCurrencies:所有币种,allCurrenciesMultiColumn:所有币种多栏式,或者传递币别的id)"),
        enable_currency_subtotal: bool = Field(default=False, description="是否开启小计区分币别"),
        accounting_titles: str = Field(default=None, description="科目代码集"),
        auxiliary_accounting_ids: List[int] = Field(default=None, description="辅助项目id集合"),
        accounting_title_category_id: int = Field(default=None, description="科目分类"),
        accounting_title_ids: List[int] = Field(default=None, description="科目id集合"),
        only_show_detail_account_auxiliary_combination: bool = Field(default=False, description="是否只显示明细科目的辅助组合")
    ) -> Dict[str, Any]:
        """
        获得科目余额总计

        Args:
            ab_id: 帐套ID
            auxiliary_accounting_category_id: 辅助类别id
            auxiliary_accounting_id: 辅助id
            start_accounting_period: 开始会计期间
            end_accounting_period: 结束会计期间
            show_auxiliary_accounting: 显示辅助核算
            hide_zero_balance: 隐藏无余额
            hide_zero_balance_and_occurrence: 隐藏无余额且无发生额
            show_detailed_account_full_name: 显示明细科目全称
            show_account_category_subtotal: 显示科目类别小计
            hide_disabled_accounts: 隐藏停用科目
            show_all_accounts: 显示全部科目
            start_accounting_title: 开始科目
            end_accounting_title: 结束科目
            accounting_title_level_type: 科目级次类型
            accounting_title_level: 科目级次范围
            currency_id: 币别
            enable_currency_subtotal: 是否开启小计区分币别
            accounting_titles: 科目代码集
            auxiliary_accounting_ids: 辅助项目id集合
            accounting_title_category_id: 科目分类
            accounting_title_ids: 科目id集合
            only_show_detail_account_auxiliary_combination: 是否只显示明细科目的辅助组合

        Returns:
            Dict[str, Any]: 返回科目余额总计数据,返回值中account_balance是转换为本位币后的余额,一个币种的原币余额是original_account_balance.
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "start_accounting_period": start_accounting_period,
            "end_accounting_period": end_accounting_period,
            "accounting_title_level_type": accounting_title_level_type
        }

        # 添加可选参数
        if sorter is not None:
            request_data["sorter"] = sorter
        if params is not None:
            request_data["params"] = params
        if filters is not None:
            request_data["filters"] = filters
        if auxiliary_accounting_category_id is not None:
            request_data["auxiliary_accounting_category_id"] = auxiliary_accounting_category_id
        if auxiliary_accounting_id is not None:
            request_data["auxiliary_accounting_id"] = auxiliary_accounting_id
        if show_auxiliary_accounting is not None:
            request_data["show_auxiliary_accounting"] = show_auxiliary_accounting
        if hide_zero_balance is not None:
            request_data["hide_zero_balance"] = hide_zero_balance
        if hide_zero_balance_and_occurrence is not None:
            request_data["hide_zero_balance_and_occurrence"] = hide_zero_balance_and_occurrence
        if show_detailed_account_full_name is not None:
            request_data["show_detailed_account_full_name"] = show_detailed_account_full_name
        if show_account_category_subtotal is not None:
            request_data["show_account_category_subtotal"] = show_account_category_subtotal
        if hide_disabled_accounts is not None:
            request_data["hide_disabled_accounts"] = hide_disabled_accounts
        if show_all_accounts is not None:
            request_data["show_all_accounts"] = show_all_accounts
        if start_accounting_title is not None:
            request_data["start_accounting_title"] = start_accounting_title
        if end_accounting_title is not None:
            request_data["end_accounting_title"] = end_accounting_title
        if accounting_title_level is not None:
            request_data["accounting_title_level"] = accounting_title_level
        if currency_id is not None:
            request_data["currency_id"] = currency_id
        if enable_currency_subtotal is not None:
            request_data["enable_currency_subtotal"] = enable_currency_subtotal
        if accounting_titles is not None:
            request_data["accounting_titles"] = accounting_titles
        if auxiliary_accounting_ids is not None:
            request_data["auxiliary_accounting_ids"] = auxiliary_accounting_ids
        if accounting_title_category_id is not None:
            request_data["accounting_title_category_id"] = accounting_title_category_id
        if accounting_title_ids is not None:
            request_data["accounting_title_ids"] = accounting_title_ids
        if only_show_detail_account_auxiliary_combination is not None:
            request_data["only_show_detail_account_auxiliary_combination"] = only_show_detail_account_auxiliary_combination

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/get_trial_bal_summary/",
            request_data
        )

        # 处理字段过滤 (注意 get_trial_bal_summary 返回的是直接列表)
        if response_data.get("success") and "data" in response_data:
            filtered_data = []
            for item in response_data["data"]:
                filtered_item = {}
                for field in fields:
                    if field in item:
                        filtered_item[field] = item[field]
                filtered_data.append(filtered_item)
            # 更新返回数据
            response_data["data"] = filtered_data

        return response_data

    @mcp.tool()
    def get_quantity_amount_general(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        fields: List[str] = Field(description="选择返回的字段，可选值：['accounting_title_category_id', 'accounting_title_sub_category_id', 'is_cash_account', 'is_auxiliary_accounting_enabled', 'is_detail_account', 'accounting_title_id', 'at_code', 'at_code_path', 'parent_at_code', 'at_name', 'at_name_path', 'auxiliary_id', 'auxiliary_code', 'auxiliary_name', 'initial_direction_str', 'ending_direction_str', 'at_direction', 'measurement_unit', 'initial_unit_price', 'initial_balance', 'initial_quantity', 'debit_current_period_amount', 'credit_current_period_amount', 'debit_current_period_quantity', 'credit_current_period_quantity', 'debit_annual_cumulative_amount', 'credit_annual_cumulative_amount', 'debit_annual_cumulative_quantity', 'credit_annual_cumulative_quantity', 'ending_balance', 'ending_unit_price', 'ending_quantity', 'is_sub_total', 'fc_code', 'fc_name', 'exchange_rate', 'currency_id']。"),
        start_accounting_period: str = Field(description="开始会计期间，格式：YYYY-MM"),
        end_accounting_period: str = Field(description="结束会计期间，格式：YYYY-MM"),
        accounting_title_level_type: int = Field(description="科目级次类型(1: 至最末级,2: 仅显示一级,3: 仅显示最末级,4: 自定义范围)"),
        current: int = Field(default=1, ge=1, description="页码"),
        pageSize: int = Field(default=10, ge=0, description="每页记录数，为0则返回所有记录"),
        sorter: Dict[str, str] = Field(default=None, description="排序字段，格式：{'字段名': 'ascend'|'descend'}"),
        params: Dict[str, Any] = Field(default=None, description="参数搜索条件"),
        filters: Dict[str, List[Any]] = Field(default=None, description="过滤条件"),
        show_auxiliary_accounting: bool = Field(default=False, description="显示辅助核算"),
        hide_zero_balance: bool = Field(default=False, description="隐藏无余额"),
        hide_zero_balance_and_occurrence: bool = Field(default=False, description="隐藏无余额且无发生额"),
        quantity_rounded: int = Field(default=2, description="数量小数位数"),
        unit_price_rounded: int = Field(default=2, description="单价小数位数"),
        start_accounting_title: str = Field(default=None, description="开始科目"),
        end_accounting_title: str = Field(default=None, description="结束科目"),
        accounting_title_level: Dict[str, int] = Field(default=None, description='科目级次范围(示例:{"startLevel": 2, "endLevel": 8})'),
        show_detailed_account_full_name: bool = Field(default=False, description="显示科目全路径名称"),
        currency_id: str = Field(default="functional", description="币别(functional:综合本位币,allCurrencies:所有币种,allCurrenciesMultiColumn:所有币种多栏式,或者传递币别的id)")
    ) -> Dict[str, Any]:
        """
        获得数量金额余额表

        返回 QuantityAmountGeneralRespData 数据结构，包含以下字段：

        基本信息字段：
        - accounting_title_category_id: Integer - 科目类别ID
        - accounting_title_sub_category_id: Integer - 科目子类别ID
        - is_cash_account: Boolean - 是否是现金科目
        - is_auxiliary_accounting_enabled: Boolean - 科目是否开启辅助核算
        - is_detail_account: Boolean - 是否是末级科目
        - accounting_title_id: Integer - 科目ID
        - at_code: String - 科目代码
        - at_code_path: String - 科目代码路径
        - parent_at_code: String - 父科目代码
        - at_name: String - 科目名称
        - at_name_path: String - 科目名称路径
        - auxiliary_id: String - 辅助科目ID组合
        - auxiliary_code: String - 辅助科目代码组合
        - auxiliary_name: String - 辅助科目名称组合
        - initial_direction_str: String - 期初余额方向 (借/贷/平)
        - ending_direction_str: String - 期末余额方向 (借/贷/平)

        方向字段：
        - at_direction: ChoiceField - 科目方向 (AccountingEntryType: 0-借方, 1-贷方)

        计量单位字段：
        - measurement_unit: String - 计量单位

        期初余额字段：
        - initial_unit_price: Decimal - 期初单价 (小数位: 6位)
        - initial_balance: Decimal - 期初金额 (小数位: 2位)
        - initial_quantity: Decimal - 期初数量 (小数位: 6位)

        本期发生额字段：
        - debit_current_period_amount: Decimal - 本期借方金额 (小数位: 2位)
        - credit_current_period_amount: Decimal - 本期贷方金额 (小数位: 2位)
        - debit_current_period_quantity: Decimal - 本期借方数量 (小数位: 6位)
        - credit_current_period_quantity: Decimal - 本期贷方数量 (小数位: 6位)

        本年累计发生额字段：
        - debit_annual_cumulative_amount: Decimal - 本年累计借方金额 (小数位: 2位)
        - credit_annual_cumulative_amount: Decimal - 本年累计贷方金额 (小数位: 2位)
        - debit_annual_cumulative_quantity: Decimal - 本年累计借方数量 (小数位: 6位)
        - credit_annual_cumulative_quantity: Decimal - 本年累计贷方数量 (小数位: 6位)

        期末余额字段：
        - ending_balance: Decimal - 期末余额 (小数位: 2位)
        - ending_unit_price: Decimal - 期末单价 (小数位: 6位)
        - ending_quantity: Decimal - 期末数量 (小数位: 6位)

        其他字段：
        - is_sub_total: Boolean - 是否是科目类别小记记录
        - fc_code: String - 原币币种代码
        - fc_name: String - 原币币种名称
        - exchange_rate: Decimal - 汇率 (小数位: 4位)
        - currency_id: String - 币别

枚举类型说明：
        - AccountingEntryType: 0-借方, 1-贷方
        - 方向字符串: 借-借方余额, 贷-贷方余额, 平-余额为零

        Returns:
            Dict[str, Any]: 返回数量金额总账数据
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "current": current,
            "pageSize": pageSize,
            "start_accounting_period": start_accounting_period,
            "end_accounting_period": end_accounting_period,
            "accounting_title_level_type": accounting_title_level_type,
            "is_quantity_accounting_enabled": True,
            "show_detailed_account_full_name": show_detailed_account_full_name,
            "currency_id": currency_id,
            "quantity_rounded": quantity_rounded,
            "unit_price_rounded": unit_price_rounded
        }

        # 添加可选参数
        if sorter is not None:
            request_data["sorter"] = sorter
        if params is not None:
            request_data["params"] = params
        if filters is not None:
            request_data["filters"] = filters
        if show_auxiliary_accounting is not None:
            request_data["show_auxiliary_accounting"] = show_auxiliary_accounting
        if hide_zero_balance is not None:
            request_data["hide_zero_balance"] = hide_zero_balance
        if hide_zero_balance_and_occurrence is not None:
            request_data["hide_zero_balance_and_occurrence"] = hide_zero_balance_and_occurrence
        if start_accounting_title is not None:
            request_data["start_accounting_title"] = start_accounting_title
        if end_accounting_title is not None:
            request_data["end_accounting_title"] = end_accounting_title
        if accounting_title_level is not None:
            request_data["accounting_title_level"] = accounting_title_level

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/get_quantity_amount_general/",
            request_data
        )

        # 处理字段过滤
        if response_data.get("success") and "data" in response_data and "data" in response_data["data"]:
            filtered_data = []
            for item in response_data["data"]["data"]:
                filtered_item = {}
                for field in fields:
                    if field in item:
                        filtered_item[field] = item[field]
                filtered_data.append(filtered_item)
            # 更新返回数据中的数据列表
            response_data["data"]["data"] = filtered_data

        return response_data

    @mcp.tool()
    def get_quantity_amount_detail(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        fields: List[str] = Field(description="选择返回的字段，可选值：['creation_time', 'voucher_prefix_number', 'at_code', 'at_name', 'at_code_path', 'at_name_path', 'auxiliary_code', 'auxiliary_name', 'at_direction', 'period', 'unit_price', 'debit_quantity', 'debit_amount', 'debit_price', 'credit_amount', 'credit_quantity', 'credit_price', 'account_balance', 'quantity_balance', 'balance_price', 'summary', 'direction_str']。"),
        start_accounting_period: str = Field(description="开始会计期间，格式：YYYY-MM"),
        end_accounting_period: str = Field(description="结束会计期间，格式：YYYY-MM"),
        accounting_title_level_type: int = Field(description="科目级次类型(1: 至最末级,2: 仅显示一级,3: 仅显示最末级,4: 自定义范围)"),
        is_quantity_accounting_enabled: bool = Field(description="是否开启数量核算"),
        current: int = Field(default=1, ge=1, description="页码"),
        pageSize: int = Field(default=10, ge=0, description="每页记录数，为0则返回所有记录"),
        sorter: Dict[str, str] = Field(default=None, description="排序字段，格式：{'字段名': 'ascend'|'descend'}"),
        params: Dict[str, Any] = Field(default=None, description="参数搜索条件"),
        filters: Dict[str, List[Any]] = Field(default=None, description="过滤条件"),
        accounting_title_id: int = Field(default=None, description="科目ID"),
        auxiliary_code: str = Field(default=None, description="辅助组合"),
        quantity_rounded: int = Field(default=2, description="数量小数位数"),
        unit_price_rounded: int = Field(default=2, description="单价小数位数"),
        start_accounting_title: str = Field(default=None, description="开始科目"),
        end_accounting_title: str = Field(default=None, description="结束科目"),
        accounting_title_level: Dict[str, int] = Field(default=None, description='科目级次范围(示例:{"startLevel": 2, "endLevel": 8})'),
        show_auxiliary_accounting: bool = Field(default=False, description="显示辅助核算"),
        hide_zero_balance: bool = Field(default=False, description="余额为零不显示"),
        hide_zero_balance_and_occurrence: bool = Field(default=False, description="无发生额且余额为0不显示"),
        hide_current_total_and_yearly_total: bool = Field(default=False, description="无发生额不显示本期合计、本年累计"),
        unit_price_selection: str = Field(default="reverse_calculation", description="单价取数(from_voucher:来自凭证,reverse_calculation:反算)")
    ) -> Dict[str, Any]:
        """
        获得数量金额明细账

        返回 QuantityAmountDetailRespData 数据结构，包含以下字段：

        基本信息字段：
        - creation_time: Date - 日期 (格式: YYYY-MM-DD)
        - voucher_prefix_number: String - 凭证字号
        - at_code: String - 科目代码
        - at_name: String - 科目名称
        - at_code_path: String - 科目代码路径
        - at_name_path: String - 科目名称路径
        - auxiliary_code: String - 辅助代码
        - auxiliary_name: String - 辅助名称

        方向字段：
        - at_direction: ChoiceField - 科目方向 (AccountingEntryType: 0-借方, 1-贷方)

        期间字段：
        - period: Date - 期间 (格式: YYYY-MM)

        单价字段：
        - unit_price: Decimal - 单价 (小数位: 6位)

        借方相关字段：
        - debit_quantity: Decimal - 借方数量 (小数位: 6位)
        - debit_amount: Decimal - 借方金额 (小数位: 2位)
        - debit_price: Decimal - 借方发生额单价 (小数位: 6位)

        贷方相关字段：
        - credit_amount: Decimal - 贷方金额 (小数位: 2位)
        - credit_quantity: Decimal - 贷方数量 (小数位: 6位)
        - credit_price: Decimal - 贷方发生额单价 (小数位: 6位)

        余额相关字段：
        - account_balance: Decimal - 科目余额 (小数位: 2位)
        - quantity_balance: Decimal - 数量余额 (小数位: 6位)
        - balance_price: Decimal - 余额单价 (小数位: 6位)

        其他字段：
        - summary: String - 摘要显示名称
        - direction_str: String - 方向名称 (借/贷/平)

        枚举类型说明：
        - AccountingEntryType: 0-借方, 1-贷方
        - 方向字符串: 借-借方余额, 贷-贷方余额, 平-余额为零

        Returns:
            Dict[str, Any]: 返回数量金额明细账数据
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "current": current,
            "pageSize": pageSize,
            "start_accounting_period": start_accounting_period,
            "end_accounting_period": end_accounting_period,
            "accounting_title_level_type": accounting_title_level_type,
            "is_quantity_accounting_enabled": is_quantity_accounting_enabled,
            "quantity_rounded": quantity_rounded,
            "unit_price_rounded": unit_price_rounded,
            "unit_price_selection": unit_price_selection
        }

        # 添加可选参数
        if sorter is not None:
            request_data["sorter"] = sorter
        if params is not None:
            request_data["params"] = params
        if filters is not None:
            request_data["filters"] = filters
        if accounting_title_id is not None:
            request_data["accounting_title_id"] = accounting_title_id
        if auxiliary_code is not None:
            request_data["auxiliary_code"] = auxiliary_code
        if start_accounting_title is not None:
            request_data["start_accounting_title"] = start_accounting_title
        if end_accounting_title is not None:
            request_data["end_accounting_title"] = end_accounting_title
        if accounting_title_level is not None:
            request_data["accounting_title_level"] = accounting_title_level
        if show_auxiliary_accounting is not None:
            request_data["show_auxiliary_accounting"] = show_auxiliary_accounting
        if hide_zero_balance is not None:
            request_data["hide_zero_balance"] = hide_zero_balance
        if hide_zero_balance_and_occurrence is not None:
            request_data["hide_zero_balance_and_occurrence"] = hide_zero_balance_and_occurrence
        if hide_current_total_and_yearly_total is not None:
            request_data["hide_current_total_and_yearly_total"] = hide_current_total_and_yearly_total

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/get_quantity_amount_detail/",
            request_data
        )

        # 处理字段过滤
        if response_data.get("success") and "data" in response_data and "data" in response_data["data"]:
            filtered_data = []
            for item in response_data["data"]["data"]:
                filtered_item = {}
                for field in fields:
                    if field in item:
                        filtered_item[field] = item[field]
                filtered_data.append(filtered_item)
            # 更新返回数据中的数据列表
            response_data["data"]["data"] = filtered_data

        return response_data
    
    @mcp.tool()
    def get_sub_ledger_det(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        fields: List[str] = Field(description="选择返回的字段，可选值：['creation_time', 'voucher_prefix_number', 'summary', 'debit_amount', 'credit_amount', 'account_balance', 'original_debit_amount', 'original_credit_amount', 'original_account_balance', 'direction_str', 'fc_code', 'exchange_rate', 'accounting_title_display_name', 'v_id']。"),
        start_accounting_period: str = Field(description="开始会计期间，格式：YYYY-MM"),
        end_accounting_period: str = Field(description="结束会计期间，格式：YYYY-MM"),
        accounting_title_level_type: int = Field(description="科目级次类型(1: 至最末级,2: 仅显示一级,3: 仅显示最末级,4: 自定义范围)"),
        current: int = Field(default=1, ge=1, description="页码"),
        pageSize: int = Field(default=10, ge=0, description="每页记录数，为0则返回所有记录"),
        sorter: Dict[str, str] = Field(default=None, description="排序字段，格式：{'字段名': 'ascend'|'descend'}"),
        params: Dict[str, Any] = Field(default=None, description="参数搜索条件"),
        filters: Dict[str, List[Any]] = Field(default=None, description="过滤条件"),
        auxiliary_accounting_category_id: int = Field(default=None, description="辅助类别id"),
        auxiliary_accounting_id: int = Field(default=None, description="辅助项目id"),
        show_subject: bool = Field(default=False, description="是否显示科目"),
        accounting_title_id: int = Field(default=None, description="科目id"),
        auxiliary_accounting_codes: str = Field(default=None, description="辅助代码"),
        accounting_titles: str = Field(default=None, description="科目代码"),
        accounting_title_level: Dict[str, int] = Field(default=None, description='科目级次范围(示例:{"startLevel": 2, "endLevel": 8})'),
        currency_id: str = Field(default='functional', description="币别(functional:综合本位币,allCurrencies:所有币种,allCurrenciesMultiColumn:所有币种多栏式,或者传递币别的id)"),
        hide_zero_balance: bool = Field(default=False, description="余额为0不显示"),
        hide_zero_balance_and_no_transaction: bool = Field(default=False, description="余额为0且发生额为0不显示"),
        keyWords: str = Field(default=None, description="关键词")
    ) -> Dict[str, Any]:
        """
        获得辅助项目明细

        返回 SubLedgerDetRespData 数据结构，包含以下字段：

        基本信息字段：
        - creation_time: Date - 制单时间 (格式: YYYY-MM-DD)
        - voucher_prefix_number: String - 凭证字号
        - summary: String - 摘要显示名称

        金额字段：
        - debit_amount: Decimal - 借方金额 (小数位: 2位)
        - credit_amount: Decimal - 贷方金额 (小数位: 2位)
        - account_balance: Decimal - 科目余额 (小数位: 2位)

        原币金额字段：
        - original_debit_amount: Decimal - 原币借方金额 (小数位: 2位)
        - original_credit_amount: Decimal - 原币贷方金额 (小数位: 2位)
        - original_account_balance: Decimal - 原币科目余额 (小数位: 2位)

        其他字段：
        - direction_str: String - 方向 (借/贷/平)
        - fc_code: String - 原币币种代码
        - exchange_rate: Decimal - 汇率 (小数位: 4位)
        - accounting_title_display_name: String - 显示科目名称
        - v_id: Integer - 凭证id

        Args:
            ab_id: 帐套ID
            start_accounting_period: 开始会计期间
            end_accounting_period: 结束会计期间
            auxiliary_accounting_category_id: 辅助类别id
            auxiliary_accounting_id: 辅助项目id
            show_subject: 是否显示科目
            accounting_title_id: 科目id
            auxiliary_accounting_codes: 辅助代码
            accounting_titles: 科目代码
            accounting_title_level_type: 科目级次类型
            accounting_title_level: 科目级次范围
            currency_id: 币别
            hide_zero_balance: 余额为0不显示
            hide_zero_balance_and_no_transaction: 余额为0且发生额为0不显示
            keyWords: 关键词

        Returns:
            Dict[str, Any]: 返回辅助项目明细数据
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "current": current,
            "pageSize": pageSize,
            "start_accounting_period": start_accounting_period,
            "end_accounting_period": end_accounting_period,
            "accounting_title_level_type": accounting_title_level_type
        }

        # 添加可选参数
        if sorter is not None:
            request_data["sorter"] = sorter
        if params is not None:
            request_data["params"] = params
        if filters is not None:
            request_data["filters"] = filters
        if auxiliary_accounting_category_id is not None:
            request_data["auxiliary_accounting_category_id"] = auxiliary_accounting_category_id
        if auxiliary_accounting_id is not None:
            request_data["auxiliary_accounting_id"] = auxiliary_accounting_id
        if show_subject is not None:
            request_data["show_subject"] = show_subject
        if accounting_title_id is not None:
            request_data["accounting_title_id"] = accounting_title_id
        if auxiliary_accounting_codes is not None:
            request_data["auxiliary_accounting_codes"] = auxiliary_accounting_codes
        if accounting_titles is not None:
            request_data["accounting_titles"] = accounting_titles
        if accounting_title_level is not None:
            request_data["accounting_title_level"] = accounting_title_level
        if currency_id is not None:
            request_data["currency_id"] = currency_id
        if hide_zero_balance is not None:
            request_data["hide_zero_balance"] = hide_zero_balance
        if hide_zero_balance_and_no_transaction is not None:
            request_data["hide_zero_balance_and_no_transaction"] = hide_zero_balance_and_no_transaction
        if keyWords is not None:
            request_data["keyWords"] = keyWords

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/get_sub_ledger_det/",
            request_data
        )

        # 处理字段过滤
        if response_data.get("success") and "data" in response_data and "data" in response_data["data"]:
            filtered_data = []
            for item in response_data["data"]["data"]:
                filtered_item = {}
                for field in fields:
                    if field in item:
                        filtered_item[field] = item[field]
                filtered_data.append(filtered_item)
            # 更新返回数据中的数据列表
            response_data["data"]["data"] = filtered_data

        return response_data

    @mcp.tool()
    def get_sub_ledger_bal(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        fields: List[str] = Field(description="选择返回的字段，可选值：['auxiliary_accounting_id', 'accounting_title_id', 'currency_id', 'key', 'prj_code', 'prj_name', 'code', 'parent_code', 'auxiliary_accounting_code', 'auxiliary_accounting_name', 'debit_initial_balance', 'credit_initial_balance', 'initial_balance', 'debit_current_period_amount', 'credit_current_period_amount', 'debit_annual_cumulative_amount', 'credit_annual_cumulative_amount', 'debit_ending_balance', 'credit_ending_balance', 'ending_balance', 'original_debit_initial_balance', 'original_credit_initial_balance', 'original_initial_balance', 'original_debit_current_period_amount', 'original_credit_current_period_amount', 'original_debit_annual_cumulative_amount', 'original_credit_annual_cumulative_amount', 'original_debit_ending_balance', 'original_credit_ending_balance', 'fc_code', 'exchange_rate']。"),
        start_accounting_period: str = Field(description="开始会计期间，格式：YYYY-MM"),
        end_accounting_period: str = Field(description="结束会计期间，格式：YYYY-MM"),
        auxiliary_accounting_category_id: int = Field(description="辅助类别id"),
        accounting_title_level_type: int = Field(description="科目级次类型(1: 至最末级,2: 仅显示一级,3: 仅显示最末级,4: 自定义范围)"),
        current: int = Field(default=1, ge=1, description="页码"),
        pageSize: int = Field(default=10, ge=0, description="每页记录数，为0则返回所有记录"),
        sorter: Dict[str, str] = Field(default=None, description="排序字段，格式：{'字段名': 'ascend'|'descend'}"),
        params: Dict[str, Any] = Field(default=None, description="参数搜索条件"),
        filters: Dict[str, List[Any]] = Field(default=None, description="过滤条件"),
        related_auxiliary_accounting_category_id: int = Field(default=None, description="关联辅助类别id"),
        related_auxiliary_accounting_id: int = Field(default=None, description="关联辅助id"),
        show_subject: bool = Field(default=False, description="是否显示科目"),
        accounting_title_id: int = Field(default=None, description="科目id"),
        auxiliary_accounting_codes: str = Field(default=None, description="辅助代码"),
        auxiliary_accounting_ids: List[int] = Field(default=None, description="辅助id清单"),
        accounting_titles: str = Field(default=None, description="科目代码"),
        accounting_title_level: Dict[str, int] = Field(default=None, description='科目级次范围(示例:{"startLevel": 2, "endLevel": 8})'),
        currency_id: str = Field(default='functional', description="币别(functional:综合本位币,allCurrencies:所有币种,allCurrenciesMultiColumn:所有币种多栏式,或者传递币别的id)"),
        hide_zero_balance: bool = Field(default=False, description="余额为0不显示"),
        hide_zero_balance_and_no_transaction: bool = Field(default=False, description="余额为0且发生额为0不显示")
    ) -> Dict[str, Any]:
        """
        获得辅助项目余额

        Returns:
            Dict[str, Any]: 返回辅助项目余额数据
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "current": current,
            "pageSize": pageSize,
            "start_accounting_period": start_accounting_period,
            "end_accounting_period": end_accounting_period,
            "auxiliary_accounting_category_id": auxiliary_accounting_category_id,
            "accounting_title_level_type": accounting_title_level_type
        }

        # 添加可选参数
        if sorter is not None:
            request_data["sorter"] = sorter
        if params is not None:
            request_data["params"] = params
        if filters is not None:
            request_data["filters"] = filters
        if related_auxiliary_accounting_category_id is not None:
            request_data["related_auxiliary_accounting_category_id"] = related_auxiliary_accounting_category_id
        if related_auxiliary_accounting_id is not None:
            request_data["related_auxiliary_accounting_id"] = related_auxiliary_accounting_id
        if show_subject is not None:
            request_data["show_subject"] = show_subject
        if accounting_title_id is not None:
            request_data["accounting_title_id"] = accounting_title_id
        if auxiliary_accounting_codes is not None:
            request_data["auxiliary_accounting_codes"] = auxiliary_accounting_codes
        if auxiliary_accounting_ids is not None:
            request_data["auxiliary_accounting_ids"] = auxiliary_accounting_ids
        if accounting_titles is not None:
            request_data["accounting_titles"] = accounting_titles
        if accounting_title_level is not None:
            request_data["accounting_title_level"] = accounting_title_level
        if currency_id is not None:
            request_data["currency_id"] = currency_id
        if hide_zero_balance is not None:
            request_data["hide_zero_balance"] = hide_zero_balance
        if hide_zero_balance_and_no_transaction is not None:
            request_data["hide_zero_balance_and_no_transaction"] = hide_zero_balance_and_no_transaction

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/get_sub_ledger_bal/",
            request_data
        )

        # 处理字段过滤
        if response_data.get("success") and "data" in response_data and "data" in response_data["data"]:
            filtered_data = []
            for item in response_data["data"]["data"]:
                filtered_item = {}
                for field in fields:
                    if field in item:
                        filtered_item[field] = item[field]
                filtered_data.append(filtered_item)
            # 更新返回数据中的数据列表
            response_data["data"]["data"] = filtered_data

        return response_data

    @mcp.tool()
    def get_sub_ledger_bal_summary(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        fields: List[str] = Field(description="选择返回的字段，可选值：['auxiliary_accounting_id', 'accounting_title_id', 'currency_id', 'key', 'prj_code', 'prj_name', 'code', 'parent_code', 'auxiliary_accounting_code', 'auxiliary_accounting_name', 'debit_initial_balance', 'credit_initial_balance', 'initial_balance', 'debit_current_period_amount', 'credit_current_period_amount', 'debit_annual_cumulative_amount', 'credit_annual_cumulative_amount', 'debit_ending_balance', 'credit_ending_balance', 'ending_balance', 'original_debit_initial_balance', 'original_credit_initial_balance', 'original_initial_balance', 'original_debit_current_period_amount', 'original_credit_current_period_amount', 'original_debit_annual_cumulative_amount', 'original_credit_annual_cumulative_amount', 'original_debit_ending_balance', 'original_credit_ending_balance', 'fc_code', 'exchange_rate']。"),
        start_accounting_period: str = Field(description="开始会计期间，格式：YYYY-MM"),
        end_accounting_period: str = Field(description="结束会计期间，格式：YYYY-MM"),
        auxiliary_accounting_category_id: int = Field(description="辅助类别id"),
        accounting_title_level_type: int = Field(description="科目级次类型(1: 至最末级,2: 仅显示一级,3: 仅显示最末级,4: 自定义范围)"),
        sorter: Dict[str, str] = Field(default=None, description="排序字段，格式：{'字段名': 'ascend'|'descend'}"),
        params: Dict[str, Any] = Field(default=None, description="参数搜索条件"),
        filters: Dict[str, List[Any]] = Field(default=None, description="过滤条件"),
        related_auxiliary_accounting_category_id: int = Field(default=None, description="关联辅助类别id"),
        related_auxiliary_accounting_id: int = Field(default=None, description="关联辅助id"),
        show_subject: bool = Field(default=False, description="是否显示科目"),
        accounting_title_id: int = Field(default=None, description="科目id"),
        auxiliary_accounting_codes: str = Field(default=None, description="辅助代码"),
        auxiliary_accounting_ids: List[int] = Field(default=None, description="辅助id清单"),
        accounting_titles: str = Field(default=None, description="科目代码"),
        accounting_title_level: Dict[str, int] = Field(default=None, description='科目级次范围(示例:{"startLevel": 2, "endLevel": 8})'),
        currency_id: str = Field(default='functional', description="币别(functional:综合本位币,allCurrencies:所有币种,allCurrenciesMultiColumn:所有币种多栏式,或者传递币别的id)"),
        hide_zero_balance: bool = Field(default=False, description="余额为0不显示"),
        hide_zero_balance_and_no_transaction: bool = Field(default=False, description="余额为0且发生额为0不显示")
    ) -> Dict[str, Any]:
        """
        获得辅助项目余额汇总

        Returns:
            Dict[str, Any]: 返回辅助项目余额汇总数据
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "start_accounting_period": start_accounting_period,
            "end_accounting_period": end_accounting_period,
            "auxiliary_accounting_category_id": auxiliary_accounting_category_id,
            "accounting_title_level_type": accounting_title_level_type
        }

        # 添加可选参数
        if sorter is not None:
            request_data["sorter"] = sorter
        if params is not None:
            request_data["params"] = params
        if filters is not None:
            request_data["filters"] = filters
        if related_auxiliary_accounting_category_id is not None:
            request_data["related_auxiliary_accounting_category_id"] = related_auxiliary_accounting_category_id
        if related_auxiliary_accounting_id is not None:
            request_data["related_auxiliary_accounting_id"] = related_auxiliary_accounting_id
        if show_subject is not None:
            request_data["show_subject"] = show_subject
        if accounting_title_id is not None:
            request_data["accounting_title_id"] = accounting_title_id
        if auxiliary_accounting_codes is not None:
            request_data["auxiliary_accounting_codes"] = auxiliary_accounting_codes
        if auxiliary_accounting_ids is not None:
            request_data["auxiliary_accounting_ids"] = auxiliary_accounting_ids
        if accounting_titles is not None:
            request_data["accounting_titles"] = accounting_titles
        if accounting_title_level is not None:
            request_data["accounting_title_level"] = accounting_title_level
        if currency_id is not None:
            request_data["currency_id"] = currency_id
        if hide_zero_balance is not None:
            request_data["hide_zero_balance"] = hide_zero_balance
        if hide_zero_balance_and_no_transaction is not None:
            request_data["hide_zero_balance_and_no_transaction"] = hide_zero_balance_and_no_transaction

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/get_sub_ledger_bal_summary/",
            request_data
        )

        # 处理字段过滤 (注意 get_sub_ledger_bal_summary 返回的是直接数据对象)
        if response_data.get("success") and "data" in response_data:
            filtered_item = {}
            for field in fields:
                if field in response_data["data"]:
                    filtered_item[field] = response_data["data"][field]
            # 更新返回数据
            response_data["data"] = filtered_item

        return response_data

    return mcp