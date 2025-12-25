"""
凭证管理模块主文件
"""
from .electronic_file import register_electronic_file_tools
from .voucher import register_voucher_tools
from .voucher_template import register_voucher_template_tools
from .voucher_template_type import register_voucher_template_type_tools

def register_voucher_mgmt_tools(mcp):
    """注册所有凭证管理相关的工具"""
    # 注册电子档案管理工具
    mcp = register_electronic_file_tools(mcp)
    # 注册凭证管理工具
    mcp = register_voucher_tools(mcp)
    # 注册凭证模板管理工具
    mcp = register_voucher_template_tools(mcp)
    # 注册凭证模板类型管理工具
    mcp = register_voucher_template_type_tools(mcp)
    return mcp