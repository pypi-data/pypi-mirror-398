from fastmcp import Context
from typing import List, Dict, Any
from pydantic import Field
from config import config

def register_auxiliary_accounting_category_tools(mcp):
    """注册辅助核算类别管理相关的工具"""

    @mcp.tool()
    def auxiliary_accounting_category_list(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        current: int = Field(default=1, ge=1, description="页码"),
        pageSize: int = Field(default=10, ge=0, description="每页记录数,为0则返回所有记录"),
        sorter: Dict[str, str] = Field(default=None, description="排序字段"),
        params: Dict[str, Any] = Field(default=None, description="参数搜索条件"),
        filters: Dict[str, List[Any]] = Field(default=None, description="过滤条件"),
        id: int = Field(default=None, description="主键ID"),
        keyWords: str = Field(default=None, max_length=32, description="关键词")
    ) -> Dict[str, Any]:
        """
        分页查询辅助核算类别列表

        Returns:
            Dict[str, Any]: 返回API响应数据
        """
        # 构建请求数据
        request_data = {
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
        if id is not None:
            request_data["id"] = id
        if ab_id is not None:
            request_data["ab_id"] = ab_id
        if keyWords is not None:
            request_data["keyWords"] = keyWords

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/auxiliary_accounting_category_list/",
            request_data
        )

        # 直接返回API响应
        return response_data

    @mcp.tool()
    def auxiliary_accounting_category_create(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        name: str = Field(description="类别名称"),
        column_labels: List[str] = Field(default=None, description="例如扩展列标签:['标签1','标签2']")
    ) -> Dict[str, Any]:
        """
        新增辅助核算类别

        Returns:
            Dict[str, Any]: 返回API响应数据
        """
        # 构建请求数据
        request_data = {
            "ab_id":ab_id,
            "name": name,
        }

        # 添加可选参数
        if column_labels is not None:
            request_data["column_labels"] = column_labels

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/auxiliary_accounting_category_create/",
            request_data
        )

        return response_data

    @mcp.tool()
    def auxiliary_accounting_category_update(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        id: int = Field(description="辅助核算类别ID"),
        name: str = Field(description="类别名称"),
        column_labels: List[str] = Field(default=None, description="例如扩展列标签:['标签1','标签2']")
    ) -> Dict[str, Any]:
        """
        更新辅助核算类别

        Returns:
            Dict[str, Any]: 返回API响应数据
        """
        # 构建请求数据
        request_data = {
            "id": id,
            "ab_id": ab_id,
            "name": name,
        }

        # 添加可选参数
        if column_labels is not None:
            request_data["column_labels"] = column_labels

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/auxiliary_accounting_category_update/",
            request_data
        )

        return response_data

    @mcp.tool()
    def auxiliary_accounting_category_batch_delete(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        ids: List[int] = Field(description="要删除的辅助核算类别ID列表")
    ) -> Dict[str, Any]:
        """
        批量删除辅助核算类别

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
            f"{config.backend_base_url}/api/general_ledger/auxiliary_accounting_category_batch_delete/",
            request_data
        )

        return response_data

    return mcp