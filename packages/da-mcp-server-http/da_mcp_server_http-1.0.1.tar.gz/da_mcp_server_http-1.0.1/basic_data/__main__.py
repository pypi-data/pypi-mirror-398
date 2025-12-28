"""
基础数据管理模块主文件
"""
from .accounting_title_category import register_accounting_title_category_tools
from .accounting_title import register_accounting_title_tools
from .auxiliary_accounting_category import register_auxiliary_accounting_category_tools
from .currency import register_currency_tools
from .voucher_prefix import register_voucher_prefix_tools
from .auxiliary_accounting import register_auxiliary_accounting_tools
from .accounting_standard import (
    register_accounting_standard_tools,
    register_accounting_title_template_tools,
    register_accounting_title_category_template_tools,
    register_report_setting_tools,
    register_calculation_formula_setting_tools
)

from .accounting_title_initialization import register_accounting_title_initialization_tools

def register_basic_data_tools(mcp):
    """注册所有基础数据管理相关的工具"""
    # 注册会计准则管理工具
    mcp = register_accounting_standard_tools(mcp)
    # 注册会计科目模板管理工具
    mcp = register_accounting_title_template_tools(mcp)
    # 注册科目分类模板管理工具
    mcp = register_accounting_title_category_template_tools(mcp)
    # 注册会计科目管理工具
    mcp = register_accounting_title_tools(mcp)
    # 注册科目分类管理工具
    mcp = register_accounting_title_category_tools(mcp)
    # 注册辅助核算类别管理工具
    mcp = register_auxiliary_accounting_category_tools(mcp)
    # 注册币别管理工具
    mcp = register_currency_tools(mcp)
    # 注册凭证字管理工具
    mcp = register_voucher_prefix_tools(mcp)
    # 注册辅助核算管理工具
    mcp = register_auxiliary_accounting_tools(mcp)
    # 注册报表设置管理工具
    mcp = register_report_setting_tools(mcp)
    # 注册报表计算公式管理工具
    mcp = register_calculation_formula_setting_tools(mcp)
    # 注册期初工具
    mcp = register_accounting_title_initialization_tools(mcp)
    return mcp