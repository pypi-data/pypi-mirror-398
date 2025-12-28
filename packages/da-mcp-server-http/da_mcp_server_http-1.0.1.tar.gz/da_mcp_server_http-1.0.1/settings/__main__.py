"""
设置管理模块主文件
"""
from .accounting_book import register_accounting_book_tools

def register_settings_tools(mcp):
    """注册所有设置管理相关的工具"""
    # 注册账套管理工具
    mcp = register_accounting_book_tools(mcp)
    return mcp