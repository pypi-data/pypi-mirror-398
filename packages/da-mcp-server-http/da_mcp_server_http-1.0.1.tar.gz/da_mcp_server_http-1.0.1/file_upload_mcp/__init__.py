"""
文件上传模块
包含文件上传到远程服务器的功能
"""

from .file_upload_tools import register_file_upload_tools

__all__ = ['register_file_upload_tools']