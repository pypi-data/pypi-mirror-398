"""
配置管理模块
使用单例模式确保配置全局一致
"""

import os
import uuid
import time
import requests
import logging
import sys
import traceback
from typing import Dict, Any
from functools import wraps

# 导入日志配置
from logging_config import setup_logger

# 创建配置模块的logger
config_logger = setup_logger(name="da_mcp_server.config")

# 以下导入仅仅为了pyinstaller打包
import diskcache
import pickletools
import sqlite3
import pathvalidate
import exceptiongroup
import webbrowser
import cachetools
import _strptime

class ConfigManager:
    """配置管理器 - 单例模式"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化配置"""
        config_logger.debug("初始化配置管理器...")
        
        # 后端服务配置
        self.backend_base_url = os.getenv('BACKEND_BASE_URL', 'http://localhost:8000')
        self.backend_token = os.getenv('BACKEND_TOKEN', '')
        config_logger.debug(f"后端服务配置 - URL: {self.backend_base_url}, Token: {'已设置' if self.backend_token else '未设置'}")

        # 文件上传服务使用后端服务配置
        self.upload_base_url = self.backend_base_url
        config_logger.debug(f"文件上传服务配置: {self.upload_base_url}")


    def configure_backend(self, base_url: str = None, token: str = None) -> Dict[str, Any]:
        """配置后端服务"""
        updated = []

        if base_url is not None:
            self.backend_base_url = base_url
            self.upload_base_url = base_url  # 文件上传服务同步更新
            updated.append(f"URL: {base_url}")

        if token is not None:
            self.backend_token = token
            updated.append("Token: 已设置")

        return {
            "success": True,
            "data": {
                "base_url": self.backend_base_url,
                "token": "***" if self.backend_token else ""
            },
            "message": f"后端服务配置已更新: {'; '.join(updated)}" if updated else "配置未变更",
            "showType": "success"
        }

    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        config_info = (
            "当前服务配置:\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"后端服务:\n"
            f"  - URL: {self.backend_base_url}\n"
            f"  - Token: {'***' if self.backend_token else '未设置'}\n"
            f"文件上传服务:\n"
            f"  - URL: {self.upload_base_url}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )

        return {
            "success": True,
            "data": {
                "backend": {
                    "base_url": self.backend_base_url,
                    "token": "***" if self.backend_token else ""
                },
                "upload": {
                    "base_url": self.upload_base_url
                }
            },
            "message": config_info,
            "showType": "success"
        }

    def generate_trace_id(self):
        """生成唯一的traceId"""
        return f"mcp_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"

    def get_auth_headers(self, ctx):
        """
        从上下文中提取认证头信息

        参数:
        - ctx: 上下文对象

        返回:
        - 包含认证头的字典，如果未找到认证信息则返回None
        """
        headers = ctx.request_context.request['headers']
        headers_dict = dict(headers)

        # 将字节键值对转换为字符串
        str_headers = {}
        for key, value in headers_dict.items():
            str_key = key.decode('utf-8') if isinstance(key, bytes) else key
            str_value = value.decode('utf-8') if isinstance(value, bytes) else value
            str_headers[str_key] = str_value

        # 获取认证令牌
        authorization = str_headers.get('authorization')
        if not authorization:
            return None

        return {
            'Authorization': authorization,
            'Content-Type': 'application/json'
        }
    def handle_api_request(self, ctx, api_url: str, request_data: Dict = None,
                          timeout: int = 30, method: str = 'POST'):
        """
        处理API请求的通用函数

        参数:
        - api_url: API地址
        - request_data: 请求数据
        - timeout: 超时时间
        - method: 请求方法

        返回:
        - 响应对象或错误信息
        """
        config_logger.debug(f"开始处理API请求: {method} {api_url}")
        config_logger.debug(f"请求超时时间: {timeout}秒")
        
        # 获取认证头
        headers = self.get_auth_headers(ctx)
        config_logger.debug(f"认证头: {headers}")
        
        try:
            if method.upper() == 'POST':
                config_logger.debug(f"发送POST请求到: {api_url}")
                if request_data:
                    config_logger.debug(f"请求数据大小: {len(str(request_data))} 字符")
                    # 在调试模式下记录请求内容（但不要记录敏感信息）
                    if config_logger.isEnabledFor(logging.DEBUG):
                        safe_data = {k: v for k, v in request_data.items() 
                                   if not any(sensitive in k.lower() 
                                            for sensitive in ['password', 'token', 'secret', 'key'])}
                        config_logger.debug(f"请求数据(安全过滤后): {safe_data}")
                response = requests.post(
                    api_url,
                    headers=headers,
                    json=request_data or {},
                    timeout=timeout
                )
                config_logger.debug(f"POST请求已发送，等待响应...")
            else:  # GET
                config_logger.debug(f"发送GET请求到: {api_url}")
                response = requests.get(
                    api_url,
                    headers=headers,
                    timeout=timeout
                )
                config_logger.debug(f"GET请求已发送，等待响应...")

            config_logger.debug(f"收到响应 - 状态码: {response.status_code}")
            config_logger.debug(f"响应头: {dict(response.headers)}")
            
            # 记录响应大小和内容
            response_text = response.text
            config_logger.debug(f"响应大小: {len(response_text)} 字符")
            
            if not response_text.strip():
                config_logger.warning("服务器返回空响应")
                return {
                    "success": False,
                    "errorCode": response.status_code,
                    "errorMessage": "服务器返回空响应",
                    "showType": "error"
                }

            # 处理响应
            try:
                response_data = response.json()
                config_logger.debug("成功解析JSON响应")
            except ValueError as e:
                config_logger.error(f"JSON解析失败: {e}")
                config_logger.debug(f"原始响应内容: {response_text[:500]}...")  # 只记录前500字符
                return {
                    "success": False,
                    "errorCode": 500,
                    "errorMessage": f"服务器响应格式错误: {str(e)}",
                    "showType": "error"
                }

            # 如果后端响应包含traceId，则移除
            if "traceId" in response_data:
                del response_data["traceId"]
                config_logger.debug("已移除traceId字段")

            # 如果后端响应不包含showType，则根据success状态设置
            if "showType" not in response_data:
                if response_data.get("success", False):
                    response_data["showType"] = "success"
                    config_logger.debug("响应成功，设置showType为success")
                else:
                    response_data["showType"] = "error"
                    config_logger.debug("响应失败，设置showType为error")

            config_logger.debug(f"处理后的响应数据: {response_data}")
            return response_data

        except requests.exceptions.ConnectionError as e:
            config_logger.error(f"连接错误: 无法连接到后端服务 {api_url}")
            config_logger.debug(f"连接错误详情: {e}")
            config_logger.debug(f"连接错误堆栈: {traceback.format_exc()}")
            return {
                "success": False,
                "errorCode": 503,
                "errorMessage": "无法连接到后端服务，请确保服务正在运行",
                "showType": "error"
            }
        except requests.exceptions.Timeout as e:
            config_logger.error(f"请求超时: {api_url} (超时时间: {timeout}秒)")
            config_logger.debug(f"超时错误详情: {e}")
            config_logger.debug(f"超时错误堆栈: {traceback.format_exc()}")
            return {
                "success": False,
                "errorCode": 408,
                "errorMessage": "请求超时，请稍后重试",
                "showType": "warning"
            }
        except Exception as e:
            config_logger.error(f"API请求处理过程中发生未知错误: {type(e).__name__}: {e}")
            config_logger.debug(f"未知错误的详细堆栈: {traceback.format_exc()}")
            
            # 特别关注可能导致MCP错误-32000的异常
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['mcp', 'http', 'protocol', 'transport', 'json', 'rpc']):
                config_logger.error("🔍 检测到可能导致MCP错误-32000的问题:")
                config_logger.error(f"  错误类型: {type(e).__name__}")
                config_logger.error(f"  错误信息: {e}")
                config_logger.error("  这可能影响MCP协议通信")
            
            return {
                "success": False,
                "errorCode": 500,
                "errorMessage": f"发生未知错误: {str(e)}",
                "showType": "error"
            }


# 创建全局配置管理器实例
config = ConfigManager()