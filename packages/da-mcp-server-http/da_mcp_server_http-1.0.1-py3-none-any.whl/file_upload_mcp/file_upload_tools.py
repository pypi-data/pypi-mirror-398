"""
文件上传工具
基于 FastMCP 的文件上传工具，支持上传文件到远程服务器
"""

import os
import mimetypes
from pathlib import Path
import requests
from typing import Dict, Any

from fastmcp import Context
from pydantic import Field
from config import config

# 文件上传服务配置
UPLOAD_TOKEN = os.getenv("UPLOAD_TOKEN", "")


def register_file_upload_tools(mcp):
    """注册文件上传相关的工具"""

    @mcp.tool(
        name="upload_file",
        description="上传文件到远程服务器。需要提供文件的本地绝对路径。"
    )
    def upload_file(
        ctx: Context,
        file_path: str = Field(..., description="要上传的文件的本地绝对路径，例如: /home/user/document.pdf")
    ) -> Dict[str, Any]:
        """上传文件到远程服务器"""
        return handle_upload_file(file_path)

    @mcp.tool(
        name="get_file_download_url",
        description="根据文件ID获取文件的下载链接。返回的下载链接格式为: {backend_base_url}/api/file/{file_id}"
    )
    def get_file_download_url(
        ctx: Context,
        file_id: str = Field(..., description="文件ID，通常是上传文件后返回的id字段")
    ) -> Dict[str, Any]:
        """获取文件下载链接"""
        return handle_get_file_download_url(file_id)

    return mcp


def handle_upload_file(file_path: str) -> Dict[str, Any]:
    """处理文件上传请求"""
    if not file_path:
        return {
            "success": False,
            "errorCode": 400,
            "errorMessage": "未提供文件路径参数 'file_path'",
            "showType": "error"
        }

    # 验证文件路径
    path = Path(file_path).expanduser().resolve()

    if not path.exists():
        return {
            "success": False,
            "errorCode": 404,
            "errorMessage": f"文件不存在\n路径: {path}",
            "showType": "error"
        }

    if not path.is_file():
        return {
            "success": False,
            "errorCode": 400,
            "errorMessage": f"路径不是一个文件\n路径: {path}",
            "showType": "error"
        }

    # 获取文件信息
    file_name = path.name
    file_size = path.stat().st_size
    mime_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"

    # 格式化文件大小
    def format_size(size_bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    # 构建上传 URL
    url = f"{config.backend_base_url}/api/file_manager/file_upload/"

    try:
        # 准备请求头
        headers = {}
        if config.backend_token:
            headers["Authorization"] = f"Bearer {config.backend_token}"

        # 上传文件
        with open(path, "rb") as f:
            files = {"file": (file_name, f, mime_type)}
            response = requests.post(url, files=files, headers=headers, timeout=300.0)

        if response.status_code in [200, 201]:
            result = response.json()
            data = result.get("data", {})

            success_text = (
                "✅ 文件上传成功!\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📄 文件名: {data.get('name', file_name)}\n"
                f"🆔 文件ID: {data.get('id', 'N/A')}\n"
                f"🔑 文件Key: {data.get('file_key', 'N/A')}\n"
                f"📦 文件大小: {format_size(data.get('size', file_size))}\n"
                f"📋 MIME类型: {data.get('mime_type', mime_type)}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━"
            )

            return {
                "success": True,
                "data": {
                    "id": data.get('id'),
                    "name": data.get('name', file_name),
                    "file_key": data.get('file_key'),
                    "size": data.get('size', file_size),
                    "mime_type": data.get('mime_type', mime_type),
                    "url": data.get('url')
                },
                "message": success_text,
                "showType": "success"
            }
        else:
            return {
                "success": False,
                "errorCode": response.status_code,
                "errorMessage": f"上传失败 (HTTP {response.status_code})\n服务器响应:\n{response.text}",
                "showType": "error"
            }

    except requests.exceptions.ConnectionError as e:
        return {
            "success": False,
            "errorCode": 503,
            "errorMessage": f"连接错误: 无法连接到服务器\n目标地址: {config.backend_base_url}\n请检查服务器是否正在运行、主机地址和端口是否正确、网络连接是否正常",
            "showType": "error"
        }

    except requests.exceptions.Timeout as e:
        return {
            "success": False,
            "errorCode": 408,
            "errorMessage": "上传超时\n文件可能过大或网络速度较慢",
            "showType": "warning"
        }

    except Exception as e:
        return {
            "success": False,
            "errorCode": 500,
            "errorMessage": f"上传过程中发生错误\n错误信息: {str(e)}",
            "showType": "error"
        }


def handle_get_file_download_url(file_id: str) -> Dict[str, Any]:
    """处理获取文件下载链接请求"""
    if not file_id:
        return {
            "success": False,
            "errorCode": 400,
            "errorMessage": "未提供文件ID参数 'file_id'",
            "showType": "error"
        }

    # 验证文件ID格式（基本检查）
    if not isinstance(file_id, str) or not file_id.strip():
        return {
            "success": False,
            "errorCode": 400,
            "errorMessage": "文件ID格式无效，file_id 必须是非空字符串",
            "showType": "error"
        }

    file_id = file_id.strip()

    # 构建下载链接
    download_url = f"{config.backend_base_url}/api/file/{file_id}"

    # 创建成功响应
    success_text = (
        "✅ 文件下载链接获取成功!\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 文件ID: {file_id}\n"
        f"🔗 下载链接: {download_url}\n"
        f"🌐 后端服务: {config.backend_base_url}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 使用说明:\n"
        f"  - 可以直接在浏览器中打开链接进行下载\n"
        f"  - 也可以在程序中使用 HTTP GET 请求获取文件\n"
        f"  - 如果需要认证，请确保请求头包含正确的 Authorization token\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )

    return {
        "success": True,
        "data": {
            "file_id": file_id,
            "download_url": download_url,
            "backend_base_url": config.backend_base_url,
            "url_pattern": "{backend_base_url}/api/file/{file_id}"
        },
        "message": success_text,
        "showType": "success"
    }