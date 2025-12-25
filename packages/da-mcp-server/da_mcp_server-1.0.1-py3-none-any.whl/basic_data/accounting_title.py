from fastmcp import Context
from typing import List, Dict, Any, Optional
from config import config
from pydantic import Field
from config import config

def register_accounting_title_tools(mcp):
    """注册会计科目管理相关的工具"""

    @mcp.tool()
    def accounting_title_list(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        fields: List[str] = Field(description="选择返回的字段，可选值：['id', 'parent_id', 'parent_name', 'parent_at_code', 'at_code', 'at_code_path', 'at_name', 'at_name_path', 'at_direction', 'is_enabled', 'is_cash_account', 'accounting_title_category_id', 'accounting_title_sub_category_id', 'accounting_title_category_name', 'accounting_title_sub_category_name', 'auxiliary_accounting_category_names', 'is_auxiliary_accounting_enabled', 'is_quantity_accounting_enabled', 'is_foreign_currency_accounting_enabled', 'measurement_unit', 'is_currency_adjustment_enabled', 'auxiliary_accounting_category_ids', 'currency_ids', 'currency_options']。如果为空，则返回所有字段。"),
        current: int = Field(default=1, ge=1, description="页码"),
        pageSize: int = Field(default=10, ge=0, description="每页记录数,为0则返回所有记录"),
        id: int = Field(default=None, description="科目主键"),
        at_code: str = Field(default=None, description="科目代码,模糊搜索"),
        at_name: str = Field(default=None,description="科目名称,模糊搜索"),
        is_detail_account: bool = Field(default=None, description="是否是明细科目"),
        accounting_title_category_id: int = Field(default=None, description="科目分类外键id"),
        keyWords: str = Field(default=None, max_length=32, description="关键词"),
    ) -> Dict[str, Any]:
        """
        分页查询会计科目列表

        Args:
            ctx: MCP上下文对象
            ab_id: 帐套ID
            current: 页码，默认为1
            pageSize: 每页记录数，默认为10，为0则返回所有记录
            id: 科目主键(可选)
            at_code: 科目代码，模糊搜索(可选)
            at_name: 科目名称，模糊搜索(可选)
            is_detail_account: 是否是明细科目(可选)
            accounting_title_category_id: 科目分类外键id(可选)
            keyWords: 关键词，最大长度32(可选)
            fields: 选择返回的字段列表(可选)。如果指定，则只返回指定字段的数据，可以节约token使用量。
                  可选值包括：['id', 'parent_id', 'parent_name', 'parent_at_code', 'at_code', 'at_code_path',
                  'at_name', 'at_name_path', 'at_direction', 'is_enabled', 'is_cash_account',
                  'accounting_title_category_id', 'accounting_title_sub_category_id',
                  'accounting_title_category_name', 'accounting_title_sub_category_name',
                  'auxiliary_accounting_category_names', 'is_auxiliary_accounting_enabled',
                  'is_quantity_accounting_enabled', 'is_foreign_currency_accounting_enabled',
                  'measurement_unit', 'is_currency_adjustment_enabled', 'auxiliary_accounting_category_ids',
                  'currency_ids', 'currency_options']。如果为空，则返回所有字段。

        Returns:
            Dict[str, Any]: 返回API响应数据，包含以下字段：
                - success: bool - 请求是否成功
                - message: str - 返回消息说明
                - data: dict - 分页数据对象，包含：
                    - current: int - 当前页码
                    - pageSize: int - 每页大小
                    - total: int - 总记录数
                    - data: list - 科目数据列表，根据fields参数返回相应字段，每个科目可能包含：
                        - id: int - 主键
                        - parent_id: int|None - 父科目
                        - parent_name: str - 父科目名称
                        - parent_at_code: str - 父科目代码
                        - at_code: str - 科目代码
                        - at_code_path: str - 科目代码路径
                        - at_name: str - 科目名称
                        - at_name_path: str - 科目名称路径
                        - at_direction: int - 方向: 0-借, 1-贷
                        - is_enabled: bool - 是否启用
                        - is_cash_account: bool - 是否现金科目
                        - accounting_title_category_id: int|None - 科目分类外键id
                        - accounting_title_sub_category_id: int|None - 类别
                        - accounting_title_category_name: str - 科目类别名称
                        - accounting_title_sub_category_name: str - 科目子类别名称
                        - auxiliary_accounting_category_names: list|None - 辅助项目
                        - is_auxiliary_accounting_enabled: bool - 是否启用辅助核算
                        - is_quantity_accounting_enabled: bool - 是否启用数量核算
                        - is_foreign_currency_accounting_enabled: bool - 是否启用外币核算
                        - measurement_unit: str|None - 计量单位
                        - is_currency_adjustment_enabled: bool - 开启期末调汇
                        - auxiliary_accounting_category_ids: list|None - 辅助核算项目清单
                        - currency_ids: list|None - 外币清单
                        - currency_options: list|None - 外币菜单选项，每项包含：
                            - value: int - 币别id
                            - label: str - 币别名称

        Examples:
            # 返回所有字段
            accounting_title_list(ab_id=1)

            # 只返回id、at_code、at_name字段
            accounting_title_list(ab_id=1, fields=["id", "at_code", "at_name"])

            # 只返回基本字段和核算相关字段
            accounting_title_list(ab_id=1, fields=["id", "at_code", "at_name", "is_auxiliary_accounting_enabled", "is_quantity_accounting_enabled", "is_foreign_currency_accounting_enabled"])
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "current": current,
            "pageSize": pageSize,
        }

        # 添加可选参数
        if id is not None:
            request_data["id"] = id
        if at_code is not None:
            request_data["at_code"] = at_code
        if at_name is not None:
            request_data["at_name"] = at_name
        if is_detail_account is not None:
            request_data["is_detail_account"] = is_detail_account
        if accounting_title_category_id is not None:
            request_data["accounting_title_category_id"] = accounting_title_category_id
        if keyWords is not None:
            request_data["keyWords"] = keyWords

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/accounting_title_list/",
            request_data
        )

        # 如果指定了字段过滤，则处理返回数据
        if fields is not None and response_data.get("success") and "data" in response_data and "data" in response_data["data"]:
            filtered_data = []
            for item in response_data["data"]["data"]:
                filtered_item = {}
                for field in fields:
                    if field in item:
                        filtered_item[field] = item[field]
                filtered_data.append(filtered_item)
            # 更新返回数据中的数据列表
            response_data["data"]["data"] = filtered_data

        # 直接返回API响应
        return response_data

    @mcp.tool()
    def accounting_title_create(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        at_code: str = Field(description="科目代码"),
        at_name: str = Field(description="科目名称"),
        at_direction: int = Field(description="方向: 0-借, 1-贷"),
        is_enabled: bool = Field(description="是否启用"),
        is_cash_account: bool = Field(description="是否现金科目"),
        is_auxiliary_accounting_enabled: bool = Field(description="是否启用辅助核算"),
        is_quantity_accounting_enabled: bool = Field(description="是否启用数量核算"),
        is_foreign_currency_accounting_enabled: bool = Field(description="是否启用外币核算"),
        accounting_title_category_id: int = Field(description="科目分类外键id"),
        accounting_title_sub_category_id: int = Field(description="类别外键id"),
        parent_id: int = Field(default=None, description="父科目"),
        measurement_unit: str = Field(default="", description="计量单位"),
        is_currency_adjustment_enabled: bool = Field(default=False, description="开启期末调汇"),
        auxiliary_accounting_category_ids: List[int] = Field(default=None, description="辅助核算项目清单"),
        currency_ids: List[int] = Field(default=None, description="外币清单"),
    ) -> Dict[str, Any]:
        """
        新增会计科目

        参数补充说明:
            1,如果系统提示要数据迁移时,请终止操作，提示用户自己操作。
            2,创建一个科目的子科目时,子科目的accounting_title_category_id一定与父科目一致。accounting_title_sub_category_id则是accounting_title_category_id下的子分类，一般与父科目也是相等的，当有有可能不同。
        3，创建一个一级科目，带辅助，外币核算，数量核算完整请求示例：
        {
            "accounting_title_sub_category_id": 1298,
            "at_code": "1902",
            "at_name": "test",
            "at_direction": 0,
            "is_cash_account": false,
            "is_auxiliary_accounting_enabled": true,
            "is_quantity_accounting_enabled": true,
            "is_foreign_currency_accounting_enabled": true,
            "auxiliary_accounting_category_ids": [
                530
            ],
            "measurement_unit": "个",
            "is_currency_adjustment_enabled": false,
            "currency_ids": [
                210,
                212
            ],
            "is_enabled": true,
            "accounting_title_category_id": 1296
        }

        4,创建一个科目的子科目请求示例:
        {
                "accounting_title_sub_category_id": 1298,
                "at_code": "190201",
                "at_name": "test_sub",
                "at_direction": 0,
                "is_cash_account": false,
                "is_auxiliary_accounting_enabled": true,
                "auxiliary_accounting_category_ids": [
                    530
                ],
                "is_quantity_accounting_enabled": true,
                "measurement_unit": "个",
                "is_foreign_currency_accounting_enabled": true,
                "is_currency_adjustment_enabled": false,
                "currency_ids": [
                    210,
                    212
                ],
                "is_enabled": true,
                "parent_id": 11724,
                "accounting_title_category_id": 1296
            }
        Returns:
            Dict[str, Any]: 返回新增记录ID
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "at_code": at_code,
            "at_name": at_name,
            "at_direction": at_direction,
            "is_enabled": is_enabled,
            "is_cash_account": is_cash_account,
            "is_auxiliary_accounting_enabled": is_auxiliary_accounting_enabled,
            "is_quantity_accounting_enabled": is_quantity_accounting_enabled,
            "is_foreign_currency_accounting_enabled": is_foreign_currency_accounting_enabled,
            "is_currency_adjustment_enabled": is_currency_adjustment_enabled
        }

        # 添加可选参数
        if parent_id is not None:
            request_data["parent_id"] = parent_id
        if accounting_title_category_id is not None:
            request_data["accounting_title_category_id"] = accounting_title_category_id
        if accounting_title_sub_category_id is not None:
            request_data["accounting_title_sub_category_id"] = accounting_title_sub_category_id
        if measurement_unit is not None:
            request_data["measurement_unit"] = measurement_unit
        if auxiliary_accounting_category_ids is not None:
            request_data["auxiliary_accounting_category_ids"] = auxiliary_accounting_category_ids
        if currency_ids is not None:
            request_data["currency_ids"] = currency_ids

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/accounting_title_create/",
            request_data
        )

        # 直接返回API响应
        return response_data

    @mcp.tool()
    def accounting_title_update(
        ctx: Context,
        ab_id: int = Field(description="帐套id"),
        id: int = Field(description="科目主键"),
        parent_id: int = Field(default=None, description="父科目"),
        at_code: str = Field(default=None, description="科目代码"),
        at_name: str = Field(default=None, description="科目名称"),
        at_direction: int = Field(default=None, description="方向: 0-借, 1-贷"),
        is_enabled: bool = Field(default=None, description="是否启用"),
        is_cash_account: bool = Field(default=None, description="是否现金科目"),
        accounting_title_category_id: int = Field(default=None, description="科目分类外键id"),
        accounting_title_sub_category_id: int = Field(default=None, description="类别"),
        is_auxiliary_accounting_enabled: bool = Field(default=None, description="是否启用辅助核算"),
        is_quantity_accounting_enabled: bool = Field(default=None, description="是否启用数量核算"),
        is_foreign_currency_accounting_enabled: bool = Field(default=None, description="是否启用外币核算"),
        measurement_unit: str = Field(default=None, description="计量单位"),
        is_currency_adjustment_enabled: bool = Field(default=None, description="开启期末调汇"),
        auxiliary_accounting_category_ids: List[int] = Field(default=None, description="辅助核算项目清单,例如:[235,236]"),
        currency_ids: List[int] = Field(default=None, description="外币清单"),
    ) -> Dict[str, Any]:
        """
        更新会计科目

        补充说明：
            1，如果返回错误提示要数据迁移时，请提示本次终止操作。
            2，更新示例，
                1）开启辅助，数量，外币核算
                {
                    "id": 12063,
                    "ab_id":86,
                    "accounting_title_sub_category_id": 1359,
                    "at_code": "171",
                    "at_name": "拨付所属单位资金",
                    "at_direction": 0,
                    "is_cash_account": false,
                    "is_auxiliary_accounting_enabled": true,
                    "is_quantity_accounting_enabled": true,
                    "is_foreign_currency_accounting_enabled": true,
                    "auxiliary_accounting_category_ids": [
                        553,
                        555
                    ],
                    "measurement_unit": "2",
                    "is_currency_adjustment_enabled": false,
                    "currency_ids": [
                        220
                    ]
                }
                2）禁止辅助，数量，外币核算
                {
                    "id": 12063,
                    "ab_id":86,
                    "accounting_title_sub_category_id": 1359,
                    "at_code": "171",
                    "at_name": "拨付所属单位资金",
                    "at_direction": 0,
                    "is_cash_account": false,
                    "is_auxiliary_accounting_enabled": false,
                    "is_quantity_accounting_enabled": false,
                    "is_foreign_currency_accounting_enabled": false
                }
        Returns:
            Dict[str, Any]: 返回影响行数
        """
        # 构建请求数据
        request_data = {
            "id": id,
            "ab_id":ab_id
        }

        # 添加可选参数
        if parent_id is not None:
            request_data["parent_id"] = parent_id
        if at_code is not None:
            request_data["at_code"] = at_code
        if at_name is not None:
            request_data["at_name"] = at_name
        if at_direction is not None:
            request_data["at_direction"] = at_direction
        if is_enabled is not None:
            request_data["is_enabled"] = is_enabled
        if is_cash_account is not None:
            request_data["is_cash_account"] = is_cash_account
        if accounting_title_category_id is not None:
            request_data["accounting_title_category_id"] = accounting_title_category_id
        if accounting_title_sub_category_id is not None:
            request_data["accounting_title_sub_category_id"] = accounting_title_sub_category_id
        if is_auxiliary_accounting_enabled is not None:
            request_data["is_auxiliary_accounting_enabled"] = is_auxiliary_accounting_enabled
        if is_quantity_accounting_enabled is not None:
            request_data["is_quantity_accounting_enabled"] = is_quantity_accounting_enabled
        if is_foreign_currency_accounting_enabled is not None:
            request_data["is_foreign_currency_accounting_enabled"] = is_foreign_currency_accounting_enabled
        if measurement_unit is not None:
            request_data["measurement_unit"] = measurement_unit
        if is_currency_adjustment_enabled is not None:
            request_data["is_currency_adjustment_enabled"] = is_currency_adjustment_enabled
        if auxiliary_accounting_category_ids is not None:
            request_data["auxiliary_accounting_category_ids"] = auxiliary_accounting_category_ids
        if currency_ids is not None:
            request_data["currency_ids"] = currency_ids


        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/accounting_title_update/",
            request_data
        )

        # 直接返回API响应
        return response_data

    @mcp.tool()
    def accounting_title_batch_delete(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        ids: List[int] = Field(description="要删除的科目ID列表"),
        confirm_delete: bool = Field(default=False, description="确认删除")
    ) -> Dict[str, Any]:
        """
        批量删除会计科目

        Args:
            ids: 要删除的科目ID列表
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
            f"{config.backend_base_url}/api/general_ledger/accounting_title_batch_delete/",
            request_data
        )

        # 直接返回API响应
        return response_data

    return mcp