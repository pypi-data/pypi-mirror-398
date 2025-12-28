# 首先应用 PyInstaller 修复
import argparse
import sys
import traceback
import os

# 在Windows上设置Python编码为UTF-8
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from config import config
from fastmcp import FastMCP
from logging_config import setup_logger, get_log_info

# 初始化全局logger
logger = setup_logger(name="da_mcp_server")

# 记录导入模块的详细信息
logger.debug("开始导入MCP服务器模块...")
try:
    from settings.__main__ import register_settings_tools
    logger.debug("成功导入 register_settings_tools")
except ImportError as e:
    logger.error(f"导入 register_settings_tools 失败: {e}")
    logger.debug(f"导入错误的详细堆栈: {traceback.format_exc()}")
    raise
# 导入其他模块并记录详细日志
try:
    logger.debug("尝试导入 voucher_mgmt.__main__")
    from voucher_mgmt.__main__ import register_voucher_mgmt_tools
    logger.debug("成功导入 register_voucher_mgmt_tools")
except ImportError as e:
    logger.error(f"导入 register_voucher_mgmt_tools 失败: {e}")
    logger.debug(f"导入错误的详细堆栈: {traceback.format_exc()}")
    raise

try:
    logger.debug("尝试导入 basic_data.__main__")
    from basic_data.__main__ import register_basic_data_tools
    logger.debug("成功导入 register_basic_data_tools")
except ImportError as e:
    logger.error(f"导入 register_basic_data_tools 失败: {e}")
    logger.debug(f"导入错误的详细堆栈: {traceback.format_exc()}")
    raise

try:
    logger.debug("尝试导入 ledger_mgmt")
    from ledger_mgmt import register_ledger_mgmt_tools
    logger.debug("成功导入 register_ledger_mgmt_tools")
except ImportError as e:
    logger.error(f"导入 register_ledger_mgmt_tools 失败: {e}")
    logger.debug(f"导入错误的详细堆栈: {traceback.format_exc()}")
    raise

try:
    logger.debug("尝试导入 financial_reports")
    from financial_reports import register_financial_report_tools, register_financial_report_query_tools, register_calculation_formula_tools
    logger.debug("成功导入 financial_reports 模块")
except ImportError as e:
    logger.error(f"导入 financial_reports 模块失败: {e}")
    logger.debug(f"导入错误的详细堆栈: {traceback.format_exc()}")
    raise

try:
    logger.debug("尝试导入 financial_reports.cash_flow_mapping_tools")
    from financial_reports.cash_flow_mapping_tools import register_cash_flow_mapping_tools
    logger.debug("成功导入 register_cash_flow_mapping_tools")
except ImportError as e:
    logger.error(f"导入 register_cash_flow_mapping_tools 失败: {e}")
    logger.debug(f"导入错误的详细堆栈: {traceback.format_exc()}")
    raise

try:
    logger.debug("尝试导入 file_manager")
    from file_manager import register_file_tools
    logger.debug("成功导入 register_file_tools")
except ImportError as e:
    logger.error(f"导入 register_file_tools 失败: {e}")
    logger.debug(f"导入错误的详细堆栈: {traceback.format_exc()}")
    raise

try:
    logger.debug("尝试导入 cashier.__main__")
    from cashier.__main__ import register_cashier_tools
    logger.debug("成功导入 register_cashier_tools")
except ImportError as e:
    logger.error(f"导入 register_cashier_tools 失败: {e}")
    logger.debug(f"导入错误的详细堆栈: {traceback.format_exc()}")
    raise

try:
    logger.debug("尝试导入 assets.__main__")
    from assets.__main__ import register_assets_tools
    logger.debug("成功导入 register_assets_tools")
except ImportError as e:
    logger.error(f"导入 register_assets_tools 失败: {e}")
    logger.debug(f"导入错误的详细堆栈: {traceback.format_exc()}")
    raise

try:
    logger.debug("尝试导入 home_statistic.__main__")
    from home_statistic.__main__ import register_home_statistic_tools
    logger.debug("成功导入 register_home_statistic_tools")
except ImportError as e:
    logger.error(f"导入 register_home_statistic_tools 失败: {e}")
    logger.debug(f"导入错误的详细堆栈: {traceback.format_exc()}")
    raise

try:
    logger.debug("尝试导入 file_upload_mcp.file_upload_tools")
    from file_upload_mcp.file_upload_tools import register_file_upload_tools
    logger.debug("成功导入 register_file_upload_tools")
except ImportError as e:
    logger.error(f"导入 register_file_upload_tools 失败: {e}")
    logger.debug(f"导入错误的详细堆栈: {traceback.format_exc()}")
    raise

try:
    logger.debug("尝试导入 financial_closing.__main__")
    from financial_closing.__main__ import register_financial_closing_tools
    logger.debug("成功导入 register_financial_closing_tools")
except ImportError as e:
    logger.error(f"导入 register_financial_closing_tools 失败: {e}")
    logger.debug(f"导入错误的详细堆栈: {traceback.format_exc()}")
    raise


