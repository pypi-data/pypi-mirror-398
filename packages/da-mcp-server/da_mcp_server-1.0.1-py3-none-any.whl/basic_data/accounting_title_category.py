from fastmcp import Context
from typing import List, Optional, Dict, Any
from pydantic import Field
from config import config


def register_accounting_title_category_tools(mcp):
    """注册科目分类管理相关的工具"""

    @mcp.tool()
    def accounting_title_category_list(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        current: int = Field(default=1, ge=1, description="页码"),
        pageSize: int = Field(default=10, ge=0, description="每页记录数,为0则返回所有记录"),
        parent_id: int = Field(default=None, description="父科目分类ID,为0表示没有父科目，为一级科目。"),
        sorter: Dict[str, str] = Field(default=None, description="排序字段，格式: {'字段名': 'ascend/descend'}"),
    ) -> Dict[str, Any]:
        """
        分页查询科目分类列表

        Returns:
            AccountingTitleCategoryListRespDto: 包含以下返回参数
                - success: bool - 请求是否成功
                - message: str - 返回消息说明
                - data: AccountingTitleCategoryPageInfo - 分页数据对象，包含：
                    - current: int - 当前页码
                    - pageSize: int - 每页大小
                    - total: int - 总记录数
                    - data: List[AccountingTitleCategoryListRespData] - 科目分类数据列表，每个元素包含：
                        - id: int - 科目分类主键
                        - parent_id: int - 父科目分类ID
                        - seq: int - 显示顺序
                        - name: str - 科目分类名称
        """
        # 构建请求数据
        request_data = {
            "current": current,
            "pageSize": pageSize,
        }
        
        # 添加可选参数
        if parent_id is not None:
            request_data["parent_id"] = parent_id
        if ab_id is not None:
            request_data["ab_id"] = ab_id
        if sorter is not None:
            request_data["sorter"] = sorter

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/accounting_title_category_list/",
            request_data
        )

        # 直接返回API响应
        return response_data

    return mcp