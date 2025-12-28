"""
结账管理模块主文件
"""
from .financial_closing_precheck import register_financial_closing_precheck_tools

def register_financial_closing_tools(mcp):
    """注册所有结账管理相关的工具"""
    # 注册结账前检查工具
    mcp = register_financial_closing_precheck_tools(mcp)
    return mcp