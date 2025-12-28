from fastmcp import Context
from typing import List, Dict, Any
from pydantic import Field
from config import config

def register_auxiliary_accounting_tools(mcp):
    """注册辅助核算管理相关的工具"""

    @mcp.tool()
    def auxiliary_accounting_list(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        current: int = Field(default=1, ge=1, description="页码"),
        pageSize: int = Field(default=10, ge=0, description="每页记录数,为0则返回所有记录"),
        sorter: Dict[str, str] = Field(default=None, description="排序字段"),
        params: Dict[str, Any] = Field(default=None, description="参数搜索条件"),
        filters: Dict[str, List[Any]] = Field(default=None, description="过滤条件"),
        auxiliary_accounting_category_id: int = Field(default=None, description="辅助核算类别ID"),
        auxiliary_accounting_category_name: str = Field(default=None, description="辅助核算类别名称"),
        keyWords: str = Field(default=None, description="关键词")
    ) -> Dict[str, Any]:
        """
        分页查询辅助核算列表
        
        Returns:
            包含分页数据和辅助核算列表的字典
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
        if auxiliary_accounting_category_id is not None:
            request_data["auxiliary_accounting_category_id"] = auxiliary_accounting_category_id
        if auxiliary_accounting_category_name is not None:
            request_data["auxiliary_accounting_category_name"] = auxiliary_accounting_category_name
        if keyWords is not None:
            request_data["keyWords"] = keyWords

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/auxiliary_accounting_list/",
            request_data
        )

        return response_data

    @mcp.tool()
    def auxiliary_accounting_create(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        auxiliary_accounting_category_id: int = Field(description="辅助核算类别ID"),
        code: str = Field(description="编码"),
        name: str = Field(description="名称"),
        remarks: str = Field(default=None, description="备注"),
        is_enabled: bool = Field(default=True, description="是否启用"),
        rf1: str = Field(default=None, description="预留字段1"),
        rf2: str = Field(default=None, description="预留字段2"),
        rf3: str = Field(default=None, description="预留字段3"),
        rf4: str = Field(default=None, description="预留字段4"),
        rf5: str = Field(default=None, description="预留字段5"),
        rf6: str = Field(default=None, description="预留字段6"),
        rf7: str = Field(default=None, description="预留字段7"),
        rf8: str = Field(default=None, description="预留字段8")
    ) -> Dict[str, Any]:
        """
        新增辅助核算
        
        Returns:
            包含新增记录ID、代码和名称的字典
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "auxiliary_accounting_category_id": auxiliary_accounting_category_id,
            "code": code,
            "name": name,
            "is_enabled": is_enabled,
        }

        # 添加可选参数
        if remarks is not None:
            request_data["remarks"] = remarks
        if rf1 is not None:
            request_data["rf1"] = rf1
        if rf2 is not None:
            request_data["rf2"] = rf2
        if rf3 is not None:
            request_data["rf3"] = rf3
        if rf4 is not None:
            request_data["rf4"] = rf4
        if rf5 is not None:
            request_data["rf5"] = rf5
        if rf6 is not None:
            request_data["rf6"] = rf6
        if rf7 is not None:
            request_data["rf7"] = rf7
        if rf8 is not None:
            request_data["rf8"] = rf8

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/auxiliary_accounting_create/",
            request_data
        )

        return response_data

    @mcp.tool()
    def auxiliary_accounting_update(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        id: int = Field(description="辅助核算ID"),
        auxiliary_accounting_category_id: int = Field(default=None, description="辅助核算类别ID"),
        code: str = Field(default=None, description="编码"),
        name: str = Field(default=None, description="名称"),
        remarks: str = Field(default=None, description="备注"),
        is_enabled: bool = Field(default=None, description="是否启用"),
        rf1: str = Field(default=None, description="预留字段1"),
        rf2: str = Field(default=None, description="预留字段2"),
        rf3: str = Field(default=None, description="预留字段3"),
        rf4: str = Field(default=None, description="预留字段4"),
        rf5: str = Field(default=None, description="预留字段5"),
        rf6: str = Field(default=None, description="预留字段6"),
        rf7: str = Field(default=None, description="预留字段7"),
        rf8: str = Field(default=None, description="预留字段8")
    ) -> Dict[str, Any]:
        """
        更新辅助核算信息

        Returns:
            包含影响行数的字典
        """
        # 构建请求数据
        request_data = {
            "id": id,
            "ab_id": ab_id,
        }

        # 添加可选参数
        if auxiliary_accounting_category_id is not None:
            request_data["auxiliary_accounting_category_id"] = auxiliary_accounting_category_id
        if code is not None:
            request_data["code"] = code
        if name is not None:
            request_data["name"] = name
        if remarks is not None:
            request_data["remarks"] = remarks
        if is_enabled is not None:
            request_data["is_enabled"] = is_enabled
        if rf1 is not None:
            request_data["rf1"] = rf1
        if rf2 is not None:
            request_data["rf2"] = rf2
        if rf3 is not None:
            request_data["rf3"] = rf3
        if rf4 is not None:
            request_data["rf4"] = rf4
        if rf5 is not None:
            request_data["rf5"] = rf5
        if rf6 is not None:
            request_data["rf6"] = rf6
        if rf7 is not None:
            request_data["rf7"] = rf7
        if rf8 is not None:
            request_data["rf8"] = rf8

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/auxiliary_accounting_update/",
            request_data
        )

        return response_data

    @mcp.tool()
    def auxiliary_accounting_batch_delete(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        ids: List[int] = Field(description="要删除的辅助核算ID列表")
    ) -> Dict[str, Any]:
        """
        批量删除辅助核算
        
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
            f"{config.backend_base_url}/api/general_ledger/auxiliary_accounting_batch_delete/",
            request_data
        )

        return response_data

    @mcp.tool()
    def auxiliary_accounting_batch_create(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        items: List[Dict[str, Any]] = Field(description="批量新增的辅助核算列表,数据结构参考单个新增的参数")
    ) -> Dict[str, Any]:
        """
        批量新增辅助核算
        
        Returns:
            包含成功创建的记录ID列表和错误信息的字典
        """
        # 构建请求数据
        request_data = {
            "ab_id":ab_id,
            "items": items,
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/auxiliary_accounting_batch_create/",
            request_data
        )

        return response_data
    
    return mcp