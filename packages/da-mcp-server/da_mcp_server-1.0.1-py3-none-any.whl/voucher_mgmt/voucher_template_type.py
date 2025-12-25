"""
凭证模板类型管理工具
"""
from fastmcp import Context
from typing import List, Dict, Any, Optional
from config import config
from pydantic import Field

def register_voucher_template_type_tools(mcp):
    """注册凭证模板类型相关工具"""

    @mcp.tool()
    def voucher_template_type_list(
        ctx: Context,
        ab_id: int = Field(description="帐套"),
        current: int = Field(default=1, ge=1, description="页码"),
        pageSize: int = Field(default=10, ge=0, description="每页记录数,为0则返回所有记录"),
    ) -> Dict[str, Any]:
        """
        分页查询凭证模板类型列表

        Args:
            ctx: MCP上下文对象
            ab_id: 帐套ID
            current: 页码，默认为1
            pageSize: 每页记录数，默认为10，为0则返回所有记录

        Returns:
            Dict[str, Any]: 返回API响应数据，包含分页信息和凭证模板类型列表
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "current": current,
            "pageSize": pageSize,
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/voucher_template_type_list/",
            request_data
        )

        # 直接返回API响应
        return response_data

    @mcp.tool()
    def voucher_template_type_create(
        ctx: Context,
        ab_id: int = Field(description="帐套"),
        name: str = Field(max_length=100, description="类型名称"),
    ) -> Dict[str, Any]:
        """
        新增凭证模板类型

        Args:
            ctx: MCP上下文对象
            ab_id: 帐套ID
            name: 类型名称

        Returns:
            Dict[str, Any]: 返回新增记录ID
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "name": name
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/voucher_template_type_create/",
            request_data
        )

        # 直接返回API响应
        return response_data

    @mcp.tool()
    def voucher_template_type_update(
        ctx: Context,
        ab_id: int = Field(description="帐套"),
        id: int = Field(description="主键"),
        name: str = Field(max_length=100, default=None, description="类型名称"),
    ) -> Dict[str, Any]:
        """
        更新凭证模板类型

        Args:
            ctx: MCP上下文对象
            id: 主键
            ab_id: 帐套ID（可选）
            name: 类型名称（可选）

        Returns:
            Dict[str, Any]: 返回影响行数
        """
        # 构建请求数据
        request_data = {
            "id": id,
            "ab_id": ab_id
        }

        # 添加可选参数
        if ab_id is not None:
            request_data["ab_id"] = ab_id
        if name is not None:
            request_data["name"] = name

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/voucher_template_type_update/",
            request_data
        )

        # 直接返回API响应
        return response_data

    @mcp.tool()
    def voucher_template_type_batch_delete(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        ids: List[int] = Field(description="要删除的记录的ID列表"),
    ) -> Dict[str, Any]:
        """
        批量删除凭证模板类型

        Args:
            ctx: MCP上下文对象
            ids: 要删除的记录的ID列表

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
            f"{config.backend_base_url}/api/general_ledger/voucher_template_type_batch_delete/",
            request_data
        )

        # 直接返回API响应
        return response_data

    return mcp