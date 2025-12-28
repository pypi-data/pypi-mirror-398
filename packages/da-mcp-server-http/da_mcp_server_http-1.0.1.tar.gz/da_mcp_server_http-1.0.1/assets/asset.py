"""
资产管理工具模块
"""
from typing import List
from fastmcp import FastMCP, Context
from pydantic import Field
from config import config

def register_asset_tools(mcp: FastMCP) -> FastMCP:
    """注册资产管理相关的工具"""

    @mcp.tool(
        name="asset_create"
    )
    def asset_create_tool(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        asset_code: str = Field(description="资产编码"),
        asset_name: str = Field(description="资产名称"),
        asset_category_id: int = Field(description="资产类别ID"),
        department_ids: List[int] = Field(description="资产使用部门,辅助类别'部门'中的辅助id"),
        start_use_date: str = Field(description="开始使用日期，格式：YYYY-MM-DD"),
        quantity: int = Field(description="数量"),
        depreciation_method: int = Field(description="折旧方法（枚举值:0-平均年限法,1-双倍余额折旧法,2-不提折旧）"),
        expected_periods: int = Field(description="预计使用期数"),
        original_value: float = Field(description="原值"),
        residual_rate: float = Field(description="残值率%"),
        initial_accumulated_depreciation: float = Field(description="期初累计折旧"),
        monthly_depreciation: float = Field(description="月折旧额"),
        asset_title: dict = Field(description="固定资产科目信息"),
        purchase_counter_title: dict = Field(description="资产购入对方科目信息"),
        accumulated_depreciation_title: dict = Field(description="累计折旧科目信息"),
        disposal_title: dict = Field(description="资产清理科目信息"),
        depreciation_expense_title: List[dict] = Field(description="折旧费用科目分摊列表"),
        current_period: str = Field(description="当前期间，格式：YYYY-MM"),
        specifications: str = Field(default="", description="规格型号（可选）"),
        location: str = Field(default="", description="存放地点（可选）"),
        user_id: int = Field(default=None, description="使用人ID,辅助类别'部门'中的辅助id（可选）"),
        tax_amount: float = Field(default=0, description="税额（可选）"),
        impairment_provision: float = Field(default=0, description="减值准备（可选）"),
        tax_title: dict = Field(default=None, description="税金科目信息（可选）"),
        impairment_title: dict = Field(default=None, description="减值准备科目信息（可选）"),
        impairment_counter_title: List[dict] = Field(default=None, description="减值准备对方科目分摊列表（可选）"),
        remarks: str = Field(default="", description="备注（可选）")
    ) -> dict:
        """
        创建新的资产

        补充信息：
            1,asset_title,purchase_counter_title,tax_title,accumulated_depreciation_title,disposal_title,impairment_title格式：
           {
               "accountingTitleId": 10690, //科目id
               "accountingTitleName": "1002 银行存款", //科目名称
               "auxiliaries": [ //辅助情况
                   {
                       "id": 454,
                       "code": "B003",
                       "name": "农业银行专用户",
                       "auxiliary_accounting_category_id": 502
                   }
               ]
           }
           这里一定要注意，构建这个参数时一定要检查科目是否开启了辅助核算，如果开启必须构建对应的auxiliaries。
           2,depreciation_expense_title(必填),impairment_counter_title（选填），列表中的数据结构示例:
           {
            "asset_id": 123, // (必填，此字段为了兼容而保留，固定等于0即可)
            "department_id" 123, //分摊部门ID（辅助核算类别为'部门'的辅助id)(必填)
            "allocation_type": "depreciation", //分摊类型(枚举：depreciation-固定资产科目,impairment-减值准备分摊)(必填)
            "allocation_ratio":20, //分摊比例（这里表示20%)(必填),
            "expense_title": { // 费用科目(必填)
               "accountingTitleId": 10690, //科目id(必填)
               "accountingTitleName": "1002 银行存款", //科目名称(必填)
               "auxiliaries": [ //辅助情况(必填，可以为空)
                   {
                       "id": 454,
                       "code": "B003",
                       "name": "农业银行专用户",
                       "auxiliary_accounting_category_id": 502
                   }
               ]
              }
           }
           这里注意分摊比例，每一项总和要等于100,同时这里的科目构建时一定要检查科目是否开启了辅助核算，如果开启必须构建对应的auxiliaries
            3,创建示例：
            1）当个部门分摊：
            {
                "asset_code": "00001",
                "asset_name": "笔记本",
                "asset_category_id": 213,
                "quantity": 1,
                "department_ids": [
                    648
                ],
                "start_use_date": "2025-10-05",
                "depreciation_method": 0,
                "expected_periods": 36,
                "original_value": 5000,
                "residual_rate": 5.00,
                "depreciation_periods": 0,
                "initial_accumulated_depreciation": 0,
                "monthly_depreciation": 131.94,
                "depreciation_current_year": 0,
                "asset_title": {
                    "accountingTitleId": 12058,
                    "atCode": "151",
                    "accountingTitleName": "151 固定资产 "
                },
                "purchase_counter_title": {
                    "accountingTitleId": 12049,
                    "accountingTitleName": "113 内部往来",
                    "auxiliary_accountings": {
                        "555": 648
                    },
                    "auxiliaries": [
                        {
                            "id": 648,
                            "code": "BM004",
                            "name": "基建工程部",
                            "auxiliary_accounting_category_id": 555
                        }
                    ],
                    "auxiliary_accounting_category_ids": [
                        555
                    ],
                    "auxiliary_accounting_category_names": [
                        "部门"
                    ]
                },
                "accumulated_depreciation_title": {
                    "accountingTitleId": 12059,
                    "atCode": "152",
                    "accountingTitleName": "152 累计折旧 "
                },
                "depreciation_expense_title": [
                    {
                        "department_id": 648,
                        "allocation_ratio": "100",
                        "asset_id": 0,
                        "allocation_type": "impairment",
                        "expense_title": {
                            "accountingTitleId": 12045,
                            "accountingTitleName": "101 现金",
                            "auxiliary_accountings": {},
                            "auxiliaries": []
                        }
                    }
                ],
                "disposal_title": {
                    "accountingTitleId": 12060,
                    "atCode": "153",
                    "accountingTitleName": "固定资产清理",
                    "currencies": [],
                    "auxiliaries": [],
                    "auxiliary_accounting_category_ids": [],
                    "auxiliary_accounting_category_names": []
                },
                "ab_id": 0,
                "current_period": "2025-10"
            }

            2）多个部门分摊：
            {
            "asset_code": "00002",
            "asset_name": "笔记本2",
            "asset_category_id": 213,
            "quantity": 1,
            "department_ids": [
                648,
                647
            ],
            "start_use_date": "2025-10-05",
            "depreciation_method": 0,
            "expected_periods": 36,
            "original_value": 6000,
            "residual_rate": 5.00,
            "depreciation_periods": 0,
            "initial_accumulated_depreciation": 0,
            "monthly_depreciation": 158.33,
            "depreciation_current_year": 0,
            "asset_title": {
                "accountingTitleId": 12058,
                "atCode": "151",
                "accountingTitleName": "151 固定资产 "
            },
            "purchase_counter_title": {
                "accountingTitleId": 12045,
                "accountingTitleName": "101 现金",
                "auxiliaries": []
            },
            "accumulated_depreciation_title": {
                "accountingTitleId": 12059,
                "atCode": "152",
                "accountingTitleName": "152 累计折旧 "
            },
            "disposal_title": {
                "accountingTitleId": 12060,
                "atCode": "153",
                "accountingTitleName": "固定资产清理",
                "currencies": [],
                "auxiliaries": [],
                "auxiliary_accounting_category_ids": [],
                "auxiliary_accounting_category_names": []
            },
            "depreciation_expense_title": [
                {
                    "department_id": 648,
                    "allocation_ratio": "33",
                    "asset_id": 0,
                    "allocation_type": "impairment",
                    "expense_title": {
                        "accountingTitleId": 12049,
                        "accountingTitleName": "113 内部往来",
                        "auxiliary_accountings": {
                            "555": 648
                        },
                        "auxiliaries": [
                            {
                                "id": 648,
                                "code": "BM004",
                                "name": "基建工程部",
                                "auxiliary_accounting_category_id": 555
                            }
                        ],
                        "auxiliary_accounting_category_ids": [
                            555
                        ],
                        "auxiliary_accounting_category_names": [
                            "部门"
                        ]
                    }
                },
                {
                    "department_id": 647,
                    "allocation_ratio": "67",
                    "asset_id": 0,
                    "allocation_type": "impairment",
                    "expense_title": {
                        "accountingTitleId": 12047,
                        "accountingTitleName": "111 短期投资",
                        "auxiliary_accountings": {},
                        "auxiliaries": []
                    }
                }
            ],
            "ab_id": 0,
            "current_period": "2025-10"
            }
        Returns:
            dict: 包含创建结果的字典，包含以下字段：
                - record_id: int - 新创建的资产ID
        """
        request_data = {
            "ab_id": ab_id,
            "asset_code": asset_code,
            "asset_name": asset_name,
            "asset_category_id": asset_category_id,
            "department_ids": department_ids,
            "start_use_date": start_use_date,
            "quantity": quantity,
            "depreciation_method": depreciation_method,
            "expected_periods": expected_periods,
            "original_value": original_value,
            "residual_rate": residual_rate,
            "initial_accumulated_depreciation": initial_accumulated_depreciation,
            "monthly_depreciation": monthly_depreciation,
            "asset_title": asset_title,
            "purchase_counter_title": purchase_counter_title,
            "accumulated_depreciation_title": accumulated_depreciation_title,
            "disposal_title": disposal_title,
            "depreciation_expense_title": depreciation_expense_title,
            "current_period": current_period,
            "specifications": specifications,
            "location": location,
            "tax_amount": tax_amount,
            "impairment_provision": impairment_provision,
            "remarks": remarks
        }
        # 只添加非None的字段
        optional_fields = {
            "user_id": user_id,
            "tax_title": tax_title,
            "impairment_title": impairment_title,
            "impairment_counter_title": impairment_counter_title
        }
        for key, value in optional_fields.items():
            if value is not None:
                request_data[key] = value
        
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/assets/asset_create/", request_data)

    @mcp.tool(
        name="asset_list"
    )
    def asset_list_tool(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        accounting_period: str = Field(description='账期'),
        current: int = Field(default=1, description="页码（可选，默认1）"),
        pageSize: int = Field(default=10, description="每页记录数（可选，默认10，为0则返回所有记录）"),
        asset_code: str = Field(default=None, description="资产编码（可选）,模糊查询"),
        asset_name: str = Field(default=None, description="资产名称（可选），模糊查询"),
        asset_category_id: int = Field(default=None, description="资产类别ID（可选）"),
        department_ids: List[int] = Field(default=None, description="使用部门ID列表（可选）"),
        entry_period_range: List[str] = Field(default=None, description="录入期间范围（可选）"),
        start_use_date_range: List[str] = Field(default=None, description="开始使用日期范围（可选）"),
        depreciation_method: int = Field(default=None, description="折旧方法（可选）"),
        new_asset_voucher: str = Field(default=None, description="新增资产凭证状态（可选，值：'all', 'generated', 'not_generated'）"),
        asset_ids: List[int] = Field(default=None, description="资产ID列表（可选）"),
        can_depreciate: bool = Field(default=None, description="是否可以折旧（可选）")
    ) -> dict:
        """
        分页查询资产
        补充说明：
        1，调用示例：
        1）简单查询
        {
            "current": 1,
            "pageSize": 20,
            "accounting_period": "2025-10",
            "ab_id": 20
        }
        2）带参数查询

        {
            "current": 1,
            "pageSize": 20,
            "accounting_period": "2025-10",
            "asset_code": "00001",
            "asset_name": "研发",
            "asset_category_id": 209,
            "department_ids": [
                648
            ],
            "start_use_date_range": [
                "2025-10-01",
                "2025-10-31"
            ],
            "entry_period_range": [
                "2025-10-05 00:00:00",
                "2025-10-05 00:00:00"
            ],
            "depreciation_method": 0,
            "new_asset_voucher": "all",
            "ab_id":20
        }

        Args:
            ctx: MCP上下文对象
            ab_id: 帐套ID
            current: 页码（可选，默认1）
            pageSize: 每页记录数（可选，默认10，为0则返回所有记录）
            asset_code: 资产编码（可选）
            asset_name: 资产名称（可选）
            asset_category_id: 资产类别ID（可选）
            department_ids: 使用部门ID列表（可选）
            entry_period_range: 录入期间范围（可选）
            start_use_date_range: 开始使用日期范围（可选）
            depreciation_method: 折旧方法（可选）
            new_asset_voucher: 新增资产凭证状态（可选，值：'all', 'generated', 'not_generated'）
            asset_ids: 资产ID列表（可选）
            can_depreciate: 是否可以折旧（可选）

        Returns:
            dict: 包含查询结果的字典，包含以下字段：
                - data: List[dict] - 资产列表数据
                - total: int - 总记录数
                - current: int - 当前页码
                - pageSize: int - 每页记录数
        """
        request_data = {
            "ab_id": ab_id,
            "current": current,
            "pageSize": pageSize,
            "accounting_period": accounting_period
        }
        # 只添加非None的字段
        optional_fields = {
            "asset_code": asset_code,
            "asset_name": asset_name,
            "asset_category_id": asset_category_id,
            "department_ids": department_ids,
            "entry_period_range": entry_period_range,
            "start_use_date_range": start_use_date_range,
            "depreciation_method": depreciation_method,
            "new_asset_voucher": new_asset_voucher,
            "asset_ids": asset_ids,
            "can_depreciate": can_depreciate
        }
        for key, value in optional_fields.items():
            if value is not None:
                request_data[key] = value
        
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/assets/asset_list/", request_data)

    @mcp.tool(
        name="asset_update",
        description="更新资产"
    )
    def asset_update_tool(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        id: int = Field(description="资产ID（主键）"),
        asset_code: str = Field(default=None, description="资产编码（可选）"),
        asset_name: str = Field(default=None, description="资产名称（可选）"),
        asset_category_id: int = Field(default=None, description="资产类别ID（可选）"),
        department_ids: List[int] = Field(default=None, description="资产使用部门ID列表（可选）"),
        start_use_date: str = Field(default=None, description="开始使用日期，格式：YYYY-MM-DD（可选）"),
        quantity: int = Field(default=None, description="数量（可选）"),
        depreciation_method: int = Field(default=None, description="折旧方法（枚举值，可选）"),
        expected_periods: int = Field(default=None, description="预计使用期数（可选）"),
        original_value: float = Field(default=None, description="原值（可选）"),
        residual_rate: float = Field(default=None, description="残值率%（可选）"),
        initial_accumulated_depreciation: float = Field(default=None, description="期初累计折旧（可选）"),
        monthly_depreciation: float = Field(default=None, description="月折旧额（可选）"),
        asset_title: dict = Field(default=None, description="固定资产科目信息（可选）"),
        purchase_counter_title: dict = Field(default=None, description="资产购入对方科目信息（可选）"),
        accumulated_depreciation_title: dict = Field(default=None, description="累计折旧科目信息（可选）"),
        disposal_title: dict = Field(default=None, description="资产清理科目信息（可选）"),
        depreciation_expense_title: List[dict] = Field(default=None, description="折旧费用科目分摊列表（可选）"),
        specifications: str = Field(default=None, description="规格型号（可选）"),
        location: str = Field(default=None, description="存放地点（可选）"),
        user_id: int = Field(default=None, description="使用人ID（可选）"),
        tax_amount: float = Field(default=None, description="税额（可选）"),
        impairment_provision: float = Field(default=None, description="减值准备（可选）"),
        tax_title: dict = Field(default=None, description="税金科目信息（可选）"),
        impairment_title: dict = Field(default=None, description="减值准备科目信息（可选）"),
        impairment_counter_title: List[dict] = Field(default=None, description="减值准备对方科目分摊列表（可选）"),
        remarks: str = Field(default=None, description="备注（可选）")
    ) -> dict:
        """
        更新资产

        要更新哪一个字段就传递哪一个字段的信息，不更新就别传递。
        
        补充信息：
            1,asset_title,purchase_counter_title,tax_title,accumulated_depreciation_title,disposal_title,impairment_title格式：
           {
               "accountingTitleId": 10690, //科目id
               "accountingTitleName": "1002 银行存款", //科目名称
               "auxiliaries": [ //辅助情况
                   {
                       "id": 454,
                       "code": "B003",
                       "name": "农业银行专用户",
                       "auxiliary_accounting_category_id": 502
                   }
               ]
           }
           2,depreciation_expense_title,impairment_counter_title，列表中的数据结构示例:
           {
            "asset_id": 123, // (必填，此字段为了兼容而保留，固定等于0即可)
            "department_id" 123, //分摊部门ID（辅助核算类别为'部门'的辅助id)
            "allocation_type": "depreciation", //分摊类型(枚举：depreciation-固定资产科目,impairment-减值准备分摊)
            "allocation_ratio":20, //分摊比例（这里表示20%),
            "expense_title": { // 费用科目
               "accountingTitleId": 10690, //科目id
               "accountingTitleName": "1002 银行存款", //科目名称
               "auxiliaries": [ //辅助情况
                   {
                       "id": 454,
                       "code": "B003",
                       "name": "农业银行专用户",
                       "auxiliary_accounting_category_id": 502
                   }
               ]
              }
           }
           这里注意分摊比例，每一项总和要等于100

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
            "asset_code": asset_code,
            "asset_name": asset_name,
            "asset_category_id": asset_category_id,
            "department_ids": department_ids,
            "start_use_date": start_use_date,
            "quantity": quantity,
            "depreciation_method": depreciation_method,
            "expected_periods": expected_periods,
            "original_value": original_value,
            "residual_rate": residual_rate,
            "initial_accumulated_depreciation": initial_accumulated_depreciation,
            "monthly_depreciation": monthly_depreciation,
            "asset_title": asset_title,
            "purchase_counter_title": purchase_counter_title,
            "accumulated_depreciation_title": accumulated_depreciation_title,
            "disposal_title": disposal_title,
            "depreciation_expense_title": depreciation_expense_title,
            "specifications": specifications,
            "location": location,
            "user_id": user_id,
            "tax_amount": tax_amount,
            "impairment_provision": impairment_provision,
            "tax_title": tax_title,
            "impairment_title": impairment_title,
            "impairment_counter_title": impairment_counter_title,
            "remarks": remarks
        }
        for key, value in optional_fields.items():
            if value is not None:
                request_data[key] = value
        
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/assets/asset_update/", request_data)

    @mcp.tool(
        name="asset_batch_delete",
        description="批量删除资产"
    )
    def asset_batch_delete_tool(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        ids: List[int] = Field(description="要删除的资产ID列表")
    ) -> dict:
        """
        批量删除资产

        Args:
            ctx: MCP上下文对象
            ids: 要删除的资产ID列表

        Returns:
            dict: 包含删除结果的字典，包含以下字段：
                - affect_rows: int - 影响的行数
        """
        request_data = {
            "ab_id": ab_id,
            "ids": ids
        }
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/assets/asset_batch_delete/", request_data)

    @mcp.tool(name="asset_batch_create")
    def asset_batch_create_tool(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        assets: List[dict] = Field(description="批量新增的资产列表,数据结构参考单个新增的参数,单个参数的ab_id可以不传递")
    ) -> dict:
        """
        批量新增资产

        补充信息：
            每个资产项目的数据结构参考asset_create_tool的参数说明

        Returns:
            dict: 包含成功创建的记录ID列表和错误信息的字典，包含以下字段：
                - success: bool - 请求是否成功
                - message: str - 返回消息说明
                - data: dict - 创建结果数据，包含：
                    - created_ids: List[int] - 成功创建的资产ID列表
                    - errors: List[dict] - 创建失败的错误信息列表
        """
        request_data = {
            "ab_id": ab_id,
            "assets": assets,
        }
        
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/assets/asset_batch_create/", request_data)

    @mcp.tool(
        name="asset_depreciation_plan_list",
        description="分页查询固定资产折旧计划"
    )
    def asset_depreciation_plan_list_tool(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        asset_id: int = Field(description="固定资产ID"),
        current: int = Field(default=1, description="页码（可选，默认1）"),
        pageSize: int = Field(default=10, description="每页记录数（可选，默认10，为0则返回所有记录）")
    ) -> dict:
        """
        分页查询固定资产折旧计划

        补充说明：
        调用示例：
        {
            "ab_id": 20,
            "asset_id": 123,
            "current": 1,
            "pageSize": 10
        }

        Args:
            ctx: MCP上下文对象
            ab_id: 帐套ID
            asset_id: 固定资产ID
            current: 页码（可选，默认1）
            pageSize: 每页记录数（可选，默认10，为0则返回所有记录）

        Returns:
            dict: 包含查询结果的字典，包含以下字段：
                - data: List[dict] - 折旧计划列表数据，每个项目包含：
                    - id: int - 主键
                    - asset_id: int - 固定资产ID
                    - period: str - 期间（格式：YYYY-MM）
                    - depreciation_amount: float - 折旧额
                - total: int - 总记录数
                - current: int - 当前页码
                - pageSize: int - 每页记录数
        """
        request_data = {
            "ab_id": ab_id,
            "asset_id": asset_id,
            "current": current,
            "pageSize": pageSize
        }
        
        return config.handle_api_request(ctx, f"{config.backend_base_url}/api/assets/asset_depreciation_plan_list/", request_data)

    return mcp