# Stateful server (maintains session state)
try:
    logger.debug("开始创建 FastMCP 实例...")
    mcp = FastMCP("da_mcp_server")
    logger.info("✅ FastMCP 实例创建成功")
    logger.debug(f"MCP 服务器名称: da_mcp_server")
    logger.debug(f"MCP 服务器对象: {mcp}")
except Exception as e:
    logger.error(f"❌ 创建 FastMCP 实例失败: {e}")
    logger.debug(f"创建实例失败的详细堆栈: {traceback.format_exc()}")
    raise

# 注册所有工具模块并记录详细日志
tool_registrations = [
    ("设置管理工具", register_settings_tools),
    ("凭证管理工具", register_voucher_mgmt_tools),
    ("基础数据管理工具", register_basic_data_tools),
    ("账簿管理工具", register_ledger_mgmt_tools),
    ("报表相关工具", register_financial_report_tools),
    ("财务报表查询工具", register_financial_report_query_tools),
    ("计算公式管理工具", register_calculation_formula_tools),
    ("文件管理工具", register_file_tools),
    ("出纳管理工具", register_cashier_tools),
    ("资产管理工具", register_assets_tools),
    ("现金流量映射工具", register_cash_flow_mapping_tools),
    ("首页统计工具", register_home_statistic_tools),
    ("文件上传工具", register_file_upload_tools),
    ("结账管理工具", register_financial_closing_tools),
]

logger.info("开始注册MCP工具模块...")
for tool_name, register_func in tool_registrations:
    try:
        logger.debug(f"正在注册 {tool_name}...")
        mcp = register_func(mcp)
        logger.info(f"✅ {tool_name} 注册成功")
    except Exception as e:
        logger.error(f"❌ {tool_name} 注册失败: {e}")
        logger.debug(f"{tool_name} 注册失败的详细堆栈: {traceback.format_exc()}")
        raise

logger.info("🎉 所有MCP工具模块注册完成")

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='DeepSea Accounting MCP Server - 支持运行时配置的服务端'
    )

    # 后端服务配置参数
    parser.add_argument(
        '--backend-url',
        help='后端服务URL (默认: http://localhost:8000)',
        default=None
    )
    parser.add_argument(
        '--backend-token',
        help='后端服务访问令牌',
        default=None
    )

    # HTTP 服务器配置参数
    transport_group = parser.add_argument_group('HTTP 服务器配置')
    transport_group.add_argument(
        '--host',
        help='HTTP 服务器主机地址 (默认: localhost)',
        default='localhost'
    )
    transport_group.add_argument(
        '--port',
        type=int,
        help='HTTP 服务器端口 (默认: 8080)',
        default=8080
    )

  
    # 日志配置参数
    log_group = parser.add_argument_group('日志配置')
    log_group.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式 (等价于 --log-level DEBUG)'
    )
    log_group.add_argument(
        '--log-dir',
        help='日志文件目录 (默认: ./logs)',
        default='./logs'
    )
    log_group.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='日志级别 (默认: INFO)',
        default='INFO'
    )
    log_group.add_argument(
        '--console-log',
        action='store_true',
        default=True,
        help='启用控制台日志输出 (默认启用)'
    )
    log_group.add_argument(
        '--no-console-log',
        action='store_true',
        help='禁用控制台日志输出'
    )
    log_group.add_argument(
        '--file-log',
        action='store_true',
        default=True,
        help='启用文件日志输出 (默认启用)'
    )
    log_group.add_argument(
        '--no-file-log',
        action='store_true',
        help='禁用文件日志输出'
    )

    return parser.parse_args()


def apply_command_line_config(args):
    """应用命令行参数配置"""
    logger.debug("开始应用命令行参数配置...")
    config_changes = []

    # 配置后端服务
    if args.backend_url or args.backend_token:
        logger.debug(f"配置后端服务 - URL: {args.backend_url}, Token: {'已设置' if args.backend_token else '未设置'}")
        try:
            config.configure_backend(args.backend_url, args.backend_token)
            if args.backend_url:
                config_changes.append(f"后端服务URL: {args.backend_url}")
                logger.debug(f"后端服务URL配置成功: {args.backend_url}")
            if args.backend_token:
                config_changes.append("后端服务Token: 已设置")
                logger.debug("后端服务Token配置成功")
        except Exception as e:
            logger.error(f"配置后端服务失败: {e}")
            logger.debug(f"配置后端服务失败的详细堆栈: {traceback.format_exc()}")
            raise
  
    logger.debug(f"命令行参数配置完成，变更项: {config_changes}")
    return config_changes

