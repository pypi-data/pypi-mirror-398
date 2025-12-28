from fastmcp import Context
from typing import Dict, Any, List
from config import config
from pydantic import Field

def register_file_tools(mcp):
    """注册文件管理相关的工具"""

    @mcp.tool(
        name="electronic_file_group_create",
        description="创建电子档案分组"
    )
    def electronic_file_group_create(
        ctx: Context,
        ab_id: int = Field(..., description="帐套ID"),
        name: str = Field(..., description="分组名称"),
        remark: str = Field("", description="备注")
    ) -> Dict[str, Any]:
        """创建电子档案分组"""
        request_data = {
            "ab_id": ab_id,
            "name": name,
            "remark": remark
        }
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/file_manager/electronic_file_group_create/", request_data)

    @mcp.tool(
        name="electronic_file_group_list",
        description="分页查询电子档案分组列表"
    )
    def electronic_file_group_list(
        ctx: Context,
        ab_id: int = Field(..., description="帐套ID"),
        current: int = Field(1, description="页码"),
        pageSize: int = Field(10, description="每页记录数"),
        sorter: Dict[str, str] = Field(None, description="排序字段"),
        params: Dict[str, Any] = Field(None, description="查询参数"),
        filters: Dict[str, List] = Field(None, description="筛选条件")
    ) -> Dict[str, Any]:
        """分页查询电子档案分组列表"""
        request_data = {
            "ab_id": ab_id,
            "current": current,
            "pageSize": pageSize
        }
        if sorter:
            request_data["sorter"] = sorter
        if params:
            request_data["params"] = params
        if filters:
            request_data["filters"] = filters

        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/file_manager/electronic_file_group_list/", request_data)

    @mcp.tool(
        name="electronic_file_group_update",
        description="更新电子档案分组"
    )
    def electronic_file_group_update(
        ctx: Context,
        ab_id: int = Field(..., description="帐套ID"),
        id: int = Field(..., description="分组ID"),
        name: str = Field(None, description="分组名称"),
        remark: str = Field(None, description="备注")
    ) -> Dict[str, Any]:
        """更新电子档案分组"""
        request_data = {
            "id": id,
            "ab_id": ab_id
        }
        if name is not None:
            request_data["name"] = name
        if remark is not None:
            request_data["remark"] = remark

        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/file_manager/electronic_file_group_update/", request_data)

    @mcp.tool(
        name="electronic_file_group_batch_delete",
        description="批量删除电子档案分组"
    )
    def electronic_file_group_batch_delete(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        ids: List[int] = Field(..., description="要删除的分组ID列表")
    ) -> Dict[str, Any]:
        """批量删除电子档案分组"""
        request_data = {
            "ab_id": ab_id,
            "ids": ids
        }
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/file_manager/electronic_file_group_batch_delete/", request_data)

    @mcp.tool(
        name="electronic_file_category_create",
        description="创建电子档案分类"
    )
    def electronic_file_category_create(
        ctx: Context,
        ab_id: int = Field(..., description="帐套ID"),
        name: str = Field(..., description="分类名称"),
        parent_id: int = Field(None, description="父级分类ID")
    ) -> Dict[str, Any]:
        """创建电子档案分类"""
        request_data = {
            "ab_id": ab_id,
            "name": name
        }
        if parent_id is not None:
            request_data["parent_id"] = parent_id

        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/file_manager/electronic_file_category_create/", request_data)

    @mcp.tool(
        name="electronic_file_category_list",
        description="分页查询电子档案分类列表"
    )
    def electronic_file_category_list(
        ctx: Context,
        ab_id: int = Field(..., description="帐套ID"),
        current: int = Field(1, description="页码"),
        pageSize: int = Field(10, description="每页记录数"),
        sorter: Dict[str, str] = Field(None, description="排序字段"),
        params: Dict[str, Any] = Field(None, description="查询参数"),
        filters: Dict[str, List] = Field(None, description="筛选条件")
    ) -> Dict[str, Any]:
        """分页查询电子档案分类列表"""
        request_data = {
            "ab_id": ab_id,
            "current": current,
            "pageSize": pageSize
        }
        if sorter:
            request_data["sorter"] = sorter
        if params:
            request_data["params"] = params
        if filters:
            request_data["filters"] = filters

        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/file_manager/electronic_file_category_list/", request_data)

    @mcp.tool(
        name="electronic_file_category_update",
        description="更新电子档案分类"
    )
    def electronic_file_category_update(
        ctx: Context,
        ab_id: int = Field(..., description="帐套ID"),
        id: int = Field(..., description="分类ID"),
        name: str = Field(None, description="分类名称"),
        parent_id: int = Field(None, description="父级分类ID")
    ) -> Dict[str, Any]:
        """更新电子档案分类"""
        request_data = {
            "id": id,
            "ab_id": ab_id
        }
        if name is not None:
            request_data["name"] = name
        if parent_id is not None:
            request_data["parent_id"] = parent_id

        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/file_manager/electronic_file_category_update/", request_data)

    @mcp.tool(
        name="electronic_file_category_batch_delete",
        description="批量删除电子档案分类"
    )
    def electronic_file_category_batch_delete(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        ids: List[int] = Field(..., description="要删除的分类ID列表")
    ) -> Dict[str, Any]:
        """批量删除电子档案分类"""
        request_data = {
            "ab_id": ab_id,
            "ids": ids
        }
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/file_manager/electronic_file_category_batch_delete/", request_data)

    @mcp.tool(
        name="get_electronic_file_category_cascader_options",
        description="获取电子档案分类级联选项"
    )
    def get_electronic_file_category_cascader_options(
        ctx: Context,
        ab_id: int = Field(..., description="帐套ID")
    ) -> Dict[str, Any]:
        """获取电子档案分类级联选项"""
        request_data = {"ab_id": ab_id}
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/file_manager/get_electronic_file_category_cascader_options/", request_data)

    return mcp