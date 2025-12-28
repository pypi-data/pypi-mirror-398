"""
凭证模板管理工具
"""
from fastmcp import Context
from typing import List, Dict, Any, Optional
from config import config
from pydantic import Field

def register_voucher_template_tools(mcp):
    """注册凭证模板相关工具"""

    @mcp.tool()
    def voucher_template_list(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        current: int = Field(default=1, ge=1, description="页码"),
        pageSize: int = Field(default=10, ge=0, description="每页记录数,为0则返回所有记录"),
        template_type_id: int = Field(default=None, description="凭证模板类型ID"),
        id: int = Field(default=None, description="凭证模板id"),
        keyWords: str = Field(default=None, max_length=100, description="凭证模板名称关键字"),
    ) -> Dict[str, Any]:
        """
        分页查询凭证模板列表

        Args:
            ctx: MCP上下文对象
            ab_id: 帐套ID
            current: 页码，默认为1
            pageSize: 每页记录数，默认为10，为0则返回所有记录
            template_type_id: 凭证模板类型ID（可选）
            id: 凭证模板ID（可选）
            keyWords: 凭证模板名称关键字（可选）

        Returns:
            Dict[str, Any]: 返回API响应数据，包含分页信息和凭证模板列表，
                          其中template_data字段已转换为JSON格式并提取了科目关键信息
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "current": current,
            "pageSize": pageSize,
        }

        # 添加可选参数
        if template_type_id is not None:
            request_data["template_type_id"] = template_type_id
        if id is not None:
            request_data["id"] = id
        if keyWords is not None:
            request_data["keyWords"] = keyWords

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/voucher_template_list/",
            request_data
        )

        # 处理返回数据
        if (response_data.get("success") and
            "data" in response_data and
            "data" in response_data["data"]):

            import json

            for item in response_data["data"]["data"]:
                if "template_data" in item and isinstance(item["template_data"], str):
                    try:
                        # 解析JSON格式的template_data
                        template_json = json.loads(item["template_data"])

                        # 提取分录的科目关键信息
                        voucher_details_summary = []
                        if "voucher_details" in template_json:
                            for detail in template_json["voucher_details"]:
                                if detail.get('accounting_title_id') != 0:
                                    # 提取关键信息
                                    detail_summary = {
                                        "summary": detail.get("summary", ""),
                                        "accounting_title_id": detail.get("accounting_title_id", 0),
                                        "accounting_title_code": '',
                                        "accounting_title_name": '',
                                        "debit_amount": detail.get("debit_amount", "0.00"),
                                        "credit_amount": detail.get("credit_amount", "0.00"),
                                        "auxiliary_code": detail.get("auxiliary_code", ""),
                                        "auxiliary_name": detail.get("auxiliary_name", "")
                                    }

                                    # 从accounting_title中提取科目信息
                                    if "accounting_title" in detail and detail["accounting_title"]:
                                        accounting_title = detail["accounting_title"]
                                        detail_summary["accounting_title_code"] = accounting_title.get("at_code", "")
                                        detail_summary["accounting_title_name"] = accounting_title.get("at_name_path", "")

                                    voucher_details_summary.append(detail_summary)

                        # 更新模板数据
                        item['template_data'] = voucher_details_summary

                    except (json.JSONDecodeError, KeyError, TypeError) as e:
                        # 如果解析失败，保留原始数据并添加错误信息
                        item["template_data_json"] = None
                        item["voucher_details_summary"] = []
                        item["template_data_parse_error"] = str(e)

        # 返回处理后的响应数据
        return response_data

    @mcp.tool()
    def voucher_template_create(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        template_type_id: int = Field(description="凭证模板类型"),
        name: str = Field(max_length=100, description="凭证模板名称"),
        template_data_json: List[Dict[str, Any]] = Field(description="凭证模板数据JSON数组，例如:[{'summary':'xxx','accounting_title_id':88,'line_number':1}]"),
        description: str = Field(max_length=500, default="", description="凭证模板描述，用于描述模板应用场景"),
    ) -> Dict[str, Any]:
        """
        新增凭证模板

        补充说明：
        2,template_data_json格式示例：[{'summary':'工资收入','accounting_title_id':88,'line_number':1}, {'summary':'其他费用','accounting_title_id':99,'line_number':2}]
        3,template_data_json中的accounting_title_id应该是一个明细科目的id

        Returns:
            Dict[str, Any]: 返回新增记录ID
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "template_type_id": template_type_id,
            "name": name,
            "description": description
        }

        # 添加template_data或template_data_json
        if template_data_json is not None:
            request_data["template_data_json"] = template_data_json

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/voucher_template_create/",
            request_data
        )

        # 直接返回API响应
        return response_data

    @mcp.tool()
    def voucher_template_update(
        ctx: Context,
        ab_id: int = Field(description="帐套"),
        id: int = Field(description="主键"),
        template_data_json: List[Dict[str, Any]] = Field(description="凭证模板数据JSON数组，例如:[{'summary':'xxx','accounting_title_id':88,'line_number':1}]"),
        template_type_id: int = Field(default=None, description="凭证模板类型"),
        name: str = Field(max_length=100, default=None, description="凭证模板名称"),
        description: str = Field(max_length=500, default=None, description="凭证模板描述，用于描述模板应用场景"),
    ) -> Dict[str, Any]:
        """
        更新凭证模板

        Returns:
            Dict[str, Any]: 返回影响行数
        """
        # 构建请求数据
        request_data = {
            "id": id,
            "ab_id": ab_id
        }

        # 添加可选参数
        if ab_id is not None:
            request_data["ab_id"] = ab_id
        if template_type_id is not None:
            request_data["template_type_id"] = template_type_id
        if name is not None:
            request_data["name"] = name
        if template_data_json is not None:
            request_data["template_data_json"] = template_data_json
        if description is not None:
            request_data["description"] = description

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/voucher_template_update/",
            request_data
        )

        # 直接返回API响应
        return response_data

    @mcp.tool()
    def voucher_template_batch_delete(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        ids: List[int] = Field(description="要删除的记录的ID列表"),
    ) -> Dict[str, Any]:
        """
        批量删除凭证模板

        Args:
            ctx: MCP上下文对象
            ids: 要删除的记录的ID列表

        Returns:
            Dict[str, Any]: 返回删除操作的结果
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "ids": ids
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/general_ledger/voucher_template_batch_delete/",
            request_data
        )

        # 直接返回API响应
        return response_data

    return mcp