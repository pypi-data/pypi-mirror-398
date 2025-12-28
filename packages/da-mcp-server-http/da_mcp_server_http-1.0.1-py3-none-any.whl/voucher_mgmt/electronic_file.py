from fastmcp import Context
from typing import List, Dict, Any

from pydantic import Field
from config import config

def register_electronic_file_tools(mcp):
    """注册电子档案管理相关的工具"""

    @mcp.tool()
    def electronic_file_update(
        ctx: Context,
        ab_id: int = Field(..., description="帐套ID"),
        id: int = Field(..., description="主键"),
        file_id: int = Field(None, description="关联上传的文件ID"),
        name: str = Field(None, description="附件名称"),
        remark: str = Field(None, description="附件备注"),
        category_id: int = Field(None, description="附件小类ID"),
        amount: float = Field(None, description="附件金额"),
        voucher_template_id: int = Field(None, description="凭证模板ID"),
        group_id: int = Field(None, description="附件所属组ID"),
        is_identified_as_invoice: bool = Field(None, description="是否已识别为发票"),
        uploaded_at: str = Field(None, description="上传时间"),
        uploaded_by_id: int = Field(None, description="上传人ID"),
        audit_status: str = Field(None, description="审核状态"),
        audit_at: str = Field(None, description="审核时间"),
        audit_by_id: int = Field(None, description="审核人ID"),
        file_size: int = Field(None, description="文件大小"),
        voucher_id: int = Field(None, description="凭证ID，如果赋值为0，表示把这个字段变为null"),
        document_type: int = Field(None, description="单据类型"),
        document_data: Dict[str, Any] = Field(None, description="单据内容")
    ) -> Dict[str, Any]:
        """
        更新电子档案

        """
        # 准备请求数据，过滤掉None值
        request_data = {}
        local_vars = locals()
        for field, value in local_vars.items():
            if field not in ['ctx', 'request_data'] and value is not None:
                request_data[field] = value

        # 调用通用API处理函数
        response_data, error_message = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/file_manager/electronic_file_update/",
            request_data
        )

        if error_message:
            return {
                "success": False,
                "message": error_message,
                "data": {}
            }

        # 直接返回API响应，不做任何校验
        return response_data

    @mcp.tool()
    def query_electronic_file_list(
        ctx: Context,
        ab_id: int = Field(..., description="帐套ID"),
        current: int = Field(1, description="页码，默认为1"),
        pageSize: int = Field(10, description="每页记录数，默认为10"),
        sorter: Dict[str, str] = Field(None, description="排序字段"),
        filters: Dict[str, List[Any]] = Field(None, description="过滤条件"),
        category_id: int = Field(None, description="附件小类ID", json_schema_extra={"min": 1}),
        voucher_id: int = Field(None, description="凭证ID"),
        ids: List[int] = Field(None, description="电子档案ID清单"),
        exclude_ids: List[int] = Field(None, description="排除电子档案ID清单"),
        is_identified_as_invoice: bool = Field(None, description="是否已识别为发票"),
        name: str = Field(None, description="附件名称"),
        remark: str = Field(None, description="备注"),
        group_id: int = Field(None, description="所属分组ID"),
        document_type: int = Field(None, description="文档类型"),
        audit_status: str = Field(None, description="审核状态"),
        start_date: str = Field(None, description="开始日期"),
        end_date: str = Field(None, description="结束日期")
    ) -> Dict[str, Any]:
        """
        查询电子档案列表
        """
        # 准备请求数据，过滤掉None值
        request_data = {}
        local_vars = locals()
        for field, value in local_vars.items():
            if field not in ['ctx', 'request_data'] and value is not None:
                request_data[field] = value

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/file_manager/electronic_file_list/",
            request_data
        )
        # 直接返回API响应，不做任何校验
        return response_data

    @mcp.tool(
        name="electronic_file_create",
        description="创建电子档案"
    )
    def electronic_file_create(
        ctx: Context,
        ab_id: int = Field(..., description="帐套ID"),
        file_id: int = Field(..., description="关联上传的文件ID"),
        name: str = Field(..., description="附件名称(对应的文件名,注意要带扩展名)"),
        amount: float = Field(..., description="附件金额"),
        file_size: int = Field(..., description="文件大小（字节）"),
        remark: str = Field(..., description="附件备注"),
        category_id: int = Field(None, description="附件小类ID", json_schema_extra={"min": 1}),
        group_id: int = Field(None, description="附件所属组ID", json_schema_extra={"min": 1}),
        is_identified_as_invoice: bool = Field(False, description="是否已识别为发票"),
        document_type: int = Field(
            None,
            description="""单据类型枚举：
                1: 全电专票
                2: 全电普票
                3: 电子专票
                4: 电子普票
                5: 凭证附件
                6: 银行回单
                7: 发票
                12: 发票查验单
                8: 合同
                9: 库存单据
                10: 证照
                11: 其他"""
        ),
        document_data: Dict[str, Any] = Field(None, description="单据内容（将识别的单据内容创建一个JSON记录）")
    ) -> Dict[str, Any]:
        """创建电子档案"""
        request_data = {
            "ab_id": ab_id,
            "file_id": file_id,
            "name": name,
            "amount": amount,
            "file_size": file_size,
            "remark": remark,
            "is_identified_as_invoice": is_identified_as_invoice
        }
        if category_id is not None:
            request_data["category_id"] = category_id
        if group_id is not None:
            request_data["group_id"] = group_id
        if document_type is not None:
            request_data["document_type"] = document_type
        if document_data is not None:
            request_data["document_data"] = document_data

        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/file_manager/electronic_file_create/", request_data)

    @mcp.tool(
        name="electronic_file_batch_delete",
        description="批量删除电子档案"
    )
    def electronic_file_batch_delete(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        ids: List[int] = Field(..., description="要删除的电子档案ID列表")
    ) -> Dict[str, Any]:
        """批量删除电子档案"""
        request_data = {
            "ab_id": ab_id,
            "ids": ids
        }
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/file_manager/electronic_file_batch_delete/", request_data)

    return mcp