def main():
    try:
        # 解析命令行参数
        args = parse_arguments()
        
        # 处理日志配置的互斥参数
        console_log = args.console_log and not args.no_console_log
        file_log = args.file_log and not args.no_file_log
        
        # 设置日志级别（debug模式优先）
        log_level = 'DEBUG' if args.debug else args.log_level
        
        # 重新配置日志系统
        logger = setup_logger(
            name="da_mcp_server",
            debug_mode=args.debug,
            log_dir=args.log_dir,
            console_log=console_log,
            file_log=file_log,
            log_level=log_level
        )
        
        logger.info("🚀 DeepSea Accounting MCP Server 启动中...")
        logger.debug("=" * 60)
        logger.debug("开始初始化MCP服务器")
        logger.debug(f"命令行参数: {vars(args)}")
        
        # 显示日志配置信息
        log_info = get_log_info()
        if file_log and log_info['directory_exists']:
            logger.info("📂 日志文件目录信息:")
            for file_info in log_info['files']:
                if 'error' in file_info:
                    logger.warning(f"  ⚠️  {file_info['name']}: {file_info['error']}")
                else:
                    logger.info(f"  📄 {file_info['name']}: {file_info['size']} 字节")

        # 应用命令行配置
        logger.debug("应用命令行配置...")
        config_changes = apply_command_line_config(args)

        # 输出配置信息
        if config_changes:
            print("命令行配置已应用:")
            for change in config_changes:
                print(f"  - {change}")
                logger.info(f"配置变更: {change}")
            print()

        # 显示当前配置
        logger.debug("获取当前服务配置...")
        try:
            current_config = config.get_config()
            logger.debug("当前配置获取成功")
            print("当前服务配置:")
            print(f"  后端服务: {current_config['data']['backend']['base_url']}")
            print(f"  文件上传服务: {current_config['data']['upload']['base_url']}")
            if file_log:
                print(f"  📁 日志目录: {log_info['log_directory']}")
            print()

            logger.info(f"后端服务配置: {current_config['data']['backend']['base_url']}")
            logger.info(f"文件上传服务配置: {current_config['data']['upload']['base_url']}")
            
        except Exception as e:
            logger.error(f"获取当前配置失败: {e}")
            logger.debug(f"获取配置失败的详细堆栈: {traceback.format_exc()}")
            print(f"警告: 无法获取服务配置 - {e}")
            print()

        logger.info("准备启动MCP服务器...")
        logger.info("传输方式: streamable-http")
        logger.info(f"服务器名称: da_mcp_server")
        logger.info(f"HTTP 服务器地址: http://{args.host}:{args.port}")
        print(f"启动MCP服务器 (HTTP模式) - http://{args.host}:{args.port}")
        logger.debug("开始运行 MCP 服务器 (streamable-http 模式)...")
        
        # 运行 HTTP 服务器
        mcp.run(
            transport="streamable-http",
            host=args.host,
            port=args.port
        )
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")
        print("\nMCP服务器已关闭")
        
    except Exception as e:
        # 确保logger已初始化
        if 'logger' not in globals():
            logger = setup_logger(name="da_mcp_server")
        
        # 添加详细的调试信息
        import os
        logger.error(f"=== MCP服务器启动失败调试信息 ===")
        logger.error(f"错误信息: {e}")
        logger.error(f"错误类型: {type(e).__name__}")
        logger.error(f"Python版本: {sys.version}")
        logger.error(f"系统平台: {sys.platform}")
        logger.error(f"当前工作目录: {os.getcwd()}")
        logger.error(f"PYTHONIOENCODING: {os.environ.get('PYTHONIOENCODING', 'Not set')}")
        logger.error(f"sys.stdout编码: {getattr(sys.stdout, 'encoding', 'Unknown')}")
        logger.error(f"sys.stderr编码: {getattr(sys.stderr, 'encoding', 'Unknown')}")
        logger.error(f"sys.stdout是否关闭: {getattr(sys.stdout, 'closed', 'Unknown')}")
        logger.error(f"sys.stderr是否关闭: {getattr(sys.stderr, 'closed', 'Unknown')}")
        
        # 尝试用print输出调试信息
        try:
            print(f"[DEBUG] 错误信息: {e}")
            print(f"[DEBUG] 错误类型: {type(e).__name__}")
        except Exception as print_error:
            print(f"[DEBUG] print也失败了: {print_error}")
            
        logger.debug(f"启动失败的详细堆栈: {traceback.format_exc()}")
        
        # 检查是否是-32000错误相关的MCP错误
        if "-32000" in str(e) or "McpError" in str(type(e).__name__):
            logger.error("🔍 检测到MCP错误 -32000，这通常表示:")
            logger.error("  1. MCP协议通信问题")
            logger.error("  2. HTTP传输配置问题")
            logger.error("  3. 客户端-服务器握手失败")
            logger.error("  4. JSON-RPC协议错误")
            logger.error("")
            logger.error("建议检查:")
            logger.error("  - 确保客户端正确配置了HTTP传输")
            logger.error("  - 检查Python环境和依赖包")
            logger.error("  - 验证防火墙和权限设置")
            logger.error("  - 查看客户端的错误日志")
            logger.error("  - 检查日志文件中的详细错误信息")
            if file_log:
                logger.error(f"  - 日志文件位置: {args.log_dir}")
        
        print(f"\n❌ MCP服务器启动失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        if args.debug:
            print(f"\n详细错误信息:\n{traceback.format_exc()}")
        if 'args' in locals() and file_log:
            print(f"\n📝 详细日志请查看: {args.log_dir}/")
        sys.exit(1)

# Run server with streamable_http transport
if __name__ == "__main__":
    main()