from fastmcp import Context
from typing import List, Dict, Any
from pydantic import Field
from config import config

def register_currency_tools(mcp):
    """注册币别管理相关的工具"""

    @mcp.tool()
    def currency_list(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        current: int = Field(default=1, ge=1, description="页码"),
        pageSize: int = Field(default=10, ge=0, description="每页记录数,为0则返回所有记录"),
        sorter: Dict[str, str] = Field(default=None, description="排序字段"),
        params: Dict[str, Any] = Field(default=None, description="参数搜索条件"),
        filters: Dict[str, List[Any]] = Field(default=None, description="过滤条件"),
        ids: List[int] = Field(default=None, description="币别id清单"),
        current_ab_id: int = Field(default=None, description="指定账套id,如果指定此值,ab_id将被忽略"),
        fc_code: str = Field(default=None, description="币别代码搜索条件"),
        fc_name: str = Field(default=None, description="币别名称搜索条件")
    ) -> Dict[str, Any]:
        """
        分页查询币别列表

        Returns:
            Dict[str, Any]: 返回API响应数据
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "current": current,
            "pageSize": pageSize,
        }

        # 添加可选参数
        if sorter is not None:
            request_data["sorter"] = sorter
        if params is not None:
            request_data["params"] = params
        if filters is not None:
            request_data["filters"] = filters
        if ids is not None:
            request_data["ids"] = ids
        if current_ab_id is not None:
            request_data["current_ab_id"] = current_ab_id
        if fc_code is not None:
            request_data["fc_code"] = fc_code
        if fc_name is not None:
            request_data["fc_name"] = fc_name

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/currency_list/",
            request_data
        )

        return response_data

    @mcp.tool()
    def currency_create(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        fc_code: str = Field(description="币别代码"),
        fc_name: str = Field(description="币别名称"),
        exchange_rate: float = Field(description="汇率")
    ) -> Dict[str, Any]:
        """
        新增币别

        Returns:
            Dict[str, Any]: 返回API响应数据
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "fc_code": fc_code,
            "fc_name": fc_name,
            "exchange_rate": exchange_rate,
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/currency_create/",
            request_data
        )

        return response_data

    @mcp.tool()
    def currency_update(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        id: int = Field(description="币别ID"),
        fc_code: str = Field(default=None, description="币别代码"),
        fc_name: str = Field(default=None, description="币别名称"),
        exchange_rate: float = Field(default=None, description="汇率")
    ) -> Dict[str, Any]:
        """
        更新币别信息

        Returns:
            Dict[str, Any]: 返回API响应数据
        """
        # 构建请求数据
        request_data = {
            "id": id,
            "ab_id": ab_id,
        }

        # 添加可选参数
        if fc_code is not None:
            request_data["fc_code"] = fc_code
        if fc_name is not None:
            request_data["fc_name"] = fc_name
        if exchange_rate is not None:
            request_data["exchange_rate"] = exchange_rate

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/currency_update/",
            request_data
        )

        return response_data

    @mcp.tool()
    def currency_batch_delete(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        ids: List[int] = Field(description="要删除的币别ID列表")
    ) -> Dict[str, Any]:
        """
        批量删除币别

        Returns:
            Dict[str, Any]: 返回API响应数据
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "ids": ids,
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/currency_batch_delete/",
            request_data
        )

        return response_data
    
    return mcp