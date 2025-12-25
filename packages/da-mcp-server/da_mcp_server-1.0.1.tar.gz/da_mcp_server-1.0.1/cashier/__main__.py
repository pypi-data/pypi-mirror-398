"""
出纳管理模块主文件
"""
from .journal_entry import register_journal_entry_tools
from .finance_account import register_finance_account_tools

def register_cashier_tools(mcp):
    """注册所有出纳管理相关的工具"""
    # 注册日记账管理工具
    mcp = register_journal_entry_tools(mcp)
    # 注册资金账户管理工具
    mcp = register_finance_account_tools(mcp)
    return mcp