from fastmcp import Context
from typing import List, Dict, Any
from config import config
from pydantic import Field
from config import config

def register_accounting_title_initialization_tools(mcp):
    """注册会计科目初始化相关的工具"""

    @mcp.tool()
    def get_accounting_title_initialization(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        accounting_title_category_id: int = Field(description="科目分类外键id"),
        currency_id: int = Field(default=None, description="币别id"),
        at_code: str = Field(default=None, description="科目代码"),
        at_name: str = Field(default=None, description="科目名称"),
        fc_code: str = Field(default=None, description="币别代码")
    ) -> Dict[str, Any]:
        """
        获取会计科目初始化数据

        Returns:
            Dict[str, Any]: 返回API响应数据，包含以下字段：
                - success: bool - 请求是否成功
                - message: str - 返回消息说明
                - data: list - 科目初始化数据列表，每个元素包含：
                    - id: int - 科目主键ID
                    - parent_id: int - 父节点id
                    - at_code: str - 科目代码
                    - at_name: str - 科目名称
                    - at_direction: int - 方向（存储为整数值）
                    - auxiliary_accounting_category_ids: list - 辅助核算项目清单
                    - auxiliary_accounting_category_names: list - 辅助项目
                    - initial_balance: Decimal - 期初余额
                    - initial_original_balance: Decimal - 期初原币余额
                    - initial_quantity: Decimal - 期初数量
                    - debit_accumulated_amount: Decimal - 借方累计金额
                    - debit_accumulated_original_amount: Decimal - 借方累计原币金额
                    - debit_accumulated_quantity: Decimal - 借方累计数量
                    - credit_accumulated_quantity: Decimal - 贷方累计数量
                    - credit_accumulated_amount: Decimal - 贷方累计金额
                    - credit_accumulated_original_amount: Decimal - 贷方累计原币金额
                    - annual_balance: Decimal - 年初余额
                    - annual_original_balance: Decimal - 年初原币余额
                    - annual_quantity: Decimal - 年初数量
                    - is_leaf_account: bool - 是否叶子科目
                    - is_auxiliary_account: bool - 是否辅助科目
                    - is_auxiliary_accounting_enabled: bool - 是否启用辅助核算
                    - is_foreign_currency_accounting_enabled: bool - 是否启用外币核算
                    - is_quantity_accounting_enabled: bool - 是否启用数量核算
                    - accounting_title_initialization_id: int - 对应的初始化数据
                    - currency_id: int - 币别
                    - exchange_rate: Decimal - 汇率
                    - accounting_title_id: int - 科目
                    - parent_at_code: str - 父科目代码
                    - fc_code: str - 币别代码
                    - children: list - 子科目列表
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "accounting_title_category_id": accounting_title_category_id
        }

        # 添加可选参数
        if currency_id is not None:
            request_data["currency_id"] = currency_id
        if at_code is not None:
            request_data["at_code"] = at_code
        if at_name is not None:
            request_data["at_name"] = at_name
        if fc_code is not None:
            request_data["fc_code"] = fc_code

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/get_accounting_title_initialization/",
            request_data
        )

        # 直接返回API响应
        return response_data

    @mcp.tool()
    def accounting_title_initialization_create(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        accounting_title_id: int = Field(description="科目ID"),
        currency_id: int = Field(description="币别ID"),
        initial_balance: float = Field(description="期初余额"),
        initial_original_balance: float = Field(description="期初原币余额"),
        initial_quantity: float = Field(description="期初数量"),
        debit_accumulated_amount: float = Field(description="借方累计金额"),
        debit_accumulated_original_amount: float = Field(description="借方累计原币金额"),
        debit_accumulated_quantity: float = Field(description="借方累计数量"),
        credit_accumulated_quantity: float = Field(description="贷方累计数量"),
        credit_accumulated_amount: float = Field(description="贷方累计金额"),
        credit_accumulated_original_amount: float = Field(description="贷方累计原币金额"),
        annual_balance: float = Field(description="年初余额"),
        annual_original_balance: float = Field(description="年初原币余额"),
        annual_quantity: float = Field(description="年初数量")
    ) -> Dict[str, Any]:
        """
        新增会计科目初始化数据,这个用于没有开启辅助核算的科目的期初初始化，如果开启了辅助核算,那么请用add_auxiliary_initialization工具先添加记录，
        再用accounting_title_initialization_update设置期初数据.

        补充说明：
        1) 科目约束：
           - 只能为明细科目创建初始化数据
           - 明细科目不能带辅助核算
           - 科目已开启外币核算时，必须指定币别且币别必须在科目支持的外币范围内
           - 科目未开启外币核算时，币别必须为本位币

        2) 余额关系校验（根据科目方向）：
           - 借方科目(at_direction=0): 期初余额 = 年初余额 + 借方累计 - 贷方累计
           - 贷方科目(at_direction=1): 期初余额 = 年初余额 + 贷方累计 - 借方累计
           - 上述关系式同时适用于：本位币金额、原币金额、数量三个维度

        3) 本位币与原币一致性约束：
           - 年初余额的本位币和原币必须同时为零或同时不为零
           - 借方累计金额的本位币和原币必须同时为零或同时不为零
           - 贷方累计金额的本位币和原币必须同时为零或同时不为零
           - 期初余额的本位币和原币必须同时为零或同时不为零

        4) 帐套状态约束：
           - 帐套开帐期间不能已结账，否则无法创建科目初始化数据

        5) 唯一性约束：
           - 同一科目+币别组合不能重复创建初始化记录

        Returns:
            Dict[str, Any]: 操作结果，包含新增记录的ID和相关信息
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "accounting_title_id": accounting_title_id,
            "currency_id": currency_id,
            "initial_balance": initial_balance,
            "initial_original_balance": initial_original_balance,
            "initial_quantity": initial_quantity,
            "debit_accumulated_amount": debit_accumulated_amount,
            "debit_accumulated_original_amount": debit_accumulated_original_amount,
            "debit_accumulated_quantity": debit_accumulated_quantity,
            "credit_accumulated_quantity": credit_accumulated_quantity,
            "credit_accumulated_amount": credit_accumulated_amount,
            "credit_accumulated_original_amount": credit_accumulated_original_amount,
            "annual_balance": annual_balance,
            "annual_original_balance": annual_original_balance,
            "annual_quantity": annual_quantity
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/accounting_title_initialization_create/",
            request_data
        )

        # 直接返回API响应
        return response_data

    @mcp.tool()
    def add_auxiliary_initialization(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        accounting_title_id: int = Field(description="科目ID"),
        data_source: List[Dict[str, Any]] = Field(description="辅助明细数据列表")
    ) -> Dict[str, Any]:
        """
        添加辅助核算明细初始化数据。
        此工具用于带辅助核算科目的初始化。通过该工具先创建科目+辅助组合的基础记录，
        然后可使用 accounting_title_initialization_update 工具填写具体的初始化数据。

        Args:
            ctx (Context): MCP 上下文对象，用于请求处理
            ab_id (int): 帐套ID，指定操作的会计帐套
            accounting_title_id (int): 科目ID，指定要添加辅助核算明细的科目
            data_source (List[Dict[str, Any]]): 辅助明细数据列表，每个字典表示一个辅助组合，
                键为辅助类别ID，值为对应的辅助核算项ID。
                键也可以为"currency_id",值为币别id,如果传递的科目没有开启外币核算，这个可以不传递。
                注意：辅助类别必须与科目开启的辅助核算类别完全对应。

            示例:
                >>> result = add_auxiliary_initialization(
                ...     ctx,
                ...     ab_id=20,
                ...     accounting_title_id=6163,
                ...     data_source=[
                ...         {
                ...             "1": 10,  # 辅助类别ID: 1, 辅助核算项ID: 10
                ...             "2": 20,   # 辅助类别ID: 2, 辅助核算项ID: 20
                ...            "currency_id": 10 #如果科目没有开启外币核算,这个可以不传递
                ...         }
                ...     ]
                ... )
                >>> print(result["success"])
                True
        Returns:
            Dict[str, Any]: 操作结果



        """
        # 构建请求数据
        request_data = {
            "data_source": data_source,
            "accounting_title_id": accounting_title_id,
            "ab_id": ab_id
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/add_auxiliary_initialization/",
            request_data
        )

        # 直接返回API响应
        return response_data

    @mcp.tool()
    def accounting_title_initialization_batch_delete(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        ids: List[int] = Field(description="要删除的初始化数据ID列表"),
        confirm_delete: bool = Field(default=False, description="确认删除")
    ) -> Dict[str, Any]:
        """
        批量删除会计科目初始化数据

        Args:
            ab_id: 帐套ID
            ids: 要删除的初始化数据ID列表
            confirm_delete: 确认删除

        Returns:
            Dict[str, Any]: 返回影响行数
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "ids": ids,
            "confirm_delete": confirm_delete
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/accounting_title_initialization_batch_delete/",
            request_data
        )

        # 直接返回API响应
        return response_data

    @mcp.tool()
    def accounting_title_initialization_update(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        id: int = Field(description="初始化数据ID"),
        initial_balance: float = Field(description="期初余额"),
        initial_original_balance: float = Field(description="期初原币余额"),
        initial_quantity: float = Field(description="期初数量"),
        debit_accumulated_amount: float = Field(description="借方累计金额"),
        debit_accumulated_original_amount: float = Field(description="借方累计原币金额"),
        debit_accumulated_quantity: float = Field(description="借方累计数量"),
        credit_accumulated_quantity: float = Field(description="贷方累计数量"),
        credit_accumulated_amount: float = Field(description="贷方累计金额"),
        credit_accumulated_original_amount: float = Field(description="贷方累计原币金额"),
        annual_balance: float = Field(description="年初余额"),
        annual_original_balance: float = Field(description="年初原币余额"),
        annual_quantity: float = Field(description="年初数量")
    ) -> Dict[str, Any]:
        """
        更新会计科目初始化数据。
        只更新传入的字段，未传入的字段保持原值不变。

        补充说明：
        1) 帐套状态约束：
           - 帐套开帐期间不能已结账，否则无法更新科目初始化数据

        2) 余额关系校验（根据科目方向）：
           - 借方科目(at_direction=0): 期初余额 = 年初余额 + 借方累计 - 贷方累计
           - 贷方科目(at_direction=1): 期初余额 = 年初余额 + 贷方累计 - 借方累计
           - 上述关系式同时适用于：本位币金额、原币金额、数量三个维度
           - 更新时会合并现有数据和新数据进行校验

        3) 本位币与原币一致性约束：
           - 年初余额的本位币和原币必须同时为零或同时不为零
           - 借方累计金额的本位币和原币必须同时为零或同时不为零
           - 贷方累计金额的本位币和原币必须同时为零或同时不为零
           - 期初余额的本位币和原币必须同时为零或同时不为零

        4) 数据一致性约束：
           - 如果科目未开启外币核算，原币字段会自动与本位币字段保持一致
           - 更新操作会保持未传入字段的原值不变

        Returns:
            Dict[str, Any]: 操作结果，包含更新的记录数和相关信息
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "id": id,
            "initial_balance": initial_balance,
            "initial_original_balance": initial_original_balance,
            "initial_quantity": initial_quantity,
            "debit_accumulated_amount": debit_accumulated_amount,
            "debit_accumulated_original_amount": debit_accumulated_original_amount,
            "debit_accumulated_quantity": debit_accumulated_quantity,
            "credit_accumulated_quantity": credit_accumulated_quantity,
            "credit_accumulated_amount": credit_accumulated_amount,
            "credit_accumulated_original_amount": credit_accumulated_original_amount,
            "annual_balance": annual_balance,
            "annual_original_balance": annual_original_balance,
            "annual_quantity": annual_quantity
        }
        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/accounting_title_initialization_update/",
            request_data
        )

        # 直接返回API响应
        return response_data

    return mcp