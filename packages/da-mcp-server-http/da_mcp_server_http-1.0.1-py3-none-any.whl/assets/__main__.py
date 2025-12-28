"""
资产管理模块主文件
"""
from .asset_category import register_asset_category_tools
from .asset import register_asset_tools

def register_assets_tools(mcp):
    """注册所有资产管理相关的工具"""
    # 注册资产类别管理工具
    mcp = register_asset_category_tools(mcp)
    # 注册资产管理工具
    mcp = register_asset_tools(mcp)
    return mcp