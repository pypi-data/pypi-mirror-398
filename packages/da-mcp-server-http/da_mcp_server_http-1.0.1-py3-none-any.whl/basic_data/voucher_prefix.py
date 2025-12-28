from fastmcp import Context
from typing import List, Dict, Any
from pydantic import Field
from config import config

def register_voucher_prefix_tools(mcp):
    """注册凭证字管理相关的工具"""

    @mcp.tool()
    def voucher_prefix_list(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        current: int = Field(default=1, ge=1, description="页码"),
        pageSize: int = Field(default=10, ge=0, description="每页记录数,为0则返回所有记录"),
        sorter: Dict[str, str] = Field(default=None, description="排序字段"),
        params: Dict[str, Any] = Field(default=None, description="参数搜索条件"),
        filters: Dict[str, List[Any]] = Field(default=None, description="过滤条件"),
        is_default: bool = Field(default=None, description="是否默认"),
        id: int = Field(default=None, description="凭证字ID")
    ) -> Dict[str, Any]:
        """
        分页查询凭证字列表
        
        Returns:
            包含分页数据和凭证字列表的字典
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
        if is_default is not None:
            request_data["is_default"] = is_default
        if id is not None:
            request_data["id"] = id

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/voucher_prefix_list/",
            request_data
        )

        return response_data

    @mcp.tool()
    def voucher_prefix_create(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        voucher_code: str = Field(description="凭证字"),
        print_title: str = Field(description="打印标题"),
        is_default: bool = Field(description="是否默认")
    ) -> Dict[str, Any]:
        """
        新增凭证字
        
        Returns:
            包含新增记录ID的字典
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "voucher_code": voucher_code,
            "print_title": print_title,
            "is_default": is_default,
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/voucher_prefix_create/",
            request_data
        )

        return response_data

    @mcp.tool()
    def voucher_prefix_update(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        id: int = Field(description="凭证字ID"),
        voucher_code: str = Field(default=None, description="凭证字"),
        print_title: str = Field(default=None, description="打印标题"),
        is_default: bool = Field(default=None, description="是否默认")
    ) -> Dict[str, Any]:
        """
        更新凭证字信息
        
        Returns:
            包含影响行数的字典
        """
        # 构建请求数据
        request_data = {
            "id": id,
            "ab_id": ab_id,
        }

        # 添加可选参数
        if voucher_code is not None:
            request_data["voucher_code"] = voucher_code
        if print_title is not None:
            request_data["print_title"] = print_title
        if is_default is not None:
            request_data["is_default"] = is_default

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/voucher_prefix_update/",
            request_data
        )

        return response_data

    @mcp.tool()
    def voucher_prefix_batch_delete(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        ids: List[int] = Field(description="要删除的凭证字ID列表")
    ) -> Dict[str, Any]:
        """
        批量删除凭证字
        
        Returns:
            包含影响行数的字典
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "ids": ids,
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/voucher_prefix_batch_delete/",
            request_data
        )

        return response_data
    
    return mcp