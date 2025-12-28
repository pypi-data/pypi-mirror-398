"""
资产类别管理工具模块
"""
from typing import List
from fastmcp import FastMCP, Context
from pydantic import Field
from config import config

def register_asset_category_tools(mcp: FastMCP) -> FastMCP:
    """注册资产类别管理相关的工具"""

    @mcp.tool(
        name="asset_category_create"
    )
    def asset_category_create_tool(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        category_code: str = Field(description="类别编码"),
        category_name: str = Field(description="类别名称"),
        depreciation_method: int = Field(description="折旧方法（枚举值）"),
        expected_useful_life: int = Field(description="预计使用年限"),
        estimated_residual_rate: float = Field(description="预计净残值率%"),
        asset_title_id: int = Field(description="固定资产科目ID"),
        accumulated_depreciation_title_id: int = Field(description="累计折旧科目ID"),
        remarks: str = Field(default="", description="备注（可选）")
    ) -> dict:
        """
        创建新的资产类别

        Returns:
            dict: 包含创建结果的字典，包含以下字段：
                - record_id: int - 新创建的资产类别ID
        """
        request_data = {
            "ab_id": ab_id,
            "category_code": category_code,
            "category_name": category_name,
            "depreciation_method": depreciation_method,
            "expected_useful_life": expected_useful_life,
            "estimated_residual_rate": estimated_residual_rate,
            "asset_title_id": asset_title_id,
            "accumulated_depreciation_title_id": accumulated_depreciation_title_id,
            "remarks": remarks
        }
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/assets/asset_category_create/", request_data)

    @mcp.tool(
        name="asset_category_list"
    )
    def asset_category_list_tool(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        current: int = Field(default=1, description="页码（可选，默认1）"),
        pageSize: int = Field(default=10, description="每页记录数（可选，默认10，为0则返回所有记录）"),
        sorter: dict = Field(default=None, description="排序字段（可选）"),
        params: dict = Field(default=None, description="搜索参数（可选）"),
        filters: dict = Field(default=None, description="过滤条件（可选）")
    ) -> dict:
        """
        分页查询资产类别

        Args:
            ctx: MCP上下文对象
            ab_id: 帐套ID
            current: 页码（可选，默认1）
            pageSize: 每页记录数（可选，默认10，为0则返回所有记录）
            sorter: 排序字段（可选）
            params: 搜索参数（可选）
            filters: 过滤条件（可选）

        Returns:
            dict: 包含查询结果的字典，包含以下字段：
                - data: List[dict] - 资产类别列表数据
                - total: int - 总记录数
                - current: int - 当前页码
                - pageSize: int - 每页记录数
        """
        request_data = {
            "ab_id": ab_id,
            "current": current,
            "pageSize": pageSize,
        }
        # 只添加非None的字段
        optional_fields = {
            "sorter": sorter,
            "params": params,
            "filters": filters
        }
        for key, value in optional_fields.items():
            if value is not None:
                request_data[key] = value
        
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/assets/asset_category_list/", request_data)

    @mcp.tool(
        name="asset_category_update"
    )
    def asset_category_update_tool(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        id: int = Field(description="资产类别ID（主键）"),
        category_code: str = Field(default=None, description="类别编码（可选）"),
        category_name: str = Field(default=None, description="类别名称（可选）"),
        depreciation_method: int = Field(default=None, description="折旧方法（可选）"),
        expected_useful_life: int = Field(default=None, description="预计使用年限（可选）"),
        estimated_residual_rate: float = Field(default=None, description="预计净残值率%（可选）"),
        asset_title_id: int = Field(default=None, description="固定资产科目ID（可选）"),
        accumulated_depreciation_title_id: int = Field(default=None, description="累计折旧科目ID（可选）"),
        remarks: str = Field(default=None, description="备注（可选）")
    ) -> dict:
        """
        更新资产类别

        Returns:
            dict: 包含更新结果的字典，包含以下字段：
                - affect_rows: int - 影响的行数
        """
        request_data = {
            "id": id,
            "ab_id": ab_id,
        }
        # 只添加非None的字段
        optional_fields = {
            "category_code": category_code,
            "category_name": category_name,
            "depreciation_method": depreciation_method,
            "expected_useful_life": expected_useful_life,
            "estimated_residual_rate": estimated_residual_rate,
            "asset_title_id": asset_title_id,
            "accumulated_depreciation_title_id": accumulated_depreciation_title_id,
            "remarks": remarks
        }
        for key, value in optional_fields.items():
            if value is not None:
                request_data[key] = value

        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/assets/asset_category_update/", request_data)

    @mcp.tool(
        name="asset_category_batch_delete",
        description="批量删除资产类别"
    )
    def asset_category_batch_delete_tool(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        ids: List[int] = Field(description="要删除的资产类别ID列表")
    ) -> dict:
        """
        批量删除资产类别

        Args:
            ctx: MCP上下文对象
            ids: 要删除的资产类别ID列表

        Returns:
            dict: 包含删除结果的字典，包含以下字段：
                - affect_rows: int - 影响的行数
        """
        request_data = {
            "ab_id": ab_id,
            "ids": ids
        }
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/assets/asset_category_batch_delete/", request_data)

    return mcp