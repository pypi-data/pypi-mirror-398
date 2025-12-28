from fastmcp import Context
from typing import List, Optional, Dict, Any
from pydantic import Field

from config import config

def register_accounting_book_tools(mcp):
    """注册账套管理相关的工具"""

    @mcp.tool()
    def accounting_book_list(
        ctx: Context,
        current: int = Field(default=1, ge=1, description="页码"),
        pageSize: int = Field(default=10, ge=0, description="每页记录数,为0则返回所有记录"),
        id: int = Field(default=None,description="帐套id(可选)"),
        account_set_name: str = Field(default=None,description='帐套名称(可选),模糊搜索'),
        accounting_standard_name: str = Field(default=None,description='会计准则名称(可选)(模糊搜索)')
    ) -> Dict[str, Any]:
        """
        分页查询帐套列表
        调用示例：
        1，查询所有帐套：
        {
            "current": 1,
            "pageSize": 0
        }
        2,id,account_set_name,accounting_standard_name,不检索就不要传递任何值
        Returns:
            AccountingBookListRespDto: 包含以下返回参数
                - success: bool - 请求是否成功
                - message: str - 返回消息说明
                - data: AccountingBookPageInfo - 分页数据对象，包含：
                    - current: int - 当前页码
                    - pageSize: int - 每页大小
                    - total: int - 总记录数
                    - data: List[AccountingBookRespData] - 帐套数据列表，每个元素包含：
                        - id: int - 帐套主键
                        - account_set_name: str - 帐套名称
                        - account_set_start_date: str - 帐套启用日期
                        - social_unified_id_code: Optional[str] - 社会统一认证码
                        - audit_required: Literal[0,1] - 是否需要审核(0-否,1-是)
                        - accounting_standard_id: Optional[int] - 会计准则外键id
                        - industry_id: Optional[int] - 行业外键id
                        - accounting_standard_name: Optional[str] - 会计标准名称
                        - accounting_standard_code: Optional[str] - 会计标准代码
                        - industry_name: Optional[str] - 行业名称
                        - user_id: Optional[int] - 用户外键
                        - user_name: Optional[str] - 账套管理员姓名
                        - accounting_manager_id: Optional[int] - 会计主管id
                        - accounting_manager_name: Optional[str] - 会计主管姓名
                        - functional_currency_id: int - 本位币id
                        - functional_currency_name: str - 本位币名称
                        - user_username: Optional[str] - 账套管理员用户名
                        - accounting_manager_username: Optional[str] - 会计主管用户名
                        - user_roles: Optional[str] - 当前用户角色
                        - max_voucher_date: str - 最大凭证日期
                        - current_financial_period: str - 帐套当前帐期
        """
        # 构建请求数据
        request_data = {
            "current": current,
            "pageSize": pageSize,
        }
        if id is not None:
            request_data["id"] = id
        if account_set_name:
            request_data["account_set_name"] = account_set_name
        if accounting_standard_name:
            request_data["accounting_standard_name"] = accounting_standard_name

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/accounting_book_list/",
            request_data
        )

        # 直接返回API响应，不做任何校验
        return response_data

    @mcp.tool()
    def query_current_user(
        ctx: Context
    ) -> Dict[str, Any]:
        """
        查询接入服务的用户信息,通过客户端带过来的key判断

        Returns:
            Dict[str, Any]: 包含以下返回参数
                - success: bool - 请求是否成功
                - message: str - 返回消息说明
                - data: Dict[str, Any] - 用户数据对象，包含：
                    - id: int - 用户ID
                    - name: str - 用户姓名
                    - userid: str - 用户名
                    - is_superuser: bool - 是否是超级管理员
                    - is_staff: bool - 是否是员工
                    - first_name: str - 名字
                    - last_name: str - 姓氏
                    - phone: str - 电话号码
                    - can_create_account_set: bool - 是否可以创建账套
        """
        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/user/query_current_user",
            {}
        )

        # 直接返回API响应，不做任何校验
        return response_data

    return mcp