# da_mcp_server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP Version](https://img.shields.io/badge/MCP-2024%2B%2B-orange.svg)](https://modelcontextprotocol.io/)

晨舟财务会计软件 MCP (Model Context Protocol) 服务器，为 Claude 等大语言模型提供财务会计操作的标准化接口。

## 🌟 特性

- **完整财务模块支持**：凭证管理、账簿管理、基础数据、资产管理、现金管理
- **标准化协议**：基于 MCP 协议，提供统一的工具调用接口
- **易于集成**：可快速接入支持 MCP 的 AI 应用
- **类型安全**：使用 Pydantic 进行数据验证和类型检查
- **高性能**：异步请求处理，支持缓存优化

## 📋 系统要求

- Python 3.8 或更高版本
- 晨舟财务会计软件（Windows 版本）
- 8GB RAM 或更高（推荐 16GB）

## 🚀 快速开始

### 安装

1. **克隆仓库**
```bash
git clone https://gitee.com/jlmpp/da_mcp_server.git
cd da_mcp_server
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```


### 运行服务器

```bash
# 开发模式运行
python server.py

# 或使用 MCP 客户端连接
mcp connect python server.py
```

### 连接到 Claude Desktop

在 Claude Desktop 的配置文件中添加：

```json
{
  "mcpServers": {
    "da_mcp_server": {
      "command": "uvx",
      "args": ["da-mcp-server","--backend-url","http://127.0.0.1:8000","--backend-token","xxxxxx"]
    }
  }
}
```

## 📚 功能模块

### 🔧 设置模块 (Settings)
- 会计账簿管理
- 会计期间配置
- 用户权限设置

### 📝 基础数据模块 (Basic Data)
- 会计科目管理
- 科目体系配置
- 辅助核算项目

### 💰 凭证管理模块 (Voucher Management)
- 凭证录入与修改
- 凭证查询与筛选
- 凭证审核与过账
- 凭证批量导入

### 📊 账簿管理模块 (Ledger Management)
- 总账查询
- 明细账查询
- 科目余额表
- 试算平衡表

### 🏦 现金管理模块 (Cashier)
- 现金日记账
- 银行日记账
- 资金流水查询
- 银行对账

### 🏢 资产管理模块 (Asset Management)
- 固定资产卡片
- 资产折旧计算
- 资产变动记录
- 折旧费用分配

## 🛠️ 可用工具

### 会计设置
- `configure_services` - 配置财务服务连接
- `accounting_book_list` - 获取会计账簿列表
- `accounting_standard_all` - 获取会计准则列表

### 科目管理
- `accounting_title_list` - 获取会计科目列表
- `accounting_title_update` - 更新会计科目
- `accounting_title_category_list` - 获取科目类别列表

### 辅助核算
- `auxiliary_accounting_category_list` - 获取辅助核算类别
- `auxiliary_accounting_list` - 获取辅助核算项目
- `auxiliary_accounting_batch_create` - 批量创建辅助核算项目

### 凭证操作
- `voucher_create` - 创建记账凭证
- `voucher_batch_create` - 批量创建凭证
- `get_voucher_list` - 获取凭证列表
- `generate_voucher_number` - 生成凭证号

### 账簿查询
- `get_trial_bal` - 获取试算平衡表
- `get_home_statistic` - 获取首页统计数据

### 报表功能
- `report_list` - 获取财务报表列表
- `balance_sheet_formula_list` - 资产负债表公式
- `profit_statement_formula_list` - 利润表公式
- `calculation_formula_batch_create` - 批量创建计算公式

## 🔌 API 示例

### 创建凭证

```python
# 通过 MCP 工具创建凭证
result = await mcp.call_tool("voucher_create", {
    "accounting_book_id": "book_001",
    "voucher_date": "2024-01-15",
    "voucher_type": "记账凭证",
    "entries": [
        {
            "account_title_id": "1001",
            "debit_amount": 10000.00,
            "credit_amount": 0.00,
            "description": "收到投资款"
        },
        {
            "account_title_id": "3001",
            "debit_amount": 0.00,
            "credit_amount": 10000.00,
            "description": "实收资本"
        }
    ]
})
```

### 查询科目余额

```python
# 获取科目余额表
balance = await mcp.call_tool("get_trial_bal", {
    "accounting_book_id": "book_001",
    "period": "2024-01",
    "account_title_id": "1001"
})
```

## 🏗️ 开发

### 项目结构

```
da_mcp_server/
├── server.py              # 主服务器入口
├── config.py              # 配置文件
├── logging_config.py      # 日志配置
├── requirements.txt       # Python 依赖
├── __init__.py           # 版本信息
├── settings/             # 设置模块
├── basic_data/           # 基础数据模块
├── voucher_mgmt/         # 凭证管理模块
├── ledger_mgmt/          # 账簿管理模块
├── cashier/              # 现金管理模块
├── assets/               # 资产管理模块
├── home_statistic/       # 统计模块
└── file_manager/         # 文件管理模块
```

### 添加新模块

1. 创建模块目录和 `__init__.py`
2. 创建 `__main__.py` 文件定义工具
3. 在 `server.py` 中导入并注册新模块

```python
# 示例：添加新模块
try:
    from new_module.__main__ import register_new_module_tools
    register_new_module_tools(mcp)
except ImportError as e:
    logger.error(f"导入新模块失败: {e}")
```

### 构建可执行文件

```bash
# 使用 PyInstaller 打包
pyinstaller da_mcp_server.spec

# 生成的可执行文件在 dist/ 目录下
```


## 📄 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🔗 相关链接

- [晨舟财务官网](http://www.shrycode.com)
- [Model Context Protocol 官网](https://modelcontextprotocol.io/)
- [Claude API 文档](https://docs.anthropic.com/claude)

## 📞 支持

如遇问题，请：

1. 查看 [Issues](https://github.com/yourusername/da_mcp_server/issues) 页面
2. 创建新的 Issue 描述问题
3. 联系技术支持：42601644@qq.com


---

**注意**：本服务器需要与晨舟财务会计软件配合使用。请确保已正确安装并配置晨舟财务软件。